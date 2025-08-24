from . import views
from django.urls import path

app_name = 'student_app'  # مهم لتجنب التعارض بين التطبيقات

urlpatterns = [
    path('insert_unviercityNumber/', views.insert_unviercityNumber, name='insert_unviercityNumber'),  
    path('instructions/', views.instructions, name='instructions'), 
    # path('student_exam/', views.student_exam, name='student_exam'), 
    path('exam_sucss/', views.exam_sucss, name='exam_sucss'), 
]