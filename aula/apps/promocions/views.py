# Create your views here.
from itertools import chain
from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.shortcuts import render_to_response
from django.template import RequestContext
from aula.apps.alumnes.models import Curs, Alumne, Grup
from aula.utils.decorators import group_required


@login_required
@group_required(['direccio'])
def llistaCursos(request):
    cursos = Curs.objects.all().order_by("nom_curs_complert")
    return render_to_response('mostraCursos.html', {"cursos" : cursos}, context_instance=RequestContext(request))


@login_required
@group_required(['direccio'])
def mostraCurs(request, curs=""):
    cursos = Curs.objects.all().order_by("nom_curs_complert")
    curs_def = Curs.objects.get(id=curs)
    grup = Grup.objects.filter(curs_id=curs)
    alumnes = Alumne.objects.filter(grup__in=grup).order_by("cognoms")

    return render_to_response('mostraCurs.html', {"curs" : curs_def, "alumnes":alumnes, "cursos":cursos}, context_instance=RequestContext(request))