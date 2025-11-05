from django.shortcuts import render
from conttroll_app.models import ExamScheduleView

# conttroll_app/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from .services.import_students import import_students_from_excel
# ملاحظة: إذا صادفت ImportError استبدل السطر أعلاه بـ:
# from conttroll_app.services.import_students import import_students_from_excel

@staff_member_required
def import_students_page(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        sheet = request.POST.get("sheet") or "ورقة1"
        header_row = request.POST.get("header_row") or "1"

        if not file:
            messages.error(request, "لم يتم اختيار ملف.")
            return redirect("import_students_page")

        try:
            header_row = int(header_row)
            result = import_students_from_excel(file, sheet_name=sheet, header_row=header_row)
            messages.success(
                request,
                f"✅ تم إدخال {result['students_created']} طالب، وإنشاء {result['terms_created']} فصل/سنة. (الصفوف المقروءة: {result['rows']})"
            )
            return redirect("import_students_page")
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء الاستيراد: {e}")

    return render(request, "jazzam/import_students.html")

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

 