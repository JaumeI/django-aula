from django.forms import ModelForm, Select

from aula.apps.extSMS.models import SMS, TelefonSMS
from aula.utils.widgets import bootStrapButtonSelect



class smsForm(ModelForm):

    #
    # Falta fer que agafi nomes els telefons que pertanyen a aquest SMS
    #
    #
    class Meta:
        model = SMS
        fields = ['telefon', 'estat']
        widgets = {
            'telefon': Select(choices=TelefonSMS.objects.all().values_list('id', 'telefon'), attrs={'class':'form-control',}),
            'estat': bootStrapButtonSelect( attrs={'class': 'buttons-sms',}),}
