from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)


class Chat(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=datetime.now())
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE) 

    def __str__(self):
        return self.name

class Document(models.Model):
    name = models.CharField(max_length=255)  # Filename
    content_type = models.CharField(max_length=100)  
    file = models.FileField(null=True)  
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    

