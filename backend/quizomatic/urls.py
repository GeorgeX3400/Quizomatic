"""
URL configuration for quizomatic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import QuizGenerateView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include rutele din accounts cu prefixul gol
    path('', include('accounts.urls')),
    path(
      'chats/<int:chat_id>/generate-quiz/',
      QuizGenerateView.as_view(),
      name='generate_quiz'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.DOCUMENTS_URL.lstrip('/'),
        document_root=settings.DOCUMENTS_ROOT
    )
