# conttroll_app/admin.py
from django.contrib import admin
from .models import  Acdimaic_and_term_from_uivercity, ExamSchedule, ExamHall, student_courses_grads, student_report_from_uivercity
from django.contrib import admin
from django.utils.html import format_html
from authentcat_app.admin import ReadOnlyViewAdminMixin 

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
admin.site.register(student_report_from_uivercity,student_report_from_uivercity_admin)
admin.site.register(Acdimaic_and_term_from_uivercity,Acdimaic_and_term_from_uivercity_admin)
admin.site.register(student_courses_grads,student_courses_grads_admin)