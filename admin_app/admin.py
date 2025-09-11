from pyexpat.errors import messages
from django.contrib import admin
from .models import Department,Major,Level,Course,Semester,University,College
from django.urls import reverse
from django.shortcuts import redirect
from django import forms
from django.forms.widgets import SelectDateWidget
from taecher_app.models import CourseStructure
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.html import format_html  # <== أضف هذا السطر





# ==================== Forms with Validation ====================================================
class UniversityForm(ModelForm):
    class Meta:
        model = University
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name", "").strip()

        if not name:
            raise ValidationError({"name": "اسم الجامعة لا يمكن أن يكون فارغاً أو مسافات فقط."})

        return cleaned_data


class CollegeForm(ModelForm):
    class Meta:
        model = College
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name", "").strip()

        if not name:
            raise ValidationError({"name": "اسم الكلية لا يمكن أن يكون فارغاً أو مسافات فقط."})

        return cleaned_data


# ==================== UniversityAdmin Classes ============================================================
class UniversityAdmin(admin.ModelAdmin):
    form = UniversityForm
    list_display = ("name", "address", "email", "phone", "logo_preview")
    search_fields = ("name", "email", "phone")
    ordering = ("name",)

    def logo_preview(self, obj):
        if obj.logo and hasattr(obj.logo, "url"):
            # تحقق من امتداد الملف
            ext = obj.logo.url.split('.')[-1].lower()
            if ext == 'svg':
                # SVG يمكن عرضه مباشرة
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer">'
                    '<img src="{}" width="60" height="60" style="object-fit:contain;" />'
                    '</a>',
                    obj.logo.url, obj.logo.url
                )
            else:
                # باقي الصور النقطية
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer">'
                    '<img src="{}" width="60" height="60" style="object-fit:contain;" />'
                    '</a>',
                    obj.logo.url, obj.logo.url
                )
        return "لا يوجد شعار"
    logo_preview.short_description = "الشعار"
# ==================== CollegeAdmin Classes ============================================================
class CollegeAdmin(admin.ModelAdmin):
    form = CollegeForm
    list_display = ("name", "university")
    search_fields = ("name", "university__name")
    list_filter = ("university",)
    ordering = ("name",)




# ==================== Admin_panel_Department table ==========================================================
class Admin_panel_Department(admin.ModelAdmin) :
    list_display = ['name','code','college']
    



# ==================== Admin_panel_Major table ==========================================================
class Admin_panel_Major(admin.ModelAdmin) :
    list_display = ['name','department','code']



# ==================== Admin_panel_Level table ==========================================================
class Admin_panel_Level(admin.ModelAdmin) :
    list_display = ['name','order','code']





# ==================== Admin_panel_CourseStructure table =========================================================
class Admin_panel_CourseStructure(admin.ModelAdmin):
    list_display = ['final_exam_max','midterm_exam_max','class_work_max','structure']



# ==================== Admin_panel_Course table ==========================================================
class Admin_panel_Course(admin.ModelAdmin):
    list_display = ['name','course_type','code','is_active','instructor','major','semester']




# Register your models here.
admin.site.register(University, UniversityAdmin)
admin.site.register(College, CollegeAdmin)
admin.site.register(Department, Admin_panel_Department)
admin.site.register(Major, Admin_panel_Major)
admin.site.register(Level, Admin_panel_Level)
admin.site.register(Semester)
admin.site.register(Course, Admin_panel_Course)
admin.site.register(CourseStructure, Admin_panel_CourseStructure)



