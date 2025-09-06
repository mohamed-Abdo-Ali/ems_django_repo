from django.utils.translation import gettext_lazy as _  
from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta
from authentcat_app.models import User
from decimal import Decimal
from student_app.models import StudentExamAttempt
from taecher_app.models import Exam, CourseStructure

from django.contrib.auth import get_user_model

User = get_user_model()




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
        'admin_app.Course',
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
        'conttroll_app.student_report_from_uivercity',
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
        return f" {self.exam.name}"





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
    






# =========================== ExamScheduleView ========================================================
class ExamScheduleView(models.Model):
    id = models.BigIntegerField(primary_key=True)
    course_id = models.BigIntegerField()
    course_name = models.CharField(max_length=100)
    course_type = models.CharField(max_length=50)  # Theoretical/Practical/Undefined
    exam_id = models.BigIntegerField()
    exam_name = models.CharField(max_length=255)
    exam_type = models.CharField(max_length=50)    # Midterm/Final/Remedial/Undefined
    exam_status = models.IntegerField(null=True, blank=True)

    department_id = models.BigIntegerField()
    department_name = models.CharField(max_length=100)

    major_id = models.BigIntegerField()
    major_name = models.CharField(max_length=100)
    level_id = models.BigIntegerField()
    level_name = models.CharField(max_length=50)
    semester_id = models.BigIntegerField()
    semester_name = models.CharField(max_length=100)

    hall_id = models.BigIntegerField()
    hall_name = models.CharField(max_length=100)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # خصائص للعرض بالعربي
    @property
    def course_type_ar(self):
        return {
            'Theoretical': 'نظري',
            'Practical': 'عملي',
        }.get(self.course_type, 'غير محدد')

    @property
    def exam_type_ar(self):
        return {
            'Midterm': 'نصفي',
            'Final': 'نهائي',
            'Remedial': 'استدراكي',
        }.get(self.exam_type, 'غير محدد')

    @property
    def course_type_class(self):
        return {
            'Theoretical': 'bg-blue-100 text-blue-800',
            'Practical': 'bg-green-100 text-green-800',
        }.get(self.course_type, 'bg-gray-100 text-gray-800')

    @property
    def exam_type_class(self):
        return {
            'Final': 'bg-red-100 text-red-800',
            'Midterm': 'bg-yellow-100 text-yellow-800',
            'Remedial': 'bg-purple-100 text-purple-800',
        }.get(self.exam_type, 'bg-gray-100 text-gray-800')

    class Meta:
        managed = False
        db_table = 'View_ExamSchedule'
        ordering = ['department_name', 'major_name', 'level_name', 'semester_name', 'exam_date', 'start_time', 'course_name']

    def __str__(self):
        return f'{self.exam_name} - {self.course_name} ({self.exam_date})'




# =========================== student_report_from_uivercity ========================================================
class student_report_from_uivercity (models.Model) :
    
    name = models.CharField(max_length=70 , verbose_name="الاسم")
    gender = models.CharField(max_length=10 , verbose_name="النوع")
    univercity_number = models.PositiveIntegerField(verbose_name="الرقم الجامعي")
    major = models.CharField(max_length=30 , verbose_name="التخصص")
    semester_id = models.PositiveSmallIntegerField(verbose_name="الفصل الدراسي")

    class Meta:
        verbose_name = _('بيانات الطلاب من التقرير الجامعة')
        verbose_name_plural = _('بيانات الطلاب من التقرير الجامعة')

        # دالة لترميز التخصص
    
    def __str__(self):
        return f"{self.name}"

    
    @staticmethod
    def major_to_number(major_name):
        mapping = {
            'تقنية المعلومات': 1,
            'علوم حاسوب': 2,
            'أمن سيبراني': 3,
        }
        return mapping.get(major_name, 0)  # 0 إذا لم يكن موجود في الخريطة




# =========================== Acdimaic_and_term_from_uivercity ========================================================
class Acdimaic_and_term_from_uivercity (models.Model) :
    Acdimaic_year = models.CharField(max_length=10 , verbose_name="السنة الدراسية")
    Acdimaic_year_semester = models.CharField(max_length=10 , verbose_name="فصل السنة الدراسية")

    class Meta:
        verbose_name = _('الفصل و الترم من تقرير الجامعة')
        verbose_name_plural = _('الفصل و الترم من تقرير الجامعة')





class student_courses_grads (models.Model) :
    
    student = models.ForeignKey(student_report_from_uivercity , on_delete= models.CASCADE , related_name="student_grads" , verbose_name="الطالب")
    course = models.ForeignKey('admin_app.Course' , on_delete= models.CASCADE , related_name="course_grads" , verbose_name="المقرر")
    
    
    # تفصيل الدرجات
    midterm_mark = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'),verbose_name="درجة الامتحان النصفي")
    final_mark = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'),verbose_name="درجة الامتحان النهائي")
    classwork_mark = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'),verbose_name="درجة الامتحان أعمال الفصل")
    total_mark = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'),verbose_name="المجموع")

    
    class Meta:
        verbose_name = _('درجات الطلاب في المقررات')
        verbose_name_plural = _('درجات الطلاب في المقررات')


    def __str__(self):
        return f"{self.student.name} "
    
    def recompute(self):
        try:
            course_structure: CourseStructure = self.course.course_structure
        except CourseStructure.DoesNotExist:
            # لو ما في CourseStructure، نوقف العملية
            raise ValidationError("هيكل المقرر غير موجود")

        midterm_mark_max = course_structure.midterm_exam_max
        final_mark_max = course_structure.final_exam_max
        class_work_mark_max = course_structure.class_work_max

        # آخر محاولة للطالب
        studentexamAttmpt_last = StudentExamAttempt.objects.filter(
            attendance__student=self.student
        ).order_by('-attempt_number').first()

        if not studentexamAttmpt_last:
            # الطالب ما عنده أي محاولة
            return

        exam_type = studentexamAttmpt_last.attendance.exam.exam_type
        total_score = studentexamAttmpt_last.total_score or 0  # لو None نحوله 0

        if exam_type == Exam.ExamTypes.FINAL:
            self.final_mark = min(total_score, final_mark_max)
        elif exam_type == Exam.ExamTypes.MIDTERM:
            self.midterm_mark = min(total_score, midterm_mark_max)


