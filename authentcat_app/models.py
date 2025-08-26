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
    last_login =None
        # السمات الأساسية
    # username from auth model
    # password from auth model
    # last_login بديل عنها تاريخ الانشاء  created_at و updated_at

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
                regex='^[\u0600-\u06FF\s]+$',
                message="يجب أن يحتوي الاسم الكامل على أحرف عربية فقط"
            )
        ]
    )
    gender = models.IntegerField(choices=GenderTypes.choices , verbose_name= 'النوع' ,default=1)
    user_type = models.IntegerField(choices=UserTypes.choices , verbose_name='نوع المستخدام', default=2)
    photo = models.ImageField(upload_to='photo/%Y/%m/%d', verbose_name='صورة المستخدام', default='photo/defualt_img.png')
    
    # حقول التتبع
    created_at = models.DateTimeField(auto_now_add=True ,verbose_name='تاريخ الانشاء')
    updated_at = models.DateTimeField(auto_now=True ,verbose_name='تاريخ التعديل') 
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users' ,verbose_name='المستخدام الذي انشئ')
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_users' ,verbose_name='المستخدام الذي عدل')
    
    
    
    
    
    last_login = models.DateTimeField(auto_now_add=True ,verbose_name='تاريخ اخر تسجيل دخول')
    
    # حقول الصلاحيات
    is_active = models.BooleanField(default=True , verbose_name='هل الحساب فعال' )
    is_superuser = models.BooleanField(default=False , verbose_name='هل الحساب سوبر لة كل الصلاحيات',help_text='سوف يكون لة كل الصلاحيات انتبة ')
    is_staff = models.BooleanField(default=False , verbose_name='هل الحساب من الموظفين')


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
        # التحقق من أن المستخدم لا يمكن أن يكون من نوعين مختلفين
        if hasattr(self, 'basicuser') and self.user_type != self.UserTypes.BASIC:
            raise ValidationError(_("المستخدم الأساسي يجب أن يكون من النوع الأساسي"))
        if hasattr(self, 'student') and self.user_type != self.UserTypes.STUDENT:
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
        return self.is_basic and hasattr(self, 'basicuser') and self.basicuser.basic_user_type == BasicUser.UserTypes.TEACHER

    @property
    def is_committee_member(self):
        return self.is_basic and hasattr(self, 'basicuser') and self.basicuser.basic_user_type == BasicUser.UserTypes.COMMITTEE

    @property
    def is_manager(self):
        return self.is_basic and hasattr(self, 'basicuser') and self.basicuser.basic_user_type == BasicUser.UserTypes.MANAGER

    @property
    def profile(self):
        if hasattr(self, '_profile'):
            return self._profile
        self._profile, created = Profile.objects.get_or_create(user=self)
        return self._profile
    
    
    def clean(self):
        super().clean()
        
        # التحقق من أن المستخدم لا يمكن أن يكون من نوعين مختلفين
        if hasattr(self, 'basicuser') and self.user_type != self.UserTypes.BASIC:
            raise ValidationError(_("المستخدم الأساسي يجب أن يكون من النوع الأساسي"))
        if hasattr(self, 'student') and self.user_type != self.UserTypes.STUDENT:
            raise ValidationError(_("الطالب يجب أن يكون من النوع طالب"))
        
        # التحقق من أن الطالب لا يمكن أن يكون staff أو superuser
        if self.user_type == self.UserTypes.STUDENT:
            if self.is_staff or self.is_superuser:
                raise ValidationError(_("الطالب لا يمكن أن يكون من الموظفين أو المديرين العامين"))



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


# ====================== BasicUser  table ======================================================================
class BasicUser(models.Model):
    class UserTypes(models.IntegerChoices):
        TEACHER = 1, _('معلم')
        COMMITTEE = 2, _('عضو لجنة مراقبة')
        MANAGER = 3, _('مدير')
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='basicuser',
        limit_choices_to={'user_type': User.UserTypes.BASIC}  # فقط للمستخدمين الأساسيين
    )
    basic_user_type = models.IntegerField(choices=UserTypes.choices)

    class Meta:
        verbose_name = _('مستخدم أساسي')
        verbose_name_plural = _('المستخدمون الأساسيون')

    def __str__(self):
        return f"{self.user.username} - {self.get_basic_user_type_display()}"

    def clean(self):
        # التحقق من أن المستخدم الأساسي لا يمكن أن يكون له سجل طالب
        if hasattr(self.user, 'student'):
            raise ValidationError(_("المستخدم الأساسي لا يمكن أن يكون طالبًا"))


@receiver(pre_save, sender=BasicUser)
def prevent_basic_user_type_change(sender, instance, **kwargs):
    if instance.pk:
        original = BasicUser.objects.get(pk=instance.pk)
        if original.basic_user_type != instance.basic_user_type:
            raise ValidationError(_("لا يمكن تغيير نوع المستخدم الأساسي بعد الإنشاء"))




# =============== Student  table =======================================================================
class Student(models.Model):
    class RegistrationTypes(models.IntegerChoices):
        REGULAR = 1, _('نظام')
        PARALLEL = 2, _('موازي')
        PRIVATE = 3, _('نفقة خاصة')
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student',
        limit_choices_to={'user_type': User.UserTypes.STUDENT}  # فقط للطلاب
    )
    university_id = models.CharField(
        _('الرقم الجامعي'),
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[0-9]{8}$',
                message="يجب أن يتكون الرقم الجامعي من 8 أرقام"
            )
        ]
    )
    
    Batch = models.ForeignKey(
        'admin_app.Batch',
        on_delete=models.CASCADE, 
            related_name='Batch', verbose_name="الدفعة")
    
    Major = models.ForeignKey(
        'admin_app.Major', 
        on_delete=models.CASCADE, 
            related_name='Major', verbose_name="التخصص")
    
    Semester = models.ForeignKey('admin_app.Semester', on_delete=models.CASCADE, 
            related_name='Semester', verbose_name="الفصل الدراسي")
        
    registration_type = models.IntegerField(_('نوع التسجيل'), choices=RegistrationTypes.choices)





    class Meta:
        verbose_name = _('طالب')
        verbose_name_plural = _('الطلاب')

    def __str__(self):
        return f"{self.user.username} - {self.user.full_name}"

    def clean(self):
        # التحقق من أن الطالب لا يمكن أن يكون له سجل مستخدم أساسي
        if hasattr(self.user, 'basicuser'):
            raise ValidationError(_("الطالب لا يمكن أن يكون مستخدمًا أساسيًا"))





# ==================== Teacher table ==========================================================
class Teacher(models.Model):
    basic_user = models.OneToOneField(
        BasicUser,
        on_delete=models.CASCADE,
        related_name='teacher',
        limit_choices_to={'basic_user_type': BasicUser.UserTypes.TEACHER}
    )

    class Meta:
        verbose_name = _('معلم')
        verbose_name_plural = _('المعلمون')

    def __str__(self):
        return f"{self.basic_user.user.username}"


# ==================== ControlCommitteeMember table ==========================================================
class ControlCommitteeMember(models.Model):
    basic_user = models.OneToOneField(
        BasicUser,
        on_delete=models.CASCADE,
        related_name='committee_member',
        limit_choices_to={'basic_user_type': BasicUser.UserTypes.COMMITTEE}
    )


    class Meta:
        verbose_name = _('عضو لجنة مراقبة')
        verbose_name_plural = _('أعضاء لجنة المراقبة')

    def __str__(self):
        return f"{self.basic_user.user.username}"


# ==================== Manager table ==========================================================
class Manager(models.Model):
    basic_user = models.OneToOneField(
        BasicUser,
        on_delete=models.CASCADE,
        related_name='manager',
        limit_choices_to={'basic_user_type': BasicUser.UserTypes.MANAGER}
    )
  
    class Meta:
        verbose_name = _('مدير')
        verbose_name_plural = _('المديرون')

    def __str__(self):
        return f"{self.basic_user.user.full_name} "















# إشارات لإضافة المستخدمين إلى المجموعات المناسبة عند الإنشاء
# ====================================================================================
@receiver(post_save, sender=Teacher)
def add_teacher_to_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name='Teachers')
        instance.basic_user.user.groups.add(group)


@receiver(post_save, sender=ControlCommitteeMember)
def add_committee_to_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name='Committee Members')
        instance.basic_user.user.groups.add(group)


@receiver(post_save, sender=Manager)
def add_manager_to_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name='Managers')
        instance.basic_user.user.groups.add(group)


@receiver(post_save, sender=Student)
def add_student_to_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name='Students')
        instance.user.groups.add(group)
        
        

@receiver(post_save, sender=BasicUser)
def set_basicuser_permissions(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        
        # جميع المستخدمين الأساسيين يصبحوا موظفين staff
        user.is_staff = True
        
        # إذا كان المدير Manager يصبح سوبر يوزر أيضًا
        if instance.basic_user_type == BasicUser.UserTypes.MANAGER:
            user.is_superuser = True
        else:
            user.is_superuser = False

        user.save()




@receiver(post_migrate)
def setup_group_permissions(sender, **kwargs):
    # إنشاء أو الحصول على مجموعة المعلمين
    teachers_group, _ = Group.objects.get_or_create(name='Teachers')
    
    # الموديلات المستهدفة
    models_to_grant = ['coursestructure', 'exam', 'question', 'answer', 'essayquestion', 'essayanswerevaluation', 'numericquestion']
    
    for model_name in models_to_grant:
        model = apps.get_model('taecher_app', model_name)  # exam_app اسم التطبيق عندك غيّره حسب اسم التطبيق
        permissions = Permission.objects.filter(content_type__app_label=model._meta.app_label,
                                                content_type__model=model._meta.model_name)
        # ربط الصلاحيات بالمجموعة
        teachers_group.permissions.add(*permissions)




@receiver(post_migrate)
def setup_group_permissions(sender, **kwargs):
    # إنشاء أو الحصول على مجموعة المعلمين
    COMMITTEE_group, _ = Group.objects.get_or_create(name='Committee Members')
    
    # الموديلات المستهدفة
    models_to_grant = ['Grade', 'CourseEnrollment', 'ExamStatusLog', 'StudentExamAttendance', 'ExamSchedule', 'ExamHall']
    
    for model_name in models_to_grant:
        model = apps.get_model('conttroll_app', model_name)  # exam_app اسم التطبيق عندك غيّره حسب اسم التطبيق
        permissions = Permission.objects.filter(content_type__app_label=model._meta.app_label,
                                                content_type__model=model._meta.model_name)
        # ربط الصلاحيات بالمجموعة
        COMMITTEE_group.permissions.add(*permissions)




@receiver(post_migrate)
def setup_group_permissions(sender, **kwargs):
    # إنشاء أو الحصول على مجموعة المعلمين
    student_group, _ = Group.objects.get_or_create(name='Students')
    
    # الموديلات المستهدفة
    models_to_grant = ['ObjectiveQuestionAttempt', 'StudentNumericAnswer', 'StudentEssayAnswer', 'StudentExamAttempt']
    
    for model_name in models_to_grant:
        model = apps.get_model('student_app', model_name)  # exam_app اسم التطبيق عندك غيّره حسب اسم التطبيق
        permissions = Permission.objects.filter(content_type__app_label=model._meta.app_label,
                                                content_type__model=model._meta.model_name)
        # ربط الصلاحيات بالمجموعة
        student_group.permissions.add(*permissions)



@receiver(post_migrate)
def setup_manager_group_permissions(sender, **kwargs):
    # إنشاء أو الحصول على مجموعة المديرين
    manager_group, _ = Group.objects.get_or_create(name='Managers')

    # جلب جميع الصلاحيات في النظام
    all_permissions = Permission.objects.all()

    # ربط كل الصلاحيات بالمجموعة
    manager_group.permissions.set(all_permissions)

