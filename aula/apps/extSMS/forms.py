from django.forms import ModelForm, Select

from aula.apps.extSMS.models import SMS, TelefonSMS
from aula.utils.widgets import bootStrapButtonSelect

NULL = (
    ('CAP','CAP TELEFON'),
)

class smsForm(ModelForm):
    class Meta:
        model = SMS
        fields = ['telefon', 'estat']
        widgets = {
            'telefon': Select(attrs={'class':'form-control'}),
            'estat': bootStrapButtonSelect(attrs={'class': 'buttons-sms', }), }

    def __init__(self, *args, **kwargs):
        super(smsForm, self).__init__(*args, **kwargs)
        telfs = TelefonSMS.objects.filter(sms=self.instance)
        if len(telfs) != 0:
            self.fields['telefon'].widget.choices = telfs.values_list('id', 'telefon')
        else:
            self.fields['telefon'].widget.choices = NULL

