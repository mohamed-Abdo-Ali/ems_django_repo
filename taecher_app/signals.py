from django.db.models.signals import post_save, post_delete, pre_save
from django.db import transaction
from django.dispatch import receiver


from student_app.models import ObjectiveQuestionAttempt, StudentEssayAnswer, StudentExamAttempt, StudentNumericAnswer
from .models import EssayAnswerEvaluation







@receiver([post_save, post_delete], sender=ObjectiveQuestionAttempt)
def update_objective_score(sender, instance, **kwargs):
    """تحديث درجة الأسئلة الموضوعية عند تعديل/حذف محاولة"""
    exam_attempt = instance.exam_attempt
    exam_attempt.calculate_scores()

@receiver([post_save, post_delete], sender=StudentNumericAnswer)
def update_numeric_score(sender, instance, **kwargs):
    """تحديث درجة الأسئلة العددية عند تعديل/حذف إجابة"""
    exam_attempt = instance.exam_attempt
    exam_attempt.calculate_scores()

@receiver([post_save, post_delete], sender=EssayAnswerEvaluation)
def update_essay_score(sender, instance, **kwargs):
    """تحديث درجة الأسئلة المقالية عند تعديل/حذف تقييم"""
    exam_attempt = instance.student_answer.exam_attempt
    exam_attempt.calculate_scores()
    
    
    
    
    
    
# الثوابت
MAX_ATTEMPTS = 5  # الحد الأقصى للمحاولات المسموح بها لكل سؤال
    
@receiver(pre_save, sender=StudentEssayAnswer)
def enforce_essay_attempts_limit(sender, instance, **kwargs):
    """
    التحكم في عدد المحاولات للإجابات المقالية (الحد الأقصى 5 محاولات لكل سؤال)
    مع حذف التقييمات المرتبطة بالمحاولة القديمة لنفس السؤال فقط
    """
    if not instance.pk:  # فقط للمحاولات الجديدة
        with transaction.atomic():
            # الحصول على الطالب والسؤال الحالي
            student = instance.exam_attempt.attendance.student
            current_question = instance.question
            
            # الحصول على محاولات الطالب لنفس السؤال فقط
            attempts = StudentEssayAnswer.objects.filter(
                question=current_question,
                exam_attempt__attendance__student=student
            ).order_by('submitted_at')  # نرتب حسب وقت التسليم
            
            # إذا وصل الطالب للحد الأقصى للمحاولات لهذا السؤال
            if attempts.count() >= MAX_ATTEMPTS:
                # أقدم محاولة لهذا السؤال
                oldest_attempt = attempts.first()
                
                # حذف جميع التقييمات المرتبطة بهذه المحاولة القديمة
                EssayAnswerEvaluation.objects.filter(
                    student_answer=oldest_attempt
                ).delete()
                
                # حذف المحاولة القديمة لنفس السؤال
                oldest_attempt.delete()
                
                # لا نحتاج لإعادة ترقيم المحاولات لأننا نستخدم وقت التسليم
                
            # تعيين وقت التسليم تلقائياً (سيتم بواسطة auto_now_add)
            # لا داعي لتعيين attempt_number لأنه غير مستخدم في هذا النهج






@receiver(pre_save, sender=ObjectiveQuestionAttempt)
def enforce_objective_attempts_limit(sender, instance, **kwargs):
    """
    التحكم في عدد المحاولات للأسئلة الموضوعية (5 محاولات لكل سؤال)
    """
    if not instance.pk:  # فقط للمحاولات الجديدة
        with transaction.atomic():
            student = instance.exam_attempt.attendance.student
            question = instance.question
            
            attempts = ObjectiveQuestionAttempt.objects.filter(
                question=question,
                exam_attempt__attendance__student=student
            ).order_by('created_at')
            
            if attempts.count() >= MAX_ATTEMPTS:
                attempts.first().delete()  # حذف أقدم محاولة