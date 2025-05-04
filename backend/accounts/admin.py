from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Chat, Document

# Register the CustomUser model using UserAdmin
class CustomUserAdmin(UserAdmin):
    # Customize the fields displayed in the admin panel
    
    list_display = ('username', 'email', 'is_staff', 'is_active')  # Customize the list display
    search_fields = ('username', 'email')  # Add search functionality

# Register the Chat model in the admin panel
class ChatAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'user')  # Display important fields
    search_fields = ('name', 'user__username')  # Add search functionality for name and user

# Register the Document model in the admin panel
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'uploaded_at', 'chat')  # Display important fields
    search_fields = ('name', 'chat__name')  # Add search functionality for name and chat

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Document, DocumentAdmin)

