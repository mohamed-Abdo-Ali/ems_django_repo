# # admin.py
# from django import forms
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from .models import User, Profile, Student, BasicUser, Teacher, ControlCommitteeMember, Manager
# from admin_app.models import Batch,Major
# from authentcat_app.models import Semester
# from django.contrib.auth import get_user_model

# class StudentCreationForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ('username', 'password', 'full_name', 'gender', 'photo')
        
#     university_id = forms.CharField(max_length=20)
#     Batch = forms.ModelChoiceField(queryset=Batch.objects.all())
#     Major = forms.ModelChoiceField(queryset=Major.objects.all())
#     Semester = forms.ModelChoiceField(queryset=Semester.objects.all())
#     registration_type = forms.ChoiceField(choices=Student.RegistrationTypes.choices)
    
#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.user_type = User.UserTypes.STUDENT
#         if commit:
#             user.save()
#             student = Student.objects.create(
#                 user=user,
#                 university_id=self.cleaned_data['university_id'],
#                 Batch=self.cleaned_data['Batch'],
#                 Major=self.cleaned_data['Major'],
#                 Semester=self.cleaned_data['Semester'],
#                 registration_type=self.cleaned_data['registration_type']
#             )
#         return user

# class TeacherCreationForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ('username', 'password', 'full_name', 'gender', 'photo')
        
#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.user_type = User.UserTypes.BASIC
#         if commit:
#             user.save()
#             basic_user = BasicUser.objects.create(
#                 user=user,
#                 basic_user_type=BasicUser.UserTypes.TEACHER
#             )
#             teacher = Teacher.objects.create(basic_user=basic_user)
#         return user

# class ProfileInline(admin.StackedInline):
#     model = Profile
#     can_delete = False
#     verbose_name_plural = 'الملف الشخصي'
    
# class StudentInline(admin.StackedInline):
#     model = Student
#     can_delete = False
#     verbose_name_plural = 'بيانات الطالب'
#     fk_name = 'user'
    
# class BasicUserInline(admin.StackedInline):
#     model = BasicUser
#     can_delete = False
#     verbose_name_plural = 'بيانات المستخدم الأساسي'
#     fk_name = 'user'

# class UserAdmin(BaseUserAdmin):
#     inlines = (ProfileInline,)
#     list_display = ('username', 'full_name', 'user_type', 'is_active')
#     list_filter = ('user_type', 'is_active')
    
#     fieldsets = (
#         (None, {'fields': ('username', 'password')}),
#         ('معلومات الشخصية', {'fields': ('full_name', 'gender', 'photo')}),
#         ('الصلاحيات', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type', 'groups', 'user_permissions')}),
#         ('تواريخ مهمة', {'fields': ('last_login', 'created_at', 'updated_at')}),
#     )
    
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('username', 'password1', 'password2'),
#         }),
#     )
    
#     def get_inline_instances(self, request, obj=None):
#         if not obj:
#             return []
#         inlines = super().get_inline_instances(request, obj)
#         if obj.is_student:
#             inlines.append(StudentInline(self.model, self.admin_site))
#         elif obj.is_basic:
#             inlines.append(BasicUserInline(self.model, self.admin_site))
#         return inlines
    
#     def get_formsets_with_inlines(self, request, obj=None):
#         for inline in self.get_inline_instances(request, obj):
#             yield inline.get_formset(request, obj), inline

# class StudentAdmin(admin.ModelAdmin):
#     form = StudentCreationForm
#     list_display = ('university_id', 'user', 'Major', 'Semester')
    
#     def get_form(self, request, obj=None, **kwargs):
#         if obj is None:
#             return StudentCreationForm
#         return super().get_form(request, obj, **kwargs)

# class TeacherAdmin(admin.ModelAdmin):
#     form = TeacherCreationForm
#     list_display = ('basic_user',)
    
#     def get_form(self, request, obj=None, **kwargs):
#         if obj is None:
#             return TeacherCreationForm
#         return super().get_form(request, obj, **kwargs)

# # إلغاء التسجيل الافتراضي ثم إعادة التسجيل مع التخصيصات

# User = get_user_model()
# # فقط ألغي التسجيل إذا كان النموذج مسجلاً بالفعل
# # if admin.site.is_registered(User):
# # admin.site.unregister(User)
# admin.site.register(User, UserAdmin)
# admin.site.register(Student, StudentAdmin)
# admin.site.register(Teacher, TeacherAdmin)
# admin.site.register(ControlCommitteeMember)
# admin.site.register(Manager)









from django.contrib import admin

# from authentcat_app.models import User,Student,BasicUser,Teacher,ControlCommitteeMember,Manager
from authentcat_app.models import User,Student,BasicUser,Teacher,ControlCommitteeMember,Manager,Profile
from django.contrib.auth.models import  Permission,Group

# Register your models here.
admin.site.register(User)
admin.site.register(Student)
admin.site.register(BasicUser)
admin.site.register(Teacher)
admin.site.register(ControlCommitteeMember)
admin.site.register(Manager)
admin.site.register(Profile)
# admin.site.register(Semester)
admin.site.register(Permission)



