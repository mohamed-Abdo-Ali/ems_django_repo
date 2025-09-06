# admin_app/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AdminAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_app'
    verbose_name = _("الإدارة") 

    def ready(self):
        # تأكد من تحميل الإشارات عند بدء التطبيق
        import admin_app.signals