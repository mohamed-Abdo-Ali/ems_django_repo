from django import template
from num2words import num2words
from taecher_app.models import EssayQuestion, NumericQuestion, Question

register = template.Library()

@register.filter
def arabic_ordinal(number):
    try:
        word = num2words(number, ordinal=True, lang='ar')
        if word.startswith('ال'):
            return word
        return 'ال' + word
    except:
        return str(number)
    
    
@register.filter
def is_question(obj):
    return isinstance(obj, Question)

@register.filter
def is_essay_question(obj):
    return isinstance(obj, EssayQuestion)

@register.filter
def is_numeric_question(obj):
    return isinstance(obj, NumericQuestion)