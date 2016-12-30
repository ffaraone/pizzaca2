from django.db import models
from django.utils.translation import ugettext as _

from ..ca.models import SubCA

STATUS_CHOICES = (
    ('new', _('New')),
    ('active', _('Active')),
    ('expired', _('Expired')),
    ('revoked', _('Revoked')),
)
COUNTRIES_CHOICES = (
    ('ES', _('Spain')),
    ('IT', _('Italy')),
    ('GB', _('United Kingdom')),
    ('US', _('United States'))
)

FORMAT_CHOICES = (
    ('P12', _('pkcs#12')),
    ('PEM', _('pem encoded'))
)

CRL_REASON_CHOICES = (
    ('unspecified', _('Unspecified')),
    ('keyCompromise', _('Key compromise')),
    ('caCompromise', _('CA compromise')),
    ('affiliationChanged', _('Affiliation changed')),
    ('superseded', _('Superseded')),
    ('cessationOfOperation', _('Cessation of operation')),
    ('certificateHold', _('Certificate hold')),
    ('removeFromCRL', _('Remove from CRL')),
)


class Server(models.Model):

    class Meta:
        permissions = (
            ('can_search_server', 'Can search for certificates'),
            ('can_generate_server', 'Can generate certificates'),
            ('can_revoke_server', 'Can revoke certificates'),
        )

    CN = models.CharField(
        max_length=255,
        verbose_name=_('Common Name'),
        help_text=_('Common Name')
    )

    O = models.CharField(
        max_length=255,
        verbose_name=_('Organization'),
        help_text=_('Organization')
    )

    OU = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Organizational unit'),
        help_text=_('Organizational unit')
    )

    ST = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('State or Province'),
        help_text=_('State or Province')
    )

    L = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Locality name'),
        help_text=_('Locality name')
    )

    C = models.CharField(
        max_length=2,
        choices=COUNTRIES_CHOICES,
        default='ES',
        verbose_name=_('Country'),
        help_text=_('Country')
    )

    E = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Email address'),
        help_text=_('Email address')
    )

    csr = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Certificate format'),
        help_text=_('Certificate format')
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

    revoked_on = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Revoked on'),
        help_text=_('Revoked on')
    )

    crl_reason = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        choices=CRL_REASON_CHOICES,
        verbose_name=_('Reason'),
        help_text=_('Reason')
    )

    issuer = models.ForeignKey(
        SubCA,
        verbose_name=_('Issuer'),
        help_text=_('Issuer')
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name=_('CA Status'),
        help_text=_('Current CA status')
    )


class Identity(models.Model):

    class Meta:
        permissions = (
            ('can_search_identity', 'Can search for certificates'),
            ('can_generate_identity', 'Can generate certificates'),
            ('can_pkcs12_identity', 'Can download pkcs#12 bundle'),
            ('can_revoke_identity', 'Can revoke certificates'),
        )

    CN = models.CharField(
        max_length=255,
        verbose_name=_('Common Name'),
        help_text=_('Common Name')
    )

    T = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Title'),
        help_text=_('Title')
    )

    GN = models.CharField(
        max_length=255,
        verbose_name=_('Given name'),
        help_text=_('Given name')
    )

    SN = models.CharField(
        max_length=255,
        verbose_name=_('Surname'),
        help_text=_('Surname')
    )

    E = models.CharField(
        max_length=255,
        verbose_name=_('Email address'),
        help_text=_('Email address')
    )

    O = models.CharField(
        max_length=255,
        verbose_name=_('Organization'),
        help_text=_('Organization')
    )

    OU = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Organizational unit'),
        help_text=_('Organizational unit')
    )

    ST = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('State or Province'),
        help_text=_('State or Province')
    )

    L = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Locality name'),
        help_text=_('Locality name')
    )

    C = models.CharField(
        max_length=2,
        choices=COUNTRIES_CHOICES,
        default='ES',
        verbose_name=_('Country'),
        help_text=_('Country')
    )

    serialNumber = models.CharField(
        max_length=255,
        verbose_name=_('Serial number'),
        help_text=_('Serial number')
    )

    issuer = models.ForeignKey(
        SubCA,
        verbose_name=_('Issuer'),
        help_text=_('Issuer')
    )

    cert_format = models.CharField(
        max_length=3,
        choices=FORMAT_CHOICES,
        default='P12',
        verbose_name=_('Certificate format'),
        help_text=_('Certificate format')
    )

    csr = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Certificate format'),
        help_text=_('Certificate format')
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

    revoked_on = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Revoked on'),
        help_text=_('Revoked on')
    )

    crl_reason = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        choices=CRL_REASON_CHOICES,
        verbose_name=_('Reason'),
        help_text=_('Reason')
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name=_('CA Status'),
        help_text=_('Current CA status')
    )
