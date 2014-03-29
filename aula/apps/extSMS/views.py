# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.forms.models import modelform_factory, modelformset_factory
from models import SMS

@login_required
def llistaSMS(request):
    #TODO:
    #Fer que no surti el numero
    #Treballar amb multiples formularis

    SmsFormet = modelformset_factory(SMS)
    formset = SmsFormet(queryset=SMS.objects.filter(estat='res', enviat=False))

    if request.method == 'POST':
        pass


        #if form.is_valid():
        #    if form.cleaned_data['envia']:
        #        try:
        #            extSMS.objects.get(incidencia=form.cleaned_data['incidencia']).delete()
        #        except extSMS.DoesNotExist:
        #            pass



    return render(request, 'mostraSMS.html', {'formset': formset})


