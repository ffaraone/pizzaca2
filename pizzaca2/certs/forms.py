from django import forms
from django.db.models import Q

from ..ca.models import SubCA
from .models import Identity, Server


class IdentityForm(forms.ModelForm):
    class Meta:
        model = Identity
        exclude = ['status', 'not_before',
            'not_after', 'revoked_on',
            'cert_format', 'csr', 'crl_reason']

    def __init__(self, user, *args, **kwargs):
        super(IdentityForm, self).__init__(*args, **kwargs)
        user_filter = Q(kind='identity')
        if not user.is_superuser:
            user_filter &= Q(operators=user.id)
        # choices = SubCA.objects.filter(user_filter).values_list('id', 'CN')
        self.fields['issuer'].queryset = SubCA.objects.filter(user_filter)


class ServerForm(forms.Form):

    issuer = forms.ChoiceField()
    csr = forms.CharField(widget=forms.Textarea)

    def __init__(self, user, *args, **kwargs):
        super(ServerForm, self).__init__(*args, **kwargs)
        user_filter = Q(kind='component')
        if not user.is_superuser:
            user_filter &= Q(operators=user.id)
        choices = SubCA.objects.filter(user_filter).values_list('id', 'CN')
        self.fields['issuer'].choices = choices
        self.fields['csr'].help_text = 'openssl req -new -newkey rsa:2048 -nodes -keyout server.key -out server.csr'
