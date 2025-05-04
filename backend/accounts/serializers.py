from rest_framework import serializers
from .models import *
from datetime import date
from django.core.exceptions import ValidationError
from drf_extra_fields.fields import Base64FileField
import mimetypes

# MODELS SERIALIZERS: 

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only':True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Both username and password are required.")

        return data




class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ['id', 'name', 'file', 'chat', 'uploaded_at']  # Removed 'content'
        read_only_fields = ['id', 'uploaded_at', 'chat']
    
        
class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ['id', 'name', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    def create(self, data):
        chat = Chat.objects.create(**data)
        return chat
