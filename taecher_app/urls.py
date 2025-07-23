from . import views
from django.urls import path

app_name = 'taecher_app'  # مهم لتجنب التعارض بين التطبيقات

urlpatterns = [
    path('', views.home, name='home'),
    # أضف مسارات أخرى هنا حسب الحاجة
]