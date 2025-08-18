from datetime import timezone
from django.db import models
from django.core.validators import MaxValueValidator  # هذا هو الاستيراد الصحيح
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from admin_app.models import Course, CourseStructure
from authentcat_app.models import Student, User,Teacher
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


# ========================== Exam table ===================================================================
class Exam(models.Model):
    class ExamTypes(models.IntegerChoices):
        MIDTERM = 1, _('نصفي')
        FINAL = 2, _('نهائي')
        TRIAL = 3, _('تجريبي')
    
    class ExamCategories(models.IntegerChoices):
        MODEL_1 = 1, _('نموذج 1')
        MODEL_2 = 2, _('نموذج 2')
        EMERGENCY = 3, _('اضطراري')
    
    name = models.CharField(max_length=255, verbose_name=_('اسم الامتحان') , blank=True)
    description = models.TextField(verbose_name=_('وصف الامتحان'), blank=True, null=True)
    duration = models.PositiveIntegerField(
        verbose_name=_('مدة الامتحان (ساعات)'),
        # validators=[models.MaxValueValidator(5, _('لا يمكن أن تتجاوز مدة الامتحان 5 ساعات'))]
        validators=[MaxValueValidator(5, _('لا يمكن أن تتجاوز مدة الامتحان 5 ساعات'))]  # التصحيح ه
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='exams',
        verbose_name=_('المقرر')
    )
    exam_type = models.IntegerField(
        choices=ExamTypes.choices,
        verbose_name=_('نوع الامتحان')
    )
    exam_category = models.IntegerField(
        choices=ExamCategories.choices,
        verbose_name=_('صنف الامتحان'),
        default=ExamCategories.MODEL_1
    )
    total_marks = models.PositiveIntegerField(
        verbose_name=_('درجة الامتحان'),
    )
    show_results = models.BooleanField(
        default=False,
        verbose_name=_('عرض النتائج مباشرة')
    )
    file = models.FileField(
        upload_to='exam_files/',
        verbose_name=_('ملف الامتحان'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_exams',
        verbose_name=_('أنشئ بواسطة')
    )
    
    class Meta:
        verbose_name = _('امتحان')
        verbose_name_plural = _('الامتحانات')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.course.name}"
    
    def clean(self):
        # الحصول على هيكل المقرر
        try:
            course_structure = self.course.course
        except CourseStructure.DoesNotExist:
            raise ValidationError(_("هيكل المقرر غير موجود"))
        
        # تحديد درجة الامتحان بناءً على نوعه وهيكل المقرر
        if self.exam_type == self.ExamTypes.MIDTERM:
            if not course_structure.midterm_exam_max:
                raise ValidationError(_("هذا المقرر لا يحتوي على امتحان نصفي"))
            self.total_marks = course_structure.midterm_exam_max
        elif self.exam_type == self.ExamTypes.FINAL:
            self.total_marks = course_structure.final_exam_max
        elif self.exam_type == self.ExamTypes.TRIAL:
            self.total_marks = self.total_marks  # أو أي قيمة أخرى للامتحان التجريبي
        
        # التحقق من أن الملف مطلوب للامتحان الاضطراري
        if self.exam_category == self.ExamCategories.EMERGENCY and not self.file:
            raise ValidationError(_("الامتحان الاضطراري يتطلب رفع ملف"))
        
        
        
# ========================== StudentExamAttendance table ===================================================================
class StudentExamAttendance(models.Model):
    class AttendanceStatus(models.IntegerChoices):
        FIRST_ATTEMPT = 0, _('أول مرة')
        RETAKE = 1, _('إعادة')
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='exam_attendances',
        verbose_name=_('الطالب')
    )
    exam = models.ForeignKey(
        Exam,
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
        Exam,
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
    
    
    
# ========================== Question table ===================================================================
class Question(models.Model):
    class QuestionTypes(models.IntegerChoices):
        TRUE_FALSE = 1, _('صح أو خطأ')
        # NUMERIC = 2, _('عددي')
        MULTIPLE_CHOICE = 3, _('اختيار من متعدد')
        # ESSAY = 4, _('مقالي')
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('عنوان السؤال'),
        null=True,
        blank= True
    )
    text = models.TextField(
        verbose_name=_('نص السؤال')
    )
    points = models.PositiveIntegerField(
        verbose_name=_('درجة السؤال'),
        default=0,
    )
    question_type = models.IntegerField(
        choices=QuestionTypes.choices,
        verbose_name=_('نوع السؤال')
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('الامتحان')
    )
    files = models.FileField(
        upload_to='question_files/',
        verbose_name=_('ملفات'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('سؤال')
        verbose_name_plural = _('الأسئلة')
        ordering = ['id']
    
    def __str__(self):
        return f"{self.title} ({self.get_question_type_display()})"
    
    def clean(self):
        # التحقق من أن مجموع درجات الأسئلة لا يتجاوز درجة الامتحان
        if self.points <= 0:
            raise ValidationError(_("يجب أن تكون درجة السؤال أكبر من الصفر"))
        
        if self.exam_id:
            total_points = Question.objects.filter(exam=self.exam).exclude(id=self.id).aggregate(
                total=models.Sum('points')
            )['total'] or 0
            if total_points + self.points > self.exam.total_marks:
                raise ValidationError(_("مجموع درجات الأسئلة يتجاوز درجة الامتحان"))


# ========================== Answer table ===================================================================
class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='السؤال المرتبط'
    )
    answer_text = models.TextField(verbose_name='نص الإجابة')
    is_correct = models.BooleanField(
        default=False,
        verbose_name='هل الإجابة صحيحة؟',
        help_text='0 للخطأ، 1 للصحيح'
    )
    
    class Meta:
        verbose_name = 'إجابة'
        verbose_name_plural = 'الإجابات'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.answer_text[:50]}... ({'صحيح' if self.is_correct else 'خطأ'})"

    def clean(self):
        super().clean()
        if self.is_correct:
            # التحقق من وجود إجابة صحيحة أخرى لهذا السؤال
            existing_correct = Answer.objects.filter(
                question=self.question,
                is_correct=True
            ).exclude(pk=self.pk if self.pk else None)
            
            if existing_correct.exists():
                raise ValidationError('يوجد بالفعل إجابة صحيحة لهذا السؤال. يمكن أن يكون هناك إجابة صحيحة واحدة فقط لكل سؤال.')
    
    def save(self, *args, **kwargs):
        self.full_clean()  # تطبيق التحقق قبل الحفظ
        super().save(*args, **kwargs)




# ========================== EssayQuestion table ===================================================================
class EssayQuestion(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='essay_questions',
        verbose_name='الاختبار المرتبط'
    )
    question_text = models.TextField(verbose_name='نص السؤال')
    marks = models.PositiveIntegerField(verbose_name='درجة السؤال', default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'سؤال مقالي'
        verbose_name_plural = 'أسئلة مقالية'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.question_text[:50]}... (درجته: {self.marks})"
    
    

# ========================== NumericQuestion table ===================================================================
class NumericQuestion(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='numeric_questions',
        verbose_name='الاختبار المرتبط'
    )
    question_text = models.TextField(verbose_name='نص السؤال')
    answer = models.FloatField(verbose_name='الإجابة الصحيحة')  # يمكن تخزين الأعداد الصحيحة والعشرية
    marks = models.PositiveIntegerField(verbose_name='درجة السؤال', default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'سؤال عددي'
        verbose_name_plural = 'أسئلة عددية'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.question_text[:50]}... (درجته: {self.marks})"






# ========================== StudentExamAttempt table ===================================================================
class StudentExamAttempt(models.Model):
    attendance = models.ForeignKey(
        StudentExamAttendance,
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

    # def calculate_scores(self):
    #     """حساب الدرجات تلقائياً"""
    #     # حساب درجة الأسئلة الموضوعية (صح/خطأ، اختيار من متعدد)
    #     objective_questions = Question.objects.filter(
    #         exam=self.attendance.exam,
    #         question_type__in=[
    #             Question.QuestionTypes.TRUE_FALSE,
    #             Question.QuestionTypes.MULTIPLE_CHOICE
    #         ]
    #     )
        
    #     objective_score = 0
    #     for question in objective_questions:
    #         last_attempt = ObjectiveQuestionAttempt.objects.filter(
    #             exam_attempt=self,
    #             question=question
    #         ).order_by('-attempt_number').first()
            
    #         if last_attempt and last_attempt.is_correct:
    #             objective_score += question.points
        
    #     self.objective_score = objective_score
        
    #     # حساب درجة الأسئلة العددية (جديد)
    #     numeric_questions = NumericQuestion.objects.filter(exam=self.attendance.exam)
    #     numeric_score = 0
        
    #     for question in numeric_questions:
    #         last_answer = StudentNumericAnswer.objects.filter(
    #             exam_attempt=self,
    #             question=question
    #         ).order_by('-attempt_number').first()
            
    #         if last_answer:
    #             numeric_score += last_answer.obtained_mark
        
    #     self.numeric_score = numeric_score
        
        
        
        
        
        
        
    #     # حساب درجة الأسئلة المقالية
    #     essay_questions = EssayQuestion.objects.filter(exam=self.attendance.exam)
    #     essay_score = 0
        
    #     for question in essay_questions:
    #         last_answer = StudentEssayAnswer.objects.filter(
    #             question=question,
    #             student=self.attendance.student
    #         ).order_by('-attempt_number').first()
            
    #         if last_answer:
    #             evaluation = EssayAnswerEvaluation.objects.filter(
    #                 student_answer=last_answer,
    #                 is_final_evaluation=True
    #             ).first()
                
    #             if evaluation:
    #                 essay_score += evaluation.awarded_marks
        
    #     self.essay_score = essay_score
    #     self.total_score = self.objective_score + self.numeric_score + self.essay_score
    #     self.save()

    # def calculate_scores(self):
    #     """حساب الدرجات التلقائي لجميع أنواع الأسئلة"""
    #     # 1. تصحيح الأسئلة الموضوعية (آخر محاولة لكل سؤال)
    #     objective_score = 0
    #     last_objective_attempts = (
    #         ObjectiveQuestionAttempt.objects
    #         .filter(exam_attempt=self)
    #         .order_by('question_id', '-attempt_number')
    #         .distinct('question_id')
    #     )
        
    #     for attempt in last_objective_attempts:
    #         if attempt.is_correct:
    #             objective_score += attempt.question.points
        
    #     self.objective_score = objective_score
        
    #     # 2. تصحيح الأسئلة العددية (آخر إجابة لكل سؤال)
    #     numeric_score = 0
    #     last_numeric_answers = (
    #         StudentNumericAnswer.objects
    #         .filter(exam_attempt=self)
    #         .order_by('question_id', '-attempt_number')
    #         .distinct('question_id')
    #     )
        
    #     for answer in last_numeric_answers:
    #         if answer.student_answer == answer.question.answer:
    #             numeric_score += answer.question.marks
        
    #     self.numeric_score = numeric_score
        
    #     # 3. تصحيح الأسئلة المقالية (آخر تقييم نهائي لكل سؤال)
    #     essay_score = 0
    #     last_essay_answers = (
    #         StudentEssayAnswer.objects
    #         .filter(exam_attempt=self)
    #         .order_by('question_id', '-attempt_number')
    #         .distinct('question_id')
    #     )
        
    #     for essay_answer in last_essay_answers:
    #         evaluation = (
    #             EssayAnswerEvaluation.objects
    #             .filter(
    #                 student_answer=essay_answer,
    #                 is_final_evaluation=True
    #             )
    #             .first()
    #         )
    #         if evaluation:
    #             essay_score += evaluation.awarded_marks
        
    #     self.essay_score = essay_score
        
    #     # حساب الدرجة الكلية
    #     self.total_score = self.objective_score + self.numeric_score + self.essay_score
        
    #     # حفظ التغييرات بدون تفعيل الإشارات مرة أخرى
    #     self.save(update_fields=[
    #         'objective_score',
    #         'numeric_score',
    #         'essay_score',
    #         'total_score'
    #     ], update_signals=False)

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
        EssayQuestion,
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
        NumericQuestion,
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
        
        # # حساب الدرجة المستحقة تلقائياً
        # if self.student_answer == self.question.answer:
        #     self.obtained_mark = self.question.marks
        # else:
        #     self.obtained_mark = 0
        
        # super().save(*args, **kwargs)
        
        
        # حساب obtained_mark تلقائياً
        self.obtained_mark = self.question.marks if self.student_answer == self.question.answer else 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"محاولة {self.attempt_number} للطالب {self.exam_attempt.attendance.student.user.username} على السؤال {self.question.id} (الدرجة: {self.obtained_mark}/{self.question.marks})"
    
    
    
    

# ========================== EssayAnswerEvaluation table ===================================================================
class EssayAnswerEvaluation(models.Model):
    student_answer = models.ForeignKey(
        StudentEssayAnswer,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name='إجابة الطالب'
    )
    awarded_marks = models.PositiveIntegerField(
        verbose_name='الدرجة المحتسبة',
        validators=[MinValueValidator(0)],
        help_text='يجب أن تكون بين 0 ودرجة السؤال'
    )
    feedback = models.TextField(verbose_name='التغذية الراجعة', blank=True)
    evaluated_by = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='essay_evaluations',
        verbose_name='مصحح بواسطة'
    )
    evaluated_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التصحيح')
    is_final_evaluation = models.BooleanField(
        default=False,
        verbose_name='تقييم نهائي',
        help_text='هل هذا التقييم هو التقييم النهائي للإجابة؟'
    )
    
    class Meta:
        verbose_name = 'تقييم إجابة مقالية'
        verbose_name_plural = 'تقييمات الإجابات المقالية'
        ordering = ['student_answer', '-evaluated_at']
    
    def clean(self):
        super().clean()
        # التأكد أن الدرجة لا تتجاوز درجة السؤال
        max_marks = self.student_answer.question.marks
        if self.awarded_marks > max_marks:
            raise ValidationError(f'الدرجة لا يمكن أن تتجاوز {max_marks}')
        
        # إذا كان التقييم نهائي، تأكد أنه لا يوجد تقييم نهائي آخر
        if self.is_final_evaluation:
            existing_final = EssayAnswerEvaluation.objects.filter(
                student_answer=self.student_answer,
                is_final_evaluation=True
            ).exclude(pk=self.pk if self.pk else None)
            
            if existing_final.exists():
                raise ValidationError('يوجد بالفعل تقييم نهائي لهذه الإجابة')
    
    def __str__(self):
        return f"تقييم محاولة {self.student_answer.attempt_number} للطالب {self.student_answer.exam_attempt.attendance.student.user.username}"







# ========================== ObjectiveQuestionAttempt table ===================================================================
class ObjectiveQuestionAttempt(models.Model):
    exam_attempt = models.ForeignKey(
        StudentExamAttempt,
        on_delete=models.CASCADE,
        related_name='objective_attempts',
        verbose_name=_('محاولة الامتحان')
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='student_attempts',
        verbose_name=_('السؤال')
    )
    chosen_answer = models.ForeignKey(
        Answer,
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
    

    # def save(self, *args, **kwargs):
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