from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.admin.models import LogEntry, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
from .models import Course
from conttroll_app.models import CourseEnrollment
from authentcat_app.models import Student

# 1. إشارة للتسجيل التلقائي عند إنشاء/تحديث المقرر
@receiver(post_save, sender=Course)
def handle_course_changes(sender, instance, created, **kwargs):
    """
    معالجة تغييرات المقرر (إنشاء/تحديث)
    """
    students = Student.objects.filter(
        Major=instance.major,
        Semester=instance.semester
    )
    
    enrollments = [
        CourseEnrollment(
            student=student,
            course=instance,
            semester=instance.semester,
            is_repeat=False,
            grade=None
        )
        for student in students
    ]
    
    with transaction.atomic():
        # 1. التسجيل في المقرر للطلاب الجدد
        created_count = CourseEnrollment.objects.bulk_create(
            enrollments,
            ignore_conflicts=True
        )
        
        # 2. حذف تسجيلات الطلاب الذين لم يعودوا في نفس التخصص/الفصل
        CourseEnrollment.objects.filter(
            course=instance
        ).exclude(
            student__in=students
        ).delete()
    
    # تسجيل الحدث
    action = 'إنشاء' if created else 'تحديث'
    LogEntry.objects.log_action(
        user_id=1,  # استبدال برقم المستخدم المسؤول
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=str(instance),
        action_flag=ADDITION,
        change_message=f'تم {action} المقرر وتسجيل {len(created_count)} طالب'
    )

# 2. إشارة لحذف تسجيلات المقرر عند حذفه
@receiver(pre_delete, sender=Course)
def handle_course_deletion(sender, instance, **kwargs):
    """
    حذف جميع تسجيلات المقرر عند حذفه
    """
    deleted_count, _ = CourseEnrollment.objects.filter(
        course=instance
    ).delete()
    
    LogEntry.objects.log_action(
        user_id=1,
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=str(instance),
        action_flag=DELETION,
        change_message=f'تم حذف المقرر و{deleted_count} تسجيل طالب'
    )

# 3. إشارة لحذف تسجيلات الطالب عند حذفه
@receiver(pre_delete, sender=Student)
def handle_student_deletion(sender, instance, **kwargs):
    """
    حذف جميع تسجيلات الطالب عند حذفه
    """
    deleted_count, _ = CourseEnrollment.objects.filter(
        student=instance
    ).delete()
    
    LogEntry.objects.log_action(
        user_id=1,
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=str(instance),
        action_flag=DELETION,
        change_message=f'تم حذف الطالب و{deleted_count} تسجيل مقرر'
    )