from django.contrib import admin
from .models import ExamHall,ExamSchedule,Grade,ExamScheduleView

# Register your models here.
admin.site.register(ExamHall)
admin.site.register(ExamSchedule)
admin.site.register(Grade)
# admin.site.register(ExamScheduleView)