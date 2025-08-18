from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import Profile, User

class CreateUserForm(forms.ModelForm):
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 group-hover:shadow-sm',
            'placeholder': 'أدخل كلمة المرور...',
            'x-model': 'password',
            '@input': 'validatePassword()'
        }),
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$',
                message="كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل وحرف واحد ورقم واحد"
            )
        ],
        error_messages={
            'required': 'كلمة المرور مطلوبة'
        }
    )
    
    class Meta:
        model = User
        fields = ['username', 'password', 'full_name', 'gender', 'photo', 
                'user_type', 'groups', 'user_permissions', 
                'is_active', 'is_staff', 'is_superuser']
       
        error_messages = {
            'username': {
                'required': "اسم المستخدم مطلوب",
                'unique': "اسم المستخدم هذا موجود بالفعل",
                'invalid': "اسم المستخدم يمكن أن يحتوي على أحرف لاتينية وأرقام و @/./+/-/_ فقط"
            },
            'full_name': {
                'required': "الاسم الكامل مطلوب",
                'unique': "هذا الاسم مسجل بالفعل لمستخدم آخر"
            },
            'gender': {
                'required': "النوع مطلوب"
            },
            'user_type': {
                'required': "نوع المستخدم مطلوب"
            },
            'photo': {
                'invalid_image': "الملف المرفوع ليس صورة صالحة"
            }
        }
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 group-hover:shadow-sm',
                'placeholder': 'اسم المستخدم...',
                'x-model': 'username',
                '@input': 'checkUsernameAvailability()'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 group-hover:shadow-sm',
                'placeholder': 'الاسم الكامل...'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 group-hover:shadow-sm'
            }),
            'user_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 group-hover:shadow-sm'
            }),
'photo': forms.ClearableFileInput(attrs={
    'class': 'hidden',  # سيتم إخفاء العنصر الأصلي
    'id': 'photo-upload-input',  # مهم للربط مع العناصر الأخرى
}),
            'groups': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 group-hover:shadow-sm'
            }),
            'user_permissions': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 group-hover:shadow-sm'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'hidden-checkbox',
                'x-model': 'isActive'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'hidden-checkbox',
                'x-model': 'isStaff'
            }),
            'is_superuser': forms.CheckboxInput(attrs={
                'class': 'hidden-checkbox',
                'x-model': 'isSuperuser'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        is_staff = cleaned_data.get('is_staff')
        is_superuser = cleaned_data.get('is_superuser')
        
        if user_type == User.UserTypes.STUDENT and (is_staff or is_superuser):
            raise ValidationError({
                'is_staff': "الطالب لا يمكن أن يكون من الموظفين",
                'is_superuser': "الطالب لا يمكن أن يكون مديرًا عامًا"
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            self.save_m2m()
        return user






# -----------------------------------  profile form  ------------------------------------------------------------------------------------
class ProfileForm(forms.ModelForm):
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 group-hover:shadow-sm',
            'placeholder': '+967XXXXXXXXX',
            'x-model': 'phoneNumber',
            '@input': 'validatePhoneNumber()'
        }),
        validators=[
            RegexValidator(
                regex=r'^\+9677[1378]\d{7}$|^\+967\d{9}$',
                message="رقم الهاتف يجب أن يكون:\n- للموبايل: +9677 ثم (1/3/7/8) ثم 7 أرقام\n- للأرضي: +967 ثم 9 أرقام"
            )
        ],
        error_messages={
            'required': 'رقم الهاتف مطلوب',
            'invalid': 'رقم هاتف يمني غير صحيح'
        }
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 group-hover:shadow-sm',
            'placeholder': 'example@domain.com'
        })
    )
    
    class Meta:
        model = Profile
        fields = ['email', 'phone_number']