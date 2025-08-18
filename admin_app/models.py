from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from authentcat_app.models import User,BasicUser
# from .models import Semester

User = get_user_model()

# ==================== Department table ==========================================================
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم القسم")
    code = models.CharField(max_length=20, unique=True, verbose_name="كود القسم")
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        verbose_name = "قسم"
        verbose_name_plural = "الأقسام"
        ordering = ['name']


# ==================== Major table ==========================================================
class Major(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم التخصص")
    code = models.CharField(max_length=20, unique=True, verbose_name="كود التخصص")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='majors')
    
    def __str__(self):
        return f"{self.name} - {self.department.name}"
    
    def clean(self):
        if Major.objects.filter(name=self.name, department=self.department).exclude(pk=self.pk).exists():
            raise ValidationError({'name': 'هذا الاسم مستخدم بالفعل في هذا القسم'})
    
    class Meta:
        verbose_name = "تخصص"
        verbose_name_plural = "التخصصات"
        ordering = ['department__name', 'name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'department'], name='unique_major_per_department')
        ]



# # ==================== Batch table ==========================================================
class Batch(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم الدفعة")
    enrollment_year = models.PositiveIntegerField(verbose_name="سنة القيد", editable=False)
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='التخصص')
    order = models.PositiveSmallIntegerField(verbose_name="ترتيب الدفعة", editable=False)
    
    def __str__(self):
        return f" الدفعة : {self.major.department.name} - {self.major.name} - {self.order} - {self.name} - ({self.enrollment_year})"
    
    def save(self, *args, **kwargs):
        # تعيين سنة القيد إذا لم يتم توفيرها
        if not self.enrollment_year:
            self.enrollment_year = timezone.now().year
        
        # تعيين الترتيب التلقائي لكل تخصص
        if not self.pk and not self.order:
            last_batch = Batch.objects.filter(major=self.major).order_by('-order').first()
            self.order = (last_batch.order + 1) if last_batch else 1
        
        super().save(*args, **kwargs)
    
    def clean(self):
        # التحقق من عدم تكرار اسم الدفعة لنفس التخصص
        if Batch.objects.filter(name=self.name, major=self.major).exclude(pk=self.pk).exists():
            raise ValidationError({'name': 'هذا الاسم مستخدم بالفعل لهذا التخصص'})
        
        # التحقق من عدم تكرار الترتيب لنفس التخصص
        if self.order and Batch.objects.filter(major=self.major, order=self.order).exclude(pk=self.pk).exists():
            raise ValidationError({'order': 'هذا الترتيب مستخدم بالفعل لهذا التخصص'})
    
    class Meta:
        verbose_name = "دفعة"
        verbose_name_plural = "الدفعات"
        ordering = ['major__name', 'order']
        constraints = [
            models.UniqueConstraint(fields=['name', 'major'], name='unique_batch_per_major'),
            models.UniqueConstraint(fields=['major', 'order'], name='unique_order_per_major')
        ]



# ==================== Level table ==========================================================
class Level(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="اسم المستوى")
    code = models.CharField(max_length=20, unique=True, verbose_name="كود المستوى")
    order = models.PositiveSmallIntegerField(unique=True, verbose_name="ترتيب المستوى")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "مستوى"
        verbose_name_plural = "المستويات"
        ordering = ['order']




# ==================== Semester table ==========================================================
class Semester(models.Model):
    """جدول الفصول الدراسية"""

    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الفصل")
    code = models.CharField(max_length=20, unique=True, verbose_name="كود الفصل")
    level = models.ForeignKey(Level, on_delete=models.CASCADE,  related_name='semester' ,verbose_name="المستوى")
    order = models.PositiveSmallIntegerField(unique=True,verbose_name="ترتيب الفصول الدراسية")

    
    def __str__(self):
        return f"{self.name}"
    
    
    class Meta:
        verbose_name = "فصل دراسي"
        verbose_name_plural = "الفصول الدراسية"
        ordering = ['order']
        



# ==================== Course table ==========================================================
class Course(models.Model):
    COURSE_TYPES = (
        (1, 'نظري'),
        (2, 'عملي'),
        (3, 'نظري/عملي'),
    )
    
    COURSE_STATUS = (
        (True, 'فعال'),
        (False, 'غير فعال'),
    )
    
    name = models.CharField(max_length=100, verbose_name="اسم المقرر")
    code = models.CharField(max_length=20, unique=True, verbose_name="كود المقرر")
    is_active = models.BooleanField(choices=COURSE_STATUS, default=True)
    course_type = models.PositiveSmallIntegerField(choices=COURSE_TYPES)
    instructor = models.ForeignKey('authentcat_app.Teacher', on_delete=models.SET_NULL, null=True,
                        related_name='courses', verbose_name="المعلم")
    
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='courses')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, 
                            related_name='courses', verbose_name="الفصل الدراسي")
    def clean(self):
        if Course.objects.filter(name=self.name, major=self.major).exclude(pk=self.pk).exists():
            raise ValidationError({'name': 'هذا الاسم مستخدم بالفعل لهذا التخصص'}) 

    def __str__(self):
        return f" {self.major.department.name} - {self.major.name} - {self.semester.name} - {self.semester.level.name} - {self.name} - {self.code} - {self.instructor.basic_user.user.full_name}"


    
    class Meta:
        verbose_name = "مقرر"
        verbose_name_plural = "المقررات"
        ordering = ['major__name', 'code']
        constraints = [
            models.UniqueConstraint(fields=['name', 'major'], name='unique_course_name_per_major')
        ]

# ==================== CourseStructure table ==========================================================
class CourseStructure(models.Model):
    final_exam_max = models.PositiveIntegerField(verbose_name="الدرجة العظمى للامتحان النهائي")
    midterm_exam_max = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="الدرجة العظمى للامتحان النصفي")
    class_work_max = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="الدرجة العظمى لأعمال الفصل")
    structure = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='course')
    
    def clean(self):
        if self.structure.course_type == 1 and self.final_exam_max != 100:
            raise ValidationError("المقرر النظري يجب أن يكون مجموعه 100 درجة")
        elif self.structure.course_type == 2 and self.final_exam_max != 50:
            raise ValidationError("المقرر العملي يجب أن يكون مجموعه 50 درجة")      

        


    class Meta:
        verbose_name = "هيكل المقرر"
        verbose_name_plural = "هياكل المقررات"
        
        
# ==================== CourseEnrollment table ==========================================================
class CourseEnrollment(models.Model):
    student = models.ForeignKey('authentcat_app.Student', on_delete=models.CASCADE, 
                            related_name='enrollments', verbose_name="الطالب")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                            related_name='enrollments', verbose_name="المقرر")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, 
                            related_name='enrollments', verbose_name="الفصل الدراسي")
    enrollment_date = models.DateField(auto_now_add=True, verbose_name="تاريخ التسجيل")
    is_repeat = models.BooleanField(default=False, verbose_name="إعادة تسجيل")
    grade = models.CharField(max_length=2, blank=True, null=True, verbose_name="الدرجة")
    
    def __str__(self):
        return f"{self.student.user.full_name} - {self.course} ({self.semester})"
    
    class Meta:
        verbose_name = "تسجيل مقرر"
        verbose_name_plural = "تسجيلات المقررات"
        ordering = ['-enrollment_date']
        constraints = [
            models.UniqueConstraint(fields=['student', 'course', 'semester'], name='unique_enrollment')
        ]