import logging

import string
import secrets

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from django.core.validators import RegexValidator
from django.db.models.signals import post_migrate
from django.apps import apps

# ======================== user table ================================================================
class User(AbstractUser):
    # إزالة الحقول غير المرغوب فيها
    first_name = None
    last_name = None
    email = None  # سيتم نقله للبروفايل
    date_joined = None
    last_login = None
    
    # تعريف خيارات الأنواع
    class UserTypes(models.IntegerChoices):
        BASIC = 1, _('أساسي')  # للمعلمين ومديرين اللجنة والمديرين
        STUDENT = 2, _('طالب')
    
    class GenderTypes(models.IntegerChoices):
        MALE = 1, _('ذكر')
        FEMALE = 0, _('أنثى')

    full_name = models.CharField(
        max_length=255,
        verbose_name='الاسم الكامل',
        unique=True,
        validators=[
            MinLengthValidator(3, message="يجب أن يكون الاسم الكامل على الأقل 3 أحرف"),
            MaxLengthValidator(255, message="يجب ألا يتجاوز الاسم الكامل 255 حرفًا"),
            RegexValidator(
                regex=r'^[\u0600-\u06FF\s]+$',
                message="يجب أن يحتوي الاسم الكامل على أحرف عربية فقط"
            )
        ]
    )
    gender = models.IntegerField(choices=GenderTypes.choices, verbose_name='النوع', default=1)
    user_type = models.IntegerField(choices=UserTypes.choices, verbose_name='نوع المستخدام', default=2)
    photo = models.ImageField(upload_to='photo/%Y/%m/%d', verbose_name='صورة المستخدام', default='photo/defualt_img.png')
    
    # حقول التتبع
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الانشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل') 
    
    
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users', verbose_name='المستخدام الذي انشئ')
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_users', verbose_name='المستخدام الذي عدل')
    
    
    
    
    # حقول الصلاحيات
    is_active = models.BooleanField(default=True, verbose_name='هل الحساب فعال')
    is_superuser = models.BooleanField(default=False, verbose_name='هل الحساب سوبر لة كل الصلاحيات', help_text='سوف يكون لة كل الصلاحيات انتبة')
    is_staff = models.BooleanField(default=False, verbose_name='هل الحساب من الموظفين')

    # علاقات المجموعات والأذونات
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')

    def __str__(self):
        return f"{self.full_name} - {self.username}"

    def clean(self):
        super().clean()
        
        
        
        # التحقق من أن الطالب لا يمكن أن يكون staff أو superuser
        if self.user_type == User.UserTypes.STUDENT:
            if self.is_staff or self.is_superuser:
                raise ValidationError(_("الطالب لا يمكن أن يكون من الموظفين أو المديرين العامين"))

        # التحقق من أن المستخدم لا يمكن أن يكون من نوعين مختلفين
        if hasattr(self, 'basicuser') and self.user_type != User.UserTypes.BASIC:
            raise ValidationError(_("المستخدم الأساسي يجب أن يكون من النوع الأساسي"))
        if hasattr(self, 'student') and self.user_type != User.UserTypes.STUDENT:
            raise ValidationError(_("الطالب يجب أن يكون من النوع طالب"))

    # وظائف مساعدة للتحقق من الأدوار
    @property
    def is_basic(self):
        return self.user_type == self.UserTypes.BASIC

    @property
    def is_student(self):
        return self.user_type == self.UserTypes.STUDENT

    @property
    def is_teacher(self):
        return hasattr(self, 'basicuser') and self.basicuser.basic_user_type == BasicUser.UserTypes.TEACHER

    @property
    def is_committee_member(self):
        return hasattr(self, 'basicuser') and self.basicuser.basic_user_type == BasicUser.UserTypes.COMMITTEE

    @property
    def is_manager(self):
        return hasattr(self, 'basicuser') and self.basicuser.basic_user_type == BasicUser.UserTypes.MANAGER

    @property
    def profile(self):
        if hasattr(self, '_profile'):
            return self._profile
        self._profile, created = Profile.objects.get_or_create(user=self)
        return self._profile


# =================== profile table =======================================================
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='_profile',
        verbose_name=_('المستخدم')
    )
    email = models.EmailField(_('البريد الإلكتروني'), unique=True)
    phone_number = models.CharField(
        _('رقم الهاتف'),
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+9677[1378]\d{7}$|^\+967\d{9}$',
                message="يجب أن يبدأ رقم الهاتف اليمني بـ +967 ويتبعه 9 أرقام (للموبايل: 7/3/8/1) أو 9 أرقام للخطوط الأرضية"
            )
        ]
    )
    
    class Meta:
        verbose_name = _('الملف الشخصي')
        verbose_name_plural = _('الملفات الشخصية')

    def __str__(self):
        return f"{self.user.username} - {self.email}"


@receiver(pre_save, sender=User)
def prevent_user_type_change(sender, instance, **kwargs):
    if instance.pk:
        original = User.objects.get(pk=instance.pk)
        if original.user_type != instance.user_type:
            raise ValidationError(_("لا يمكن تغيير نوع المستخدم بعد الإنشاء"))


# ====================== BasicUser  table (يرث من User) ======================================================================
class BasicUser(User):
    """
    نموذج للمستخدمين الأساسيين (يمكن أن يكونوا معلمين، لجنة، مديرين في نفس الوقت)
    """
    class UserTypes(models.IntegerChoices):
        MANAGER = 1, _('مدير')
        COMMITTEE = 2, _('عضو لجنة مراقبة')
        TEACHER = 3, _('معلم')
    
    basic_user_type = models.IntegerField(choices=UserTypes.choices, verbose_name='نوع المستخدم الأساسي')
    
    class Meta:
        verbose_name = _('مستخدم أساسي')
        verbose_name_plural = _('المستخدمون الأساسيون')

    def clean(self):
        super().clean()
        # التحقق من عدم وجود سجل طالب لنفس المستخدم
        if hasattr(self, 'student_ptr'):
            raise ValidationError(_("المستخدم لا يمكن أن يكون طالباً ومستخدماً أساسياً في نفس الوقت"))

    def save(self, *args, **kwargs):
        # التأكد من أن المستخدم من النوع الأساسي
        self.user_type = User.UserTypes.BASIC
        self.is_staff = True
        
        # إذا كان المدير Manager يصبح سوبر يوزر أيضًا
        if self.basic_user_type == self.UserTypes.MANAGER:
            self.is_superuser = True
        else:
            self.is_superuser = False
            
        super().save(*args, **kwargs)


@receiver(pre_save, sender=BasicUser)
def prevent_basic_user_type_change(sender, instance, **kwargs):
    if instance.pk:
        original = BasicUser.objects.get(pk=instance.pk)
        if original.basic_user_type != instance.basic_user_type:
            raise ValidationError(_("لا يمكن تغيير نوع المستخدم الأساسي بعد الإنشاء"))





# =============== Student  table (يرث من User) =======================================================================
class Student(User):

    class Meta:
        verbose_name = _('طالب')
        verbose_name_plural = _('الطلاب')

    def clean(self):
        super().clean()
        # التحقق من عدم وجود سجل مستخدم أساسي لنفس المستخدم
        if hasattr(self, 'basicuser_ptr'):
            raise ValidationError(_("المستخدم لا يمكن أن يكون طالباً ومستخدماً أساسياً في نفس الوقت"))

    def save(self, *args, **kwargs):
        # التأكد من أن المستخدم من النوع طالب
        self.user_type = User.UserTypes.STUDENT
        self.is_staff = False
        self.is_superuser = False
        super().save(*args, **kwargs)



# =============== buffer_Student  =======================================================================

from django.apps import apps
import csv, secrets, string

def create_buffer_users_secure_csv(file_path='buffer_users.csv'):
    StudentReport = apps.get_model('conttroll_app', 'student_report_from_uivercity')
    BufferStudent = apps.get_model('authentcat_app', 'buffer_Student')

    total_students = StudentReport.objects.count()

    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Username', 'Password'])

        for _ in range(total_students):
            username = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*()_+-=") for _ in range(16))
            BufferStudent.objects.create(username=username, password=password)
            writer.writerow([username, password])

class buffer_Student(models.Model):
    username = models.CharField(max_length=100 , verbose_name="اسم المستخدام")
    password = models.CharField(max_length=100, verbose_name="كملة المرور")

    class Meta:
        verbose_name = _('مستخدمين المؤقتين للطلاب العشوائين')
        verbose_name_plural = _('مستخدمين المؤقتين للطلاب العشوائين')


# ==================== Teacher table (يرث من BasicUser) ==========================================================
class Teacher(BasicUser):
    # يمكن إضافة حقول خاصة بالمعلم هنا إذا لزم الأمر
    
    class Meta:
        verbose_name = _('معلم')
        verbose_name_plural = _('المعلمون')

    def __str__(self):
        return f"{self.username} - معلم"

    def save(self, *args, **kwargs):
        self.basic_user_type = BasicUser.UserTypes.TEACHER
        super().save(*args, **kwargs)


# ==================== ControlCommitteeMember table (يرث من BasicUser) ==========================================================
class ControlCommitteeMember(BasicUser):
    # يمكن إضافة حقول خاصة بعضو اللجنة هنا إذا لزم الأمر
    
    class Meta:
        verbose_name = _('عضو لجنة مراقبة')
        verbose_name_plural = _('أعضاء لجنة المراقبة')

    def __str__(self):
        return f"{self.username} - عضو لجنة"

    def save(self, *args, **kwargs):
        self.basic_user_type = BasicUser.UserTypes.COMMITTEE
        super().save(*args, **kwargs)


# ==================== Manager table (يرث من BasicUser) ==========================================================
class Manager(BasicUser):
    # يمكن إضافة حقول خاصة بالمدير هنا إذا لزم الأمر
    
    class Meta:
        verbose_name = _('مدير')
        verbose_name_plural = _('المديرون')

    def __str__(self):
        return f"{self.username} - مدير"

    def save(self, *args, **kwargs):
        self.basic_user_type = BasicUser.UserTypes.MANAGER
        self.is_superuser = True
        super().save(*args, **kwargs)


# إشارات للتحقق من عدم وجود تضارب بين الطالب والمستخدم الأساسي
# ====================================================================================


@receiver(pre_save, sender=BasicUser)
def check_basic_user_constraints(sender, instance, **kwargs):
    # التحقق من عدم وجود سجل طالب بنفس البيانات
    if Student.objects.filter(username=instance.username).exclude(pk=instance.pk).exists():
        raise ValidationError(_("يوجد طالب بنفس اسم المستخدم"))
    
    # منع تغيير نوع المستخدم الأساسي بعد الإنشاء
    if instance.pk:
        original = BasicUser.objects.get(pk=instance.pk)
        if original.basic_user_type != instance.basic_user_type:
            raise ValidationError(_("لا يمكن تغيير نوع المستخدم الأساسي بعد الإنشاء"))


@receiver(pre_save, sender=Student)
def check_student_constraints(sender, instance, **kwargs):
    # التحقق من عدم وجود مستخدم أساسي بنفس البيانات
    if BasicUser.objects.filter(username=instance.username).exclude(pk=instance.pk).exists():
        raise ValidationError(_("يوجد مستخدم أساسي بنفس اسم المستخدم"))








# إشارات لإضافة المستخدمين إلى المجموعات المناسبة عند الإنشاء
# ====================================================================================
@receiver(post_save, sender=Teacher)
def add_teacher_to_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name='Teachers')
        instance.groups.add(group)


@receiver(post_save, sender=ControlCommitteeMember)
def add_committee_to_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name='Committee Members')
        instance.groups.add(group)


@receiver(post_save, sender=Manager)
def add_manager_to_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name='Managers')
        instance.groups.add(group)


@receiver(post_save, sender=Student)
def add_student_to_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name='Students')
        instance.groups.add(group)


# إشارات لإعداد الصلاحيات للمجموعات
# ====================================================================================
@receiver(post_migrate)
def setup_teacher_permissions(sender, **kwargs):
    # إنشاء أو الحصول على مجموعة المعلمين
    teachers_group, _ = Group.objects.get_or_create(name='Teachers')
    
    # الموديلات المستهدفة
    models_to_grant = ['CourseStructure','Exam','Question','EssayQuestion','NumericQuestion','TrueFalseQuestion','MultipleChoiceQuestion','Answer','EssayAnswerEvaluation']
    
    for model_name in models_to_grant:
        try:
            model = apps.get_model('taecher_app', model_name)
            permissions = Permission.objects.filter(
                content_type__app_label=model._meta.app_label,
                content_type__model=model._meta.model_name
            )
            teachers_group.permissions.add(*permissions)
        except Exception as e:
            logging.error( f"حدث خطأ غير متوقع: {str(e)}")


@receiver(post_migrate)
def setup_committee_permissions(sender, **kwargs):
    # إنشاء أو الحصول على مجموعة اللجنة
    committee_group, _ = Group.objects.get_or_create(name='Committee Members')
    
    # الموديلات المستهدفة
    models_to_grant = ['ExamStatusLog', 'StudentExamAttendance', 'ExamSchedule', 'ExamHall']
    
    for model_name in models_to_grant:
        try:
            model = apps.get_model('conttroll_app', model_name)
            permissions = Permission.objects.filter(
                content_type__app_label=model._meta.app_label,
                content_type__model=model._meta.model_name
            )
            committee_group.permissions.add(*permissions)
        except Exception as e:
            logging.error(f"حدث خطأ غير متوقع: {str(e)}")



@receiver(post_migrate)
def setup_student_permissions(sender, **kwargs):
    # إنشاء أو الحصول على مجموعة الطلاب
    student_group, _ = Group.objects.get_or_create(name='Students')
    
    # الموديلات المستهدفة
    models_to_grant = ['StudentExamAttempt','StudentEssayAnswer','StudentNumericAnswer','StudentTrueFalseQutionAnswer','StudentMultipleChoiceQuestionAnswer']
    
    for model_name in models_to_grant:
        try:
            model = apps.get_model('student_app', model_name)
            permissions = Permission.objects.filter(
                content_type__app_label=model._meta.app_label,
                content_type__model=model._meta.model_name
            )
            student_group.permissions.add(*permissions)
        except Exception as e:
            logging.error( f"حدث خطأ غير متوقع: {str(e)}")



@receiver(post_migrate)
def setup_manager_permissions(sender, **kwargs):
    # إنشاء أو الحصول على مجموعة المديرين
    manager_group, _ = Group.objects.get_or_create(name='Managers')

    # جلب جميع الصلاحيات في النظام
    all_permissions = Permission.objects.all()

    # ربط كل الصلاحيات بالمجموعة
    manager_group.permissions.set(all_permissions)

