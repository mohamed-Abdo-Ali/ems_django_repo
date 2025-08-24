from django.contrib import admin

from conttroll_app.models import ExamStatusLog, StudentExamAttendance
from student_app.models import ObjectiveQuestionAttempt, StudentEssayAnswer, StudentExamAttempt, StudentNumericAnswer
from .models import Answer, Exam, NumericQuestion,Question,EssayQuestion,EssayAnswerEvaluation

# Register your models here.
admin.site.register(Exam)
admin.site.register(StudentExamAttendance)
admin.site.register(ExamStatusLog)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(EssayQuestion)
admin.site.register(EssayAnswerEvaluation)
admin.site.register(StudentEssayAnswer)
admin.site.register(StudentExamAttempt)
admin.site.register(ObjectiveQuestionAttempt)
admin.site.register(StudentNumericAnswer)
admin.site.register(NumericQuestion)