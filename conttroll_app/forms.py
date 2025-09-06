# conttroll_app/forms.py
from django import forms
from admin_app.models import Department, Major, Level, Semester, Course
from authentcat_app.models import Student

class MatrixFilterForm(forms.Form):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(), label="القسم",
        widget=forms.Select(attrs={'class': 'select2', 'data-placeholder': 'اختر القسم'})
    )
    major = forms.ModelChoiceField(
        queryset=Major.objects.none(), label="التخصص",
        widget=forms.Select(attrs={'class': 'select2', 'data-placeholder': 'اختر التخصص'})
    )
    level = forms.ModelChoiceField(
        queryset=Level.objects.all(), label="المستوى",
        widget=forms.Select(attrs={'class': 'select2', 'data-placeholder': 'اختر المستوى'})
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.none(), label="الفصل",
        widget=forms.Select(attrs={'class': 'select2', 'data-placeholder': 'اختر الفصل'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dep = self.data.get('department') or self.initial.get('department')
        if dep:
            self.fields['major'].queryset = Major.objects.filter(department_id=dep).order_by('name')


        lvl = self.data.get('level') or self.initial.get('level')
        if lvl:
            self.fields['semester'].queryset = Semester.objects.filter(level_id=lvl).order_by('order')


class CourseRegisterForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(), label="المقرر",
        widget=forms.Select(attrs={'class': 'select2', 'data-placeholder': 'اختر المقرر'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and getattr(user, 'is_teacher', False):
            self.fields['course'].queryset = Course.objects.filter(instructor_id=user.pk).order_by('code', 'name')


class StudentTranscriptForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(), label="الطالب",
        widget=forms.Select(attrs={'class': 'select2', 'data-placeholder': 'اختر الطالب'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and getattr(user, 'is_student', False):
            self.fields['student'].queryset = Student.objects.filter(pk=user.pk)
            self.fields['student'].initial = user.pk
            # نخليه للعرض فقط (شكل Select2 يظل جميل)
            self.fields['student'].widget.attrs['disabled'] = True