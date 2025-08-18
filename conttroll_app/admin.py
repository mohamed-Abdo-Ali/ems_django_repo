from django.contrib import admin
from .models import ExamHall,ExamSchedule

# Register your models here.
admin.site.register(ExamHall)
admin.site.register(ExamSchedule)