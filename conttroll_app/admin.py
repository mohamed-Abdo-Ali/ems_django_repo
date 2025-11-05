# conttroll_app/admin.py
from django.contrib import admin
from .models import  Acdimaic_and_term_from_uivercity, ExamSchedule, ExamHall, student_courses_grads, student_report_from_uivercity
from django.contrib import admin
from django.utils.html import format_html
from authentcat_app.admin import ReadOnlyViewAdminMixin

from django import forms

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.safestring import mark_safe

from .models import student_report_from_uivercity
from .services.import_students import import_students_from_excel
from .services.buffer_users import create_buffer_users_for_students  # جديد

@admin.register(student_report_from_uivercity)
class StudentReportAdmin(admin.ModelAdmin):
    change_list_template = "admin/conttroll_app/student_report_from_uivercity/change_list.html"

    list_display = ("id", "name", "gender", "univercity_number", "major", "semester_display")
    search_fields = ("name", "univercity_number", "major")

    def get_list_filter(self, request):
        field_names = {f.name for f in self.model._meta.get_fields()}
        filters = ["gender"]
        if "semester" in field_names:
            filters.append("semester")
        elif "semester_id" in field_names:
            filters.append("semester_id")
        return filters

    def semester_display(self, obj):
        if hasattr(obj, "semester") and getattr(obj, "semester") is not None:
            return str(getattr(obj, "semester"))
        return getattr(obj, "semester_id", "")
    semester_display.short_description = "الفصل الدراسي"

    def get_urls(self):
        urls = super().get_urls()
        info = (self.model._meta.app_label, self.model._meta.model_name)
        custom = [
            path("import-excel/", self.admin_site.admin_view(self.import_excel), name=f"{info[0]}_{info[1]}_import"),
        ]
        return custom + urls

    def import_excel(self, request):
        info = (self.model._meta.app_label, self.model._meta.model_name)
        changelist_url = reverse(f"admin:{info[0]}_{info[1]}_changelist")

        if request.method != "POST":
            return redirect(changelist_url)

        f = request.FILES.get("file")
        sheet = request.POST.get("sheet") or "ورقة1"
        header_row = request.POST.get("header_row") or "1"

        if not f:
            self.message_user(request, "لم يتم اختيار ملف.", level=messages.ERROR)
            return redirect(changelist_url)

        try:
            header_row = int(header_row)
        except ValueError:
            header_row = 1

        try:
            # 1) استيراد الطلاب
            result = import_students_from_excel(f, sheet_name=sheet, header_row=header_row)
            self.message_user(
                request,
                f"✅ تم إدخال {result['students_created']} طالب، وإنشاء {result['terms_created']} فصل/سنة. (الصفوف المقروءة: {result['rows']})",
                level=messages.SUCCESS,
            )

            # 2) إنشاء المستخدمين العشوائيين للطلاب الذين أُضيفوا الآن
            created_ids = result.get("created_ids") or []
            if created_ids:
                file_path, public_url, created_count = create_buffer_users_for_students(created_ids)
                if public_url:
                    self.message_user(
                        request,
                        mark_safe(f"👤 تم إنشاء {created_count} مستخدم عشوائي. تنزيل الملف: <a href='{public_url}' target='_blank'>تحميل CSV</a>"),
                        level=messages.SUCCESS,
                    )
                else:
                    self.message_user(
                        request,
                        f"👤 تم إنشاء {created_count} مستخدم. حُفظ CSV في: {file_path}",
                        level=messages.INFO,
                    )
            else:
                self.message_user(request, "لا يوجد طلاب جدد لإنشاء مستخدمين لهم.", level=messages.WARNING)

        except Exception as e:
            self.message_user(request, f"حدث خطأ أثناء الاستيراد: {e}", level=messages.ERROR)

        return redirect(changelist_url)





# conttroll_app/admin.py
# from django.contrib import admin, messages
# from django.shortcuts import redirect
# from django.urls import path, reverse

# from .models import student_report_from_uivercity
# from .services.import_students import import_students_from_excel

# @admin.register(student_report_from_uivercity)
# class StudentReportAdmin(admin.ModelAdmin):
#     change_list_template = "admin/conttroll_app/student_report_from_uivercity/change_list.html"

#     # استبدل 'semester' بـ 'semester_display'
#     list_display = ("id", "name", "gender", "univercity_number", "major", "semester_display")
#     search_fields = ("name", "univercity_number", "major")

#     # فلترة مرنة حسب الحقول الموجودة فعلاً
#     def get_list_filter(self, request):
#         field_names = {f.name for f in self.model._meta.get_fields()}
#         filters = ["gender"]
#         if "semester" in field_names:
#             filters.append("semester")       # FK موجودة فعليًا
#         elif "semester_id" in field_names:
#             filters.append("semester_id")    # IntegerField موجود فعليًا
#         return filters

#     # عرض مرن لقيمة الفصل
#     def semester_display(self, obj):
#         # لو عندك FK اسمها semester
#         if hasattr(obj, "semester") and getattr(obj, "semester") is not None:
#             return str(getattr(obj, "semester"))
#         # fallback: لو عندك حقل رقمي اسمه semester_id
#         return getattr(obj, "semester_id", "")
#     semester_display.short_description = "الفصل الدراسي"

#     def get_urls(self):
#         urls = super().get_urls()
#         info = (self.model._meta.app_label, self.model._meta.model_name)
#         custom = [
#             path(
#                 "import-excel/",
#                 self.admin_site.admin_view(self.import_excel),
#                 name=f"{info[0]}_{info[1]}_import",
#             ),
#         ]
#         return custom + urls

#     def import_excel(self, request):
#         info = (self.model._meta.app_label, self.model._meta.model_name)
#         changelist_url = reverse(f"admin:{info[0]}_{info[1]}_changelist")

#         if request.method != "POST":
#             return redirect(changelist_url)

#         f = request.FILES.get("file")
#         sheet = request.POST.get("sheet") or "ورقة1"
#         header_row = request.POST.get("header_row") or "1"

#         if not f:
#             self.message_user(request, "لم يتم اختيار ملف.", level=messages.ERROR)
#             return redirect(changelist_url)

#         try:
#             header_row = int(header_row)
#         except ValueError:
#             header_row = 1

#         try:
#             result = import_students_from_excel(f, sheet_name=sheet, header_row=header_row)
#             self.message_user(
#                 request,
#                 f"✅ تم إدخال {result['students_created']} طالب، وإنشاء {result['terms_created']} فصل/سنة. (الصفوف المقروءة: {result['rows']})",
#                 level=messages.SUCCESS,
#             )
#         except Exception as e:
#             self.message_user(request, f"حدث خطأ أثناء الاستيراد: {e}", level=messages.ERROR)

#         return redirect(changelist_url)





class ExcelUploadForm(forms.Form):
    file = forms.FileField(label="ملف الإكسل (.xlsx)")
    sheet = forms.CharField(label="اسم الشيت", initial="ورقة1", required=False)
    header_row = forms.IntegerField(label="رقم صف العناوين (Header)", initial=1, min_value=0) 

class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "marks_obtained", "total_marks",  "attempt_number", "locked")
    list_filter = ()
    search_fields = ("student__username", "student__full_name", "exam__name", "exam__course__code")

class CourseGradeAdmin(admin.ModelAdmin):
    list_display = ("course","student", "semester", "total_mark", "letter_grade", "is_passed")
    list_filter = ()
    search_fields = ("student__username", "student__full_name", "course__code", "course__name")
    actions = ["recompute_selected"]
    # readonly_fields=("midterm_mark","final_mark","grade_points","student", "course", "academic_year", "semester", "total_mark", "letter_grade", "is_passed")
    fieldsets = (
        (None, {
            "fields": (
                "classwork_mark","student", "course", "semester", "total_mark", "letter_grade", "is_passed"
                
            ),
        }),
    )

    @admin.action(description="إعادة احتساب الدرجات المختارة")
    def recompute_selected(self, request, queryset):
        for cg in queryset:
            cg.recompute()
        self.message_user(request, f"تمت إعادة احتساب {queryset.count()} سجل.")





class ReportPresetAdmin(ReadOnlyViewAdminMixin,admin.ModelAdmin):
    list_display = ('name', 'report_type', 'human_summary_col', 'owner', 'pinned', 'created_at', 'open_link')
    list_filter = ('report_type', 'pinned', 'owner')
    search_fields = ('name',)

    def human_summary_col(self, obj):
        return obj.human_summary
    human_summary_col.short_description = "التفاصيل"

    def open_link(self, obj):
        return format_html('<a class="button" target="_blank" href="{}">تشغيل</a>', obj.run_url)
    open_link.short_description = "تشغيل"




class student_report_from_uivercity_admin(admin.ModelAdmin):
    list_display = ('row_number', 'name','major', 'gender', 'univercity_number', 'semester_id')
    list_filter = ()
    search_fields = ('name', 'gender','major', 'univercity_number', 'semester_id')
    list_per_page = 100  # عرض 100 صف لكل صفحة
    list_max_show_all = 2000  # زر "عرض الكل" إذا أحب المستخدم عرض كل الصفوف

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            cl = response.context_data['cl']  # ChangeList
            # ترقيم حسب النتائج المعروضة فقط (صفحة واحدة)
            for index, obj in enumerate(cl.result_list, start=1):
                obj.row_number_val = index
        except (AttributeError, KeyError):
            pass
        return response

    def row_number(self, obj):
        return getattr(obj, 'row_number_val', '-')
    row_number.short_description = "م"


class Acdimaic_and_term_from_uivercity_admin(admin.ModelAdmin):
    list_display = ('Acdimaic_year', 'Acdimaic_year_semester')

class student_courses_grads_admin(admin.ModelAdmin):
    list_display = ('student', 'course','midterm_mark','final_mark','classwork_mark','total_mark')




# سجّل بقية الموديلات لديك إن لم تكن مسجلة
admin.site.register(ExamHall)
admin.site.register(ExamSchedule)
# admin.site.register(student_report_from_uivercity,student_report_from_uivercity_admin)
admin.site.register(Acdimaic_and_term_from_uivercity,Acdimaic_and_term_from_uivercity_admin)
admin.site.register(student_courses_grads,student_courses_grads_admin)
# admin.site.register(StudentReportAdmin)