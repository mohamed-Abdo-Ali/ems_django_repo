from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student
from admin_app.models import Course
from conttroll_app.models import CourseEnrollment

@receiver(post_save, sender=Student)
def auto_enroll_student_in_courses(sender, instance, created, **kwargs):
    """
    تسجيل/تحديث تسجيلات الطالب في المقررات عند أي تغيير في بياناته
    """
    # الحصول على المقررات الحالية للتخصص والفصل الدراسي
    current_courses = Course.objects.filter(
        major=instance.Major,
        semester=instance.Semester
    )
    
    # 1. التسجيل في المقررات الجديدة غير المسجلة
    for course in current_courses:
        CourseEnrollment.objects.get_or_create(
            student=instance,
            course=course,
            semester=instance.Semester,
            defaults={'is_repeat': False, 'grade': None}
        )
    
    # 2. إلغاء تسجيل المقررات التي لم تعد متاحة (اختياري)
    # احذف هذا الجزء إذا كنت تريد الاحتفاظ بالسجلات التاريخية
    CourseEnrollment.objects.filter(
        student=instance
    ).exclude(
        course__in=current_courses
    ).delete()