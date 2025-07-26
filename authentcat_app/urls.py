from . import views
from django.urls import path

app_name = 'authentcat_app'  # مهم لتجنب التعارض بين التطبيقات

urlpatterns = [
    path('', views.home, name='home'),
    
]