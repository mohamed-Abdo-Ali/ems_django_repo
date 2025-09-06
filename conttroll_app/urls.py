from . import views
from django.urls import path
# from .views import exam_schedule_view

app_name = 'conttroll_app'  # مهم لتجنب التعارض بين التطبيقات

urlpatterns = [
    path('', views.home, name='home'),
    path('exam-schedule/',views.exam_schedule_view, name='exam-schedule'),
]





