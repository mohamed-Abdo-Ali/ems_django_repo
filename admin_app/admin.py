from django.contrib import admin
from .models import Department,Major,Batch,Level,Course,Semester,AcademicYear

from taecher_app.models import CourseStructure
from conttroll_app.models import CourseEnrollment
class Admin_panel_Department(admin.ModelAdmin) :
    list_display = ['name','code']
    
class Admin_panel_Major(admin.ModelAdmin) :
    list_display = ['name','department','code']
    
class Admin_panel_Batch(admin.ModelAdmin) :
    list_display = ['name','major','order']
    
class Admin_panel_Level(admin.ModelAdmin) :
    list_display = ['name','order','code']
    
class Admin_panel_Course(admin.ModelAdmin) :
    list_display = ['name','course_type','code','is_active','instructor','major','semester']
    
    
class Admin_panel_CourseStructure(admin.ModelAdmin):
    list_display = ['final_exam_max','midterm_exam_max','class_work_max','structure']
    
class Admin_panel_CourseEnrollment(admin.ModelAdmin) :
    list_display = ['grade','is_repeat','enrollment_date','semester','course','student']
    
# Register your models here.
admin.site.register(Department, Admin_panel_Department)
admin.site.register(Major, Admin_panel_Major)
admin.site.register(Level, Admin_panel_Level)
admin.site.register(Semester)
admin.site.register(Batch, Admin_panel_Batch)
admin.site.register(Course, Admin_panel_Course)
admin.site.register(CourseStructure, Admin_panel_CourseStructure)
admin.site.register(CourseEnrollment, Admin_panel_CourseEnrollment)
admin.site.register(AcademicYear)



