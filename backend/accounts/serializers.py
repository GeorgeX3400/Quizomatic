from rest_framework import serializers
from .models import *
from datetime import date
from django.core.exceptions import ValidationError
from drf_extra_fields.fields import Base64FileField
import mimetypes

# ── MODELS SERIALIZERS ─────────────────────────────────────────────────────────────────

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

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
    # Expose the extracted JSON and flattened text, but read‐only
    extracted_json = serializers.JSONField(read_only=True)
    extracted_text = serializers.CharField(read_only=True)

    class Meta:
        model = Document
        # Add the new fields here so the client sees them in GET responses
        fields = [
            'id',
            'name',
            'file',
            'chat',
            'uploaded_at',
            'extracted_json',
            'extracted_text',
        ]
        read_only_fields = [
            'id',
            'uploaded_at',
            'chat',
            'extracted_json',
            'extracted_text',
        ]

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ['id', 'name', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def create(self, data):
        chat = Chat.objects.create(**data)
        return chat

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ChatMessage
        fields = ['id', 'role', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp']
