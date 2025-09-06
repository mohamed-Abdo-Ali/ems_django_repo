from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ConttrollAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "conttroll_app"
    verbose_name = _("الكنترول") 