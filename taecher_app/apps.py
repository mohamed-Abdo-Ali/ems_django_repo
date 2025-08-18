from django.apps import AppConfig


class TaecherAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "taecher_app"
        
    def ready(self):
        # تأكد من استيراد الإشارات عند بدء التطبيق
        import taecher_app.signals  # noqa