from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os

def user_chat_directory_path(instance, filename):
    """
    File will be uploaded to:
      MEDIA_ROOT/<username>/<chat_id>/<filename>
    """
    username = instance.chat.user.username
    return os.path.join(username, filename)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)


class Chat(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=[('user','User'),('assistant','Assistant')])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

documents_storage = FileSystemStorage(location=settings.DOCUMENTS_ROOT)


def document_upload_path(instance, filename):
    """
    Upload files to:
      MEDIA_ROOT/<username>/uploaded/document_<userId>_<YYYYMMDD><ext>
    """
    user_id  = instance.chat.user.id
    date_str = datetime.now().strftime('%Y%m%d')
    base, ext = os.path.splitext(filename)
    new_name = f"document_{user_id}_{date_str}{ext}"
    return os.path.join(instance.chat.user.username, "uploaded", new_name)

class Document(models.Model):
    chat          = models.ForeignKey(Chat, related_name='documents', on_delete=models.CASCADE)
    name          = models.CharField(max_length=255)   # original filename
    content_type  = models.CharField(max_length=100)   # MIME type (e.g. 'application/pdf')
    file          = models.FileField(upload_to=document_upload_path)
    extracted_text= models.TextField(blank=True)       # OCR’d text goes here
    uploaded_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chat.user.username}/uploaded/{self.name}"

