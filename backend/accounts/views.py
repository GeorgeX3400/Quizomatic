from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from django.http import JsonResponse
from .forms import CustomUserCreationForm, CustomLoginForm
from .serializers import *
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import io
from django.middleware.csrf import get_token
import subprocess
from .models import Chat, ChatMessage
from .serializers import ChatMessageSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import re
from rest_framework_simplejwt.tokens import RefreshToken

from pathlib import Path
from django.conf import settings

from .ocr_utils import extract_pages, write_json_pages
from datetime import datetime


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard')
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')



# Authentication views:

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]   
    

class ChatsView(generics.ListAPIView):  
   queryset = Chat.objects.all()
   permission_classes = (IsAuthenticated, )
   serializer_class = ChatSerializer

   def get_queryset(self):
       return Chat.objects.filter(user=self.request.user)
   
   def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ChatCreateView(generics.CreateAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class DocumentAddView(generics.CreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def perform_create(self, serializer):
                # 1) Validate that chat_id was provided
        chat_id = self.request.data.get("chat_id")
        if not chat_id:
            raise serializers.ValidationError({"chat_id": "This field is required."})

        # 2) Ensure the chat belongs to the current user
        chat = get_object_or_404(Chat, id=chat_id, user=self.request.user)

        # 3) Ensure a file was actually uploaded
        file_obj = self.request.FILES.get("file")
        if not file_obj:
            raise serializers.ValidationError({"file": "No file was submitted."})

        # 4) Save the Document instance (Django will write the file to disk under MEDIA_ROOT/<username>/uploaded/…)
        doc = serializer.save(
            chat=chat,
            name=file_obj.name,
            content_type=file_obj.content_type
        )

        # 5) Build the absolute filesystem path to the uploaded file
        #    `doc.file.name` might be something like "alexn/uploaded/mydoc.pdf"
        file_path = Path(settings.MEDIA_ROOT) / doc.file.name

        # 6) Run OCR on that single file; this returns a list of page‐dicts
        try:
            pages = extract_pages(str(file_path))
        except Exception as e:
            # If OCR fails for any reason, just store an empty list (or log e if you like)
            pages = []

        # 7) Save the OCR’d JSON into the Document record
        doc.extracted_json = pages
        #    (Optional) also store a flattened text blob:
        doc.extracted_text = "\n\n".join(p["text"] for p in pages)
        doc.save()

        # 8) Write a JSON file to MEDIA_ROOT/<username>/processed/
        username = chat.user.username
        processed_dir = Path(settings.MEDIA_ROOT) / username / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Name the output file based on the original filename (no extension) + timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(doc.name).stem  # e.g. "mydoc"
        out_filename = f"{base_name}_pages_{timestamp}.json"
        out_path = processed_dir / out_filename

        write_json_pages(pages, out_path)


class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Document.objects.filter(chat__user=self.request.user)
        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            qs = qs.filter(chat__id=chat_id)
        return qs

class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        """
        List all messages in a chat (user + assistant), ordered by timestamp,
        but strip out any <think>…</think> tags from assistant messages.
        """
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        msgs = chat.messages.order_by('timestamp')
        serializer = ChatMessageSerializer(msgs, many=True)
        data = serializer.data

        # Clean assistant messages
        for item in data:
            if item['role'] == 'assistant':
                item['content'] = re.sub(
                    r'<think>[\s\S]*?</think>',
                    '',
                    item['content']
                ).strip()

        return Response(data)

    def post(self, request, chat_id):
        """
        Save the user message, call Ollama to generate an assistant reply,
        clean out <think>…</think>, save it, and return it.
        """
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        user_text = request.data.get('message', '').strip()
        if not user_text:
            return Response(
                {'detail': 'No message provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1) Save user message
        ChatMessage.objects.create(
            chat=chat,
            role='user',
            content=user_text
        )

        # 2) Call Ollama Chat Completions API
        import requests
        try:
            messages = [
                {
                "role": "system",
                "content": "You are a helpful assistant."
                }
            ]

            # 2b) Pull every past turn from the DB, ordered chronologically
            past = ChatMessage.objects.filter(chat=chat).order_by("timestamp")
            for msg in past:
                # msg.role is 'user' or 'assistant'
                # msg.content has already been cleaned in your GET
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # 2c) Finally add the *new* user message
            messages.append({"role": "user", "content": user_text})

            # 3) SEND to Ollama with the full context
            ollama_resp = requests.post(
                "http://127.0.0.1:11434/v1/chat/completions",
                json={
                    "model": "qwen3:8B",
                    "messages": messages
                },
                timeout=60
            )
            ollama_resp.raise_for_status()
            payload = ollama_resp.json()
            raw_reply = payload["choices"][0]["message"]["content"]
        except Exception as e:
            return Response(
                {'detail': 'LLM generation error', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 3) Clean and save assistant message
        assistant_text = re.sub(
            r'<think>[\s\S]*?</think>',
            '',
            raw_reply
        ).strip()

        ChatMessage.objects.create(
            chat=chat,
            role='assistant',
            content=assistant_text
        )

        # 4) Return the cleaned reply
        return Response({'reply': assistant_text})
    
import json
import requests
class QuizGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        # 1) Verify the chat belongs to this user
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

        # 2) Parse quiz parameters
        num_q = int(request.data.get("num_questions", 5))
        difficulty = request.data.get("difficulty", "easy")

        # 3) Build the “messages” payload for Ollama, injecting each document’s extracted_json
        messages = [
            { "role": "system", "content": "You are a helpful assistant." }
        ]

        for doc in chat.documents.all():
            if doc.extracted_json:
                # Serialize the OCR’d JSON pages into one string
                json_str = json.dumps(doc.extracted_json, ensure_ascii=False)
                system_msg = f"Document '{doc.name}' OCR contents (pages):\n{json_str}"
                messages.append({ "role": "system", "content": system_msg })

        # 4) Append the quiz‐generation instruction as a user message
        # 4) Append the quiz‐generation instruction as a user message
        quiz_prompt = (
            f"Generate a quiz of {difficulty} difficulty with {num_q} questions. "
            "Each question must be strictly multiple‐choice with exactly four options. "
            "Respond in JSON only, in this format per question array element: "
            "{ \"question\": \"Your question text here\", "
            "\"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"], "
            "\"answer\": \"<one of the four options exactly>\" }. "
            "Do not include any true/false questions, and do not add any extra text—output only the JSON array."
        )

        messages.append({ "role": "user", "content": quiz_prompt })

        # 5) Send the full context to Ollama’s chat API
        try:
            ollama_resp = requests.post(
                "http://127.0.0.1:11434/v1/chat/completions",
                json={
                    "model": "qwen3:8B",
                    "messages": messages
                },
                timeout=1000
            )
            ollama_resp.raise_for_status()
            payload = ollama_resp.json()
            raw_quiz = payload["choices"][0]["message"]["content"]
        except Exception as e:
            return Response(
                { "detail": "LLM generation error", "error": str(e) },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 6) Strip out any <think>…</think> tags (if present)
        quiz_text = re.sub(r"^.*?</think>\s*", "", raw_quiz, flags=re.DOTALL).strip()

        # 7) Save the quiz as a new assistant message in ChatMessage
        quiz_msg = ChatMessage.objects.create(
            chat=chat,
            role="assistant",
            content=quiz_text
        )

        # 8) Serialize that new message and return it
        serializer = ChatMessageSerializer(quiz_msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class SubmitQuizView(APIView):
    """
    POST /chats/<chat_id>/submit-quiz/
    Payload: {
      "quiz": [ { "question": "...", "options": [ "...", "...", ... ] }, ... ],
      "answers": {
         "0": "<the option string or index chosen>",
         "1": "<…>",
         "2": "<…>"
      }
    }
    This saves a JSON file under MEDIA_ROOT/<username>/quizzes/.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        # 1) Verify chat exists and belongs to this user:
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

        # 2) Extract “quiz” and “answers” from the request body:
        quiz = request.data.get("quiz")
        answers = request.data.get("answers")
        if quiz is None or answers is None:
            return Response(
                {"detail": "Both 'quiz' and 'answers' must be provided in the JSON body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) Build the folder MEDIA_ROOT/<username>/quizzes/ if it doesn't exist
        username = request.user.username
        quizzes_dir = Path(settings.MEDIA_ROOT) / username / "quizzes"
        quizzes_dir.mkdir(parents=True, exist_ok=True)

        # 4) Generate a timestamped filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quiz_{chat.id}_{timestamp}.json"
        file_path = quizzes_dir / filename

        # 5) Build the payload to write
        payload = {
            "username": username,
            "chat_id": chat.id,
            "timestamp": timestamp,
            "quiz": quiz,      
            # note: `quiz` is exactly the array your frontend sent (questions + options)
            "answers": answers 
            # e.g. { "0": "B", "1": "True", "2": "C", ... }
        }

        # 6) Write JSON to disk
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return Response(
                {"detail": f"Could not write file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 7) Return a success response with the public URL for download
        public_url = f"{settings.MEDIA_URL}{username}/quizzes/{filename}"
        return Response(
            {
                "detail": "Quiz answers saved successfully.",
                "saved_path": public_url
            },
            status=status.HTTP_201_CREATED
        )

class QuizTipsView(APIView):
    """
    POST /chats/<chat_id>/quiz-tips/
    Body: {
      "quiz": [
         { "question": "...", "options": ["A","B","C","D"] },
         { ... }
      ],
      "answers": { "0": "Option B", "1": "Option D", … }
    }
    This view generates “tips & tricks” on the user’s submitted answers and
    returns it as a ChatMessage, exactly like a normal chat reply.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        # 1) Verify chat belongs to current user
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

        # 2) Extract the quiz + answers payload
        quiz = request.data.get("quiz")
        answers = request.data.get("answers")
        if not isinstance(quiz, list) or not isinstance(answers, dict):
            return Response(
                {"detail": "Payload must include 'quiz' (array) and 'answers' (object)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) Build the Ollama prompt
        #    First, gather any document context exactly as in QuizGenerateView:
        messages = [
            {"role": "system", "content": "You are a helpful tutor who provides improvement tips."}
        ]
        #    If there are any OCR’d documents in this chat, prepend them:
        for doc in chat.documents.all():
            if doc.extracted_json:
                json_str = json.dumps(doc.extracted_json, ensure_ascii=False)
                system_msg = f"Document '{doc.name}' OCR contents (pages):\n{json_str}"
                messages.append({"role": "system", "content": system_msg})

        #    Now append the user prompt that asks for tips on their submitted answers:
        #    We embed the quiz questions + the user’s answers.
        #    (You can tweak the wording as you wish.)
        quiz_str_list = []
        for idx, q in enumerate(quiz):
            question_text = q.get("question", "")
            options_list = q.get("options", [])
            given_answer = answers.get(str(idx), "[no answer]")
            # format each question, options, and the user’s chosen answer:
            quiz_str_list.append(
                f"Q{idx+1}: {question_text}\n"
                f"   Options: {options_list}\n"
                f"   Your answer: {given_answer}"
            )
        quiz_block = "\n\n".join(quiz_str_list)

        user_prompt = (
            "I have just completed the following quiz. Please provide detailed improvement "
            "tips on each of my answers (for example: explain why my chosen option is correct/incorrect, "
            "offer general strategies for similar questions, and highlight any common pitfalls). "
            "Do not return a JSON structure—just reply normally in clear, instructional prose.\n\n"
            f"Here are the quiz questions + my answers:\n\n{quiz_block}"
        )
        messages.append({"role": "user", "content": user_prompt})

        # 4) Send entire context to Ollama’s chat completions endpoint
        try:
            ollama_resp = requests.post(
                "http://127.0.0.1:11434/v1/chat/completions",
                json={
                    "model": "qwen3:8B",
                    "messages": messages
                },
                timeout=120
            )
            ollama_resp.raise_for_status()
            payload = ollama_resp.json()
            raw_reply = payload["choices"][0]["message"]["content"]
        except Exception as e:
            return Response(
                {"detail": "LLM generation error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 5) Strip any <think>…</think> tags if present
        assistant_text = re.sub(r"<think>[\s\S]*?</think>", "", raw_reply).strip()

        # 6) Save as a ChatMessage (so it shows up in the chat stream)
        tip_msg = ChatMessage.objects.create(
            chat=chat,
            role="assistant",
            content=assistant_text
        )

        # 7) Return that new message back to the frontend
        serializer = ChatMessageSerializer(tip_msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)