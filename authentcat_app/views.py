from django.contrib import auth  
import re
from .models import  Profile, buffer_Student
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login  # هذا ما ناقصك
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q
from django.contrib.auth.decorators import login_required




# ============================ sign_in function viwe ===============================================
def sign_in(request):
    if request.method == 'POST' and 'login_button_template' in request.POST:
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me') == 'on'

        if not username or not password:
            messages.error(request, "يجب إدخال اسم المستخدم وكلمة المرور")
            return render(request, 'authentcat_app/sign_in.html')

        # محاولة التحقق من الطلاب أولًا (buffer_Student)
        try:
            student = buffer_Student.objects.get(username=username, password=password)
            # تم التحقق من الطالب بنجاح (مقارنة نصية)
            request.session['student_username'] = student.username  # تخزين اسم الطالب في الجلسة
            request.session['student_password'] = student.password  # تخزين اسم الطالب في الجلسة
            return redirect('student_app:insert_unviercityNumber')
        except buffer_Student.DoesNotExist:
            # إذا لم يكن الطالب، نتحقق من المستخدم الأساسي
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    request.session.set_expiry(0 if not remember_me else 1209600)
                    login(request, user)

                    # التحقق من الملف الشخصي
                    try:
                        profile = Profile.objects.get(user=user)
                        if not profile.phone_number or not profile.email:
                            return redirect('authentcat_app:insert_phoneEmail')
                    except Profile.DoesNotExist:
                        return redirect('authentcat_app:insert_phoneEmail')

                    # إعادة التوجيه حسب نوع المستخدم الأساسي
                    if hasattr(user, 'is_basic') and user.is_basic:
                        return redirect('/admin/')
                    elif hasattr(user, 'is_student') and user.is_student:
                        return redirect('student_app:insert_unviercityNumber')
                    else:
                        return redirect('authentcat_app:home')
                else:
                    messages.error(request, "حسابك معطل. يرجى التواصل مع الإدارة")
            else:
                messages.error(request, "اسم المستخدم أو كلمة المرور غير صحيحة")

            return render(request, 'authentcat_app/sign_in.html')

    return render(request, 'authentcat_app/sign_in.html')





# ============================ password_reset function viwe ===============================================
def password_reset(request):
    return render(request, 'authentcat_app/password_reset.html')


# ============================ insert_phoneEmail function viwe ===============================================
def show_profile(request):
    email = None
    phone = None

    current_user = request.user
    user_profile_data = get_object_or_404(Profile, user=current_user)
    phone = user_profile_data.phone_number
    email = user_profile_data.email
        
    if request.method == 'POST' and 'edit_profile_butt' in request.POST :
        return redirect ('authentcat_app:update_profile')
    
    context ={
        'phone': phone,
        'email': email
    }
    
    
    if request.method == 'POST' and 'ok_butt' in request.POST :
        return redirect ('authentcat_app:sign_in')
    
    

    return render(request, 'authentcat_app/show_profile.html',context)



# ============================ update_profile function viwe ===============================================
@login_required
def update_profile(request):
    
    profile = Profile.objects.get_or_create(user=request.user)[0]
    
    original_phone = None
    new_phone = None
    original_email = None
    new_email = None
    
    form_data = request.session.pop('form_data', {})

    if request.method == 'POST' and 'submit_butt' in request.POST:
        new_phone = request.POST.get('phone', '').strip()
        new_email = request.POST.get('email', '').strip().lower()
        
        # حفظ القيم الأصلية قبل أي مقارنة
        original_email = profile.email.lower()
        original_phone = profile.phone_number


        # التحقق من التغييرات الفعلية
        no_changes = new_email == original_email or new_phone == original_phone
        
        
        if no_changes:
            messages.info(request, 'لم تقم بإجراء أي تغييرات')
            request.session['form_data'] = {'phone': new_phone, 'email': new_email}
            return redirect('authentcat_app:update_profile')
            
        errors = False
        
        # التحقق من صحة الإيميل (فقط إذا تغير)
        if new_email != original_email:
            if not new_email:
                messages.error(request, 'البريد الإلكتروني مطلوب')
                errors = True
            elif Profile.objects.filter(email=new_email).exclude(user=request.user).exists():
                messages.error(request, 'البريد الإلكتروني مستخدم بالفعل')
                errors = True

        # التحقق من صحة الهاتف (فقط إذا تغير)
        if new_phone != original_phone:
            if not new_phone:
                messages.error(request, 'رقم الهاتف مطلوب')
                errors = True
            elif not re.match(r'^(77|78|70|71|73)\d{7}$', new_phone):
                messages.error(request, 'رقم هاتف يمني غير صحيح')
                errors = True

        if errors:
            request.session['form_data'] = {'phone': new_phone, 'email': new_email}
            return redirect('authentcat_app:update_profile')

        # تحديث البيانات
        if new_email != original_email:
            profile.email = new_email
        
        if new_phone != original_phone:
            profile.phone_number = new_phone
        
        profile.save()
        
        messages.success(request, 'تم التحديث بنجاح')
        request.session['form_data'] = {'phone': '', 'email': ''}
        original_phone = ''
        new_phone = ''
        original_email = ''
        new_email = ''
        return redirect('authentcat_app:update_profile')
    

    context = {
        'email': form_data.get('email', profile.email),
        'phone': form_data.get('phone', profile.phone_number)
    }
    return render(request, 'authentcat_app/insert_phoneEmail.html', context)



    
    
# ============================ insert_phoneEmail function viwe ===============================================
def insert_phoneEmail(request):
    context = None

    if not request.user.is_authenticated:
        messages.error(request, "انت غير مسجل الدخول الرجاء تسجيل الدخول اولا ثم إخال رقم الهاتف و الايميل")
        return redirect('authentcat_app:sign_in')
        
    current_user = request.user
    
    try:
        profile = Profile.objects.get(user = current_user )
        return redirect('authentcat_app:show_profile')
    except Profile.DoesNotExist:
        
            
        if request.method == 'POST' and 'submit_butt' in request.POST:
            phone_number = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
        
        
            
        
            
            context={
                'email':email,
                'phone_number':phone_number
            }
            
        
            # التحقق من وجود البيانات
            if not phone_number or not email:
                messages.error(request, "يجب إدخال كل من رقم الهاتف والبريد الإلكتروني")
                return redirect('authentcat_app:insert_phoneEmail')
            
            # التحقق من صيغة رقم الهاتف اليمني
            yemeni_phone_pattern = r'^(77|78|70|71|73)\d{7}$'
            if not re.match(yemeni_phone_pattern, phone_number):
                messages.error(request, "رقم الهاتف يجب أن يكون يمنيًا (يبدأ بـ 77 أو 78 أو 70 أو 71 أو 73) ويتكون من 9 أرقام")
                return render(request, 'authentcat_app/insert_phoneEmail.html',context)
                
            
            
            # التحقق من صيغة البريد الإلكتروني
            if '@' not in email or '.' not in email.split('@')[-1]:
                messages.error(request, "البريد الإلكتروني غير صالح")
                return render(request, 'authentcat_app/insert_phoneEmail.html',context)
                
            
            # التحقق من عدم تكرار رقم الهاتف أو البريد الإلكتروني لمستخدم آخر
            exists_phone_number = Profile.objects.filter(
                Q(phone_number=phone_number)
            ).exclude(user=request.user).exists()
            
            
            # التحقق من عدم تكرار رقم الهاتف أو البريد الإلكتروني لمستخدم آخر
            exists_email = Profile.objects.filter(
                Q(email=email.lower().strip())
            ).exclude(user=request.user).exists()
            
            
            if exists_phone_number:
                messages.error(request, "رقم الهاتف مستخدم مسبقاً")
                return render(request, 'authentcat_app/insert_phoneEmail.html',context)
            
            if exists_email:
                messages.error(request, "الايميل مستخدم مسبقاً")
                return render(request, 'authentcat_app/insert_phoneEmail.html',context)
                
            try:
                # إنشاء أو تحديث الملف الشخصي
                Profile.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'phone_number': phone_number,
                        'email': email.lower().strip()
                    }
                )
                messages.success(request, "تم حفظ بياناتك بنجاح")
                if request.user.is_basic:
                    return redirect('/admin/')
                else :
                    return redirect('student_app:insert_unviercityNumber')
                    
            
            except IntegrityError:
                messages.error(request, "حدث خطأ أثناء الحفظ")
                return render(request, 'authentcat_app/insert_phoneEmail.html',context)
        
                


        
    return render(request, 'authentcat_app/insert_phoneEmail.html',context)



# ============================ logout function viwe ===============================================

def logout_fun(request):
    if request.user.is_authenticated:
        connected_user = request.user  
        auth.logout(request)

        if connected_user.is_student:
            messages.success(
                request,
                f"تم تسجيل خروج المستخدم {connected_user.username} من نوع  {connected_user.get_user_type_display()} بنجاح"
            )

    return redirect('authentcat_app:sign_in')








# ============================ profile function viwe ===============================================
def profile(request):
    return render(request, 'authentcat_app/profile.html')






# ============================ change_password function viwe ===============================================
def change_password(request):
    return render(request, 'authentcat_app/change_password.html')




