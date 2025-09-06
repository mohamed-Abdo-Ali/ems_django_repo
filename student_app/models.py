from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone  
from taecher_app.models import  Exam,CourseStructure,Question
from django.db.models.signals import post_save
from django.dispatch import receiver




# ========================== StudentExamAttempt ===================================================================
class StudentExamAttempt(models.Model):
    attendance = models.ForeignKey(
        'conttroll_app.StudentExamAttendance',
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('سجل الحضور')
    )
    attempt_number = models.PositiveIntegerField(
        verbose_name=_('رقم المحاولة'),
        default=1,
        editable=False,
        validators=[MinValueValidator(1)]
    )
    start_time = models.DateTimeField(
        verbose_name=_('وقت بداية المحاولة'),
        auto_now_add=True
    )
    end_time = models.DateTimeField(
        verbose_name=_('وقت نهاية المحاولة'),
        null=True,
        blank=True
    )
    student_notes = models.TextField(
        verbose_name=_('ملاحظات الطالب'),
        max_length=500,
        blank=True,
        null=True
    )

    # درجات الأنواع المختلفة
    objective_score = models.PositiveIntegerField(default=0, verbose_name=_('درجة الأسئلة متعدد الخيارات'))
    numeric_score = models.PositiveIntegerField(default=0, verbose_name=_('درجة الأسئلة العددية'))
    essay_score = models.PositiveIntegerField(default=0, verbose_name=_('درجة الأسئلة المقالية'))
    true_false_score = models.PositiveIntegerField(default=0, verbose_name=_('درجة أسئلة الصح والخطأ'))
    total_score = models.PositiveIntegerField(default=0, verbose_name=_('الدرجة الكلية'))

    is_submitted = models.BooleanField(default=False, verbose_name=_('تم التسليم'))

    class Meta:
        verbose_name = _('محاولة امتحان الطالب')
        verbose_name_plural = _('محاولات امتحانات الطلاب')
        unique_together = ('attendance', 'attempt_number')
        ordering = ['attendance', 'attempt_number']

    def __str__(self):
        return f"محاولة {self.attempt_number} للطالب {self.attendance.student.name} في امتحان {self.attendance.exam.name}"

    # ========================== حفظ attempt + رقم المحاولة + إجمالي الدرجات
    def save(self, *args, **kwargs):
        if not self.pk:
            last_attempt = StudentExamAttempt.objects.filter(
                attendance=self.attendance
            ).order_by('-attempt_number').first()
            self.attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1

        # إجمالي الدرجات من الأنواع المختلفة
        self.total_score = self.objective_score + self.numeric_score + self.essay_score + self.true_false_score

        super().save(*args, **kwargs)

    # ========================== حساب الدرجات
    def calculate_scores(self):
        # Multiple Choice
        mc_score = sum(a.awarded_mark for a in self.multiple_choice_attempts.all())
        # True/False
        tf_score = sum(a.awarded_mark for a in self.true_false_attempts.all())
        # Numeric
        numeric_score = sum(a.obtained_mark for a in self.numeric_attempts.all())
        # Essay
        essay_score = 0
        for essay_answer in self.essay_attempts.all():
            evaluation = (essay_answer.evaluations
                .filter(is_final_evaluation=True)
                .order_by('-evaluated_at')
                .first())
            if evaluation:
                essay_score += evaluation.awarded_marks

        self.objective_score = mc_score
        self.true_false_score = tf_score
        self.numeric_score = numeric_score
        self.essay_score = essay_score
        self.total_score = self.objective_score + self.true_false_score + self.numeric_score + self.essay_score
        self.save(update_fields=[
            'objective_score', 'true_false_score', 'numeric_score', 'essay_score', 'total_score'
        ])

    # ========================== تحديث جدول درجات الطالب تلقائياً بعد التسليم
    def update_student_course_grade(self):
        
        from conttroll_app.models import student_courses_grads
        
        student = self.attendance.student
        exam = self.attendance.exam
        total_score = self.total_score or 0

        try:
            student_course_grade, created = student_courses_grads.objects.get_or_create(
                student=student,
                course=exam.course,
                defaults={
                    'midterm_mark': 0,
                    'final_mark': 0,
                    'classwork_mark': 0,
                    'total_mark': 0
                }
            )

            course_structure = exam.course.course_structure
            midterm_max = course_structure.midterm_exam_max
            final_max = course_structure.final_exam_max

            if exam.exam_type == Exam.ExamTypes.MIDTERM:
                student_course_grade.midterm_mark = min(Decimal(total_score), midterm_max)
            elif exam.exam_type == Exam.ExamTypes.FINAL:
                student_course_grade.final_mark = min(Decimal(total_score), final_max)
    

            # تحديث المجموع الكلي
            total = (
            Decimal(student_course_grade.midterm_mark) +
            Decimal(student_course_grade.final_mark) +
            Decimal(student_course_grade.classwork_mark)
            )
            student_course_grade.total_mark = total
            student_course_grade.save()

        except CourseStructure.DoesNotExist:
            raise ValidationError(f"هيكل المقرر غير موجود للمقرر: {exam.course.name}")

    #     # إحصائيات الإجابات
    def get_answered_stats(self):
        exam = self.attendance.exam
        # إجمالي الأسئلة في هذا الامتحان (جميع الأنواع)
        total_questions = Question.objects.filter(exam=exam).count()

        # عدد الأسئلة المجاب عليها فعليًا (مع تفادي التكرار باستخدام distinct)
        answered_mc = self.multiple_choice_attempts.filter(
            chosen_answer__isnull=False
        ).values('question').distinct().count()

        answered_tf = self.true_false_attempts.filter(
            chosen_answer__isnull=False
        ).values('question').distinct().count()

        answered_numeric = self.numeric_attempts.values('question').distinct().count()

        answered_essay = self.essay_attempts.exclude(
            answer_text__isnull=True
        ).exclude(
            answer_text__exact=''
        ).values('question').distinct().count()

        return {
            'total_questions': total_questions,
            'answered_count': answered_mc + answered_tf + answered_numeric + answered_essay,
            'by_type': {
                'mc': answered_mc,
                'tf': answered_tf,
                'numeric': answered_numeric,
                'essay': answered_essay
            }
        }

    @property
    def duration_seconds(self):
        end = self.end_time or timezone.now()
        return int((end - self.start_time).total_seconds())

    @property
    def duration_human(self):
        s = self.duration_seconds
        h, rem = divmod(s, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h} ساعة {m} دقيقة {s} ثانية"
        return f"{m} دقيقة {s} ثانية"






# ==========================  لتحديث الدرجات بعد التسليم
@receiver(post_save, sender=StudentExamAttempt)
def after_student_attempt_saved(sender, instance, created, **kwargs):
    if instance.is_submitted:
        instance.update_student_course_grade()





# ========================== StudentEssayAnswer table ===================================================================
class StudentEssayAnswer(models.Model):
    exam_attempt = models.ForeignKey(
        StudentExamAttempt,
        on_delete=models.CASCADE,
        related_name='essay_attempts',
        verbose_name=_('محاولة الامتحان'),
    )
    question = models.ForeignKey(
        'taecher_app.EssayQuestion',
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name='السؤال المقالي'
    )

    
    answer_text = models.TextField(verbose_name='إجابة الطالب')
    attempt_number = models.PositiveIntegerField(
        verbose_name='رقم المحاولة',
        default=1,
        editable=False  # جعل الحقل غير قابل للتعديل يدوياً
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='وقت التسليم')
    
    class Meta:
        verbose_name = 'إجابة طالب مقالية'
        verbose_name_plural = 'إجابات الطلاب المقالية'
        unique_together = ('question', 'attempt_number')
        ordering = ['question', 'attempt_number']

    def save(self, *args, **kwargs):
        # إذا كانت هذه محاولة جديدة (ليس لها pk)
        if not self.pk:
            # الحصول على آخر محاولة لنفس السؤال ونفس الطالب
            last_attempt = StudentEssayAnswer.objects.filter(
                question=self.question,
                # student=self.exam_attempt.attendance.student
            ).order_by('-attempt_number').first()
            
            # تعيين رقم المحاولة الجديد
            self.attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"محاولة {self.attempt_number} للطالب {self.exam_attempt.attendance.student.name} على السؤال {self.question.id}"
    




# ========================== StudentNumericAnswer table ===================================================================
class StudentNumericAnswer(models.Model):
    exam_attempt = models.ForeignKey(
        StudentExamAttempt,
        on_delete=models.CASCADE,
        related_name='numeric_attempts',
        verbose_name=_('محاولة الامتحان'),
    )
    question = models.ForeignKey(
        'taecher_app.NumericQuestion',
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name='السؤال العددي'
    )
    student_answer = models.FloatField(verbose_name='إجابة الطالب الرقمية')
    obtained_mark = models.FloatField(
        verbose_name='الدرجة المستحقة',
        default=0,
        editable=False  # سيتم حسابها تلقائياً عند الحفظ
    )
    attempt_number = models.PositiveIntegerField(
        verbose_name='رقم المحاولة',
        default=1,
        editable=False
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='وقت التسليم')
    
    class Meta:
        verbose_name = 'إجابة طالب عددية'
        verbose_name_plural = 'إجابات الطلاب العددية'
        unique_together = ('question', 'attempt_number')
        ordering = ['question', 'attempt_number']

    def save(self, *args, **kwargs):
        # إذا كانت هذه محاولة جديدة (ليس لها pk)
        if not self.pk:
            # الحصول على آخر محاولة لنفس السؤال ونفس الطالب
            last_attempt = StudentNumericAnswer.objects.filter(
                question=self.question,
            ).order_by('-attempt_number').first()
            
            # تعيين رقم المحاولة الجديد
            self.attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1
        
       
        self.obtained_mark = self.question.points if self.student_answer == self.question.answer else 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"محاولة {self.attempt_number} للطالب {self.exam_attempt.attendance.student.name} على السؤال {self.question.id} (الدرجة: {self.obtained_mark}/{self.question.points})"
    
    





# ========================== ObjectiveQuestionAttempt table ===================================================================
class StudentTrueFalseQutionAnswer(models.Model):
    exam_attempt = models.ForeignKey(
        StudentExamAttempt,
        on_delete=models.CASCADE,
        related_name='true_false_attempts',
        verbose_name=_('محاولة الامتحان')
    )
    question = models.ForeignKey(
        'taecher_app.TrueFalseQuestion',
        on_delete=models.CASCADE,
        related_name='student_attempts',
        verbose_name=_('السؤال')
    )
    chosen_answer = models.ForeignKey(
        'taecher_app.Answer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الإجابة المختارة')
    )
    
    attempt_number = models.PositiveIntegerField(
        verbose_name=_('رقم المحاولة للسؤال'),
        default=1,
        editable=False  # جعل الحقل غير قابل للتعديل يدوياً
    )
    
    
    is_correct = models.BooleanField(
        verbose_name=_('الإجابة صحيحة'),
        default=False,
        editable=False  # جعل الحقل غير قابل للتعديل يدوياً
    )
    
    awarded_mark = models.PositiveIntegerField(
        verbose_name=_('الدرجة المحتسبة'),
        default=0,
        editable=False  # جعل الحقل غير قابل للتعديل يدوياً
    )
    
    created_at = models.DateTimeField(
        verbose_name=_('وقت المحاولة'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('إحابات سؤال صح و خطاء')
        verbose_name_plural = _('إجابات الأسئلة صح و خطاء')
        unique_together = ('exam_attempt', 'question', 'attempt_number')
        ordering = ['question', 'attempt_number']

    def __str__(self):
        return f"محاولة {self.attempt_number} للطالب {self.exam_attempt.attendance.student.name} على السؤال {self.question.id} (الدرجة: {self.awarded_mark}/{self.question.points})"

    def save(self, *args, **kwargs):
        # إذا كانت هذه محاولة جديدة (ليس لها pk)
        if not self.pk:
            # الحصول على آخر محاولة لنفس السؤال (بغض النظر عن محاولة الامتحان)
            last_attempt = StudentTrueFalseQutionAnswer.objects.filter(
                question=self.question,
                exam_attempt=self.exam_attempt
            ).order_by('-attempt_number').first()
            
            # تعيين رقم المحاولة الجديد
            self.attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1
        
       
        # حساب is_correct و awarded_mark تلقائياً
        if self.chosen_answer:
            self.is_correct = self.chosen_answer.is_correct
            self.awarded_mark = self.question.points if self.is_correct else 0
        super().save(*args, **kwargs)
        



# ========================== StudentMultipleChoiceQuestionAnswer ===================================================================
class StudentMultipleChoiceQuestionAnswer(models.Model):
    exam_attempt = models.ForeignKey(
        StudentExamAttempt,
        on_delete=models.CASCADE,
        related_name='multiple_choice_attempts',
        verbose_name=_('محاولة الامتحان')
    )
    question = models.ForeignKey(
        'taecher_app.MultipleChoiceQuestion',
        on_delete=models.CASCADE,
        related_name='student_attempts',
        verbose_name=_('السؤال')
    )
    chosen_answer = models.ForeignKey(
        'taecher_app.Answer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الإجابة المختارة')
    )
    
    attempt_number = models.PositiveIntegerField(
        verbose_name=_('رقم المحاولة للسؤال'),
        default=1,
        editable=False  # جعل الحقل غير قابل للتعديل يدوياً
    )
    
    
    is_correct = models.BooleanField(
        verbose_name=_('الإجابة صحيحة'),
        default=False,
        editable=False  # جعل الحقل غير قابل للتعديل يدوياً
    )
    
    awarded_mark = models.PositiveIntegerField(
        verbose_name=_('الدرجة المحتسبة'),
        default=0,
        editable=False  # جعل الحقل غير قابل للتعديل يدوياً
    )
    
    created_at = models.DateTimeField(
        verbose_name=_('وقت المحاولة'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('محاولة سؤال متعدد الخيارات')
        verbose_name_plural = _('محاولات الأسئلة متعدد الخيارات')
        unique_together = ('exam_attempt', 'question', 'attempt_number')
        ordering = ['question', 'attempt_number']

    def __str__(self):
        # return f"محاولة {self.attempt_number} للطالب {self.exam_attempt.attendance.student.user.username} على السؤال {self.question.id} (الدرجة: {self.awarded_mark}/{self.question.qution.points})"
        return f"محاولة {self.attempt_number} للطالب {self.exam_attempt.attendance.student.name} على السؤال {self.question.id} (الدرجة: {self.awarded_mark}/{self.question.points})"

    def save(self, *args, **kwargs):
        # إذا كانت هذه محاولة جديدة (ليس لها pk)
        if not self.pk:
            # الحصول على آخر محاولة لنفس السؤال (بغض النظر عن محاولة الامتحان)
            last_attempt = StudentMultipleChoiceQuestionAnswer.objects.filter(
                question=self.question,
                exam_attempt=self.exam_attempt
            ).order_by('-attempt_number').first()
            
            # تعيين رقم المحاولة الجديد
            self.attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1
        
       
        # حساب is_correct و awarded_mark تلقائياً
        if self.chosen_answer:
            self.is_correct = self.chosen_answer.is_correct
            self.awarded_mark = self.question.points if self.is_correct else 0
        super().save(*args, **kwargs)
        
