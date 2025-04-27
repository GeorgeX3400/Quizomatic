from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register the CustomUser model using UserAdmin
class CustomUserAdmin(UserAdmin):
    # Customize the fields displayed in the admin panel
    
    list_display = ('username', 'email', 'is_staff', 'is_active')  # Customize the list display
    search_fields = ('username', 'email')  # Add search functionality
# Register your models h
admin.site.register(CustomUser, CustomUserAdmin)