# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import render_to_response
from django.forms.models import modelformset_factory
from django.template import RequestContext
from django.db.models import Q
import subprocess
from datetime import date
import re
from aula.apps.alumnes.models import Alumne, Grup
from aula.apps.usuaris.models import User2Professor
from aula.utils.tools import getImpersonateUser
from models import SMS, TelefonTutors
from forms import smsForm, TelfForm
from aula.utils.decorators import group_required


@login_required
@group_required(['consergeria'])
def llistaSMS(request):

    credentials = getImpersonateUser(request)
    (user, l4 ) = credentials


    #TODO:
    # HIG:: Controlar el CAP TELEFON a l'hora d'enviar-los
    # LOW:: Mostrar els intents centrats verticalment
    # LOW:: Reemplasar el mes als SMS per Gener, Febrer...
    # MID:: Afegir boto esborrar anulats



    SmsFormset = modelformset_factory(SMS, form=smsForm, extra = 0)

    if request.method == 'POST':
        formset = SmsFormset(request.POST)
        for form in formset.forms:
            if form.is_valid():
                form.save()
        subprocess.Popen(["python", "aula/apps/extSMS/enviar.py"])
    formset = SmsFormset(queryset=SMS.objects.filter(enviat=False).order_by('-estat', '-dia', 'alumne__grup__curs', 'alumne__grup__nom_grup', 'alumne'))

    return render_to_response('mostraSMS.html', {'formset': formset, 'head': 'Envia SMS'}, context_instance=RequestContext(request))



def enviaSMS(request):
    username = 'jaumei@gmail.com'
    hash = 'antonio'
    numbers = ('34691250084')
    sender = 'ATAPIS'
    message = 'El seu fill ha faltat el dia 14 de abril'
    test_flag = 0
    values = {'test'    : test_flag,
          'uname'   : username,
          'hash'    : hash,
          'message' : message,
          'from'    : sender,
          'selectednums' : numbers }

    url = 'http://www.txtlocal.com/sendsmspost.php'

    # postdata = urllib.urlencode(values)
    # req = urllib2.Request(url, postdata)

    print 'Attempt to send SMS ...'
    # try:
    #     response = urllib2.urlopen(req)
    #     response_url = response.geturl()
    #     if response_url==url:
    #         print 'SMS sent!'
    # except urllib2.URLError, e:
    #     print 'Send failed!'
    #     print e.reason
    print hash
    return llistaSMS(request)





@login_required
@group_required(['consergeria'])
def triaGrupsTelefons(request):
    grups = Grup.objects.all().order_by("descripcio_grup")
    return render_to_response('mostraGrups.html', {"grups" : grups}, context_instance=RequestContext(request))


# DAVID -- TODO -- 2.0 -- Funcio per la nova pantalla
# Agafar tots els alumnes i fer bootstrap-radios amb els seus telefons...
# @login_required
# @group_required(['consergeria'])
# def generaTelefons(request, grup=""):
#
#     TelefonFormset = modelformset_factory(TelefonTutors, form=TelfForm, extra = 0)
#
#     alumnes = Alumne.objects.filter(grup=grup, data_baixa__isnull = True ).order_by('grup__curs', 'grup__nom_grup', 'nom')
#     if request.method == 'POST':
#         print request.POST
#         formset = TelefonFormset(request.POST, queryset=alumnes)
#         for form in formset:
#             if form.is_valid():
#                 form.save()
#                 #print form.fields[""].
#             else:
#                 print form.errors
#
#
#     grup_actual = Grup.objects.get(id=grup)
#     formset = TelefonFormset(queryset=alumnes)
#
#     return render_to_response('generaTelefons.html', {'formset': formset, 'grup':grup_actual, 'head': 'Genera Telefons'}, context_instance=RequestContext(request))
#################################

@login_required
@group_required(['consergeria'])
def generaTelefons(request, grup=""):

    credentials = getImpersonateUser(request)
    (user, _ ) = credentials

    professor = User2Professor( user )
    grup_actual = Grup.objects.get(id=grup)
    head = u"Genera Telefons"
    formset = []

    tots_ok = request.method == 'POST'
    missatge = ""
    #un formulari per a cada alumne.
    for alumne in Alumne.objects.filter(grup = grup):

        infoform_added = False

        if request.method == 'POST':
            form = TelfForm(request.POST, prefix=str(alumne.pk), alumne=alumne)
            if form.is_valid():
                #esborro els que hi havia i poso els nous:
                alumne = Alumne.objects.get(pk=form.cleaned_data['idAlumne'])
                #alumne.telefontutors_set.delete() <-- Aixo no va, no sabem arreglar-ho, ho fem a la linia de sota mes rudimentari
                tt_temporals = TelefonTutors.objects.filter(alumne=alumne)
                for temp in tt_temporals: temp.delete()
                for telf in form.cleaned_data['telefons']:
                    #r, is_new = TelefonTutors.objects.create(alumne=alumne, telefon=telf) <-- Tampoc ho sabem arreglar, ho fem OldSchool
                    tt = TelefonTutors()
                    tt.alumne = alumne
                    tt.telefon = telf
                    tt.save()
                # r.resposta = form.cleaned_data[form.q_valida]
                # r.save()
            else:
                print form.errors
                tots_ok = False
        else:
            form = TelfForm(prefix=str(alumne.pk), alumne=alumne)
            form.infoForm = alumne
            formset.append(form)
        #
        # if not infoform_added:
        #     infoform_added = True
        #     form.infoForm = alumne
        #     form.formSetDelimited = True
        #     formset.append(form)

    if tots_ok:
        missatge = "MOSTRAR AVIS DE TOT OK"

    return render_to_response('generaTelefons.html',{'formset': formset,'head': head,'grup':grup_actual, 'missatge': missatge,'formSetDelimited':True},context_instance=RequestContext(request))