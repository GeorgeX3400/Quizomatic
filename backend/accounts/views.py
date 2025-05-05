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
        chat_id = self.request.data.get('chat_id')
        if not chat_id:
            raise serializers.ValidationError({'chat_id': 'This field is required.'})
            
        chat = get_object_or_404(Chat, id=chat_id, user=self.request.user)
        file = self.request.FILES.get('file')
        if not file:
            raise serializers.ValidationError({'file': 'No file was submitted.'})
            
        serializer.save(chat=chat, file=file)

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
            ollama_resp = requests.post(
                "http://127.0.0.1:11434/v1/chat/completions",
                json={
                    "model": "qwen3:4B",
                    "messages": [
                        {"role": "system",  "content": "You are a helpful assistant."},
                        {"role": "user",    "content": user_text}
                    ]
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
    
class QuizGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        # 1) Verify the chat
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

        # 2) Parse the payload
        num_q = int(request.data.get('num_questions', 5))
        difficulty = request.data.get('difficulty', 'easy')

        # 3) Generate the prompt for the LLM
        prompt = (
            f"Generate a quiz of {difficulty} difficulty with {num_q} questions. "
            "The questions should be either multiple choice (\"question\": 'the question', \"options\": [o1, o2, o3, o4], \"answer\": o_) "
            "or true/false style (\"question\": 'a statement', \"answer\": true/false). "
            "Create the quiz in JSON format, having the objects in a list. Do not add any additional text in the response (or in the options), I want only the JSON."
        )

        # 4) Call Ollama Chat Completions API
        import requests
        try:
            ollama_resp = requests.post(
                "http://127.0.0.1:11434/v1/chat/completions",
                json={
                    "model": "qwen3:4B",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=1000
            )
            ollama_resp.raise_for_status()
            payload = ollama_resp.json()
            quiz = payload["choices"][0]["message"]["content"]
            
        except Exception as e:
            return Response(
                {'detail': 'LLM generation error', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Preprocess the response to remove everything from the start to the last </think> tag
        quiz = re.sub(r'^.*?</think>\s*', '', quiz, flags=re.DOTALL).strip()
        print(quiz)
        # 5) Return the quiz generated by the LLM
        return Response({"quiz": quiz})
