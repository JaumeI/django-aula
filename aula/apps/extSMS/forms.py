from django import forms
import re
from django.forms import ModelForm
from aula.apps.alumnes.models import Alumne

from aula.apps.extSMS.models import SMS, TelefonTutors
from aula.utils.widgets import bootStrapButtonSelect

NULL = (
    ('OFF', 'No hi ha cap telefon'),
)

# DAVID -- TODO -- 2.0 - JA no es demanen telefons
class smsForm(ModelForm):
    class Meta:
        model = SMS
        # fields = ['telefon', 'estat']
        fields = ['estat']
        widgets = {
            #'telefon': Select(attrs={'class':'form-control'}),
            'estat': bootStrapButtonSelect(attrs={'class': 'buttons-sms', }), }

    # def __init__(self, *args, **kwargs):
    #     super(smsForm, self).__init__(*args, **kwargs)
    #     telfs = TelefonSMS.objects.filter(sms=self.instance)
    #     if len(telfs) != 0:
    #         self.fields['telefon'].widget.choices = telfs.values_list('id', 'telefon')
    #     else:
    #         self.fields['telefon'].widget.choices = NULL

# class TelfForm(ModelForm):
#     class Meta:
#         model = TelefonTutors
#         fields = ['telefon']
#         widgets = {
#             #'telefon': bootStrapButtonSelect(attrs={'class': 'buttons-sms',}),
#             #'telefon' : ModelChoiceField,
#         }
#
#     def __init__(self, *args, **kwargs):
#         super(TelfForm, self).__init__(*args, **kwargs)
#         telfs = Alumne.objects.get(id=self.instance.id).telefons
#         telfs = re.findall("\d{9}\d*", telfs)
#         results = {}
#         for telf in telfs:
#             results[telf] = telf
#         if results:
#             self.fields['telefon'] = ChoiceField(choices=results.items())
#             # self.fields['telefon'].widget.choices = results.iteritems()
#             # self.fields['telefon'].choices = results.iteritems()
#         else:
#             self.fields['telefon'] = ChoiceField(choices=NULL)
#             # self.fields['telefon'].widget.choices = NULL
#             # self.fields['telefon'].choices = NULL
class TelfForm(forms.Form):
    idAlumne = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        alumne = kwargs.pop('alumne')
        super(TelfForm, self).__init__(*args, **kwargs)
        telfs = alumne.telefons
        telfs = re.findall("\d{9}\d*", telfs)
        telefons_choice = [(telf, telf) for telf in telfs]
        self.fields["idAlumne"].initial = alumne.id
        self.fields["telefons"] = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple,
                                                         choices=telefons_choice, initial=[t.telefon for t in alumne.telefontutors_set.all()])
