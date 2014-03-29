from django import forms
import django
from django.forms import ModelForm, TextInput, RadioSelect, Select

from aula.apps.extSMS.models import SMS



class smsForm(ModelForm):

    class Meta:
        model = SMS
        fields = ['alumne', 'dia', 'estat', 'intents']
        widgets = {
            'alumne': Select(attrs={'class': 'disabled form-control', 'readonly': 'readonly'}),
            'estat': RadioSelect(),
            'intents': TextInput(attrs={'class': 'disabled form-control', 'readonly': 'readonly'}),
        }
