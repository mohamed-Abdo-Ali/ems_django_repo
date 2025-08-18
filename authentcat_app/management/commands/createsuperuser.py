from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.core.exceptions import ValidationError
from getpass import getpass

class Command(BaseCommand):
    help = 'Create a superuser for custom User model without email'
    
    def add_arguments(self, parser):
        # إزالة جميع الحقول الافتراضية وإضافة الحقول المطلوبة فقط
        parser.add_argument('--username', dest='username', default=None,
            help='Specifies the username for the superuser.')
        parser.add_argument('--noinput', action='store_false', dest='interactive',
            help='Tells Django to NOT prompt the user for input of any kind.')
    
    def handle(self, *args, **options):
        username = options.get('username')
        interactive = options.get('interactive')
        
        if interactive:
            username = input('Username: ')
            password = getpass('Password: ')
            password2 = getpass('Password (again): ')
            
            if password != password2:
                raise ValidationError("Passwords don't match")
            
            full_name = input('Full Name (optional) [Admin]: ') or 'Admin'
            gender = input('Gender (1 for Male, 0 for Female) [1]: ') or '1'
            user_type = input('User Type (1 for BASIC, 2 for STUDENT) [1]: ') or '1'
        else:
            # في حالة --noinput
            password = None
            full_name = 'Admin'
            gender = 1
            user_type = 1
        
        # إنشاء المستخدم مباشرة بدون استخدام create_superuser
        try:
            user = self.UserModel.objects.create(
                username=username,
                full_name=full_name,
                gender=int(gender),
                user_type=int(user_type),
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            if password:
                user.set_password(password)
            user.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'Superuser "{username}" created successfully'
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f'Error creating superuser: {str(e)}'
            ))