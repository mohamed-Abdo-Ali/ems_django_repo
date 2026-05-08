from django.contrib import messages
from django.contrib import admin
from django import forms
from django.db import transaction
from authentcat_app.models import BasicUser, Teacher
from conttroll_app.models import ExamStatusLog, StudentExamAttendance
from .models import Answer, Exam, NumericQuestion,Question,EssayQuestion,EssayAnswerEvaluation,MultipleChoiceQuestion,TrueFalseQuestion
from django.core.exceptions import PermissionDenied





from django.contrib import admin
from admin_app.models import  Course
from .models import CourseStructure
# ==================== Admin_panel_CourseStructure table =========================================================

class Admin_panel_CourseStructure(admin.ModelAdmin):
    list_display = ['final_exam_max', 'midterm_exam_max', 'class_work_max', 'structure']

    # 🔹 عرض فقط الهياكل الخاصة بالمعلم في صفحة العرض
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(structure__instructor=request.user)

    # 🔹 تقييد قائمة المقررات في صفحة الإضافة لتشمل فقط مقررات المعلم
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "structure" and not request.user.is_superuser:
            kwargs["queryset"] = Course.objects.filter(instructor=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(CourseStructure, Admin_panel_CourseStructure)






# =============================== ReadOnlyViewAdminMixin =================================================================================================
class ReadOnlyViewAdminMixin:
    # منع الإضافة والتعديل
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # لا تعطل الحذف كي لا يتعطل الحذف المتسلسل من النماذج الفرعية
    def has_delete_permission(self, request, obj=None):
        return True

    # إزالة الحذف الجماعي من صفحة القائمة
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    # منع الحذف المباشر من صفحة هذا الموديل
    def delete_view(self, request, object_id, extra_context=None):
        raise PermissionDenied("لا يمكن الحذف من هذه الصفحة. احذف من النماذج الفرعية (EssayQuestion/NumericQuestion/TrueFalseQuestion/MultipleChoiceQuestion).")




# =============================== QuestionAdminPanel =======================================================
class QuestionAdminPanel(ReadOnlyViewAdminMixin, admin.ModelAdmin):
    change_list_template = 'taecher_app/shared_grouped_change_list.html'
    ordering = ('exam__id', 'id')
    list_filter = ()
    list_display = ('exam', 'text', 'points', 'question_type', 'created_by')
    readonly_fields = ['created_by']
    search_fields = ['text', 'exam__name', 'exam__course__name']

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data'):
            # اجلب كل الأسئلة مع الامتحان والمقرر والكاتب
            qs = self.get_queryset(request).select_related('exam', 'exam__course', 'created_by').order_by('exam__id', 'id')
            # طبّق البحث لو موجود
            search_term = request.GET.get('q', '')
            qs, _ = self.get_search_results(request, qs, search_term)

            from collections import OrderedDict
            grouped = OrderedDict()
            for q in qs:
                ex_id = q.exam_id
                if ex_id not in grouped:
                    grouped[ex_id] = {
                        'exam': q.exam,
                        'questions': []
                    }
                grouped[ex_id]['questions'].append(q)

            response.context_data['grouped_exams'] = list(grouped.values())
            # اسم URL لتعديل السؤال
            response.context_data['question_change_url_name'] = 'admin:taecher_app_question_change'
            # عنوان الصفحة
            response.context_data['title'] = 'الأسئلة حسب الامتحان'
        return response

    class Media:
        css = {'all': ('css/question_grouped.css',)}
        js = ('js/question_grouped.js',)


# =============================== EssayQuestionAdminPanel =======================================================
class EssayQuestionAdminPanel(admin.ModelAdmin):
    change_list_template = 'taecher_app/shared_grouped_change_list.html'
    list_filter = ()
    list_display = ['exam','text','points','question_type','created_by']
    ordering = ['exam__id','id']
    search_fields = ['text', 'exam__name', 'exam__course__name']
        
    # fieldsets  لصفحة التعديل و الاضافة
    fieldsets = (
        (None, {
            'fields': ( 'exam','text','points')
            # 'fields': ( 'exam','text','points','question_type','created_by')
            
        }),
    )
    
    
    def save_model(self, request, obj, form, change):
        if not request.user.is_basic:
            # عرض رسالة خطأ في واجهة الإدارة
            messages.error(request, "المستخدم لا يمكنة إنشاء الاسئلة.")
        else :  
            try:
                basic_user = BasicUser.objects.get(pk=request.user.pk)
                obj.created_by = basic_user
                obj.question_type = Question.QuestionTypes.ESSAY
                super().save_model(request, obj, form, change)
                # messages.success(request, "تم حفظ السؤال بنجاح.")  # رسالة نجاح اختيارية
            except basic_user.DoesNotExist:
                messages.error(request, "لا يوجد سجل معلم مرتبط بالمستخدم الحالي.")
            except Exception as e:
                messages.error(request, f"حدث خطأ غير متوقع: {str(e)}")
                

    class Media:
        css = {'all': ('css/question_grouped.css',)}
        js = ('js/question_grouped.js',)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data'):
            qs = self.get_queryset(request)\
                    .select_related('exam', 'exam__course', 'created_by')\
                    .order_by('exam__id', 'id')
            search_term = request.GET.get('q', '')
            qs, use_distinct = self.get_search_results(request, qs, search_term)
            if use_distinct:
                qs = qs.distinct()

            from collections import OrderedDict
            grouped = OrderedDict()
            for q in qs:
                ex_id = q.exam_id
                if ex_id not in grouped:
                    grouped[ex_id] = {'exam': q.exam, 'questions': []}
                grouped[ex_id]['questions'].append(q)

            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            response.context_data['grouped_exams'] = list(grouped.values())
            response.context_data['admin_change_url_name'] = f'admin:{app_label}_{model_name}_change'
            response.context_data['title'] = 'الأسئلة المقالية حسب الامتحان'
        return response




# =============================== NumericQuestionAdminPanel =======================================================
class NumericQuestionAdminPanel(admin.ModelAdmin):
    change_list_template = 'taecher_app/shared_grouped_change_list.html'
    list_filter = ()
    list_display = ['exam','text','points','question_type','created_by']
    ordering = ['exam__id','id']
    search_fields = ['text', 'exam__name', 'exam__course__name']

    class Media:
        css = {'all': ('css/question_grouped.css',)}
        js = ('js/question_grouped.js',)


        # fieldsets  لصفحة التعديل و الاضافة
    fieldsets = (
        (None, {
            'fields': ( 'exam','text','points','answer')
            # 'fields': ( 'exam','text','points','question_type','created_by')
            
        }),
    )




    def save_model(self, request, obj, form, change):
        if not request.user.is_basic:
            # عرض رسالة خطأ في واجهة الإدارة
            messages.error(request, "المستخدم لا يمكنة إنشاء الاسئلة.")
        else :  
            try:
                basic_user = BasicUser.objects.get(pk=request.user.pk)
                obj.created_by = basic_user
                obj.question_type = Question.QuestionTypes.NUMERIC
                super().save_model(request, obj, form, change)
                # messages.success(request, "تم حفظ السؤال بنجاح.")  # رسالة نجاح اختيارية
            except basic_user.DoesNotExist:
                messages.error(request, "لا يوجد سجل معلم مرتبط بالمستخدم الحالي.")
            except Exception as e:
                messages.error(request, f"حدث خطأ غير متوقع: {str(e)}")



    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data'):
            qs = self.get_queryset(request)\
                    .select_related('exam', 'exam__course', 'created_by')\
                    .order_by('exam__id', 'id')
            search_term = request.GET.get('q', '')
            qs, use_distinct = self.get_search_results(request, qs, search_term)
            if use_distinct:
                qs = qs.distinct()

            from collections import OrderedDict
            grouped = OrderedDict()
            for q in qs:
                ex_id = q.exam_id
                if ex_id not in grouped:
                    grouped[ex_id] = {'exam': q.exam, 'questions': []}
                grouped[ex_id]['questions'].append(q)

            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            response.context_data['grouped_exams'] = list(grouped.values())
            response.context_data['admin_change_url_name'] = f'admin:{app_label}_{model_name}_change'
            response.context_data['title'] = 'الأسئلة العددية حسب الامتحان'
        return response

    # بقية الأكواد كما لديك



# =============================== MultipleCMultipleChoiceQuestionFormhoiceQuestionForm =================================================================================================
class MultipleChoiceQuestionForm(forms.ModelForm):
    choice_1 = forms.CharField(label='الاختيار 1', required=False)
    choice_2 = forms.CharField(label='الاختيار 2', required=False)
    choice_3 = forms.CharField(label='الاختيار 3', required=False)
    choice_4 = forms.CharField(label='الاختيار 4', required=False)
    choice_5 = forms.CharField(label='الاختيار 5', required=False)
    choice_6 = forms.CharField(label='الاختيار 6', required=False)

    correct_choice = forms.ChoiceField(
        choices=[('1', 'الاختيار 1'), ('2', 'الاختيار 2'), ('3', 'الاختيار 3')],
        widget=forms.Select,           # Dropdown
        label='الإجابة الصحيحة'
    )

    class Meta:
        model = MultipleChoiceQuestion
        fields = ('exam', 'text', 'points')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        max_choices = 6
        min_visible = 3

        if self.is_bound:
            # أثناء POST: وسّع الخيارات حسب المدخلات حتى لا يفشل التحقق
            visible_count = min_visible
            data = self.data
            # أكبر اندكس ممتلئ
            for i in range(max_choices, 0, -1):
                if data.get(f'choice_{i}', '').strip():
                    visible_count = max(visible_count, i)
                    break
            # لو المستخدم اختار صحيحة تتجاوز المرئي
            try:
                cc = int(data.get('correct_choice', '0'))
                visible_count = max(visible_count, cc)
            except ValueError:
                pass
        else:
            # GET: لو تعديل، اعرض عدد الحقول حسب الإجابات الموجودة، وإلا 3
            if self.instance and self.instance.pk:
                answers = list(self.instance.answers.all().order_by('id')[:max_choices])
                for idx, ans in enumerate(answers, start=1):
                    self.fields[f'choice_{idx}'].initial = ans.answer_text
                    if ans.is_correct:
                        self.fields['correct_choice'].initial = str(idx)
                visible_count = max(min_visible, min(len(answers), max_choices))
            else:
                visible_count = min_visible

        # ضبط خيارات الـ Dropdown بحسب العدد المرئي
        self.fields['correct_choice'].choices = [(str(i), f'الاختيار {i}') for i in range(1, visible_count + 1)]
        if not self.fields['correct_choice'].initial:
            self.fields['correct_choice'].initial = '1'

    def clean(self):
        cleaned = super().clean()
        choices = [cleaned.get(f'choice_{i}', '') for i in range(1, 7)]
        filled = [(i, c.strip()) for i, c in enumerate(choices, start=1) if c and c.strip()]

        if len(filled) < 2:
            raise forms.ValidationError("يجب إدخال خيارين على الأقل.")
        if len(filled) > 6:
            raise forms.ValidationError("الحد الأقصى هو 6 خيارات.")

        correct = cleaned.get('correct_choice')
        if correct:
            idx = int(correct)
            if not choices[idx - 1] or not choices[idx - 1].strip():
                raise forms.ValidationError("حدد الإجابة الصحيحة من بين الخيارات المُدخلة.")
        else:
            raise forms.ValidationError("يجب تحديد إجابة صحيحة واحدة فقط.")

        return cleaned




# =============================== MultipleChoiceQuestionAdminPanel =======================================================
class MultipleChoiceQuestionAdminPanel(admin.ModelAdmin):
    change_list_template = 'taecher_app/shared_grouped_change_list.html'
    form = MultipleChoiceQuestionForm
    list_filter = ()
    list_display = ['exam','text','points','question_type','created_by']
    ordering = ['exam__id','id']
    search_fields = ['text', 'exam__name', 'exam__course__name']

    class Media:
        css = {'all': ('css/question_grouped.css', 'css/mcq_admin.css',)}
        js = ('js/question_grouped.js', 'js/mcq_admin.js',)

    def save_model(self, request, obj, form, change):
        if not request.user.is_basic:  # أو request.user.is_teacher
            messages.error(request, "المستخدم لا يمكنه إنشاء الأسئلة.")
            return

        try:
            basic_user = BasicUser.objects.get(pk=request.user.pk)
        except BasicUser.DoesNotExist:
            messages.error(request, "لا يوجد مستخدم أساسي مرتبط بالحساب الحالي.")
            return

        obj.created_by = basic_user
        obj.question_type = Question.QuestionTypes.MULTIPLE_CHOICE
        super().save_model(request, obj, form, change)

        # أنشئ/حدّث الإجابات
        choices = []
        for i in range(1, 7):
            txt = form.cleaned_data.get(f'choice_{i}', '')
            if txt and txt.strip():
                choices.append((i, txt.strip()))
        correct_idx = int(form.cleaned_data['correct_choice'])

        with transaction.atomic():
            obj.answers.all().delete()
            for i, text in choices:
                Answer.objects.create(
                    question=obj,
                    answer_text=text,
                    is_correct=(i == correct_idx)
                )

    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data'):
            qs = self.get_queryset(request)\
                    .select_related('exam', 'exam__course', 'created_by')\
                    .order_by('exam__id', 'id')
            search_term = request.GET.get('q', '')
            qs, use_distinct = self.get_search_results(request, qs, search_term)
            if use_distinct:
                qs = qs.distinct()

            from collections import OrderedDict
            grouped = OrderedDict()
            for q in qs:
                ex_id = q.exam_id
                if ex_id not in grouped:
                    grouped[ex_id] = {'exam': q.exam, 'questions': []}
                grouped[ex_id]['questions'].append(q)

            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            response.context_data['grouped_exams'] = list(grouped.values())
            response.context_data['admin_change_url_name'] = f'admin:{app_label}_{model_name}_change'
            response.context_data['title'] = 'أسئلة الاختيار من متعدد حسب الامتحان'
        return response

    # الباقي (fieldsets/save_model) كما لديك




# =============================== TrueFalseQuestionForm =================================================================================================
class TrueFalseQuestionForm(forms.ModelForm):
    correct_answer = forms.ChoiceField(
        choices=(('true', 'صح'), ('false', 'خطأ')),
        widget=forms.RadioSelect,
        label='الإجابة الصحيحة'
    )

    class Meta:
        model = TrueFalseQuestion
        fields = ('exam', 'text', 'points')  # لا نعرض أي حقل للإجابات هنا

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تعبئة أولية عند التعديل إن وُجدت إجابات
        if self.instance and self.instance.pk:
            ans = {a.answer_text.strip(): a.is_correct for a in self.instance.answers.all()}
            if ans.get('صح'):
                self.fields['correct_answer'].initial = 'true'
            elif ans.get('خطأ'):
                self.fields['correct_answer'].initial = 'false'
        else:
            self.fields['correct_answer'].initial = 'true'  # الافتراضي


# =============================== TrueFalseQuestionnAdminPanel =================================================================================================
class TrueFalseQuestionnAdminPanel(admin.ModelAdmin):
    change_list_template = 'taecher_app/shared_grouped_change_list.html'
    form = TrueFalseQuestionForm
    list_filter = ()
    list_display = ['exam','text','points','question_type','created_by']
    ordering = ['exam__id','id']
    search_fields = ['text', 'exam__name', 'exam__course__name']

    class Media:
        css = {'all': ('css/question_grouped.css',)}
        js = ('js/question_grouped.js',)

    def save_model(self, request, obj, form, change):
        # تحقق الصلاحيات
        if not request.user.is_basic:  # أو استخدم request.user.is_teacher لو تبغاها للمعلمين فقط
            messages.error(request, "المستخدم لا يمكنه إنشاء الأسئلة.")
            return

        try:
            basic_user = BasicUser.objects.get(pk=request.user.pk)
        except BasicUser.DoesNotExist:
            messages.error(request, "لا يوجد مستخدم أساسي مرتبط بالحساب الحالي.")
            return

        obj.created_by = basic_user
        obj.question_type = Question.QuestionTypes.TRUE_FALSE
        super().save_model(request, obj, form, change)

        correct_flag = form.cleaned_data['correct_answer'] == 'true'

        # أنشئ/حدّث إجابتين: "صح" و"خطأ" وتأكد أن واحدة فقط صحيحة
        with transaction.atomic():
            # احذف أي إجابات زائدة ليست "صح/خطأ"
            obj.answers.exclude(answer_text__in=['صح', 'خطأ']).delete()

            true_ans, created = Answer.objects.get_or_create(
                question=obj, answer_text='صح',
                defaults={'is_correct': correct_flag}
            )
            if not created:
                true_ans.is_correct = correct_flag
                true_ans.save()

            false_ans, created = Answer.objects.get_or_create(
                question=obj, answer_text='خطأ',
                defaults={'is_correct': not correct_flag}
            )
            if not created:
                false_ans.is_correct = not correct_flag
                false_ans.save()

    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data'):
            qs = self.get_queryset(request)\
                    .select_related('exam', 'exam__course', 'created_by')\
                    .order_by('exam__id', 'id')
            search_term = request.GET.get('q', '')
            qs, use_distinct = self.get_search_results(request, qs, search_term)
            if use_distinct:
                qs = qs.distinct()

            from collections import OrderedDict
            grouped = OrderedDict()
            for q in qs:
                ex_id = q.exam_id
                if ex_id not in grouped:
                    grouped[ex_id] = {'exam': q.exam, 'questions': []}
                grouped[ex_id]['questions'].append(q)

            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            response.context_data['grouped_exams'] = list(grouped.values())
            response.context_data['admin_change_url_name'] = f'admin:{app_label}_{model_name}_change'
            response.context_data['title'] = 'أسئلة الصح والخطأ حسب الامتحان'
        return response





# =============================== AnswerAdminPanel (grouped) ===========================================
class AnswerAdminPanel(ReadOnlyViewAdminMixin, admin.ModelAdmin):
    change_list_template = 'taecher_app/change_list.html'
    ordering = ('question__exam__id', 'question__id', 'id')
    list_filter = ()
    list_display = ('question', 'answer_text', 'is_correct')
    search_fields = (
        'answer_text',
        'question__text',
        'question__exam__name',
        'question__exam__course__name',
    )

    class Media:
        css = {'all': ('css/question_grouped_answer.css',)}
        js = ('js/answer_grouped.js',)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data'):
            qs = self.get_queryset(request).select_related(
                'question',
                'question__exam',
                'question__exam__course',
                'question__created_by',
            ).order_by('question__exam__id', 'question__id', 'id')

            search_term = request.GET.get('q', '')
            qs, use_distinct = self.get_search_results(request, qs, search_term)
            if use_distinct:
                qs = qs.distinct()

            from collections import OrderedDict
            grouped = OrderedDict()
            for ans in qs:
                exam = ans.question.exam
                ex_id = exam.id
                if ex_id not in grouped:
                    grouped[ex_id] = {
                        'exam': exam,
                        'questions': OrderedDict()
                    }
                q_id = ans.question_id
                if q_id not in grouped[ex_id]['questions']:
                    grouped[ex_id]['questions'][q_id] = {
                        'question': ans.question,
                        'answers': []
                    }
                grouped[ex_id]['questions'][q_id]['answers'].append(ans)

            # تحويل القواميس لقوائم لاستخدامها بسهولة في القالب
            groups = []
            for ex in grouped.values():
                q_list = list(ex['questions'].values())
                groups.append({'exam': ex['exam'], 'questions': q_list})

            app_label = self.model._meta.app_label              # taecher_app
            model_name = self.model._meta.model_name            # answer
            response.context_data['groups'] = groups
            response.context_data['answer_change_url_name'] = f'admin:{app_label}_{model_name}_change'
            # روابط مفيدة أخرى
            from .models import Question, Exam
            response.context_data['question_change_url_name'] = f'admin:{Question._meta.app_label}_{Question._meta.model_name}_change'
            response.context_data['exam_change_url_name'] = f'admin:{Exam._meta.app_label}_{Exam._meta.model_name}_change'
            response.context_data['course_change_url_name'] = 'admin:admin_app_course_change'
            response.context_data['title'] = 'الإجابات حسب الامتحان والسؤال'
        return response




# =============================== ExamAdminPanel ===========================================
from django.contrib import admin
from .models import Exam, Teacher

class ExamAdminPanel(admin.ModelAdmin):
    list_display = ('name', 'course', 'exam_type', 'exam_category', 'total_marks', 'show_results', 'created_by', 'created_at')
    search_fields = ('name', 'course__name', 'created_by__username')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'course', 'exam_type', 'exam_category', 'duration', 'show_results', 'file')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            teacher = Teacher.objects.filter(pk=request.user.pk).first()
            if teacher:
                obj.created_by = teacher
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        teacher = Teacher.objects.filter(pk=request.user.pk).first()
        if teacher:
            return qs.filter(created_by=teacher)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        return obj.created_by and obj.created_by.pk == request.user.pk

    def has_delete_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        return obj.created_by and obj.created_by.pk == request.user.pk

    def has_view_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        return obj.created_by and obj.created_by.pk == request.user.pk

# إلغاء أي تسجيل قديم قبل التسجيل الجديد
try:
    admin.site.unregister(Exam)
except admin.sites.NotRegistered:
    pass

admin.site.register(Exam, ExamAdminPanel)






# class ExamAdminPanel(admin.ModelAdmin):
#     list_display = ('name', 'course', 'exam_type', 'exam_category', 'total_marks', 'show_results', 'created_by', 'created_at')
#     list_filter = ()
#     search_fields = ('name', 'course__name', 'created_by__user__username')
#     ordering = ('-created_at',)
#     fieldsets = (
#         (None, {
#             'fields': ('name', 'description', 'course', 'exam_type', 'exam_category', 'duration', 'show_results', 'file')
#         }),
#     )
#     # readonly_fields = ['total_marks']


#     def save_model(self, request, obj, form, change):
#         if not obj.created_by:
#             teacher = Teacher.objects.filter(pk=request.user.pk).first()
#             obj.created_by = teacher # إذا كان لديك ربط المستخدم بالمعلم
#         super().save_model(request, obj, form, change)




# =============================== StudentExamAttendance_admin ===========================================
class StudentExamAttendance_admin(admin.ModelAdmin):
    list_display = ('student','exam', 'attendance_date')




# Register your models here.
# admin.site.register(Exam , ExamAdminPanel)
admin.site.register(StudentExamAttendance,StudentExamAttendance_admin)
admin.site.register(ExamStatusLog)
admin.site.register(Question, QuestionAdminPanel)
admin.site.register(EssayQuestion , EssayQuestionAdminPanel)
admin.site.register(NumericQuestion , NumericQuestionAdminPanel)
admin.site.register(MultipleChoiceQuestion , MultipleChoiceQuestionAdminPanel)
admin.site.register(TrueFalseQuestion , TrueFalseQuestionnAdminPanel)
admin.site.register(Answer , AnswerAdminPanel)
admin.site.register(EssayAnswerEvaluation)
