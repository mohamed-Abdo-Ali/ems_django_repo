from . import views
from django.urls import path

app_name = 'core_app'  # مهم لتجنب التعارض بين التطبيقات

urlpatterns = [
    path('', views.home, name='home'),
    # أضف مسارات أخرى هنا حسب الحاجة
]