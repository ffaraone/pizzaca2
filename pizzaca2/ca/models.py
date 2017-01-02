from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext as _
from ..users.models import User

STATUS_CHOICES = (
    ('new', _('New')),
    ('active', _('Active')),
    ('expired', _('Expired')),
)
COUNTRIES_CHOICES = (
    ('ES', _('Spain')),
    ('IT', _('Italy')),
    ('GB', _('United Kingdom')),
    ('US', _('United States'))
)


class CA(models.Model):

    CN = models.CharField(
        max_length=255,
        verbose_name=_('Common Name'),
        help_text=_('CA Common Name')
    )

    O = models.CharField(
        max_length=255,
        verbose_name=_('Organization'),
        help_text=_('Organization info')
    )

    OU = models.CharField(
        max_length=255,
        verbose_name=_('Organizational Unit'),
        help_text=_('Organizational unit')
    )

    C = models.CharField(
        max_length=2,
        choices=COUNTRIES_CHOICES,
        default='ES',
        verbose_name=_('Country'),
        help_text=_('Country')
    )

    not_before = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Not before'),
        help_text=_('Not before')
    )

    not_after = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Not after'),
        help_text=_('Not after')
    )

    last_modified = models.DateTimeField(
        blank=True,
        null=True,
        auto_now=True,
        verbose_name=_('Last modified'),
        help_text=_('Last modified')
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name=_('CA Status'),
        help_text=_('Current CA status')
    )

    def __str__(self):
        return 'CN={CN}, O={O}, OU={OU}, C={C}'.format(
            CN=self.CN,
            O=self.O,
            OU=self.OU,
            C=self.C)


class SubCA(models.Model):

    SUBCA_KIND_CHOICES = (
        ('component', _('Component')),
        ('identity', _('Identity')),
    )

    CN = models.CharField(
        max_length=255,
        verbose_name=_('Common Name'),
        help_text=_('CA Common Name')
    )

    OU = models.CharField(
        max_length=255,
        verbose_name=_('Organizational Unit'),
        help_text=_('Organizational unit')
    )

    kind = models.CharField(
        max_length=10,
        choices=SUBCA_KIND_CHOICES,
        default='identity',
        verbose_name=_('SubCA Kind'),
        help_text=_('SubCA Kind')
    )

    not_before = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Not before'),
        help_text=_('Not before')
    )

    not_after = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Not after'),
        help_text=_('Not after')
    )

    last_modified = models.DateTimeField(
        blank=True,
        null=True,
        auto_now=True,
        verbose_name=_('Last modified'),
        help_text=_('Last modified')
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name=_('SubCA Status'),
        help_text=_('Current SubCA status')
    )

    ca = models.ForeignKey(
        CA,
        related_name='sub_cas'
    )

    operators = models.ManyToManyField(User)

    def __str__(self):
        return self.CN
