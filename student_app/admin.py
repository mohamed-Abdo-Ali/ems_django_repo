from django.contrib import admin
from .models import  StudentEssayAnswer, StudentExamAttempt, StudentNumericAnswer,StudentTrueFalseQutionAnswer,StudentMultipleChoiceQuestionAnswer






admin.site.register(StudentExamAttempt)
admin.site.register(StudentNumericAnswer)
admin.site.register(StudentEssayAnswer)
admin.site.register(StudentTrueFalseQutionAnswer)
admin.site.register(StudentMultipleChoiceQuestionAnswer)