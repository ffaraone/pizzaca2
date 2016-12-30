from django.apps import AppConfig


class PubSiteConfig(AppConfig):
    name = 'pizzaca2.pubsite'
    verbose_name = "Public site"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass
