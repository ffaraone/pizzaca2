from django.apps import AppConfig


class CAConfig(AppConfig):
    name = 'pizzaca2.ca'
    verbose_name = "CA"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass
