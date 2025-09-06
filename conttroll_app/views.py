from django.shortcuts import render
from conttroll_app.models import ExamScheduleView





# =========================== home ========================================================
def home(request):
    return render(request, 'conttroll_app/home.html')



# =========================== exam_schedule_view ========================================================
def exam_schedule_view(request):
    
    schedules = ExamScheduleView.objects.all().order_by('exam_date', 'start_time')
    
    context = {
        'exam_schedules': schedules,
    }
    return render(request, 'conttroll_app/ExamSchedule.html', context)

 