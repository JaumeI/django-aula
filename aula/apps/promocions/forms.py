from django import forms
from django.db import models
from django.forms import ModelForm
from aula.apps.alumnes.models import Alumne
from aula.utils.widgets import bootStrapButtonSelect

__author__ = 'David'
CHOICES = (
    ('0','MOU'),
    ('1','IGUAL'),
    ('2','MARXA'),

)
class promoForm(ModelForm):
    decisio = forms.ChoiceField(widget=bootStrapButtonSelect(attrs={'class': 'buttons-promos disabled', }),choices=CHOICES,)
    class Meta:
        model = Alumne
        fields  = []

class newAlumne(ModelForm):
    class Meta:
        model = Alumne
        fields = ['grup', 'nom', 'cognoms', 'data_neixement', 'correu_tutors', 'correu_relacio_familia_pare', 'correu_relacio_familia_mare', 'tutors_volen_rebre_correu', 'centre_de_procedencia', 'localitat', 'telefons', 'tutors', 'adreca']
