# taecher_app/single.py
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save

from student_app.models import (
    StudentTrueFalseQutionAnswer,
    StudentMultipleChoiceQuestionAnswer,
    StudentEssayAnswer,
    StudentNumericAnswer
)
from .models import EssayAnswerEvaluation


# ========== تحديث الدرجات عند أي تعديل ==========
@receiver([post_save, post_delete], sender=StudentTrueFalseQutionAnswer)
def recalc_on_tf_change(sender, instance, **kwargs):
    instance.exam_attempt.calculate_scores()





@receiver([post_save, post_delete], sender=StudentMultipleChoiceQuestionAnswer)
def recalc_on_mc_change(sender, instance, **kwargs):
    instance.exam_attempt.calculate_scores()





@receiver([post_save, post_delete], sender=StudentNumericAnswer)
def recalc_on_numeric_change(sender, instance, **kwargs):
    instance.exam_attempt.calculate_scores()





@receiver([post_save, post_delete], sender=EssayAnswerEvaluation)
def recalc_on_essay_eval_change(sender, instance, **kwargs):
    instance.student_answer.exam_attempt.calculate_scores()





# ========== محاولة واحدة فقط لكل سؤال داخل محاولة الامتحان ==========
def _upsert_by_exam_attempt_and_question(sender, instance):
    """
    إذا كانت هناك محاولة سابقة لنفس السؤال ضمن نفس محاولة الامتحان،
    نقوم بتحديثها بدلاً من إنشاء سجل جديد (محاولة واحدة فقط لكل سؤال).
    """
    if instance.pk:
        return
    existing = sender.objects.filter(
        exam_attempt=instance.exam_attempt,
        question=instance.question
    ).order_by('-attempt_number').first()
    if existing:
        # تحديث بدل إنشاء
        instance.pk = existing.pk
        instance.attempt_number = existing.attempt_number
    else:
        # أول مرة
        instance.attempt_number = 1




@receiver(pre_save, sender=StudentTrueFalseQutionAnswer)
def enforce_single_attempt_tf(sender, instance, **kwargs):
    _upsert_by_exam_attempt_and_question(sender, instance)




@receiver(pre_save, sender=StudentMultipleChoiceQuestionAnswer)
def enforce_single_attempt_mc(sender, instance, **kwargs):
    _upsert_by_exam_attempt_and_question(sender, instance)




@receiver(pre_save, sender=StudentNumericAnswer)
def enforce_single_attempt_numeric(sender, instance, **kwargs):
    _upsert_by_exam_attempt_and_question(sender, instance)




@receiver(pre_save, sender=StudentEssayAnswer)
def enforce_single_attempt_essay(sender, instance, **kwargs):
    _upsert_by_exam_attempt_and_question(sender, instance)




