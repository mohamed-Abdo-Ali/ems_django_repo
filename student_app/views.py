from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils import timezone  # This is correct!
from conttroll_app.models import ExamScheduleView, StudentExamAttendance, student_report_from_uivercity
from taecher_app.models import EssayQuestion,Exam,Question,Answer,NumericQuestion , TrueFalseQuestion , MultipleChoiceQuestion
from .models import StudentMultipleChoiceQuestionAnswer,StudentTrueFalseQutionAnswer,StudentEssayAnswer,StudentExamAttempt,StudentNumericAnswer
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth import logout



# ============================ home function viwe =======================================================================================
def home(request):
    return render(request, 'student_app/home.html')






# ============================ insert_unviercityNumber function viwe =======================================================================================
def insert_unviercityNumber(request):
    
    
    
    print("=========================",request.user)
    univercity_number = None
    if not any(
        getattr(request.user, attr, False) 
        for attr in ["is_basic", "is_teacher", "is_committee_member", "is_manager"]
    ):
        if request.method == 'POST' and 'button_next' in request.POST:
            
            if not request.POST.get('form_university_id', '').strip():
                messages.info(request, "الرجاء إدخال الرقم الجامعي")
                return redirect('student_app:insert_unviercityNumber')
            else : 
                univercity_number = request.POST.get('form_university_id', '').strip()
            


            if not request.POST.get('form_attendace_statu', '') == 'on':
                messages.info(request, "الرجاء التحديد على تسجيل الحضور")
                return redirect('student_app:insert_unviercityNumber')

            try:

                student = student_report_from_uivercity.objects.get(univercity_number =  univercity_number)
                
                major_number = student.major_to_number(student.major)


                today = timezone.now().date()
                schedule_qs = ExamScheduleView.objects.filter(
                    semester_id=student.semester_id,
                    major_id=major_number,
                    exam_date=today
                ).order_by('exam_date')
                

                if not schedule_qs.exists():
                    messages.info(request, 'لا توجد امتحانات متاحة لك اليوم')
                    return redirect('authentcat_app:sign_in')
                
                # سنأخذ أول امتحان اليوم (يمكنك لاحقاً إتاحة اختيار من بين أكثر من امتحان)
                exam_id = schedule_qs.first().exam_id 
                exam = get_object_or_404(Exam, id=exam_id)



                with transaction.atomic():
                    attendance, _ = StudentExamAttendance.objects.get_or_create(
                        student=student,
                        exam=exam,
                        defaults={'status': StudentExamAttendance.AttendanceStatus.FIRST_ATTEMPT}
                    )

                    print("=======> ",schedule_qs)
                    # محاولة واحدة فقط للامتحان
                    attempt = StudentExamAttempt.objects.filter(attendance=attendance).order_by('-attempt_number').first()
                    if attempt:
                        if attempt.is_submitted:
                            messages.warning(request, "لقد أتممت هذا الامتحان سابقاً. لا توجد محاولات إضافية.")
                            return redirect('authentcat_app:sign_in')
                        
                        # وإلا: نكمل على نفس المحاولة
                    else:
                        attempt = StudentExamAttempt.objects.create(attendance=attendance)

                # خزّن في الجلسة
                request.session['exam_id'] = exam.id
                request.session['attempt_id'] = attempt.id
                request.session['univercity_number'] = univercity_number

                messages.success(request, f"مرحباً {student.name} - تم تجهيز محاولتك للاختبار")
                
                return redirect('student_app:instructions')
            

            except student_report_from_uivercity.DoesNotExist :
                messages.error(request, "لا يوجد طالب برقم هذة البطاقة تاكد من رقم البطاقة")
                return redirect('student_app:insert_unviercityNumber')
                
            except Exception as e:
                messages.error(request, f"حدث خطأ غير متوقع: {str(e)}")
                return redirect('student_app:insert_unviercityNumber')


    else :
        messages.error(request, "هذة الصفحة للطلاب انت لست طالب")
        return redirect('authentcat_app:sign_in')


        
    
    context = {'university_id': univercity_number}
    return render(request, 'student_app/insert_unviercityNumber.html')






# ============================ instructions function viwe =======================================================================================
def instructions(request):
    
    univercity_number = request.session.get('univercity_number')
    
    if not any(
        getattr(request.user, attr, False) 
        for attr in ["is_basic", "is_teacher", "is_committee_member", "is_manager"]
    ):
        stud = student_report_from_uivercity.objects.filter(univercity_number =  univercity_number).first()
        if stud:
            print(stud)
        else:
            print("لا يوجد طالب")
        university_id = univercity_number
    else :
        messages.error(request, "هذة الصفحة للطلاب انت لست طالب")
        return redirect('authentcat_app:sign_in')
   
    
    
    
    
    last_attempt = request.session.get('last_attempt', [])
    attendance = request.session.get('attendance', [])

    
    
    request.session['last_attempt'] = last_attempt
    request.session['attendance'] = attendance
    
    
    
    # استرجاع القيم من الـ session
    Exams_available_ids = request.session.get('Exams_available_ids', [])
    Exams_available_ids_from_schedule = request.session.get('Exams_available', [])
    
    request.session['Exams_available_ids'] = Exams_available_ids
    request.session['Exams_available'] = [Exams_available_ids_from_schedule]  # نخزن الـ IDs فقط
    
    if request.method == 'POST' and 'submit_butt' in request.POST:
        # التحقق من تحديد خيار تسجيل الحضور
        if not request.POST.get('agree', '') == 'on':
            messages.info(request, "الرجاء التحديد قرات كل الارشادات")
            return redirect('student_app:instructions') 

        return redirect('student_app:student_exam')
    
    
    
    
    


    return render(request, 'student_app/instructions.html')





# ============================ student_exam function viwe =======================================================================================
def student_exam(request):
    
    # if request.user.is_basic or request.user.is_teacher or  request.user.is_committee_member  or  request.user.is_manager:
    #     pass
    # else : 
    #     messages.error(request , "هذة الصفحة خاصة ب الطلاب انت لست طالب")
    #     return redirect('authentcat_app:sign_in')
    

    attempt_id = request.session.get('attempt_id')
    exam_id = request.session.get('exam_id')
    if not attempt_id or not exam_id:
        messages.warning(request, "لا توجد محاولة نشطة")
        return redirect('student_app:instructions')

    attempt = get_object_or_404(StudentExamAttempt, id=attempt_id)
    first_exam = attempt.attendance.exam  # الامتحان الحالي من المحاولة

    # جلب الأسئلة من الجدول الأساسي والاستفادة من الوراثة عبر question_type
    questions = (Question.objects
        .filter(exam=first_exam)
        .select_related('exam')
        .prefetch_related('answers')
        .order_by('id'))

    # إعداد بيانات العرض مع الإجابات المحفوظة (upsert)
    items = []
    for q in questions:
        item = {
            'q': q,
            'type': q.question_type,
            'points': q.points,
            'text': q.text,
            'answers': list(q.answers.all()),
            'saved_choice_id': None,
            'saved_numeric': '',
            'saved_essay': '',
        }
        if q.question_type == Question.QuestionTypes.MULTIPLE_CHOICE:
            try:
                sub = q.multiplechoicequestion
                rec = StudentMultipleChoiceQuestionAnswer.objects.filter(exam_attempt=attempt, question=sub).first()
                if rec:
                    item['saved_choice_id'] = rec.chosen_answer_id
            except MultipleChoiceQuestion.DoesNotExist:
                pass

        elif q.question_type == Question.QuestionTypes.TRUE_FALSE:
            try:
                sub = q.truefalsequestion
                rec = StudentTrueFalseQutionAnswer.objects.filter(exam_attempt=attempt, question=sub).first()
                if rec:
                    item['saved_choice_id'] = rec.chosen_answer_id
            except TrueFalseQuestion.DoesNotExist:
                pass

        elif q.question_type == Question.QuestionTypes.NUMERIC:
            try:
                sub = q.numericquestion
                rec = StudentNumericAnswer.objects.filter(exam_attempt=attempt, question=sub).first()
                if rec:
                    item['saved_numeric'] = rec.student_answer
            except NumericQuestion.DoesNotExist:
                pass

        elif q.question_type == Question.QuestionTypes.ESSAY:
            try:
                sub = q.essayquestion
                rec = StudentEssayAnswer.objects.filter(exam_attempt=attempt, question=sub).first()
                if rec:
                    item['saved_essay'] = rec.answer_text
            except EssayQuestion.DoesNotExist:
                pass

        items.append(item)

    univercity_number = request.session.get('univercity_number')
    stud = student_report_from_uivercity.objects.filter(univercity_number =  univercity_number).first()
    
    connected_user = get_object_or_404(student_report_from_uivercity, univercity_number =  univercity_number)
    the_student = get_object_or_404(student_report_from_uivercity, univercity_number =  univercity_number)
    
    

    # معالجة حفظ الإجابات (AJAX)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            if attempt.is_submitted:
                return JsonResponse({'status': 'error', 'message': 'تم تسليم الامتحان. لا يمكنك التعديل.'}, status=400)

            question_id = int(request.POST.get('question_id'))
            q = get_object_or_404(Question, id=question_id, exam=first_exam)

            # objective (TF/MC)
            if 'answer_id' in request.POST:
                answer_id = int(request.POST.get('answer_id'))
                answer_obj = get_object_or_404(Answer, id=answer_id, question_id=q.id)

                if q.question_type == Question.QuestionTypes.MULTIPLE_CHOICE:
                    sub = q.multiplechoicequestion
                    existing = StudentMultipleChoiceQuestionAnswer.objects.filter(
                        exam_attempt=attempt, question=sub
                    ).first()
                    if existing:
                        existing.chosen_answer = answer_obj
                        existing.save()
                    else:
                        StudentMultipleChoiceQuestionAnswer.objects.create(
                            exam_attempt=attempt, question=sub, chosen_answer=answer_obj
                        )

                elif q.question_type == Question.QuestionTypes.TRUE_FALSE:
                    sub = q.truefalsequestion
                    existing = StudentTrueFalseQutionAnswer.objects.filter(
                        exam_attempt=attempt, question=sub
                    ).first()
                    if existing:
                        existing.chosen_answer = answer_obj
                        existing.save()
                    else:
                        StudentTrueFalseQutionAnswer.objects.create(
                            exam_attempt=attempt, question=sub, chosen_answer=answer_obj
                        )
                else:
                    return JsonResponse({'status': 'error', 'message': 'نوع السؤال غير موضوعي'}, status=400)

                return JsonResponse({'status': 'success'})

            # essay
            if 'answer_text' in request.POST:
                answer_text = (request.POST.get('answer_text') or '').strip()
                sub = q.essayquestion
                existing = StudentEssayAnswer.objects.filter(exam_attempt=attempt, question=sub).first()
                if existing:
                    existing.answer_text = answer_text
                    existing.save()
                else:
                    StudentEssayAnswer.objects.create(
                        exam_attempt=attempt, question=sub, answer_text=answer_text
                    )
                return JsonResponse({'status': 'success'})

            # numeric
            if 'answer_value' in request.POST:
                try:
                    val = float(request.POST.get('answer_value'))
                except (TypeError, ValueError):
                    return JsonResponse({'status': 'error', 'message': 'قيمة غير صالحة'}, status=400)
                sub = q.numericquestion
                existing = StudentNumericAnswer.objects.filter(exam_attempt=attempt, question=sub).first()
                if existing:
                    existing.student_answer = val
                    existing.save()
                else:
                    StudentNumericAnswer.objects.create(
                        exam_attempt=attempt, question=sub, student_answer=val
                    )
                return JsonResponse({'status': 'success'})

            return JsonResponse({'status': 'error', 'message': 'طلب غير معروف'}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # إنهاء الامتحان
    if request.method == 'POST' and 'finsh_submet_exam_butt' in request.POST:
        if attempt.is_submitted:
            return redirect('student_app:exam_sucss')
        attempt.is_submitted = True
        attempt.end_time = timezone.now()
        attempt.save(update_fields=['is_submitted', 'end_time'])
        attempt.calculate_scores()
        return redirect('student_app:exam_sucss')
    
    stats = attempt.get_answered_stats()

    context = {
        'attempt': attempt,
        'exam': first_exam,
        'items': items,
        'connected_user': connected_user,
        'the_student': the_student,
        'is_submitted': attempt.is_submitted,
        # إضافات جديدة:
        'answered_count': stats['answered_count'],
        'total_questions': stats['total_questions'],
        'elapsed_seconds': attempt.duration_seconds,  # سيُحتسب تلقائياً (إنتهى أم لا)
        'start_time': attempt.start_time,
        'end_time': attempt.end_time,
    }
    print("========================")
    
    return render(request, 'student_app/student_exam.html', context) 



# ============================ exam_sucss function viwe =======================================================
def exam_sucss(request):
    attempt_id = request.session.get('attempt_id')
    if not attempt_id:
        messages.warning(request, "لا توجد محاولة")
        return redirect('authentcat_app:sign_in')

    attempt = get_object_or_404(StudentExamAttempt, id=attempt_id)

    # نظّف الجلسة وسجّل الخروج
    request.session.pop('attempt_id', None)
    request.session.pop('exam_id', None)
    logout(request)

    stats = attempt.get_answered_stats()

    grad = attempt.total_score 
    print(" =====> the grad is === : ",grad)
    
    context = {
        'total_score': attempt.total_score,
        'answered_count': stats['answered_count'],
        'total_questions': stats['total_questions'],
        'duration_seconds': attempt.duration_seconds,
        'duration_human': attempt.duration_human,
        'start_time': attempt.start_time,
        'end_time': attempt.end_time,
    }
    return render(request, 'student_app/exam_sucss.html', context)

