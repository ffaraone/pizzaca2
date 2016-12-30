from django.apps import AppConfig


class CertsConfig(AppConfig):
    name = 'pizzaca2.certs'
    verbose_name = "Certificates"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass
