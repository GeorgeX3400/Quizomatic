from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # Ruta pentru calea goală – redirecționează spre login
    path('', lambda request: redirect('login'), name='home'),
    
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
