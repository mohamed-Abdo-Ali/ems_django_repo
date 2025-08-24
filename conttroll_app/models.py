from django.utils.translation import gettext_lazy as _  
from django.db import models
from admin_app.models import Course
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from authentcat_app.models import User,Student
# from taecher_app.models import Exam
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

# Create your models here.


# ========================== ExamHall table =========================================================
class ExamHall(models.Model):
    """
    نموذج يمثل قاعة امتحانات في الجامعة
    """
    name = models.CharField(
        max_length=100,
        verbose_name="اسم القاعة",
        help_text="اسم القاعة كما هو معروف في الجامعة"
    )
    
    location = models.CharField(
        max_length=200,
        verbose_name="موقع القاعة",
        help_text="مثال: الدور الأول - مبنى كلية الهندسة"
    )
    
    capacity = models.PositiveIntegerField(
        verbose_name="سعة القاعة",
        help_text="عدد الطلاب الذين تستوعبهم القاعة"
    )
    
    notes = models.TextField(
        verbose_name="ملاحظات",
        blank=True,
        null=True,
        help_text="أي معلومات إضافية عن القاعة"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشطة",
        help_text="هل هذه القاعة متاحة للاستخدام حالياً؟"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )

    class Meta:
        verbose_name = "قاعة امتحان"
        verbose_name_plural = "قاعات الامتحانات"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.location} (سعة: {self.capacity})"
    
    

# ========================== ExamSchedule table =========================================================
class ExamSchedule(models.Model):
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='exam_schedule',
        verbose_name=_('المقرر الدراسي')
    )
    exam_date = models.DateField(verbose_name=_('تاريخ الامتحان'))
    start_time = models.TimeField(verbose_name=_('وقت بدء الامتحان'))
    end_time = models.TimeField(verbose_name=_('وقت انتهاء الامتحان'))
    hall = models.ForeignKey(
        ExamHall,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_exams',
        verbose_name=_('قاعة الامتحان')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "authentcat_app.controlcommitteemember",
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_exam_schedules',
        verbose_name=_('أنشئ بواسطة')
    )

    class Meta:
        verbose_name = _('جدول الامتحانات')
        verbose_name_plural = _('الجداول الزمنية للامتحانات')
        ordering = ['exam_date', 'start_time']
        unique_together = [['course'], ['hall', 'exam_date', 'start_time']]

    def __str__(self):
        return f"{self.course.name} - {self.exam_date} {self.start_time} to {self.end_time}"

    def clean(self):
        # التحقق من أن وقت الانتهاء بعد وقت البداية
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError(_('وقت الانتهاء يجب أن يكون بعد وقت البداية'))


        # التحقق من عدم وجود تعارض في القاعة في نفس الوقت
        conflicting_exams = ExamSchedule.objects.filter(
            hall=self.hall,
            exam_date=self.exam_date
        ).exclude(pk=self.pk).filter(
            models.Q(start_time__lt=self.end_time, end_time__gt=self.start_time)
        )
        
        if conflicting_exams.exists():
            raise ValidationError(_('هناك تعارض في الجدول مع امتحان آخر في نفس القاعة  و في نفس الوقت'))

    @property
    def duration(self):
        """حساب مدة الامتحان بالساعات والدقائق"""
        if self.start_time and self.end_time:
            start = timedelta(hours=self.start_time.hour, minutes=self.start_time.minute)
            end = timedelta(hours=self.end_time.hour, minutes=self.end_time.minute)
            duration = end - start
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            return f"{hours}:{minutes:02d}"
        return "00:00"
    



        
# ========================== StudentExamAttendance table ===================================================================
class StudentExamAttendance(models.Model):
    class AttendanceStatus(models.IntegerChoices):
        FIRST_ATTEMPT = 0, _('أول مرة')
        RETAKE = 1, _('إعادة')
    
    student = models.ForeignKey(
        'authentcat_app.Student',
        on_delete=models.CASCADE,
        related_name='exam_attendances',
        verbose_name=_('الطالب')
    )
    exam = models.ForeignKey(
        'taecher_app.Exam',
        on_delete=models.CASCADE,
        related_name='student_attendances',
        verbose_name=_('الامتحان')
    )
    attendance_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الحضور')
    )
    status = models.IntegerField(
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.FIRST_ATTEMPT,
        verbose_name=_('حالة الحضور')
    )
    score = models.PositiveIntegerField(
        verbose_name=_('الدرجة'),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('حضور طالب للامتحان')
        verbose_name_plural = _('حضور الطلاب للامتحانات')
        unique_together = ('student', 'exam')  # كل طالب يمكن أن يحضر الامتحان مرة واحدة فقط
    
    def __str__(self):
        return f"{self.student.user.username} - {self.exam.name}"





# ========================== ExamStatusLog table ===================================================================
class ExamStatusLog(models.Model):
    class StatusChoices(models.IntegerChoices):
        CREATED = 1, _('منشئ')
        SENT_TO_CONTROL = 2, _('مرسل للكنترول')
        RECEIVED_BY_CONTROL = 3, _('مستلم من الكنترول')
        CANCELLED = 4, _('ملغي')
    
    exam = models.ForeignKey(
        'taecher_app.Exam',
        on_delete=models.CASCADE,
        related_name='status_logs',
        verbose_name=_('الامتحان')
    )
    status = models.IntegerField(
        choices=StatusChoices.choices,
        verbose_name=_('الحالة')
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='exam_status_changes',
        verbose_name=_('تم التغيير بواسطة')
    )
    change_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ التغيير')
    )
    notes = models.TextField(
        verbose_name=_('ملاحظات'),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('سجل حالة الامتحان')
        verbose_name_plural = _('سجلات حالات الامتحانات')
        ordering = ['-change_date']
    
    def __str__(self):
        return f"{self.exam.name} - {self.get_status_display()}"
    






# ==================== CourseEnrollment table ==========================================================
class CourseEnrollment(models.Model):
    student = models.ForeignKey('authentcat_app.Student', on_delete=models.CASCADE, 
                            related_name='enrollments', verbose_name="الطالب")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                            related_name='enrollments', verbose_name="المقرر")
    semester = models.ForeignKey('admin_app.Semester', on_delete=models.CASCADE, 
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
        
     





# =========================== ExamScheduleView ========================================================
class ExamScheduleView(models.Model):
    id = models.IntegerField(primary_key=True)
    course_id = models.IntegerField()
    course_name = models.CharField(max_length=100)
    course_type = models.CharField(max_length=50)
    exam_id = models.IntegerField()
    exam_name = models.CharField(max_length=255)
    exam_type = models.CharField(max_length=50)
    exam_status = models.IntegerField(null=True, blank=True)
    major_id = models.IntegerField()
    major_name = models.CharField(max_length=100)
    level_id = models.IntegerField()
    level_name = models.CharField(max_length=50)
    semester_id = models.IntegerField()
    semester_name = models.CharField(max_length=50)
    hall_id = models.IntegerField()
    hall_name = models.CharField(max_length=100)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        managed = False
        # db_table = 'ems_view_exam_schedule'
        db_table = 'ems_view_exam_schedule'





# =========================== Grade table ========================================================
class Grade(models.Model):
    student = models.ForeignKey(
        "authentcat_app.Student", on_delete=models.CASCADE, related_name="grades"
    )
    course = models.ForeignKey(
        "admin_app.Course", on_delete=models.CASCADE, related_name="grades"
    )
    academic_year = models.ForeignKey(
        "admin_app.AcademicYear", on_delete=models.CASCADE, related_name="grades"
    )
    semester = models.ForeignKey(
        "admin_app.Semester", on_delete=models.CASCADE, related_name="grades"
    )
    exam = models.ForeignKey(
        "taecher_app.Exam", on_delete=models.CASCADE, related_name="grades"
    )
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)  # الدرجة التي حصل عليها
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)     # الدرجة الكاملة
    grade = models.CharField(max_length=5, blank=True, null=True)         # A, B, C ... (اختياري)

    class Meta:
        verbose_name = "الدرجة"
        verbose_name_plural = "الدرجات"
        unique_together = ("student", "course", "academic_year", "exam")

    def __str__(self):
        return f"{self.student} - {self.course} - {self.marks_obtained}/{self.total_marks}"


