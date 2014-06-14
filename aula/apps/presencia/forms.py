# This Python file uses the following encoding: utf-8
from aula.utils.widgets import DateTextImput
from django import forms as forms
from django.forms import ModelForm, RadioSelect
from django.forms.widgets import DateInput, TextInput
from aula.apps.horaris.models import FranjaHoraria
from aula.apps.presencia.models import ControlAssistencia  , EstatControlAssistencia
from aula.apps.usuaris.models import Professor
from django.utils.datetime_safe import datetime
from aula.apps.alumnes.models import Nivell, Grup
from aula.utils.widgets import bootStrapButtonSelect


class ControlAssistenciaForm(ModelForm):
    estat = forms.ModelChoiceField(
                        #Exluim el justificat per a que només ho puguin fer conserge i direcció
                        queryset= EstatControlAssistencia.objects.all().exclude(id=4),
                        empty_label=None,
                        widget = bootStrapButtonSelect( attrs={'class':'presenciaEstat'} ),
                    )
    class Meta:
        model = ControlAssistencia
        fields = ('estat', )

#----------------------------------------------------------------

class afegeixGuardiaForm(forms.Form):
    professor = forms.ModelChoiceField( 
                        queryset= Professor.objects.all(),
                        required= True,
                        help_text=u'Tria a quin professor fas la guardia.',   
                    )
    franges = forms.ModelMultipleChoiceField( 
                        queryset= FranjaHoraria.objects.all(),
                        required= True,
                        help_text=u'Tria en quines franges horàries fas guardia.',
             )


#-------------------------------------------------------------------------------------------------------------
class regeneraImpartirForm(forms.Form):
    
    data_inici = forms.DateField(label=u'Data regeneració', 
                                       initial=datetime.today(),
                                       required = True, 
                                       help_text=u'Data en que entra en vigor l\'horari actual',  
                                       widget = DateTextImput() )
    
    franja_inici = forms.ModelChoiceField(queryset= FranjaHoraria.objects.all(), 
                                          required = True)
        
    confirma = forms.BooleanField( label=u'Confirma regenerar horaris',required = True,
                                   help_text=u'És un procés costos, confirma que el vols fer',  )
    
    def clean_data_regeneracio(self):
        data = self.cleaned_data['data_regeneracio']
        if data <  datetime.today():
            raise forms.ValidationError(u'Només es pot regenerar amb dates iguals o posteriors a avui.')

        # Always return the cleaned data, whether you have changed it or
        # not.
        return data

    
    def clean_confirma(self):
        data = self.cleaned_data['confirma']
        if not data:
            raise forms.ValidationError(u'Confirma la regeneració d\'horari.')

        return data
    

#---------------------------------------------------------------------------------------------------------------

#from alumnes.models import Alumne
class marcarComHoraSenseAlumnesForm(forms.Form):

    marcar_com_hora_sense_alumnes = forms.BooleanField(
                                                          required = False,
           help_text=u'''Marca aquesta opció si a aquesta hora no tens alumnes. (Per exemple optatives trimestrals)'''  )

    expandir_a_totes_les_meves_hores = forms.BooleanField(
                                                          required = False,
           help_text=u'''Marca aquesta opció per marcar a totes les classes que fas durant la setmana, no
                       només a aquesta classe.'''  )
    
#from alumnes.models import Alumne
class afegeixAlumnesLlistaExpandirForm(forms.Form):

    expandir_a_totes_les_meves_hores = forms.BooleanField(
                                                          required = False,
           help_text=u'''Marca aquesta opció per posar els alumnes a totes les classes que fas durant la setmana, no
                       només a aquesta classe. (Per exemple optatives)'''  )

    matmulla = forms.BooleanField(
                            label = u'''Moure l'alumne''',
                            help_text=u'''Marca aquesta opció treure l'alumne d'altres classes d'altres professors d'aquesta mateixa hora''',  
                            required = False,
                            initial = False
                            )

    
#from alumnes.models import Alumne
class afegeixTreuAlumnesLlistaForm(forms.Form):
    alumnes = forms.ModelMultipleChoiceField( queryset= None, 
                                          required = False,
                                          help_text=u'''Pots triar o destriar més d'un alumne prement la tecla CTRL
                                                      mentre fas clic.
                                                      Per triar tots els alumnes selecciona el primer, 
                                                      baixa fins a l'últim i selecciona'l mantenint ara apretada
                                                      la tecla Shift ('Majúscules'),''')
    
    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset', None)
        self.etiqueta = kwargs.pop('etiqueta', None)
        super(afegeixTreuAlumnesLlistaForm,self).__init__(*args,**kwargs)
        self.fields['alumnes'].label = self.etiqueta 
        self.fields['alumnes'].queryset = self.queryset



class calculadoraUnitatsFormativesForm(forms.Form):
    
    grup = forms.ModelChoiceField( queryset = None )
    assignatura = forms.ModelMultipleChoiceField( queryset = None )
    dataInici = forms.DateField(help_text=u'Data on començar a comptar', 
                                       initial= datetime.today(),
                                       required = True,                                          
                                       widget = DateTextImput() )
    hores = forms.IntegerField( help_text=u'Hores de la UF')    

    def __init__(self, *args, **kwargs):
        self.assignatures = kwargs.pop('assignatures', None)
        self.grups = kwargs.pop('grups', None)
        super(calculadoraUnitatsFormativesForm,self).__init__(*args,**kwargs)
        self.fields['assignatura'].queryset = self.assignatures 
        self.fields['grup'].queryset = self.grups


class faltesAssistenciaEntreDatesForm(forms.Form):
    
    grup = forms.ModelChoiceField( queryset = None )
    assignatura = forms.ModelMultipleChoiceField( queryset = None )
    dataDesDe = forms.DateField(help_text=u'Data on començar a comptar', 
                                       initial= datetime.today(),
                                       required = True,                                          
                                       widget = DateTextImput() )
    horaDesDe = forms.ModelChoiceField( queryset = FranjaHoraria.objects.all(), initial = [ FranjaHoraria.objects.all()[0] ] )
    dataFinsA = forms.DateField(help_text=u'Data on començar a comptar', 
                                       initial= datetime.today(),
                                       required = True,                                          
                                       widget = DateTextImput() )
    horaFinsA = forms.ModelChoiceField( queryset = FranjaHoraria.objects.all(), initial =[  FranjaHoraria.objects.reverse()[0] ])

    def __init__(self, *args, **kwargs):
        self.assignatures = kwargs.pop('assignatures', None)
        self.grups = kwargs.pop('grups', None)
        super(faltesAssistenciaEntreDatesForm,self).__init__(*args,**kwargs)
        self.fields['assignatura'].queryset = self.assignatures 
        self.fields['grup'].queryset = self.grups


class alertaAssistenciaForm(forms.Form):
    data_inici = forms.DateField(label=u'Data inici', 
                                       initial=datetime.today(),
                                       required = True, 
                                       help_text=u'Dia inicial pel càlcul',  
                                       widget = DateTextImput() )
    
    data_fi = forms.DateField(label=u'Data fi', 
                                       initial=datetime.today(),
                                       required = True, 
                                       help_text=u'Dia final pel càlcul',  
                                       widget = DateTextImput() )
    
    tpc = forms.IntegerField( label = u'filtre %', 
                              max_value=100, 
                              min_value=1, initial = 25  ,
                              help_text=u'''Filtra alumnes amb % de absència superior a aquest valor.''' ,
                              widget = TextInput(attrs={'class':"slider"} )  )
    
    nivell = forms.ModelChoiceField( 
                        queryset= Nivell.objects.all(), 
                        required = True, 
                        empty_label = None,
                    )    
    ordenacio = forms.ChoiceField(  choices = ( ('a', u'Nom alumne',), ('ca', u'Curs i alumne',),('n',u'Per % Assistència',), ('cn',u'Per Curs i % Assistència',), ), 
                                    required = True, 
                                    label = u'Ordenació', initial = 'a', help_text = u'Tria com vols ordenats els resultats')

    #toExcel = forms.BooleanField( u'Mostrar resultats en Full de Càlcul', help_text = u"Marcant aquesta casella els resultats no es mostren per pantalla, es decarregaran en un full de càlcul.")


#----------------------------------------------------------------------------------------------


class passaLlistaGrupDataForm( forms.Form ):
    grup = forms.ModelChoiceField( queryset = Grup.objects.all()  )
    dia =  forms.DateField(label=u'Dia', 
                                       initial=datetime.today(),
                                       help_text=u'Dia a passar llista.',  
                                       widget = DateTextImput() )

  



