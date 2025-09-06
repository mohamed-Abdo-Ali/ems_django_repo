from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from getpass import getpass
import re
from authentcat_app.models import Manager

COMMON_PASSWORDS = {'password', '123456', '123456789', 'admin', 'admin123', 'qwerty', '111111', '123123'}

def password_strength(password):
    length = len(password)
    score = 0
    if re.search(r'[a-z]', password): score += 1
    if re.search(r'[A-Z]', password): score += 1
    if re.search(r'\d', password): score += 1
    if re.search(r'[\W_]', password): score += 1
    if length >= 8: score += 1
    if score <= 2:
        return "Weak"
    elif score == 3 or score == 4:
        return "Medium"
    else:
        return "Strong"

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r'[A-Z]', password):
        return "Password must include at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return "Password must include at least one lowercase letter."
    if not re.search(r'\d', password):
        return "Password must include at least one number."
    if not re.search(r'[\W_]', password):
        return "Password must include at least one special character."
    if password in COMMON_PASSWORDS:
        return "Password is too common."
    return None

class Command(BaseCommand):
    help = 'Create a strong interactive Manager superuser'

    def add_arguments(self, parser):
        parser.add_argument('--username', dest='username', default=None,
            help='Specify the username for the superuser')
        parser.add_argument('--noinput', action='store_false', dest='interactive',
            help='Do not prompt for input')

    def handle(self, *args, **options):
        UserModel = get_user_model()
        username = options.get('username')
        interactive = options.get('interactive')

        if interactive:
            # ================= Username =================
            while True:
                username = input('Username: ').strip()
                if not username:
                    self.stdout.write(self.style.WARNING("Username cannot be empty."))
                    continue
                if UserModel.objects.filter(username=username).exists():
                    self.stdout.write(self.style.WARNING("Username already exists. Please choose another."))
                    continue
                break

            # ================= Full Name =================
            while True:
                full_name = input('Full Name: ').strip()
                if not full_name:
                    self.stdout.write(self.style.WARNING("Full Name cannot be empty."))
                    continue
                if len(full_name) < 3 or len(full_name) > 255:
                    self.stdout.write(self.style.WARNING("Full Name must be between 3 and 255 characters."))
                    continue
                if UserModel.objects.filter(full_name=full_name).exists():
                    self.stdout.write(self.style.WARNING("full_name already exists. Please choose another."))
                    continue
                break

            # ================= Gender =================
            while True:
                gender = input('Gender (1=Male, 0=Female): ').strip()
                if gender in ('0', '1'):
                    break
                else:
                    self.stdout.write(self.style.WARNING("Invalid gender. Enter 1 for Male or 0 for Female."))

            # ================= Password =================
            while True:
                password = getpass('Password: ')
                password2 = getpass('Password (again): ')

                if not password:
                    self.stdout.write(self.style.WARNING("Password cannot be empty."))
                    continue
                if password != password2:
                    self.stdout.write(self.style.WARNING("Passwords do not match."))
                    continue

                msg = validate_password(password)
                if msg:
                    self.stdout.write(self.style.WARNING(msg))
                    continue

                self.stdout.write(self.style.SUCCESS(f"Password strength: {password_strength(password)}"))
                break

        else:
            if not username:
                username = 'admin'
            password = 'Admin@123'
            full_name = 'System Manager'
            gender = 1

        try:
            user = Manager.objects.create(
                username=username,
                full_name=full_name,
                gender=int(gender),
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )
            user.set_password(password)


            # ===================== Handle created_by / updated_by =====================
            if Manager.objects.count() == 1:
                # إذا كان أول مستخدم في النظام
                user.created_by = user
                user.updated_by = user
                user.save()
            else :
                user.save()
            # =========================================================================

            self.stdout.write(self.style.SUCCESS(
                f'Manager superuser "{username}" created successfully'
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f'Error creating superuser: {str(e)}'
            ))
