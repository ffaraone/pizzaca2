from django.forms import ModelForm

from .models import CA, SubCA


class CAForm(ModelForm):
    class Meta:
        model = CA
        exclude = ['status', 'not_before', 'not_after']


class SubCAForm(ModelForm):
    class Meta:
        model = SubCA
        exclude = ['status', 'operators', 'not_before', 'not_after']

    def __init__(self, *args, **kwargs):
        super(SubCAForm, self).__init__(*args, **kwargs)
        self.fields['ca'].queryset = CA.objects.filter(status='active')
