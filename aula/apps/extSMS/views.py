# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.forms.models import modelform_factory, modelformset_factory
from models import SMS
from forms import smsForm
from django.db.models import Q

@login_required
def llistaSMS(request):
    #TODO:
    # Cal fer un cron::
    #   Cada dia a les 00:00 tots els anulats: enviat = True
    #Treballar amb multiples formularis
    SmsFormset = modelformset_factory(SMS, form=smsForm, extra = 0)
    if request.method == 'POST':
        #ACTUALITZA ELS PUTOS FORMS!!!
        print "Entro per POST"
        formset = SmsFormset(request.POST)
        print "Guardo el FORMSET"
        if formset.is_valid():
            formset.save()

    formset = SmsFormset(queryset=SMS.objects.filter(~Q(estat='enviar'), enviat=False))
    return render(request, 'mostraSMS.html', {'formset': formset})


