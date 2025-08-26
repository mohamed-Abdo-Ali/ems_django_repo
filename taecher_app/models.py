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
# from .models import CourseStructure




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
        
        

    
# ========================== Question table ===================================================================
class Question(models.Model):
    class QuestionTypes(models.IntegerChoices):
        TRUE_FALSE = 1, _('صح أو خطأ')
        # NUMERIC = 2, _('عددي')
        MULTIPLE_CHOICE = 3, _('اختيار من متعدد')
        # ESSAY = 4, _('مقالي')

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('الامتحان')
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
        return f"({self.get_question_type_display()})"
    
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
    




# ========================== EssayAnswerEvaluation table ===================================================================
class EssayAnswerEvaluation(models.Model):
    student_answer = models.ForeignKey(
        'student_app.StudentEssayAnswer', 
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








