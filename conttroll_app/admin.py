from django.contrib import admin
from .models import ExamHall,ExamSchedule,Grade

# Register your models here.
admin.site.register(ExamHall)
admin.site.register(ExamSchedule)
admin.site.register(Grade)