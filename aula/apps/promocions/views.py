# Create your views here.
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms.models import modelformset_factory
from django.shortcuts import render_to_response
from django.template import RequestContext
from aula.apps.alumnes.models import Alumne, Grup
from aula.apps.promocions.forms import promoForm, newAlumne
from aula.utils.decorators import group_required


@login_required
@group_required(['direccio'])
def llistaGrups(request):
    grups = Grup.objects.all().order_by("descripcio_grup")
    return render_to_response('mostraGrups.html', {"grups" : grups}, context_instance=RequestContext(request))

@login_required
@group_required(['direccio'])
def nouAlumne(request):
    #Aqui va el tractament del formulari i tota la polla...

    if request.method == 'POST':
        # Ve per post, he de guardar l'alumne si les dades estan correctes
        pass
    form = newAlumne()
    return render_to_response('mostraFormulari.html', {'form': form}, context_instance=RequestContext(request))

@login_required
@group_required(['direccio'])
def mostraGrup(request, grup=""):

    from datetime import date
    PromoFormset = modelformset_factory(Alumne, form=promoForm, extra = 0)
    if request.method == 'POST':
        curs_vinent = request.POST.get('curs_desti')
        formset = PromoFormset(request.POST)
        for form in formset.forms:
            if form.is_valid():

                decisio = form.cleaned_data['decisio']
                if (decisio == "2"):

                    id =  form.cleaned_data['id'].id
                    alumne = Alumne.objects.get(id=id)
                    alumne.data_baixa = date.today()
                    alumne.estat_sincronitzacio = 'DEL'
                    alumne.motiu_bloqueig = 'Baixa'
                    alumne.save()


                if (decisio == "0"):

                    id = form.cleaned_data['id'].id
                    alumne = Alumne.objects.get(id = id)
                    alumne.grup_id = curs_vinent
                    alumne.save()


        pass

    grups = Grup.objects.all().order_by("descripcio_grup")
    grup_actual = Grup.objects.get(id=grup)
    alumnes = Alumne.objects.filter(grup=grup, data_baixa__isnull = True ).order_by("cognoms")
    if (len(alumnes) == 0):

        msg = "Aquest grup no te alumnes actualment."
        return render_to_response('mostraGrups.html', {"grups" : grups, "msg": msg}, context_instance=RequestContext(request))

    formset = PromoFormset(queryset=alumnes)

    return render_to_response('mostraGrup.html', {"grup_actual" : grup_actual, "formset" : formset, "grups":grups}, context_instance=RequestContext(request))