from django.urls import path
from django.shortcuts import redirect
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Ruta pentru calea goală – redirecționează spre login
    path('', lambda request: redirect('login'), name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('v2/register/', views.RegisterView.as_view(), name='v2_register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('chats/', views.ChatsView.as_view(), name='chats'),
    path('chats/create/', views.ChatCreateView.as_view(), name='chat_create'),
    path('documents/',views.DocumentListView.as_view(), name='documents' ),
    path('documents/add/', views.DocumentAddView.as_view(), name='document_add')
]
