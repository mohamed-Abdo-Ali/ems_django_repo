from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from authentcat_app.models import User,BasicUser
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, EmailValidator
from django.db.models import Q

# from .models import Semester
User = get_user_model()




# ==================== University table ==========================================================
class University(models.Model):
    name = models.CharField(
        "اسم الجامعة",
        max_length=255,
        unique=True,            # لا تتكرر نفس الجامعة
        blank=False,
        null=False
    )
    address = models.TextField("عنوان الجامعة", blank=True)
    email = models.EmailField(
        "البريد الإلكتروني",
        unique=True,            # لا يتكرر نفس البريد
        validators=[EmailValidator(message="صيغة البريد الإلكتروني غير صحيحة")]
    )
    phone = models.CharField(
        "رقم الهاتف",
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{7,15}$',
                message="رقم الهاتف يجب أن يكون من 7 إلى 15 رقم ويمكن أن يبدأ بـ +"
            )
        ]
    )
    logo = models.ImageField(
        "شعار الجامعة",
        upload_to="university_logos/",
        blank=True,
        null=True
    )

    def clean(self):
        # تحقق إضافي: الاسم لا يكون فراغ فقط
        if not self.name.strip():
            raise ValidationError({"name": "اسم الجامعة لا يمكن أن يكون فارغاً."})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "جامعة"
        verbose_name_plural = "الجامعات"
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                check=~Q(name=""),   # الاسم لا يكون فارغ نصياً
                name="university_name_not_empty"
            )
        ]




# ==================== College table ==========================================================
class College(models.Model):
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name="colleges",
        verbose_name="الجامعة"
    )
    name = models.CharField(
        "اسم الكلية",
        max_length=255,
        blank=False,
        null=False
    )

    def clean(self):
        # تحقق إضافي: الاسم لا يكون فراغ فقط
        if not self.name.strip():
            raise ValidationError({"name": "اسم الكلية لا يمكن أن يكون فارغاً."})

    def __str__(self):
        return f"{self.name} - {self.university.name}"

    class Meta:
        verbose_name = "كلية"
        verbose_name_plural = "الكليات"
        ordering = ['name']
        constraints = [
            # لا تتكرر نفس الكلية داخل نفس الجامعة
            models.UniqueConstraint(
                fields=['university', 'name'],
                name="unique_college_per_university"
            ),
            models.CheckConstraint(
                check=~Q(name=""),
                name="college_name_not_empty"
            )
        ]




# ==================== Department table ==========================================================
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم القسم")
    code = models.CharField(max_length=20, unique=True, verbose_name="كود القسم")
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="Dept_colleges", verbose_name="الكلية")
    
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
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='majors',verbose_name="القسم")
    
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
        


# ==================== Catalog of courses ==========================================================
class CourseCatalog(models.Model):
    
    COURSE_TYPES = (
        (1, 'نظري'),
        (2, 'عملي'),
    )
    
    COURSE_STATUS = (
        (True, 'فعال'),
        (False, 'غير فعال'),
    )
    name = models.CharField(max_length=100, verbose_name="اسم المقرر")
    code = models.CharField(max_length=20, unique=True, verbose_name="كود المقرر")
    description = models.TextField(blank=True, null=True, verbose_name="وصف المقرر")
    course_type = models.PositiveSmallIntegerField(choices=COURSE_TYPES,verbose_name="نوع المقرر")
    is_active = models.BooleanField(choices=COURSE_STATUS, default=True)
    
    
    class Meta:
        verbose_name = "مقرر (كتالوج)"
        verbose_name_plural = "المقررات (كتالوج)"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"



# ==================== Instance of a course being taught =================================================
class Course(CourseCatalog):

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='courses', verbose_name="الفصل الدراسي")
    instructor = models.ForeignKey('authentcat_app.Teacher', on_delete=models.SET_NULL, null=True, related_name='courses', verbose_name="المعلم")
    major = models.ForeignKey('admin_app.Major', on_delete=models.CASCADE, related_name='courses',verbose_name="التخصص")

    class Meta:
        verbose_name = "مقرر"
        verbose_name_plural = "المقررات"
        ordering = ['semester']


    def __str__(self):
        return f"{self.name} ({self.major})"





