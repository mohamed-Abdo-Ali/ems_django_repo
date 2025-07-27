from . import views
from django.urls import path

app_name = 'authentcat_app'  # مهم لتجنب التعارض بين التطبيقات

urlpatterns = [
    path('', views.sign_in, name='sign_in'),
    path('password_reset/', views.password_reset, name='password_reset'),   
    path('insert_phoneEmail/', views.insert_phoneEmail, name='insert_phoneEmail'),   
]