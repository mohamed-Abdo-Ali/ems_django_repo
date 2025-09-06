from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TaecherAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "taecher_app"
    verbose_name = _('المعلم')
        
    def ready(self):
        # تأكد من استيراد الإشارات عند بدء التطبيق
        import taecher_app.signals  # noqa