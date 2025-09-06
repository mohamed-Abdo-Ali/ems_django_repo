from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthentcatAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authentcat_app"
    verbose_name = _("الحسابات") 

    
    def ready(self):
        # تأكد من تحميل الإشارات عند بدء التطبيق
        import authentcat_app.signals
