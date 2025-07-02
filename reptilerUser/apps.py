from django.apps import AppConfig # type: ignore


class ReptilerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reptilerUser'
    
    def ready(self):
        import reptilerUser.signals
