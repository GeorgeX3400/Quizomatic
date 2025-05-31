# accounts/views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import JsonResponse
from django.middleware.csrf import get_token
from pathlib import Path
from django.conf import settings
from datetime import datetime
import re
import json
import requests
import traceback
from .forms import CustomUserCreationForm, CustomLoginForm
from .serializers import (
    CustomUserSerializer,
    ChatSerializer,
    ChatMessageSerializer,
    DocumentSerializer
)
from .models import CustomUser, Chat, ChatMessage, Document
from .ocr_utils import extract_pages, write_json_pages


# ─── Registration / Login / Logout / Dashboard ───────────────────────

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


# ─── API: User Registration (v2) ─────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]


# ─── API: List & Create Chats ────────────────────────────────────────

class ChatsView(generics.ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show chats owned by the current user
        return Chat.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ChatCreateView(generics.CreateAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically assign `user=self.request.user`
        serializer.save(user=self.request.user)


# ─── API: Document Upload & List ────────────────────────────────────


class DocumentAddView(generics.CreateAPIView):
    """
    API endpoint pentru încărcarea unui document în chat.
    După salvare, se apelează OCR-ul și se păstrează rezultatul.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def perform_create(self, serializer):
        # 1) Verificăm că a venit chat_id
        chat_id = self.request.data.get("chat_id")
        if not chat_id:
            raise serializers.ValidationError({"chat_id": "This field is required."})

        # 2) Verificăm că chat-ul aparține user-ului curent
        chat = get_object_or_404(Chat, id=chat_id, user=self.request.user)

        # 3) Verificăm că s-a încărcat un fișier
        file_obj = self.request.FILES.get("file")
        if not file_obj:
            raise serializers.ValidationError({"file": "No file was submitted."})

        # 4) Salvăm obiectul Document (Django va plasa fișierul în MEDIA_ROOT conform setării `upload_to`)
        doc = serializer.save(
            chat=chat,
            name=file_obj.name,
            content_type=file_obj.content_type
        )

        # 5) Obținem calea absolută către fișierul salvat
        #    Django stochează într-un câmp FileField un atribut `.path` care e calea absolută
        file_path = Path(doc.file.path)  # <— este important să folosim .file.path

        # 6) Rulăm OCR și prindem eventuale erori
        try:
            pages = extract_pages(str(file_path))
        except Exception as e:
            # Logăm în consolă tot stacktrace-ul ca să vedem unde pică OCR-ul
            print("=== [DocumentAddView] Eroare în extract_pages ===")
            traceback.print_exc()
            pages = []

        # 7) Salvăm rezultatul JSON și extragem textul simplu
        doc.extracted_json = pages
        doc.extracted_text = "\n\n".join(p.get("text", "") for p in pages)
        doc.save()

        # 8) Creăm subfolderul processed/<username>/ dacă nu există
        username = chat.user.username
        processed_dir = Path(settings.MEDIA_ROOT) / username / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        # 9) Generăm un nume pentru fișierul JSON + timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(doc.name).stem  # ex: "document_22_20250531"
        out_filename = f"{base_name}_pages_{timestamp}.json"
        out_path = processed_dir / out_filename

        # 10) Scriem lista de pagini ca JSON în acest fișier
        write_json_pages(pages, out_path)

class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return documents for the current user's chats
        qs = Document.objects.filter(chat__user=self.request.user)
        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            qs = qs.filter(chat__id=chat_id)
        return qs


# ─── API: Chat Messages ─────────────────────────────────────────────

class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        """
        GET /api/chats/<chat_id>/messages/
        List all messages in the chat (user + assistant), ordered by timestamp,
        but strip out any <think>…</think> tags from assistant messages.
        """
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        msgs = chat.messages.order_by('timestamp')
        serializer = ChatMessageSerializer(msgs, many=True)
        data = serializer.data

        # Remove any <think>…</think> blocks from assistant content
        for item in data:
            if item['role'] == 'assistant':
                item['content'] = re.sub(r'<think>[\s\S]*?</think>', '', item['content']).strip()

        return Response(data)

    def post(self, request, chat_id):
        """
        POST /api/chats/<chat_id>/messages/
        Save the user message, call Ollama to generate a response, clean out
        any <think>…</think> from the assistant output, save it, and return it.
        """
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        user_text = request.data.get('message', '').strip()
        if not user_text:
            return Response({'detail': 'No message provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1) Save the user message
        ChatMessage.objects.create(chat=chat, role='user', content=user_text)

        # 2) Build the full chat context to send to Ollama
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        past = ChatMessage.objects.filter(chat=chat).order_by("timestamp")
        for msg in past:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_text})

        # 3) Call Ollama's chat completions endpoint
        try:
            ollama_resp = requests.post(
                "http://127.0.0.1:11434/v1/chat/completions",
                json={"model": "qwen3:8B", "messages": messages},
                timeout=60
            )
            ollama_resp.raise_for_status()
            payload = ollama_resp.json()
            raw_reply = payload["choices"][0]["message"]["content"]
        except Exception as e:
            return Response({'detail': 'LLM generation error', 'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4) Clean out any <think>…</think> tags
        assistant_text = re.sub(r'<think>[\s\S]*?</think>', '', raw_reply).strip()

        # 5) Save the assistant message
        ChatMessage.objects.create(chat=chat, role='assistant', content=assistant_text)

        # 6) Return the assistant reply
        return Response({'reply': assistant_text})


# ─── API: Generate Quiz (multiple‐choice or true/false) ─────────────────

class QuizGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

        # 1) Read parameters
        num_q = int(request.data.get("num_questions", 5))
        difficulty = request.data.get("difficulty", "easy")
        question_type = request.data.get("question_type", "multiple")
        if question_type not in ("multiple", "truefalse"):
            question_type = "multiple"

        # 2) Build system + document context
        messages = [{"role": "system", "content": "You are a helpful assistant."}]

        # ─── AICI SCHIMBĂM condiția ─────────────────────────────
        #    (în loc de `if getattr(...)` punem `if doc.extracted_json is not None`)
        for doc in chat.documents.all():
            if doc.extracted_json is not None:
                # Dacă lista e goală, json_str va fi "[]"; dacă nu, va conține
                # textul OCR‐at page by page
                try:
                    json_str = json.dumps(doc.extracted_json, ensure_ascii=False)
                except Exception:
                    # Ca să nu se oprească totul dacă extracted_json nu e valid JSON
                    json_str = "[]"

                system_msg = f"Document '{doc.name}' OCR contents (pages):\n{json_str}"
                messages.append({"role": "system", "content": system_msg})
        # ───────────────────────────────────────────────────────

        # 3) Create the user prompt depending on question_type
        if question_type == "multiple":
            quiz_prompt = (
                f"Generate a quiz of {difficulty} difficulty with {num_q} questions. "
                "Each question must be strictly multiple-choice with exactly four options. "
                "Respond in JSON only, with each array element formatted as:\n"
                "{ \"question\": \"Your question text here\", "
                "\"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"], "
                "\"answer\": \"<one of the four options exactly>\" }.\n"
                "Do not include any true/false questions, and do not add any extra text—output only the JSON array."
            )
        else:
            quiz_prompt = (
                f"Generate a quiz of {difficulty} difficulty with {num_q} questions. "
                "Each question must be strictly True/False (no multiple-choice). "
                "Respond in JSON only, with each array element formatted as:\n"
                "{ \"question\": \"Your statement here\", \"answer\": true_or_false }.\n"
                "Use lowercase `true` or `false` for the answer. "
                "Do not include any multiple-choice questions, și nu adăuga text suplimentar—output doar JSON array."
            )

        messages.append({"role": "user", "content": quiz_prompt})

        # 4) Send to Ollama
        try:
            ollama_resp = requests.post(
                "http://127.0.0.1:11434/v1/chat/completions",
                json={"model": "qwen3:8B", "messages": messages},
                timeout=60
            )
            ollama_resp.raise_for_status()
            payload = ollama_resp.json()
            raw_quiz = payload["choices"][0]["message"]["content"]
        except Exception as e:
            # Într-un caz real, ai log în consolă: traceback.print_exc()
            return Response({
                "detail": "LLM generation error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 5) Strip out any <think>…</think> tags
        quiz_text = re.sub(r"^.*?</think>\s*", "", raw_quiz, flags=re.DOTALL).strip()

        # 6) Save as a ChatMessage și returnează JSON-ul
        quiz_msg = ChatMessage.objects.create(chat=chat, role="assistant", content=quiz_text)
        serializer = ChatMessageSerializer(quiz_msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
# ─── API: Submit Quiz Answers ────────────────────────────────────────

class SubmitQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        """
        POST /api/chats/<chat_id>/submit-quiz/
        Body: {
          "quiz": [ { "question": "...", "options": [ ... ] }, ... ],
          "answers": { "0": "<option chosen>", "1": "<...>", ... }
        }
        Saves a JSON file under MEDIA_ROOT/<username>/quizzes/ and returns its public URL.
        """
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

        quiz = request.data.get("quiz")
        answers = request.data.get("answers")
        if quiz is None or answers is None:
            return Response(
                {"detail": "Both 'quiz' and 'answers' must be provided in the JSON body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = request.user.username
        quizzes_dir = Path(settings.MEDIA_ROOT) / username / "quizzes"
        quizzes_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quiz_{chat.id}_{timestamp}.json"
        file_path = quizzes_dir / filename

        payload = {
            "username": username,
            "chat_id": chat.id,
            "timestamp": timestamp,
            "quiz": quiz,
            "answers": answers
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return Response({"detail": f"Could not write file: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        public_url = f"{settings.MEDIA_URL}{username}/quizzes/{filename}"
        return Response({"detail": "Quiz answers saved successfully.", "saved_path": public_url},
                        status=status.HTTP_201_CREATED)


# ─── API: Tips & Tricks for Quiz Answers ────────────────────────────

class QuizTipsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        """
        POST /api/chats/<chat_id>/quiz-tips/
        Body: {
          "quiz": [ { "question": "...", "options": [ ... ] }, ... ],
          "answers": { "0": "<option chosen>", "1": "<...>", ... }
        }
        Generate improvement tips and return as a normal ChatMessage.
        """
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

        quiz = request.data.get("quiz")
        answers = request.data.get("answers")
        if not isinstance(quiz, list) or not isinstance(answers, dict):
            return Response(
                {"detail": "Payload must include 'quiz' (array) and 'answers' (object)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1) Build system + document context
        messages = [
            {"role": "system", "content": "You are a helpful tutor who provides improvement tips."}
        ]
        for doc in chat.documents.all():
            if getattr(doc, "extracted_json", None):
                json_str = json.dumps(doc.extracted_json, ensure_ascii=False)
                system_msg = f"Document '{doc.name}' OCR contents (pages):\n{json_str}"
                messages.append({"role": "system", "content": system_msg})

        # 2) Build a textual block with each question & the user’s chosen answer
        quiz_lines = []
        for idx, q in enumerate(quiz):
            question_text = q.get("question", "")
            options_list = q.get("options", [])
            given_answer = answers.get(str(idx), "[no answer]")
            quiz_lines.append(
                f"Q{idx+1}: {question_text}\n"
                f"   Options: {options_list}\n"
                f"   Your answer: {given_answer}"
            )
        quiz_block = "\n\n".join(quiz_lines)

        user_prompt = (
            "I have just completed the following quiz. "
            "Please provide detailed improvement tips on each of my answers "
            "(e.g. explain why my chosen option is correct/incorrect, "
            "offer strategies for similar questions, and highlight common pitfalls). "
            "Do not return a JSON structure—just reply normally in clear, instructional prose.\n\n"
            f"Here are the quiz questions + my answers:\n\n{quiz_block}"
        )
        messages.append({"role": "user", "content": user_prompt})

        # 3) Send to Ollama
        try:
            ollama_resp = requests.post(
                "http://127.0.0.1:11434/v1/chat/completions",
                json={"model": "qwen3:8B", "messages": messages},
                timeout=120
            )
            ollama_resp.raise_for_status()
            payload = ollama_resp.json()
            raw_reply = payload["choices"][0]["message"]["content"]
        except Exception as e:
            return Response({"detail": "LLM generation error", "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4) Strip out any <think>…</think> tags
        assistant_text = re.sub(r'<think>[\s\S]*?</think>', '', raw_reply).strip()

        # 5) Save as a ChatMessage and return it
        tip_msg = ChatMessage.objects.create(chat=chat, role="assistant", content=assistant_text)
        serializer = ChatMessageSerializer(tip_msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
