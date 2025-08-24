from datetime import timezone
from django.db import models
from django.core.validators import MaxValueValidator  # هذا هو الاستيراد الصحيح
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from admin_app.models import Course
from authentcat_app.models import Student, User,Teacher
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from taecher_app.models import  EssayAnswerEvaluation


# ========================== StudentExamAttempt table ===================================================================
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
    objective_score = models.PositiveIntegerField(
        verbose_name=_('درجة الأسئلة الموضوعية'),
        default=0
    )
    numeric_score = models.PositiveIntegerField(  # أضفنا هذا الحقل الجديد
        verbose_name=_('درجة الأسئلة العددية'),
        default=0
    )
    essay_score = models.PositiveIntegerField(
        verbose_name=_('درجة الأسئلة المقالية'),
        default=0
    )
    total_score = models.PositiveIntegerField(
        verbose_name=_('الدرجة الكلية'),
        default=0
    )
    is_submitted = models.BooleanField(
        verbose_name=_('تم التسليم'),
        default=False
    )

    class Meta:
        verbose_name = _('محاولة امتحان الطالب')
        verbose_name_plural = _('محاولات امتحانات الطلاب')
        unique_together = ('attendance', 'attempt_number')
        ordering = ['attendance', 'attempt_number']

    def __str__(self):
        return f"محاولة {self.attempt_number} للطالب {self.attendance.student.user.username} في امتحان {self.attendance.exam.name}"

    def save(self, *args, **kwargs):
        if not self.pk:
            last_attempt = StudentExamAttempt.objects.filter(
                attendance=self.attendance
            ).order_by('-attempt_number').first()
            self.attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1
        
        self.total_score = self.objective_score + self.numeric_score + self.essay_score
        super().save(*args, **kwargs)

    def calculate_scores(self):
        """حساب الدرجات التلقائي لجميع أنواع الأسئلة"""
        # 1. تصحيح الأسئلة الموضوعية (آخر محاولة لكل سؤال)
        objective_score = 0
        last_objective_attempts = (
            ObjectiveQuestionAttempt.objects
            .filter(exam_attempt=self)
            .order_by('question_id', '-attempt_number')
            .distinct('question_id')
        )
        
        for attempt in last_objective_attempts:
            if attempt.is_correct:
                objective_score += attempt.question.points
        
        self.objective_score = objective_score
        
        # 2. تصحيح الأسئلة العددية (آخر إجابة لكل سؤال)
        numeric_score = 0
        last_numeric_answers = (
            StudentNumericAnswer.objects
            .filter(exam_attempt=self)
            .order_by('question_id', '-attempt_number')
            .distinct('question_id')
        )
        
        for answer in last_numeric_answers:
            if answer.student_answer == answer.question.answer:
                numeric_score += answer.question.marks
        
        self.numeric_score = numeric_score
        
        # 3. تصحيح الأسئلة المقالية (آخر تقييم نهائي لكل سؤال)
        essay_score = 0
        last_essay_answers = (
            StudentEssayAnswer.objects
            .filter(exam_attempt=self)
            .order_by('question_id', '-attempt_number')
            .distinct('question_id')
        )
        
        for essay_answer in last_essay_answers:
            evaluation = (
                EssayAnswerEvaluation.objects
                .filter(
                    student_answer=essay_answer,
                    is_final_evaluation=True
                )
                .first()
            )
            if evaluation:
                essay_score += evaluation.awarded_marks
        
        self.essay_score = essay_score
        
        # حساب الدرجة الكلية
        self.total_score = self.objective_score + self.numeric_score + self.essay_score
        
        # حفظ التغييرات باستخدام update_fields فقط
        self.save(update_fields=[
            'objective_score',
            'numeric_score',
            'essay_score',
            'total_score'
        ])



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
    is_final = models.BooleanField(
        default=False,
        verbose_name='إجابة نهائية',
        help_text='هل هذه الإجابة هي النسخة النهائية المقدمة؟'
    )
    
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
        return f"محاولة {self.attempt_number} للطالب {self.exam_attempt.attendance.student.user.username} على السؤال {self.question.id}"
    




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
    is_final = models.BooleanField(
        default=False,
        verbose_name='إجابة نهائية',
        help_text='هل هذه الإجابة هي النسخة النهائية المقدمة؟'
    )
    
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
                # student=self.exam_attempt.attendance.student
            ).order_by('-attempt_number').first()
            
            # تعيين رقم المحاولة الجديد
            self.attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1
        
       
        self.obtained_mark = self.question.marks if self.student_answer == self.question.answer else 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"محاولة {self.attempt_number} للطالب {self.exam_attempt.attendance.student.user.username} على السؤال {self.question.id} (الدرجة: {self.obtained_mark}/{self.question.marks})"
    
    
    
    

# ========================== ObjectiveQuestionAttempt table ===================================================================
class ObjectiveQuestionAttempt(models.Model):
    exam_attempt = models.ForeignKey(
        StudentExamAttempt,
        on_delete=models.CASCADE,
        related_name='objective_attempts',
        verbose_name=_('محاولة الامتحان')
    )
    question = models.ForeignKey(
        'taecher_app.Question',
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
        verbose_name = _('محاولة سؤال موضوعي')
        verbose_name_plural = _('محاولات الأسئلة الموضوعية')
        unique_together = ('exam_attempt', 'question', 'attempt_number')
        ordering = ['question', 'attempt_number']

    def __str__(self):
        return f"محاولة {self.attempt_number} للطالب {self.exam_attempt.attendance.student.user.username} على السؤال {self.question.id} (الدرجة: {self.awarded_mark}/{self.question.points})"
    

    def save(self, *args, **kwargs):
        # إذا كانت هذه محاولة جديدة (ليس لها pk)
        if not self.pk:
            # الحصول على آخر محاولة لنفس السؤال (بغض النظر عن محاولة الامتحان)
            last_attempt = ObjectiveQuestionAttempt.objects.filter(
                question=self.question
            ).order_by('-attempt_number').first()
            
            # تعيين رقم المحاولة الجديد
            self.attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1
        
       
        # حساب is_correct و awarded_mark تلقائياً
        if self.chosen_answer:
            self.is_correct = self.chosen_answer.is_correct
            self.awarded_mark = self.question.points if self.is_correct else 0
        super().save(*args, **kwargs)
        
