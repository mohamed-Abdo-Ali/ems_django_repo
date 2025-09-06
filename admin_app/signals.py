from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

from .models import Course
from authentcat_app.models import Student

# مهم: لا تُخزّن المستخدم في متغير على مستوى الملف
# from django_currentuser.middleware import get_current_user  # ممكن
from django_currentuser.middleware import get_current_authenticated_user as get_current_user

def log_with_current_user(instance, action_flag, change_message):
    user = get_current_user()
    # بعض الحالات (سكريبت/اختبارات) لن يكون هناك مستخدم
    if not user or not getattr(user, "is_authenticated", False):
        return
    LogEntry.objects.log_action(
        user_id=user.pk,
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=str(instance),
        action_flag=action_flag,
        change_message=change_message,
    )
