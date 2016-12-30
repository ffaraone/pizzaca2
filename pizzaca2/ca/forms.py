from django.forms import ModelForm

from .models import CA, SubCA


class CAForm(ModelForm):
    class Meta:
        model = CA
        exclude = ['status', 'not_before', 'not_after']


class SubCAForm(ModelForm):
    class Meta:
        model = SubCA
        exclude = ['status', 'operators']
