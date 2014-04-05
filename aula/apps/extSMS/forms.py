from django import forms
import django
from django.forms import ModelForm, TextInput, RadioSelect, Select

from aula.apps.extSMS.models import SMS



class smsForm(ModelForm):
    class Meta:
        model = SMS
        fields = ['estat']
        widgets = {
            'estat': RadioSelect(),
        }
