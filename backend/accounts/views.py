# accounts/views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, serializers
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from pathlib import Path
from django.conf import settings
from datetime import datetime
import re
import json
import traceback
import glob

from .forms import CustomUserCreationForm, CustomLoginForm
from .serializers import (
    CustomUserSerializer,
    ChatSerializer,
    ChatMessageSerializer,
    DocumentSerializer
)
from .models import CustomUser, Chat, ChatMessage, Document
from .ocr_utils import extract_pages, write_json_pages
from .llm_access import LLMAccess  # ← your new façade

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
        return Chat.objects.filter(user=self.request.user)

class ChatCreateView(generics.CreateAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# ─── API: Document Upload & List ────────────────────────────────────

class DocumentAddView(generics.CreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def perform_create(self, serializer):
        chat_id = self.request.data.get("chat_id")
        if not chat_id:
            raise serializers.ValidationError({"chat_id": "This field is required."})

        chat = get_object_or_404(Chat, id=chat_id, user=self.request.user)
        file_obj = self.request.FILES.get("file")
        if not file_obj:
            raise serializers.ValidationError({"file": "No file was submitted."})

        doc = serializer.save(
            chat=chat,
            name=file_obj.name,
            content_type=file_obj.content_type
        )

        file_path = Path(doc.file.path)
        try:
            pages = extract_pages(str(file_path))
        except Exception:
            traceback.print_exc()
            pages = []

        doc.extracted_json = pages
        doc.extracted_text = "\n\n".join(p.get("text", "") for p in pages)
        doc.save()

        username = chat.user.username
        processed_dir = Path(settings.MEDIA_ROOT) / username / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(doc.name).stem
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

# ─── API: Chat Messages ─────────────────────────────────────────────

class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        msgs = chat.messages.order_by('timestamp')
        serializer = ChatMessageSerializer(msgs, many=True)
        data = serializer.data

        for item in data:
            if item['role'] == 'assistant':
                item['content'] = re.sub(r'<think>[\s\S]*?</think>', '', item['content']).strip()

        return Response(data)

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        user_text = request.data.get('message', '').strip()
        if not user_text:
            return Response({'detail': 'No message provided.'}, status=status.HTTP_400_BAD_REQUEST)

        ChatMessage.objects.create(chat=chat, role='user', content=user_text)

        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        past = ChatMessage.objects.filter(chat=chat).order_by("timestamp")
        for msg in past:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_text})

        try:
            assistant_text = LLMAccess.chat_completions(messages, timeout=60)
        except RuntimeError as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        ChatMessage.objects.create(chat=chat, role='assistant', content=assistant_text)
        return Response({'reply': assistant_text})

# ─── API: Generate Quiz ──────────────────────────────────────────────

# in accounts/views.py

class QuizGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

        # 1) parse params
        num_q = int(request.data.get("num_questions", 5))
        difficulty = request.data.get("difficulty", "easy")
        qtype = request.data.get("question_type", "multiple")
        if qtype not in ("multiple", "truefalse"):
            qtype = "multiple"

        # 2) gather all OCR JSON pages into one big string
        all_pages = []
        for doc in chat.documents.all():
            if doc.extracted_json:
                all_pages.extend(doc.extracted_json)
        if not all_pages:
            return Response(
                {"detail": "No OCR content found on any document."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # convert pages list → JSON string
        doc_json_str = json.dumps(all_pages, ensure_ascii=False)

        # 3) build the system + single user message
        messages = [
            {"role": "system", "content": "You are a helpful teaching assistant."},
            {
                "role": "user",
                "content": (
                    "Use *only* the following document content (OCR pages JSON) as your source. "
                    "Do not draw on any external knowledge or hallucinate.  \n\n"
                    f"{doc_json_str}\n\n"
                    "Now generate a quiz in Romanian "
                    f"of *{difficulty}* difficulty with *{num_q}* questions "
                    f"based *strictly* on that content. "
                    + (
                        "Each must be multiple-choice with exactly four options, in JSON format:  \n"
                        '{ "question": "...", "options": ["A","B","C","D"], "answer": "A" }'
                        if qtype == "multiple"
                        else
                        'Each must be True/False only, in JSON format:  \n'
                        '{ "question": "...", "answer": true_or_false }'
                    )
                )
            }
        ]

        # 4) call your LLMAccess facade
        try:
            quiz_text = LLMAccess.chat_completions(messages, timeout=120)
        except RuntimeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 5) strip any stray <think> tags
        clean = re.sub(r"^.*?</think>\s*", "", quiz_text, flags=re.DOTALL).strip()

        # 6) save & return
        quiz_msg = ChatMessage.objects.create(chat=chat, role="assistant", content=clean)
        serializer = ChatMessageSerializer(quiz_msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# ─── API: Submit Quiz Answers ────────────────────────────────────────

# accounts/views.py

class SubmitQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        quiz = request.data.get("quiz")
        answers = request.data.get("answers")
        if quiz is None or answers is None:
            return Response(
                {"detail": "Both 'quiz' and 'answers' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1) Salvare fișier JSON
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
            return Response(
                {"detail": f"Could not write file: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        public_url = f"{settings.MEDIA_URL}{username}/quizzes/{filename}"

        # 2) Construire prompt de review
        review_lines = []
        for idx, q in enumerate(quiz):
            opts = q.get("options", [])
            user_ans = answers.get(str(idx), "[no answer]")
            review_lines.append(
                f"Q{idx+1}: {q.get('question','')}\n"
                f"   Options: {opts}\n"
                f"   Your answer: {user_ans}"
            )
        review_block = "\n\n".join(review_lines)

        # 3) Adăugare context sistem + (opțional) documente
        messages = [
            {"role": "system", "content": "Ești un tutore prietenos și foarte bine pregătit care oferă feedback detaliat și clar în limba română."
            "Te rog să răspunzi **fără niciun fel de formatare Markdown** "
            "(fără #, *, –, backticks etc.), folosind doar texte simple, "
            "structurate în paragrafe clare." }
        ]
        for doc in chat.documents.all():
            if doc.extracted_json:
                try:
                    js = json.dumps(doc.extracted_json, ensure_ascii=False)
                except:
                    js = "[]"
                messages.append({
                    "role": "system",
                    "content": f"Document '{doc.name}' OCR pages:\n{js}"
                })

        # 4) Prompt-ul user
        messages.append({
            "role": "user",
            "content": (
                "Te rog să revizuiești următorul quiz și răspunsurile mele:\n\n"
                "Pentru fiecare întrebare, spune-mi:\n"
                "  1) Care este răspunsul corect,\n"
                "  2) Dacă răspunsul meu a fost corect sau greșit,\n"
                "  3) O scurtă explicație dacă am greșit.\n\n"
                f"{review_block}"
                "IMPORTANT: nu folosi format Markdown, ci prezintă totul în paragrafe de text simple."
            )
        })

        # 5) Apel LLM pentru review
        try:
            review_text = LLMAccess.chat_completions(messages, timeout=120)
        except RuntimeError as e:
            return Response(
                {"detail": f"Could not generate review: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 6) Curățare tag-uri <think>
        clean_review = re.sub(r"<think>[\s\S]*?</think>", "", review_text).strip()

        # 7) Salvare review în ChatMessage
        review_msg = ChatMessage.objects.create(
            chat=chat, role="assistant", content=clean_review
        )

        # 8) Răspuns HTTP cu link-ul și obiectul review
        return Response({
            "saved_path": public_url,
            "review": ChatMessageSerializer(review_msg).data
        }, status=status.HTTP_201_CREATED)
# ─── API: Tips & Tricks for Quiz Answers ────────────────────────────

class QuizTipsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        quiz = request.data.get("quiz")
        answers = request.data.get("answers")
        if not isinstance(quiz, list) or not isinstance(answers, dict):
            return Response(
                {"detail": "Payload must include 'quiz' (array) and 'answers' (object)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        messages = [{"role": "system", "content": "Ești un tutore prietenos și util, specializat în oferirea de sfaturi practice și recomandări detaliate pentru îmbunătățirea performanțelor la quiz-uri."
                     "Te rog să răspunzi **fără niciun fel de formatare Markdown** "
                     "(fără #, *, –, backticks etc.), folosind doar texte simple, "
                     "structurate în paragrafe clare."}]
        for doc in chat.documents.all():
            if getattr(doc, "extracted_json", None):
                json_str = json.dumps(doc.extracted_json, ensure_ascii=False)
                messages.append({
                    "role": "system",
                    "content": f"Document '{doc.name}' OCR contents (pages):\n{json_str}"
                })

        quiz_lines = []
        for idx, q in enumerate(quiz):
            question_text = q.get("question", "")
            options_list = q.get("options", [])
            given = answers.get(str(idx), "[no answer]")
            quiz_lines.append(f"Q{idx+1}: {question_text}\n   Options: {options_list}\n   Your answer: {given}")
        quiz_block = "\n\n".join(quiz_lines)

        user_prompt = (
            "Tocmai am finalizat quiz-ul de mai jos. Te rog să îmi oferi sfaturi detaliate de îmbunătățire pentru fiecare răspuns:\n\n"
            f"{quiz_block}"
            "IMPORTANT: nu folosi format Markdown, ci prezintă totul în paragrafe de text simple."
        )
        messages.append({"role": "user", "content": user_prompt})

        try:
            assistant_text = LLMAccess.chat_completions(messages, timeout=120)
        except RuntimeError as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        tip_msg = ChatMessage.objects.create(chat=chat, role='assistant', content=assistant_text)
        serializer = ChatMessageSerializer(tip_msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class QuizSummaryView(APIView):
    """
    POST /api/chats/<chat_id>/quiz-summary/
    Încarcă toate fișierele JSON cu quiz-urile salvate pentru user,
    construiește un prompt pentru LLM care să identifice punctele slabe
    pe baza tuturor quiz-urilor, și returnează review-ul ca ChatMessage.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        username = request.user.username
        quizzes_dir = Path(settings.MEDIA_ROOT) / username / "quizzes"

        # 1) Listăm toate fișierele JSON
        files = glob.glob(str(quizzes_dir / "*.json"))
        if not files:
            return Response(
                {"detail": "Nu am găsit niciun quiz salvat pentru tine."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2) Construim un bloc de text cu toate quiz-urile + răspunsurile tale
        all_entries = []
        for fp in files:
            try:
                data = json.load(open(fp, encoding="utf-8"))
                quiz = data.get("quiz", [])
                answers = data.get("answers", {})
                for idx, q in enumerate(quiz):
                    question = q.get("question","[fără text]")
                    correct = q.get("answer", None)  # presupunem că ai salvat și answer
                    user_ans = answers.get(str(idx), "[no answer]")
                    all_entries.append({
                        "question": question,
                        "correct": correct,
                        "you": user_ans
                    })
            except Exception:
                continue

        # 3) Formatăm textul pentru LLM
        summary_lines = []
        for i, e in enumerate(all_entries, start=1):
            summary_lines.append(
                f"{i}. Q: {e['question']}\n"
                f"   Correct answer: {e['correct']}\n"
                f"   Your answer: {e['you']}"
            )
        summary_block = "\n\n".join(summary_lines)

        # 4) Pregătim mesajele pentru LLM
        msgs = [
            {"role": "system", "content": "Ești un tutore de încredere care analizează evoluția performanțelor mele de-a lungul timpului și oferă recomandări de îmbunătățire."
            "Te rog să răspunzi **fără niciun fel de formatare Markdown** "
            "(fără #, *, –, backticks etc.), folosind doar texte simple, "
            "structurate în paragrafe clare." },
            {"role": "user", "content":
                "Am făcut următoarele quiz-uri de-a lungul timpului. "
                "Te rog să-mi spui, pe ansamblu:\n"
                "  - Care sunt domeniile mele slabe (tematici frecvent greșite)?\n"
                "  - Cum pot să mă îmbunătățesc în fiecare dintre ele.\n\n"
                f"{summary_block}"
                "IMPORTANT: nu folosi format Markdown, ci prezintă totul în paragrafe de text simple."
            }
        ]

        # 5) Apel LLM
        try:
            advice = LLMAccess.chat_completions(msgs, timeout=180)
        except RuntimeError as e:
            return Response({"detail": f"Eroare LLM: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        advice = re.sub(r"<think>[\s\S]*?</think>", "", advice).strip()

        # 6) Salvăm și returnăm ca ChatMessage
        adv_msg = ChatMessage.objects.create(chat=chat, role="assistant", content=advice)
        return Response(ChatMessageSerializer(adv_msg).data, status=status.HTTP_201_CREATED)