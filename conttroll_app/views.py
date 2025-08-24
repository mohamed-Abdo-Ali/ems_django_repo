from django.shortcuts import render
# from .models import ExamScheduleView
from datetime import datetime

from conttroll_app.models import ExamScheduleView

# Create your views here.





def home(request):
    return render(request, 'conttroll_app/home.html')




def exam_schedule_view(request):
    current_year = datetime.now().year
    next_year = current_year + 1
    academic_year = f"{current_year}/{next_year}"
    
    schedules = ExamScheduleView.objects.all().order_by('exam_date', 'start_time')
    
    context = {
        'exam_schedules': schedules,
        'academic_year': academic_year
    }
    return render(request, 'conttroll_app/ExamSchedule.html', context)

 