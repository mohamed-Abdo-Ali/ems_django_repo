# conttroll_app/services/buffer_users.py
import os, csv, secrets, string
from django.apps import apps
from django.conf import settings
from django.utils import timezone

def _random_username(length=8):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def _random_password(length=16):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    return "".join(secrets.choice(alphabet) for _ in range(length))

def create_buffer_users_for_students(student_ids, subdir="buffer_exports"):
    # جلب الموديلات عبر apps لتجنب الاستيراد الحلقي
    StudentReport = apps.get_model('conttroll_app', 'student_report_from_uivercity')
    BufferStudent = apps.get_model('authentcat_app', 'buffer_Student')

    # جهّز مسار الحفظ
    media_root = getattr(settings, "MEDIA_ROOT", None) or str(settings.BASE_DIR)
    export_dir = os.path.join(media_root, subdir)
    os.makedirs(export_dir, exist_ok=True)

    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"buffer_users_{ts}.csv"
    file_path = os.path.join(export_dir, filename)

    created_count = 0
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["student_id", "name", "univercity_number", "username", "password"])

        for sid in student_ids:
            student = StudentReport.objects.filter(pk=sid).first()
            if not student:
                continue

            # توليد اسم مستخدم فريد
            tries = 0
            username = _random_username()
            while BufferStudent.objects.filter(username=username).exists() and tries < 5:
                username = _random_username()
                tries += 1
            if BufferStudent.objects.filter(username=username).exists():
                username = f"{username}{secrets.randbelow(1000)}"

            password = _random_password()

            BufferStudent.objects.create(username=username, password=password)
            writer.writerow([
                sid,
                getattr(student, "name", ""),
                getattr(student, "univercity_number", ""),
                username,
                password
            ])
            created_count += 1

    # تحضير رابط عام للتحميل إذا MEDIA_URL مضبوط
    public_url = None
    media_url = getattr(settings, "MEDIA_URL", None)
    if media_url and media_root and file_path.startswith(media_root):
        rel_path = os.path.relpath(file_path, media_root).replace("\\", "/")
        public_url = media_url.rstrip("/") + "/" + rel_path

    return file_path, public_url, created_count