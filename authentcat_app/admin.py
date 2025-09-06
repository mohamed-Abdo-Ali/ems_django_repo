from typing import __all__
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from authentcat_app.models import User, Student, BasicUser, Teacher, ControlCommitteeMember, Manager, Profile, buffer_Student
from django.contrib.auth.models import Permission, Group
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError



# =============================== ReadOnlyViewAdminMixin =================================================================================================
class ReadOnlyViewAdminMixin:
    # منع الإضافة والتعديل
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # لا تعطل الحذف كي لا يتعطل الحذف المتسلسل من النماذج الفرعية
    def has_delete_permission(self, request, obj=None):
        return True

    # إزالة الحذف الجماعي من صفحة القائمة
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    # منع الحذف المباشر من صفحة هذا الموديل
    def delete_view(self, request, object_id, extra_context=None):
        raise PermissionDenied("لا يمكن الحذف من هذه الصفحة. احذف من النماذج الفرعية (Teacher/Student/Manager/ControlCommitteeMember).")



# =============================== UserAdminPanel =================================================================================================
class UserAdminPanel(ReadOnlyViewAdminMixin, UserAdmin):
    ordering = ('user_type', 'id')
    list_filter = ()
    list_display = (
        'username',
        'full_name', 'gender', 'user_type',
        'created_at', 'updated_at',
        'last_login', 'is_active', 'is_superuser', 'is_staff',
        'get_groups'
    )

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = "المجموعات"

    filter_horizontal = ('groups', 'user_permissions')
    
    readonly_fields = ['created_at', 'updated_at','username','full_name','gender','user_type','photo','is_active','is_staff','is_superuser']
    

    search_fields = ['username', 'full_name', 'user_type']



# =============================== BasicUserAdminPanel =================================================================================================
class BasicUserAdminPanel(ReadOnlyViewAdminMixin , UserAdmin):
    ordering = ('basic_user_type', 'id')
    list_filter = ()
    list_display = (
        'username',
        'full_name', 'gender', 'user_type', 'basic_user_type',
        'last_login', 'is_active', 'is_superuser', 'is_staff',
        'get_groups'
    )

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = "المجموعات"

    readonly_fields = ['username','full_name','gender','user_type','basic_user_type','last_login','is_active','is_superuser','is_staff']


    search_fields = ['username', 'full_name', 'user_type', 'basic_user_type']



# =============================== TeacherAdminPanel =================================================================================================
class TeacherAdminPanel(UserAdmin):
    list_filter = ()  # ما في فلترة
    list_display = [ 'id','username', 'full_name', 'gender', 'is_active','last_login']
    ordering = ['id']  # الترتيب حسب id تصاعدياً
    filter_horizontal = ('groups', 'user_permissions')
    
    
    # fieldsets لصفحة التعديل
    fieldsets = (
        (None, {
            'fields': ('username', 'full_name', 'gender', 'photo', 'is_active', 'groups', 'user_permissions')
        }),
    )
    
    # add_fieldsets لصفحة الإضافة
    add_fieldsets = (
        (None, {
            'fields': ('username', 'password1', 'password2', 'full_name', 'gender')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان إنشاء جديد
            obj.created_by = request.user
        obj.updated_by = request.user  # عند التعديل دائماً
        obj.basic_user_type = obj.UserTypes.TEACHER  # تحديد نوع المستخدم
        super().save_model(request, obj, form, change)





    
# =============================== ManagerAdminPanel =================================================================================================
class ManagerAdminPanel(UserAdmin):
    list_filter = ()  # ما في فلترة
    list_display = [ 'id','username', 'full_name', 'gender', 'is_active','last_login']
    ordering = ['id']  # الترتيب حسب id تصاعدياً
    filter_horizontal = ('groups', 'user_permissions')
    
    
    # fieldsets لصفحة التعديل
    fieldsets = (
        (None, {
            'fields': ('username', 'full_name', 'gender', 'photo', 'is_active', 'groups', 'user_permissions')
        }),
    )
    
    # add_fieldsets لصفحة الإضافة
    add_fieldsets = (
        (None, {
            'fields': ('username', 'password1', 'password2', 'full_name', 'gender')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان إنشاء جديد
            if User.objects.count() == 1:
                obj.created_by = obj
                obj.updated_by = obj
            else :
                obj.created_by = request.user
        else :
            obj.updated_by = request.user  # عند التعديل دائماً
        obj.basic_user_type = obj.UserTypes.MANAGER  # تحديد نوع المستخدم
        super().save_model(request, obj, form, change)





    
# =============================== ControlCommitteeMemberAdminPanel =================================================================================================
class ControlCommitteeMemberAdminPanel(UserAdmin):
    list_filter = ()  # ما في فلترة
    list_display = [ 'id','username', 'full_name', 'gender', 'is_active','last_login']
    ordering = ['id']  # الترتيب حسب id تصاعدياً
    filter_horizontal = ('groups', 'user_permissions')
    
    
    # fieldsets لصفحة التعديل
    fieldsets = (
        (None, {
            'fields': ('username', 'full_name', 'gender', 'photo', 'is_active', 'groups', 'user_permissions')
        }),
    )
    
    # add_fieldsets لصفحة الإضافة
    add_fieldsets = (
        (None, {
            'fields': ('username', 'password1', 'password2', 'full_name', 'gender')
        }),
    )

        
    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان إنشاء جديد
            obj.created_by = request.user
        obj.updated_by = request.user  # عند التعديل دائماً
        obj.basic_user_type = obj.UserTypes.COMMITTEE  # تحديد نوع المستخدم
        super().save_model(request, obj, form, change)




    
    
class StudentAdminPanel(UserAdmin):
    list_filter = ()  # ما في فلترة
    list_display = ['username', 'full_name', 'gender', 'is_active','last_login']
    filter_horizontal = ('groups', 'user_permissions')
    
    ordering = ['id']  # الترتيب حسب id تصاعدياً
    
    # fieldsets لصفحة التعديل
    fieldsets = (
        (None, {
            'fields': ('username', 'full_name', 'gender','photo', 'is_active', 'groups', 'user_permissions')
        }),
    )
    
    # add_fieldsets لصفحة الإضافة
    add_fieldsets = (
        (None, {
            'fields': ('username', 'password1', 'password2', 'full_name','gender')
        }),
    )
    
    
    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان إنشاء جديد
            obj.created_by = request.user
        obj.updated_by = request.user  # عند التعديل دائماً
        obj.basic_user_type = obj.UserTypes.STUDENT  # تحديد نوع المستخدم
        super().save_model(request, obj, form, change)
    
            
# admin.site.register(User)
admin.site.register(User,UserAdminPanel)
admin.site.register(Student,StudentAdminPanel)
admin.site.register(BasicUser,BasicUserAdminPanel)
admin.site.register(Teacher, TeacherAdminPanel)
admin.site.register(ControlCommitteeMember,ControlCommitteeMemberAdminPanel)
admin.site.register(Manager,ManagerAdminPanel)
admin.site.register(Profile)
admin.site.register(Permission)
admin.site.register(buffer_Student)