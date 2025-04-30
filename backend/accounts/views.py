from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from django.http import JsonResponse
from .forms import CustomUserCreationForm, CustomLoginForm
from .serializers import *
from rest_framework import status, generics
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import io
from django.middleware.csrf import get_token
from rest_framework_simplejwt.tokens import RefreshToken
from .forms import FileUploadForm
from .models import FileUpload
import json
from django.core.exceptions import ValidationError
import os

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

def validate_file(file):
    allowed_extensions = ['.pdf', '.docx', '.txt']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file type: {ext}")


@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')



@login_required
def upload_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.user = request.user
            upload.save()
            return redirect('upload')
    else:
        form = FileUploadForm()

    uploads = FileUpload.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'accounts/upload.html', {
        'form': form,
        'uploads': uploads,
    })

# Authentication views:

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]   

class HomeView(APIView):  
   permission_classes = (IsAuthenticated, )
   def get(self, request):
    content = {'message': 'Hello'}
    return Response(content)

