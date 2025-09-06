from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from authentcat_app.models import Teacher
from admin_app.models import Course

from django_currentuser.middleware import get_current_authenticated_user as get_current_user

# ==================== CourseStructure table ==========================================================
class CourseStructure(models.Model):
    final_exam_max = models.PositiveIntegerField(verbose_name="الدرجة العظمى للامتحان النهائي")
    midterm_exam_max = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="الدرجة العظمى للامتحان النصفي")
    class_work_max = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="الدرجة العظمى لأعمال الفصل")
    structure = models.OneToOneField('admin_app.Course', on_delete=models.CASCADE, related_name='course_structure',verbose_name="المقرر")

    class Meta:
        verbose_name = "هيكل المقرر"
        verbose_name_plural = "هياكل المقررات"

    def clean(self):
        if self.structure.course_type == 1 :
            if (self.final_exam_max + self.midterm_exam_max + self.class_work_max) != 100:
                raise ValidationError("المقرر النظري يجب أن يكون مجموعه 100 درجة")
        elif self.structure.course_type == 2 and self.final_exam_max != 50:
            if (self.final_exam_max + self.midterm_exam_max + self.class_work_max) != 50 :
                raise ValidationError("المقرر العملي يجب أن يكون مجموعه 50 درجة")


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

    name = models.CharField(max_length=255, verbose_name=_('اسم الامتحان'), blank=True)
    description = models.TextField(verbose_name=_('وصف الامتحان'), blank=True, null=True)
    duration = models.PositiveIntegerField(
        verbose_name=_('مدة الامتحان (ساعات)'),
        validators=[MaxValueValidator(5, _('لا يمكن أن تتجاوز مدة الامتحان 5 ساعات'))]
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams', verbose_name=_('المقرر'))
    exam_type = models.IntegerField(choices=ExamTypes.choices, verbose_name=_('نوع الامتحان'))
    exam_category = models.IntegerField(choices=ExamCategories.choices, verbose_name=_('صنف الامتحان'), default=ExamCategories.MODEL_1)
    total_marks = models.PositiveIntegerField(verbose_name=_('درجة الامتحان'))
    show_results = models.BooleanField(default=False, verbose_name=_('عرض النتائج مباشرة'))
    file = models.FileField(upload_to='exam_files/', verbose_name=_('ملف الامتحان'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='created_exams', verbose_name=_('أنشئ بواسطة'))

    class Meta:
        verbose_name = _('امتحان')
        verbose_name_plural = _('الامتحانات')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.course.name}"

  
    
    def clean(self):
        user = get_current_user()
        
        if not user.is_teacher :
            raise ValidationError(_("يسمح فقط للمعلمين إنشاء الاسئلة انت لست معلم"))
            
        
        try:
            course_structure = self.course.course_structure
        except CourseStructure.DoesNotExist:
            raise ValidationError(_(" هيكل المقرر غير موجود الرجاء اولا إنشاء هيكل المقرر و توزيع الدرجات" ))

        if self.exam_type == self.ExamTypes.MIDTERM:
            if not course_structure.midterm_exam_max:
                raise ValidationError(_("هذا المقرر لا يحتوي على امتحان نصفي"))
            self.total_marks = course_structure.midterm_exam_max
        elif self.exam_type == self.ExamTypes.FINAL:
            self.total_marks = course_structure.final_exam_max
        elif self.exam_type == self.ExamTypes.TRIAL:
            self.total_marks = self.total_marks  # للامتحان التجريبي

        if self.exam_category == self.ExamCategories.EMERGENCY and not self.file:
            raise ValidationError(_("الامتحان الاضطراري يتطلب رفع ملف"))
    
# ========================== Question table ===================================================================
class Question(models.Model):
    class QuestionTypes(models.IntegerChoices):
        TRUE_FALSE = 1, _('صح أو خطأ')
        NUMERIC = 2, _('عددي')
        MULTIPLE_CHOICE = 3, _('اختيار من متعدد')
        ESSAY = 4, _('مقالي')

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions', verbose_name=_('الامتحان'))
    text = models.TextField(verbose_name=_('نص السؤال'))
    points = models.PositiveIntegerField(verbose_name=_('درجة السؤال'), default=0)
    question_type = models.IntegerField(choices=QuestionTypes.choices, verbose_name=_('نوع السؤال'))
    files = models.FileField(upload_to='question_files/', verbose_name=_('ملفات'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authentcat_app.BasicUser', on_delete=models.CASCADE, related_name='created_questions', verbose_name='المعلم الذي انشئ السؤال')

    class Meta:
        verbose_name = _('سؤال')
        verbose_name_plural = _('الأسئلة')
        ordering = ['id']

    def __str__(self):
        return f"({self.get_question_type_display()}) {self.text[:50]}"

    def clean(self):
        if self.points <= 0:
            raise ValidationError(_("يجب أن تكون درجة السؤال أكبر من الصفر"))
        if self.exam_id:
            total_points = Question.objects.filter(exam=self.exam).exclude(id=self.id).aggregate(total=models.Sum('points'))['total'] or 0
            if total_points + self.points > self.exam.total_marks:
                raise ValidationError(_("مجموع درجات الأسئلة يتجاوز درجة الامتحان"))


# ========================== EssayQuestion table ===================================================================
class EssayQuestion(Question):
    class Meta:
        verbose_name = 'سؤال مقالي'
        verbose_name_plural = 'أسئلة مقالية'

    def clean(self):
        super().clean()
        
    def save(self, *args, **kwargs):
        
        self.question_type = Question.QuestionTypes.ESSAY
        super().save(*args, **kwargs)

# ========================== NumericQuestion table ===================================================================
class NumericQuestion(Question):
    answer = models.FloatField(verbose_name='الإجابة الصحيحة')

    class Meta:
        verbose_name = 'سؤال عددي'
        verbose_name_plural = 'أسئلة عددية'

    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        self.question_type = Question.QuestionTypes.NUMERIC
        super().save(*args, **kwargs)
        
        
# ========================== TrueFalseQuestion table ===================================================================
class TrueFalseQuestion(Question):
    

    class Meta:
        verbose_name = 'سؤال صح و خطأ'
        verbose_name_plural = 'أسئلة صح و خطأ'

    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        self.question_type = Question.QuestionTypes.TRUE_FALSE
        super().save(*args, **kwargs)
        
        
        
# ========================== MultipleChoiceQuestion table ===================================================================
class MultipleChoiceQuestion(Question):

    class Meta:
        verbose_name = 'سؤال اختيار من متعدد'
        verbose_name_plural = 'أسئلة اختيار من متعدد'

    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        self.question_type = Question.QuestionTypes.MULTIPLE_CHOICE
        super().save(*args, **kwargs)
        
        
        
# ========================== Answer table ===================================================================
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='السؤال المرتبط')
    answer_text = models.TextField(verbose_name='نص الإجابة')
    is_correct = models.BooleanField(default=False, verbose_name='هل الإجابة صحيحة؟')

    class Meta:
        verbose_name = 'إجابة'
        verbose_name_plural = 'الإجابات'
        ordering = ['id']

    def __str__(self):
        return f"{self.answer_text[:50]}... ({'صحيح' if self.is_correct else 'خطأ'})"

    def clean(self):
        if self.is_correct:
            existing_correct = Answer.objects.filter(question=self.question, is_correct=True).exclude(pk=self.pk if self.pk else None)
            if existing_correct.exists():
                raise ValidationError('يوجد بالفعل إجابة صحيحة لهذا السؤال. يمكن أن يكون هناك إجابة صحيحة واحدة فقط لكل سؤال.')


# ========================== EssayAnswerEvaluation table ===================================================================
class EssayAnswerEvaluation(models.Model):
    student_answer = models.ForeignKey('student_app.StudentEssayAnswer', on_delete=models.CASCADE, related_name='evaluations', verbose_name='إجابة الطالب')
    awarded_marks = models.PositiveIntegerField(verbose_name='الدرجة المحتسبة', validators=[MinValueValidator(0)])
    feedback = models.TextField(verbose_name='التغذية الراجعة', blank=True)
    evaluated_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='essay_evaluations', verbose_name='مصحح بواسطة')
    evaluated_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التصحيح')
    is_final_evaluation = models.BooleanField(default=False, verbose_name='تقييم نهائي')

    class Meta:
        verbose_name = 'تقييم إجابة مقالية'
        verbose_name_plural = 'تقييمات الإجابات المقالية'
        ordering = ['student_answer', '-evaluated_at']

    def clean(self):
        super().clean()
        max_marks = self.student_answer.question.points
        if self.awarded_marks > max_marks:
            raise ValidationError(f'الدرجة لا يمكن أن تتجاوز {max_marks}')
        if self.is_final_evaluation:
            existing_final = EssayAnswerEvaluation.objects.filter(student_answer=self.student_answer, is_final_evaluation=True).exclude(pk=self.pk if self.pk else None)
            if existing_final.exists():
                raise ValidationError('يوجد بالفعل تقييم نهائي لهذه الإجابة')

    def __str__(self):
        return f"تقييم الطالب {self.student_answer.exam_attempt.attendance.student.name}"

