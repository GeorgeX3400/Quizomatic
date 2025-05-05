from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import os

def user_chat_directory_path(instance, filename):
    """
    File will be uploaded to:
      MEDIA_ROOT/<username>/<chat_id>/<filename>
    """
    username = instance.chat.user.username
    chat_id  = instance.chat.id
    return os.path.join(username, str(chat_id), filename)


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

class Document(models.Model):
    chat          = models.ForeignKey(Chat, related_name='documents', on_delete=models.CASCADE)
    name          = models.CharField(max_length=255)               # original filename
    content_type  = models.CharField(max_length=100)               # e.g. 'image/png' or 'application/pdf'
    file          = models.FileField(upload_to=user_chat_directory_path)
    extracted_text= models.TextField(blank=True)                   # OCR’d text goes here
    uploaded_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chat.user.username}/{self.chat.id}/{self.name}"
    

