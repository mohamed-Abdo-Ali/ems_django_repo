from django.contrib import auth  
from io import BytesIO
import re
from admin_app.models import Batch, Course, Major,Level,User,Semester
from .models import BasicUser, ControlCommitteeMember, Profile,Student, Teacher,User,Manager
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login  # هذا ما ناقصك
from .forms import  CreateUserForm,ProfileForm
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
import os
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models import Q
from django.contrib.auth.decorators import login_required



# ============================ login function viwe ===============================================
def sign_in(request):
    
    if request.method == 'POST' and 'login_button_template' in request.POST:
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me') == 'on'
        
         # التحقق من المدخلات
        if not username or not password:
            messages.error(request, "يجب إدخال اسم المستخدم وكلمة المرور")
            return render(request, 'authentcat_app/sign_in.html')
        
        user = authenticate(username=username, password=password)
            
            
        if user is not None:  # إذا تمت المصادقة بنجاح
            if user.is_active:  # إذا كان الحساب نشط
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)  # 14 يومًا
                    
                login(request, user)
                
                # التحقق من وجود ملف شخصي للمستخدم
                try:
                    profile = Profile.objects.get(user=user)
                    
                    # إذا كان الملف الشخصي ناقصًا بعض البيانات
                    if not profile.phone_number or not profile.email:
                        return redirect('authentcat_app:insert_phoneEmail')
                    else:
                        if request.user.is_teacher:
                            return redirect('student_app:insert_unviercityNumber')
                        if  request.user.is_student:
                            return redirect('student_app:insert_unviercityNumber')
                        if  request.user.is_committee_member:
                            return redirect('student_app:insert_unviercityNumber')
                        if  request.user.is_teacher:
                            return redirect('student_app:insert_unviercityNumber')
                        
                except Profile.DoesNotExist:
                    # إذا لم يكن هناك ملف شخصي
                    return redirect('authentcat_app:insert_phoneEmail')
            else:
                messages.error(request, "حسابك معطل. يرجى التواصل مع الإدارة")
        else:  # إذا فشلت المصادقة
            # نتحقق أولاً إذا كان المستخدم موجودًا قبل محاولة الحصول عليه
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                if not user.is_active:
                    messages.error(request, "حسابك معطل. يرجى التواصل مع الإدارة")
                else:
                    messages.error(request, "اسم المستخدام او كلمة المرور غير صحيحة")
            else:
                messages.error(request, "اسم المستخدام او كلمة المرور غير صحيحة")
            
        return render(request, 'authentcat_app/sign_in.html')
    else:
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






# ============================ create_teacher function viwe ===============================================
def create_teacher(request):
    
    Subjects = Course.objects.all()
    Permissions = Permission.objects.all()
    
    context ={
        'Subjects':Subjects,
        'Permissions':Permissions,
    }
    
    # basic virable data
    # ======================
    username = None 
    password = None 
    confirm_password = None 
    full_name = None 
    gender = None
    account_status = None
    uploaded_photo = None


    # if request is POST and cklecked buttom submet name=form_creat_buttom
    if request.method == 'POST' and 'form_creat_buttom' in request.POST :

        # Get value from the form
        # ===========================================================================        
        if request.POST.get('form_username', '').strip() : username = request.POST.get('form_username')
        else : messages.info(request, "الرجاء إدخال الاسم")
            
        
        if 'form_password' in request.POST : password = request.POST['form_password']
        else : messages.error(request, "الرجاء إدخال كملة المرور")
        
        if 'form_confirm_password' in request.POST : confirm_password = request.POST['form_confirm_password']
        else : messages.error(request, "الرجاء إدخال تاكيد كملة المرور")
        
        if 'form_fullname' in request.POST :
            messages.info(request, "form_fullname")
            full_name = request.POST['form_fullname']
        else : messages.error(request, "الرجاء إدخال الاسم")
        
        # if 'gender' in request.POST : gender = request.POST['gender']
        # else : messages.error(request, "الرجاء  تحديد النوع")
        
        # if 'account_status' in request.POST : account_status = request.POST['genaccount_statusder']
        # else : messages.error(request, "الرجاء تحديد حالة الحساب")
        
        # if 'photo-upload' in request.POST : account_status = request.POST['photo-upload']
        # else : messages.error(request, "الرجاء إختيار الصورة")

        # # معالجة اصورة
        # # ===============================
        # if 'photo-upload' in request.FILES:
        #     uploaded_photo = request.FILES['photo-upload']
        #     if uploaded_photo.size > 5*1024*1024:
        #         messages.error(request, 'حجم الصورة يجب أن يكون أقل من 5MB')
        #     fs = FileSystemStorage()
        #     photo = fs.save(uploaded_photo.name, uploaded_photo)
        # else :
        #     messages.error(request, "الرجاء إختيار الصورة")
    else :
        pass    
    
    
    # # ========= فحص قيم كل الحقول ===================================================================================
    # if username and password and confirm_password and full_name and gender and account_status and uploaded_photo :
    #     pass
    # else :
    #     messages.error(request , "افحص كل الحقول")
        
        

        
        # # التحقق من تطابق كلمة المرور
        # if password != confirm_password:
        #     messages.error(request, 'كلمة المرور غير متطابقة')
        
        # # التحقق من طول كلمة المرور
        # if len(password) < 4:
        #     messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        
        # # التحقق من وجود اسم المستخدم
        # if User.objects.filter(username=username).exists():
        #     messages.error(request, 'اسم المستخدم موجود مسبقاً')


        
        # # معالجة صورة المعلم
        # if 'photo-upload' in request.FILES:
        #     uploaded_photo = request.FILES['photo-upload']
        #     if uploaded_photo.size > 5*1024*1024:
        #         messages.error(request, 'حجم الصورة يجب أن يكون أقل من 5MB')
        #     fs = FileSystemStorage()
        #     photo = fs.save(uploaded_photo.name, uploaded_photo)
        
        # # إنشاء حساب المستخدم
        # user = User.objects.create(
        #     username=username,
        #     password=make_password(password),
        #     full_name=full_name,
        #     gender=gender,
        #     user_type=1, #مستخدام اساسي
        #     is_active=account_status,
        #     photo=photo  
        # )


        # # إنشاء حساب المستخدم اساسي من نوع معلم 
        # user_basic_user = BasicUser.objects.create(
        #     user=user, 
        #     basic_user_type = 1, #معلم 
        # )

        # # إنشاء حساب المستخدم اساسي من نوع معلم 
        # user_teacher = Teacher.objects.create(
        #     basic_user=user_basic_user, 
        # )
                
        # messages.success(request, 'تم إنشاء المعلم بنجاح')
        # return redirect('authentcat_app:sign_in')
    
    return render(request, 'authentcat_app/create_teacher.html',context)




# ============================ create_controll function viwe ===============================================
def create_controll(request):
    
    if request.method == 'POST':
        # استقبال البيانات من النموذج
        username = request.POST.get('form_username')
        password = request.POST.get('form_password')
        confirm_password = request.POST.get('form_confirm_password')
        full_name = request.POST.get('form_fullname')
        gender = request.POST.get('gender')
        account_status = request.POST.get('account_status') == 'on'

        
        # التحقق من صحة البيانات الأساسية
        if not username or not password or not confirm_password or not full_name:
            messages.error(request, 'جميع الحقول الإجبارية مطلوبة')
        
        # التحقق من تطابق كلمة المرور
        if password != confirm_password:
            messages.error(request, 'كلمة المرور غير متطابقة')
        
        # التحقق من طول كلمة المرور
        if len(password) < 4:
            messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        
        # التحقق من وجود اسم المستخدم
        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود مسبقاً')


        
        # معالجة الصورة
        photo = None
        if 'photo-upload' in request.FILES:
            uploaded_photo = request.FILES['photo-upload']
            if uploaded_photo.size > 5*1024*1024:
                messages.error(request, 'حجم الصورة يجب أن يكون أقل من 5MB')
            fs = FileSystemStorage()
            photo = fs.save(uploaded_photo.name, uploaded_photo)
        
        # إنشاء حساب المستخدم
        user = User.objects.create(
            username=username,
            password=make_password(password),
            full_name=full_name,
            gender=gender,
            user_type=1, #مستخدام اساسي
            is_active=account_status,
            photo=photo  
        )


        # إنشاء حساب المستخدم اساسي من نوع كنترول 
        user_basic_user = BasicUser.objects.create(
            user=user, 
            basic_user_type = 2, #عضو لجنة الكنترول 
        )

        # إنشاء حساب المستخدم اساسي من نوع معلم 
        user_controll = ControlCommitteeMember.objects.create(
            basic_user=user_basic_user, 
        )
                
        messages.success(request, 'تم إنشاء الكنترول بنجاح')
        return redirect('authentcat_app:sign_in')
    
    return render(request, 'authentcat_app/create_controll.html')








# ============================ create_admin function viwe ===============================================
def create_admin(request):
    
    if request.method == 'POST':
        # استقبال البيانات من النموذج
        username = request.POST.get('form_username')
        password = request.POST.get('form_password')
        confirm_password = request.POST.get('form_confirm_password')
        full_name = request.POST.get('form_fullname')
        gender = request.POST.get('gender')
        account_status = request.POST.get('account_status') == 'on'

        
        # التحقق من صحة البيانات الأساسية
        if not username or not password or not confirm_password or not full_name:
            messages.error(request, 'جميع الحقول الإجبارية مطلوبة')
        
        # التحقق من تطابق كلمة المرور
        if password != confirm_password:
            messages.error(request, 'كلمة المرور غير متطابقة')
        
        # التحقق من طول كلمة المرور
        if len(password) < 4:
            messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        
        # التحقق من وجود اسم المستخدم
        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود مسبقاً')


        
        # معالجة الصورة
        photo = None
        if 'photo-upload' in request.FILES:
            uploaded_photo = request.FILES['photo-upload']
            if uploaded_photo.size > 5*1024*1024:
                messages.error(request, 'حجم الصورة يجب أن يكون أقل من 5MB')
            fs = FileSystemStorage()
            photo = fs.save(uploaded_photo.name, uploaded_photo)
        
        # إنشاء حساب المستخدم
        user = User.objects.create(
            username=username,
            password=make_password(password),
            full_name=full_name,
            gender=gender,
            user_type=1, #مستخدام اساسي
            is_active=account_status,
            photo=photo  
        )


        # إنشاء حساب المستخدم اساسي من نوع مدير 
        user_basic_user = BasicUser.objects.create(
            user=user, 
            basic_user_type = 3, # المدير 
        )

        # إنشاء حساب المستخدم اساسي من نوع مدير 
        user_admin = Manager.objects.create(
            basic_user=user_basic_user, 
        )
                
        messages.success(request, 'تم إنشاء المدير بنجاح')
        return redirect('authentcat_app:sign_in')
    
    return render(request, 'authentcat_app/create_admin.html')





# ============================ create_student function viwe ===============================================
def create_student(request):
    # جلب البيانات للقوائم المنسدلة
    majors = Major.objects.all()
    batches = Batch.objects.all()
    semesters = Semester.objects.all()
    
    if request.method == 'POST':
        # استقبال البيانات من النموذج
        username = request.POST.get('form_username')
        password = request.POST.get('form_password')
        confirm_password = request.POST.get('form_confirm_password')
        full_name = request.POST.get('form_fullname')
        gender = request.POST.get('gender')
        account_status = request.POST.get('account_status') == 'on'
        university_id = request.POST.get('university_id')
        major_id = request.POST.get('major')
        batch_id = request.POST.get('batch')
        semester_id = request.POST.get('semester')
        registration_type = request.POST.get('registration_type')
        
        # التحقق من صحة البيانات الأساسية
        if not username or not password or not confirm_password or not full_name:
            messages.error(request, 'جميع الحقول الإجبارية مطلوبة')
        
        # التحقق من تطابق كلمة المرور
        if password != confirm_password:
            messages.error(request, 'كلمة المرور غير متطابقة')
        
        # التحقق من طول كلمة المرور
        if len(password) < 4:
            messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        
        # التحقق من وجود اسم المستخدم
        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود مسبقاً')

        
        # التحقق من البيانات الأكاديمية
        if not university_id or not major_id or not batch_id or not semester_id:
            messages.error(request, 'جميع الحقول الأكاديمية مطلوبة')

        
        # معالجة صورة الطالب
        photo = None
        if 'photo-upload' in request.FILES:
            uploaded_photo = request.FILES['photo-upload']
            if uploaded_photo.size > 5*1024*1024:
                messages.error(request, 'حجم الصورة يجب أن يكون أقل من 5MB')
            fs = FileSystemStorage()
            photo = fs.save(uploaded_photo.name, uploaded_photo)
        
        # إنشاء حساب المستخدم
        user = User.objects.create(
            username=username,
            password=make_password(password),
            full_name=full_name,
            gender=gender,
            user_type=User.UserTypes.STUDENT,
            is_active=account_status,
            photo=photo  # إذا كنت تريد حفظ الصورة في User وليس Student
        )

        # إنشاء سجل الطالب (بدون حقول User)
        student = Student.objects.create(
            user=user,  # فقط ربط بالـ User
            university_id=university_id,
            registration_type=registration_type,
            Batch_id=batch_id,  # لاحظ استخدام _id للعلاقات
            Major_id=major_id,
            Semester_id=semester_id
        )
                
        messages.success(request, 'تم إنشاء الطالب بنجاح')
        return redirect('authentcat_app:sign_in')
    
    return render(request, 'authentcat_app/create_student.html', {
        'majors': majors,
        'batches': batches,
        'semesters': semesters,
    })







# def create_student(request):
#     # basic virable data
#     username = None 
#     password = None 
#     confirm_password = None 
#     fullname = None 
#     image = None
#     # Personal virable data
#     email = None
#     phone = None
#     gender = None
#     account_state = None
#     # Personal varible data
#     univercity_id = None
#     Major_id = None
#     Batch_id = None
#     Semester_id = None
    
    
#     # Get value from the form
#     if 'form_username' in request.POST : username = request.POST['form_username']
#     else : messages.error(request, "الرجاء إدخال اسم المستخدام")
    
#     if 'form_password' in request.POST : password = request.POST['form_password']
#     else : messages.error(request, "الرجاء إدخال كملة المرور")
    
#     if 'form_fullname' in request.POST : fullname = request.POST['form_fullname']
#     else : messages.error(request, "الرجاء إدخال الاسم ")

#     if 'form_confirm_password' in request.POST : confirm_password = request.POST['form_confirm_password']
#     else : messages.error(request, "الرجاء تاكيد كلمة المرور")

#     if 'form_email' in request.POST : email = request.POST['form_email']
#     else : messages.error(request, "الرجاء إدخال كملة المرور")

#     if 'form_phone' in request.POST : phone = request.POST['form_phone']
#     else : messages.error(request, "الرجاء إدخال كملة المرور")

    
    
    
#     # جلب البيانات للقوائم المنسدلة
#     majors = Major.objects.all()
#     batches = Batch.objects.all()
#     semesters = Semester.objects.all()
#     level = Level.objects.all()
    
#     context = {
#         'majors': majors,
#         'batches': batches,
#         'semesters': semesters,
#         'level': level,
        
#         'form': CreateUserForm(),
#     }
#     if request.method == 'POST' and 'create_student_buttom' in request.post :
#         form = CreateUserForm(request.POST)
#         if form.is_valid():  # التصحيح: يجب استدعاء الدالة is_valid()
#             user = form.save(commit=False)  # حفظ المؤقت بدون حفظ في DB
            
#             # إذا كان الفورم لا يقوم بالتشفير تلقائياً:
#             if hasattr(user, 'set_password'):
#                 user.set_password(form.cleaned_data['password'])  # تشفير كلمة المرور
            
#             user.save()  # الحفظ النهائي في قاعدة البيانات
#             messages.success(request, 'تم إنشاء المستخدم بنجاح!')
#             return redirect('student_app:insert_unviercityNumber')  # توجيه إلى صفحة قائمة المستخدمين
#         else:
#             messages.error(request, 'حدث خطأ في البيانات المدخلة')
#     else:
#         form = CreateUserForm()
    
#     return render(request, 'authentcat_app/create_student.html',context)




