from django.apps import AppConfig


class AuthentcatAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authentcat_app"

    def ready(self):
        # تأكد من تحميل الإشارات عند بدء التطبيق
        import authentcat_app.signals
