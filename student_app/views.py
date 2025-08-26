from django.shortcuts import get_object_or_404, redirect, render
from authentcat_app.models import User,Student
from admin_app.models import Semester
from django.contrib import messages
from django.utils import timezone
from conttroll_app.models import ExamScheduleView, StudentExamAttendance
from taecher_app.models import EssayQuestion,Exam,Question,Answer,NumericQuestion
from .models import ObjectiveQuestionAttempt,StudentEssayAnswer,StudentExamAttempt,StudentNumericAnswer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json


# Create your views here.
# ============================ home function viwe =======================================================================================
def home(request):
    return render(request, 'student_app/home.html')







# ============================ insert_unviercityNumber function viwe =======================================================================================
def insert_unviercityNumber(request):
    university_id = ''
    context = {}
    
    if not request.user.is_authenticated :
        messages.error(request, "انت غير مسجل الدخول الرجاء تسجيل الدخول اولا ثم تسجيل الحضور")
        return redirect('authentcat_app:sign_in')
    else :
        if not hasattr(request.user, 'student'):
            messages.error(request, " هذا الحساب ليس حساب طالب الرجاء تسجيل الدخول بحساب طالب لان هذة الصفحة خاصة ب الطلاب")
            return redirect('authentcat_app:sign_in')
        else :
            stud = Student.objects.filter(user=request.user).first()
            if stud:
                print(stud)
            else:
                print("لا يوجد طالب")
            university_id = stud.university_id

            
        # university_id_student = request.user
        
    if request.method == 'POST' and 'button_next' in request.POST:
        
        university_id = request.POST.get('form_university_id')
        
        
        
        # التحقق من إدخال الرقم الجامعي
        if not request.POST.get('form_university_id', '').strip():
            messages.info(request, "الرجاء إدخال الرقم الجامعي")
            return redirect('student_app:insert_unviercityNumber') 
        

        # التحقق من تحديد خيار تسجيل الحضور
        if not request.POST.get('form_attendace_statu', '') == 'on':
            messages.info(request, "الرجاء التحديد على تسجيل الحضور")
            return redirect('student_app:insert_unviercityNumber') 



        try:
            student = Student.objects.get(university_id=university_id)
            
            
            
            if not student.user.is_active:
                messages.error(request, f"حساب الطالب {student.user.full_name} موقوف من قبل الإدارة")
                return redirect('student_app:insert_unviercityNumber') 
                
            
            if not hasattr(student, 'user'):
                messages.warning(request, "هذا الطالب ليس لديه حساب مستخدم مرتبط")
                return redirect('student_app:insert_unviercityNumber') 
                

            # الحصول على الامتحانات المتاحة للطالب اليوم
            today = timezone.now().date()
            Exams_available = ExamScheduleView.objects.filter(
                semester_id=student.Semester.id,
                major_id=student.Major.id,
                exam_date=today
            ).order_by('exam_date')


            if not Exams_available.exists():
                messages.info(request, 'لا توجد امتحانات متاحة لك اليوم')
                return redirect('student_app:insert_unviercityNumber')

            Exams_available_ids = [exam.exam_id for exam in Exams_available]
            Exams_available_data = Exam.objects.filter(id__in=Exams_available_ids)
            
            # إنشاء أو تحديث سجلات الحضور والمحاولات
            for exam in Exams_available_data:
                # الحصول على سجل الحضور أو إنشائه إذا لم يكن موجوداً
                attendance, created = StudentExamAttendance.objects.get_or_create(
                    student=student,
                    exam=exam,
                    defaults={'status': StudentExamAttendance.AttendanceStatus.FIRST_ATTEMPT}
                )
                
                # إذا كان الحضور موجوداً مسبقاً، نغير حالته إلى "إعادة"
                if not created:
                    attendance.status = StudentExamAttendance.AttendanceStatus.RETAKE
                    attendance.save()
                
                
               
                # فلاترة محاولة جديدة لهذا الحضور
                last_attempt = StudentExamAttempt.objects.filter(
                    attendance=attendance
                ).order_by('-attempt_number').first()
                
                
                if last_attempt :
                    request.session['last_attempt'] = last_attempt.id
                    print("========> last_attempt number : ",last_attempt.attempt_number)
                    print("========> last_attempt id : ",last_attempt.id)
                    
                else :
                    # إنشاء محاولة جديدة لهذا الحضور
                    StudentExamAttempt.objects.create(
                        attendance=attendance,
                        attempt_number=last_attempt
                    )
                    request.session['last_attempt'] = last_attempt.id+1

            # تخزين بيانات الامتحانات في الجلسة
            request.session['Exams_available_ids'] = Exams_available_ids
            request.session['student_id'] = student.id
            
            
            # ارسال رقم المحاولة و سجل الحضور
          
            request.session['attendance'] = attendance.id+1
            
            
            messages.success(request, f"مرحباً {student.user.full_name} - تم تسجيل محاولتك الجديدة بنجاح")
            return redirect('student_app:instructions')

        except Student.DoesNotExist:
            messages.error(request, f"لا يوجد طالب مسجل بهذا الرقم {university_id}")
        except Exception as e:
            messages.error(request, f"حدث خطأ غير متوقع: {str(e)}")
    
    
    
    context = {
            'university_id':university_id,
        }
    
    
    return render(request, 'student_app/insert_unviercityNumber.html',context)



# ============================ instructions function viwe =======================================================================================
def instructions(request):
    
    
        
    if not request.user.is_authenticated :
        messages.error(request, "انت غير مسجل الدخول الرجاء تسجيل الدخول اولا ثم تسجيل الحضور")
        return redirect('authentcat_app:sign_in')
    else :
        if not hasattr(request.user, 'student'):
            messages.error(request, " هذا الحساب ليس حساب طالب الرجاء تسجيل الدخول بحساب طالب لان هذة الصفحة خاصة ب الطلاب")
            return redirect('authentcat_app:sign_in')
        else :
            stud = Student.objects.filter(user=request.user).first()
            if stud:
                print(stud)
            else:
                print("لا يوجد طالب")
            university_id = stud.university_id

            
        # university_id_student = request.user
        
    
    
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

@csrf_exempt
# @require_POST
def student_exam(request):
    
    
            
    if not request.user.is_authenticated :
        messages.error(request, "انت غير مسجل الدخول الرجاء تسجيل الدخول اولا ثم تسجيل الحضور")
        return redirect('authentcat_app:sign_in')
    else :
        if not hasattr(request.user, 'student'):
            messages.error(request, " هذا الحساب ليس حساب طالب الرجاء تسجيل الدخول بحساب طالب لان هذة الصفحة خاصة ب الطلاب")
            return redirect('authentcat_app:sign_in')
        else :
            stud = Student.objects.filter(user=request.user).first()
            if stud:
                print(f"===> student name : {stud.user.full_name}")
                print(f"===> student university number : {stud.university_id}")
            else:
                print("===> لا يوجد طالب")
            university_id = stud.university_id

            
        
    
    
    
    Exams_available_ids = request.session.get('Exams_available_ids', [])
    
    if not Exams_available_ids:
        messages.warning(request,"لا يوجد إمتحان")
        return redirect('student_app:instructions')
    
    Exams_available_ids_from_schedule = request.session.get('Exams_available', [])
    
    exams = Exam.objects.all()
    all_question = Question.objects.all()
    ansers = Answer.objects.all()
    
    exam_questions = Question.objects.filter(exam_id__in=Exams_available_ids)
    Exams_available = Exam.objects.filter(id__in=Exams_available_ids)
    
    
    exam_questions = Question.objects.filter(
    exam_id__in=Exams_available_ids
    ).prefetch_related('answers')
    
    essay_questions = EssayQuestion.objects.filter(
        exam_id__in=Exams_available_ids
    )
    
    numericQuestion_questions = NumericQuestion.objects.filter(
        exam_id__in=Exams_available_ids
    )
    
    
    
    last_attempt2 = request.session.get('last_attempt')
    print("===> last_attempt : ",last_attempt2)
    attendance = request.session.get('attendance')

    
    last_attempt = StudentExamAttempt.objects.get(id=last_attempt2)
    
    
    
    
    exam_question_all_qution = list(exam_questions) + list(essay_questions) + list(numericQuestion_questions)
    
    if not exam_question_all_qution:
        messages.warning(request,"لا توجد اسئلة للامتحان")
        return redirect('student_app:instructions')
        

    
    connected_user = request.user
    first_exam = Exam.objects.filter(id__in=Exams_available_ids).first()
    the_student = Student.objects.get(user = request.user)
    
    

    
    context ={
        'last_attempt':last_attempt,
        'exam_question_all_qution':exam_question_all_qution,
        'the_student':the_student,
        'first_exam':first_exam,
        'connected_user':connected_user,
        'exam_questions' : exam_questions,
        'essay_questions' : essay_questions,
    }
    
    

    
    
    
    if request.method == 'POST' :
        try:
            question_id = request.POST.get('question_id')
            question_type = request.POST.get('question_type')        
            print(f"===> resive qution ID: {question_id} type : {question_type}")
            
            if question_type == 'objective':
                answer_id = request.POST.get('answer_id')
                
                question_obj = get_object_or_404(Question, id=question_id)
                answer_obj = get_object_or_404(Answer, id=answer_id)
                
                objectiveQuestionAttempt = ObjectiveQuestionAttempt .objects.create(
                    exam_attempt = last_attempt,
                    question = question_obj,
                    # defaults={'chosen_answer': answer_obj}
                    chosen_answer = answer_obj
                )
                if objectiveQuestionAttempt :
                    print("===> ok add ")
                print(f"===> answer qution ID : {question_id}, answer id ID: {answer_id}")
                
                
                
            elif question_type == 'essay':
                answer_text = request.POST.get('answer_text')
                
                question_obj = get_object_or_404(EssayQuestion, id=question_id)
                
                print("===> last_attempt2====>", last_attempt)
                print("===> question_obj:", question_obj)
                print("===> answer_text:", answer_text)

                studentEssayAnswer =  StudentEssayAnswer.objects.create(
                    exam_attempt = last_attempt,
                    question = question_obj,
                    answer_text = answer_text
                    # defaults={'answer_text': answer_text}
                )
                print("===> ok add ")
                # if studentEssayAnswer :
                    # print("======> ok add ")
                print(f"===> answer qution ID: : {question_id}, text : {answer_text}")
                
                
                
            elif question_type == 'numeric':
                answer_value = request.POST.get('answer_value')
                
                question_obj = get_object_or_404(NumericQuestion, id=question_id)
                
                studentNumericAnswer = StudentNumericAnswer.objects.create(
                    exam_attempt = last_attempt,
                    question = question_obj,
                    student_answer = answer_value
                )
                if studentNumericAnswer :
                    print("===> ok add ")
                print(f"===> answer qution ID : {question_id}, value : {answer_value}")
            
            # return JsonResponse({'status': 'success', 'message': 'تم الحفظ بنجاح'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
        
    
    
    # print("post data : ", request.POST)
    if request.method == 'POST' and 'finsh_submet_exam_butt' in request.POST:
        
        request.session['last_attempt'] = last_attempt2
        return redirect('student_app:exam_sucss') 
    
    
    
    
    
    return render(request, 'student_app/student_exam.html',context)
    



# ============================ exam_sucss function viwe =======================================================================================
def exam_sucss(request):
    
    connected_user_stud = None
    
    if not request.user.is_authenticated :
        messages.error(request, "انت غير مسجل الدخول الرجاء تسجيل الدخول اولا ثم تسجيل الحضور")
        return redirect('authentcat_app:sign_in')
    else :
        if not hasattr(request.user, 'student'):
            messages.error(request, " هذا الحساب ليس حساب طالب الرجاء تسجيل الدخول بحساب طالب لان هذة الصفحة خاصة ب الطلاب")
            return redirect('authentcat_app:sign_in')
        else :
            stud = Student.objects.filter(user=request.user).first()
            if stud:
                print(stud)
                connected_user_stud = stud
            else:
                print("لا يوجد طالب")
    
    Exams_available_ids = request.session.get('Exams_available_ids', [])
    first_exam = Exam.objects.filter(id__in=Exams_available_ids).first()
    
    
    studentExamAttendance = StudentExamAttendance.objects.filter(student = connected_user_stud , exam = first_exam ).first()
    
    studentExamAttempt = StudentExamAttempt.objects.filter(attendance = studentExamAttendance).last()
    
    # last_attempt2 = request.session.get('last_attempt')
    # last_attempt = StudentExamAttempt.objects.get(id=last_attempt2)
    
    
    context={
        'total_score': studentExamAttempt.total_score
    }
    
    return render(request, 'student_app/exam_sucss.html',context)





