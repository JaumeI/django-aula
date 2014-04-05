# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response
from django.forms.models import modelform_factory, modelformset_factory
from django.template import RequestContext, loader
from django.template.context import Context
from aula.utils.tools import getImpersonateUser
from models import SMS
from forms import smsForm
from django.db.models import Q
from aula.utils.decorators import group_required
from aula.utils.context_processors import calcula_menu

@login_required
@group_required(['consergeria'])
def llistaSMS(request):

    credentials = getImpersonateUser(request)
    (user, l4 ) = credentials

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

    return render_to_response('mostraSMS.html', {'formset': formset, 'head': 'Envia SMS'}, context_instance=RequestContext(request))



