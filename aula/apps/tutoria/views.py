# This Python file uses the following encoding: utf-8

from aula.utils.widgets import DateTimeTextImput,DateTextImput
#templates
from django.template import RequestContext
from django.http import HttpResponse

#workflow
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect

#auth
from django.contrib.auth.decorators import login_required
from aula.apps.usuaris.models import User2Professor, User2Professional, Accio, LoginUsuari
from aula.utils.decorators import group_required

#forms
from aula.apps.tutoria.forms import  justificaFaltesW1Form, informeSetmanalForm,\
    seguimentTutorialForm, elsMeusAlumnesTutoratsEntreDatesForm

#helpers
from aula.utils import tools
from aula.apps.presencia.models import  ControlAssistencia, EstatControlAssistencia,\
    Impartir
from django.utils.datetime_safe import  date, datetime
from datetime import timedelta
from aula.apps.tutoria.models import Actuacio, Tutor, SeguimentTutorialPreguntes,\
    SeguimentTutorial, SeguimentTutorialRespostes, ResumAnualAlumne,\
    CartaAbsentisme
from aula.apps.alumnes.models import Alumne, Grup
from django.forms.models import modelform_factory, modelformset_factory
from django import forms
from django.db.models import Min, Max, Q

#exceptions
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS,\
    ObjectDoesNotExist
from django.http import Http404
from aula.apps.horaris.models import FranjaHoraria, Horari
from aula.apps.incidencies.models import Incidencia, Expulsio
from aula.utils.tools import llista
from aula.apps.avaluacioQualitativa.forms import alumnesGrupForm
from aula.utils.forms import dataForm, ckbxForm, choiceForm
from aula.apps.avaluacioQualitativa.models import RespostaAvaluacioQualitativa
from django.utils import simplejson
from django.core import serializers
from aula.apps.tutoria.reports import reportCalendariCursEscolarTutor
from aula.apps.tutoria.rpt_elsMeusAlumnesTutorats import elsMeusAlumnesTutoratsRpt
from aula.apps.tutoria.others import calculaResumAnualProcess
from aula.apps.tutoria.rpt_gestioCartes import gestioCartesRpt
from aula.apps.tutoria import report_carta_absentisme
from aula.apps.tutoria.report_carta_absentisme import report_cartaAbsentisme
from aula.apps.tutoria.rpt_totesLesCartes import totesLesCartesRpt
from django.core.urlresolvers import reverse

@login_required
@group_required(['professors','professional'])
def lesMevesActuacions(request):

    credentials = tools.getImpersonateUser(request) 
    (user, _ ) = credentials
    
    professional = User2Professional( user )     
    
    report = []
    for alumne in  Alumne.objects.filter( actuacio__professional = professional ).distinct():
            taula = tools.classebuida()

            taula.titol = tools.classebuida()
            taula.titol.contingut = ''
            taula.titol.enllac = None

            taula.capceleres = []
            
            capcelera = tools.classebuida()
            capcelera.amplade = 200
            capcelera.contingut = u'{0} ({1})'.format(unicode( alumne ) , unicode( alumne.grup ) )
            capcelera.enllac = reverse('tutoria__alumne__detall', args=[ alumne.pk , 'all' ])
            taula.capceleres.append(capcelera)

            capcelera = tools.classebuida()
            capcelera.amplade = 70
            capcelera.contingut = u'Qui?'
            taula.capceleres.append(capcelera)

            capcelera = tools.classebuida()
            capcelera.amplade = 70
            capcelera.contingut = u'Amb qui?'
            taula.capceleres.append(capcelera)
            
            capcelera = tools.classebuida()
            capcelera.amplade = 200
            capcelera.contingut = u'Assumpte'
            taula.capceleres.append(capcelera)
            
            capcelera = tools.classebuida()
            capcelera.amplade = ''
            capcelera.contingut = u'Esborra'
            taula.capceleres.append(capcelera)
            
            taula.fileres = []
            for actuacio in alumne.actuacio_set.filter( professional = professional).order_by('moment_actuacio').reverse():
                
                filera = []
                
                #-moment--------------------------------------------
                camp = tools.classebuida()
                camp.enllac = None
                camp.contingut = unicode(actuacio.moment_actuacio)
                camp.enllac = "/tutoria/editaActuacio/{0}".format( actuacio.pk )
                filera.append(camp)

                #-qui--------------------------------------------
                camp = tools.classebuida()
                camp.enllac = None
                camp.contingut = u'''{0} ({1})'''.format(
                                             unicode( actuacio.professional ),
                                             unicode(actuacio.get_qui_fa_actuacio_display() ) )
                filera.append(camp)

                #-amb qui--------------------------------------------
                camp = tools.classebuida()
                camp.enllac = None
                camp.contingut = unicode(actuacio.get_amb_qui_es_actuacio_display() )
                filera.append(camp)

                #-assumpte--------------------------------------------
                camp = tools.classebuida()
                camp.enllac = None
                camp.contingut = unicode(actuacio.assumpte )
                filera.append(camp)

                #-delete--------------------------------------------
                camp = tools.classebuida()
                camp.enllac = '/tutoria/esborraActuacio/{0}'.format(actuacio.pk )
                camp.contingut = '[ X ]'
                filera.append(camp)


                #--
                taula.fileres.append( filera )
            
            report.append(taula)
        
    return render_to_response(
                'actuacions.html',
                    {'report': report,
                     'head': 'Informació actuacions' ,
                    },
                    context_instance=RequestContext(request))            
        

from aula.apps.alumnes.forms import triaAlumneForm

@login_required
@group_required(['professors','professional'])
def novaActuacio(request):

    credentials = tools.getImpersonateUser(request) 
    (user, l4 ) = credentials
    
    formset = []
    if request.method == 'POST':
        
        actuacio = Actuacio()
        actuacio.professional = User2Professional( user)
        actuacio.credentials = credentials
        formAlumne = triaAlumneForm(request.POST ) #todo: multiple=True (multiples alumnes de cop)  
        widgets = { 'moment_actuacio': DateTimeTextImput()}      
        formActuacioF = modelform_factory(Actuacio, exclude=['alumne','professional'], widgets = widgets)
        formActuacio = formActuacioF(request.POST, instance = actuacio ) 
        if formAlumne.is_valid():
            
            alumne = formAlumne.cleaned_data['alumne']
            #actuacio = formActuacio.save(commit=False)
            actuacio.alumne = alumne
            if formActuacio.is_valid():
                actuacio.save()

                #LOGGING
                Accio.objects.create( 
                        tipus = 'AC',
                        usuari = user,
                        l4 = l4,
                        impersonated_from = request.user if request.user != user else None,
                        text = u"""Enregistrada actuació a l'alumne {0}. """.format( actuacio.alumne )
                    )          
                        
                url = '/tutoria/lesMevesActuacions/'
                return HttpResponseRedirect( url )    

        formset.append( formAlumne )
        formset.append( formActuacio )
        
    else:

        formAlumne = triaAlumneForm( ) #todo: multiple=True (multiples alumnes de cop)       
        widgets = { 'moment_actuacio': DateTimeTextImput()} 
        formActuacio = modelform_factory(Actuacio, exclude=['alumne','professional'],widgets = widgets) 

        formset.append( formAlumne )
        formset.append( formActuacio )
    
    
        
    return render_to_response(
                'formset.html',
                    {'formset': formset,
                     'head': 'Actuació' ,
                    },
                    context_instance=RequestContext(request))


@login_required
@group_required(['professors','professional'])
def editaActuacio(request, pk):
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    
    actuacio = Actuacio.objects.get( pk = pk)
    
    professor = User2Professor(user)
    
    #seg-------------------
    te_permis = (l4 or 
                actuacio.professional.pk == user.pk or  
                professor in actuacio.alumne.tutorsDeLAlumne() or
                user.groups.filter(name__in= [u'direcció', u'psicopedagog'] ).exists() 
                )
    if  not te_permis:
        raise Http404() 
    
    
    actuacio.credentials = credentials

    infoForm = [
          ('Alumne',unicode( actuacio.alumne) ),
          ('Professional', unicode( actuacio.professional ) )      
                ]
    
    formActuacioF = modelform_factory(Actuacio, exclude=['alumne','professional'])
    formActuacioF.base_fields['moment_actuacio'].widget = forms.DateTimeInput(attrs={'class':'DateTimeAnyTime'} )
    formset = []
    if request.method == 'POST':
        
        formActuacio = formActuacioF(request.POST, instance = actuacio ) 
        if formActuacio.is_valid():
            actuacio.save()

            #LOGGING
            Accio.objects.create( 
                    tipus = 'AC',
                    usuari = user,
                    l4 = l4,
                    impersonated_from = request.user if request.user != user else None,
                    text = u"""Editada actuació a l'alumne {0}. """.format( actuacio.alumne )
                )     
                            
            url = '/tutoria/lesMevesActuacions/'
            return HttpResponseRedirect( url )    

        formset.append( formActuacio )
        
    else:

        formActuacio = formActuacioF( instance = actuacio ) 

        formset.append( formActuacio )
        
    return render_to_response(
                'formset.html',
                    {'formset': formset,
                     'infoForm': infoForm,
                     'head': 'Actuació' ,
                    },
                    context_instance=RequestContext(request))

@login_required
@group_required(['professors','professional'])
def esborraActuacio(request, pk):
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    
    actuacio = Actuacio.objects.get( pk = pk )
    
    #seg-------------------
    te_permis = l4 or actuacio.professional.pk == user.pk 
    if  not te_permis:
        raise Http404()
            
    actuacio.credentials = credentials
    url_next = '/tutoria/lesMevesActuacions/'
    try:
        actuacio.delete()
        
        #LOGGING
        Accio.objects.create( 
                tipus = 'AC',
                usuari = user,
                l4 = l4,
                impersonated_from = request.user if request.user != user else None,
                text = u"""Esborrada actuació a l'alumne {0}. """.format( actuacio.alumne )
            )     
                        
    except ValidationError, e:
        import itertools
        resultat = { 'errors': list( itertools.chain( *e.message_dict.values() ) ), 
                    'warnings':  [], 'infos':  [], 'url_next': url_next }
        return render_to_response(
                       'resultat.html', 
                       {'head': u'Error a l\'esborrar actuació.' ,
                        'msgs': resultat },
                       context_instance=RequestContext(request))    
            
    return HttpResponseRedirect( url_next )  

# @login_required
# @group_required(['professors'])
# def justificaFaltes(request, pk, year, month, day):
#     credentials = tools.getImpersonateUser(request)
#     (user, l4) = credentials
#     professor = User2Professor(user)
#
#     formset = []
#     head='Justificar faltes'
#     missatge = ''
#
#     alumne = Alumne.objects.get( pk = int(pk) )
#
#     #---seg-----
#     esAlumneTutorat = professor in alumne.tutorsDeLAlumne()
#     te_permis = l4 or esAlumneTutorat
#     if  not te_permis:
#         raise Http404()
#
#     algunDeBe = False
#
#     dia_impartir = date( year = int(year), month = int(month), day = int(day) )
#
#     ControlAssistenciaFormF = modelformset_factory(ControlAssistencia, fields=( 'estat',), extra = 0 )
#
#     controls = ControlAssistencia.objects.filter(
#                             alumne = alumne,
#                             impartir__dia_impartir = dia_impartir
#                         ).order_by( 'alumne', '-impartir__dia_impartir', 'impartir__horari__hora'  )
#
#     if request.method == 'POST':
#
#         formCA=ControlAssistenciaFormF(request.POST, prefix='ca',queryset  = controls )
#
#         for form in formCA:
#             control_a = form.instance
#             form.fields['estat'].label = u'{0} {1} {2}'.format( control_a.alumne, control_a.impartir.dia_impartir, control_a.impartir.horari.hora )
#             form.instance.credentials = credentials
#             if 'estat' in form._get_changed_data() and form.is_valid():
#                 ca=form.save(commit=False)
#                 ca.credentials = credentials
#                 algunDeBe = True
#                 ca=form.save()
#
#         if algunDeBe:
#             missatge = u'Les faltes han estat justificades.'
#             #LOGGING
#             Accio.objects.create(
#                     tipus = 'JF',
#                     usuari = user,
#                     l4 = l4,
#                     impersonated_from = request.user if request.user != user else None,
#                     text = u"""Justificades faltes de l'alumne {0} del dia {1}. """.format( alumne, dia_impartir )
#                 )
#         else:
#             missatge = u'''No s'ha justificat cap falta.'''
#
#     else:
#         controls = ControlAssistencia.objects.filter(
#                             alumne = alumne,
#                             impartir__dia_impartir = dia_impartir
#                         ).order_by( 'alumne', '-impartir__dia_impartir', 'impartir__horari__hora'  )
#
#         formCA=ControlAssistenciaFormF( prefix='ca',queryset  = controls )
#
#         for form in formCA:
#             control_a = form.instance
#             form.fields['estat'].label = u'{0} {1} {2}'.format( control_a.alumne, control_a.impartir.dia_impartir, control_a.impartir.horari.hora )
#
#
#
#     return render_to_response(
#                   "formset.html",
#                   {"formset": formCA,
#                    "head": head,
#                    "missatge": missatge,
#                    },
#                   context_instance=RequestContext(request))

@login_required
@group_required(['professors'])
def informeSetmanalMKTable(request, pk, year, month, day, inclouControls = True, inclouIncidencies = True):
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    professor = User2Professor(user)
    
    data = date( year = int(year), month= int(month), day = int(day) )
    
    alumnes = None
    if pk == 'all':
        q_tutors_individualitat = Q( tutorindividualitzat__professor = professor )
        q_tutors_grup = Q( grup__tutor__professor = professor )
        alumnes = Alumne.objects.filter(q_tutors_individualitat | q_tutors_grup   ).distinct()
        grup = "Tots els alumnes"
    else:
        grup = Grup.objects.get( pk = int(pk) )
        alumnes = grup.alumne_set.all()
    
    pk_alumnes = [ a.pk for a in alumnes ]
    
    #busco el dilluns i el divendres
    dia_de_la_setmana = data.weekday()
     
    delta = timedelta( days = (-1 * dia_de_la_setmana ) )
    dilluns = data + delta
    
    #named instances
    estatPresent = EstatControlAssistencia.objects.get( codi_estat = 'P' )
    estatFalta = EstatControlAssistencia.objects.get( codi_estat = 'F' )
    estatJustificada = EstatControlAssistencia.objects.get( codi_estat = 'J' )
    estatRetras = EstatControlAssistencia.objects.get( codi_estat = 'R' )
    
    #marc horari per cada dia
    dades = tools.classebuida()
    dades.grup = grup
    dades.alumnes = alumnes.order_by( 'cognoms', 'nom' )
    dades.f = []
    dades.r = []
    dades.j = []
    dades.I = []
    dades.i = []
    dades.E = []
    dades.e = [] 
    dades.c = []    #controls

    
    dades.dia_hores = tools.diccionari()
    dades.marc_horari = {}
    for delta in [0,1,2,3,4]:
        dia = dilluns + timedelta( days = delta )
        
        forquilla = Horari.objects.filter( 
                                    impartir__controlassistencia__alumne__in = pk_alumnes,
                                    impartir__dia_impartir = dia                                            
                                ).aggregate( desde=Min( 'hora__hora_inici' ), finsa=Max( 'hora__hora_inici' )  )
        if forquilla['desde'] and forquilla['finsa']:
            dades.marc_horari[dia] = { 'desde':forquilla['desde'],'finsa':forquilla['finsa']}
            dades.dia_hores[dia] = llista()
            for hora in FranjaHoraria.objects.filter( hora_inici__gte = forquilla['desde'],
                                                      hora_inici__lte = forquilla['finsa'] ).order_by('hora_inici'):
                dades.dia_hores[dia].append(hora)            
        
    dades.quadre = tools.diccionari()
    
    for alumne in dades.alumnes:

        dades.quadre[unicode(alumne)] = []

        for dia, hores in dades.dia_hores.itemsEnOrdre():
            
            hora_inici = FranjaHoraria.objects.get( hora_inici = dades.marc_horari[dia]['desde'] )
            hora_fi    = FranjaHoraria.objects.get( hora_inici = dades.marc_horari[dia]['finsa'] )

            q_controls = Q( impartir__dia_impartir = dia ) & \
                         Q( impartir__horari__hora__gte = hora_inici) & \
                         Q( impartir__horari__hora__lte = hora_fi) & \
                         Q( alumne = alumne )

            controls = [ c for c in ControlAssistencia.objects.filter( q_controls ) ]

            q_incidencia = Q(dia_incidencia = dia) & \
                            Q(franja_incidencia__gte = hora_inici) & \
                            Q(franja_incidencia__lte = hora_fi) & \
                            Q(alumne = alumne)

            incidencies = [ i for i in  Incidencia.objects.filter( q_incidencia ) ]                                   

            q_expulsio = Q(dia_expulsio = dia) & \
                         Q(franja_expulsio__gte = hora_inici) & \
                         Q(franja_expulsio__lte = hora_fi) & \
                         Q(alumne = alumne) & \
                         ~Q(estat = 'ES') 

            expulsions = [ e for e in Expulsio.objects.filter( q_expulsio ) ]                    

            for hora in hores:
     
                cella = tools.classebuida()
                cella.txt = ''
                #present = estatPresent in [ c.estat for c in controls]
                hiHaControls = len( [ c for c in controls if c.impartir.horari.hora == hora] )>0
                haPassatLlista = hiHaControls and len( [ c for c in controls if c.estat is not None and c.impartir.horari.hora == hora] )>0
                
                if inclouIncidencies:
                    cella.f = [ c for c in controls if c.estat == estatFalta and c.impartir.horari.hora == hora]
                    cella.r = [ c for c in controls if c.estat == estatRetras and c.impartir.horari.hora == hora] 
                    cella.j = [ c for c in controls if c.estat == estatJustificada and c.impartir.horari.hora == hora ]
                    cella.I = [ i for i in incidencies if not i.es_informativa and i.franja_incidencia == hora ]
                    cella.i = [ i for i in incidencies if i.es_informativa and i.franja_incidencia == hora]
                    cella.E = [e for e in expulsions if not e.es_expulsio_per_acumulacio_incidencies and e.franja_expulsio == hora ] 
                    cella.e = [e for e in expulsions if  e.es_expulsio_per_acumulacio_incidencies and e.franja_expulsio == hora ] 
                else:
                    cella.f = []
                    cella.r = []
                    cella.j = []
                    cella.I = []
                    cella.i = []
                    cella.E = []
                    cella.e = []

                if inclouControls:
                    cella.c = [ c for c in controls if c.impartir.horari.hora == hora]
                else:
                    cella.c = [ ]
                    
                dades.f.extend(cella.f)
                dades.r.extend(cella.r)
                dades.j.extend(cella.j)
                dades.I.extend(cella.I)
                dades.i.extend(cella.i)
                dades.E.extend(cella.E)
                dades.e.extend(cella.e)
                dades.c.extend(cella.c)

                if not hiHaControls:
                    cella.color = '#505050'
                else:
                    if not haPassatLlista:
                        cella.color = '#E0E0E0'
                    else:
                        cella.color = 'white'
                
                dades.quadre[unicode(alumne)].append( cella )
                
    return dades

@login_required
@group_required(['professors'])
def informeSetmanalPrint(request, pk, year, month, day, suport):
    #pk és el grup. Per tots els alumnes tutorats marcar pk = All.
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    professor = User2Professor(user)

    #--seg----
    grup = Grup.objects.get( pk = int(pk) ) if pk != 'all' else 'Tots els alumnes'
    esTutorDelGrup = pk != 'all' and grup in Grup.objects.filter( tutor__professor = professor )
    teAlumnesTutoratsIndividuals = pk == 'all' and professor.tutorindividualitzat_set.count() > 0
    tePermis = l4 or esTutorDelGrup or teAlumnesTutoratsIndividuals
    if not tePermis:
        return Http404
        
    errorsTrobats = None
    
    
    
    try:
        dades = informeSetmanalMKTable(request, pk, year, month, day)
 
    except Exception, e:
        errorsTrobats = e
                                              
    if errorsTrobats:
        url_next = 'javascript:window.close();'
        resultat = { 'errors': [ errorsTrobats ], 
                'warnings':  [], 'infos':  [], 'url_next': url_next }
        return render_to_response(
                   'resultat.html', 
                   {'head': u'Error preparant el llistat:' ,
                    'msgs': resultat },
                   context_instance=RequestContext(request))         
    else:
        return render_to_response(
              "informeSetmanal.html", 
              {"head": u'Informe setmanal grup {0}'.format( grup ),
               "dades": dades
               },
              context_instance=RequestContext(request))

        

@login_required
@group_required(['professors'])
def informeSetmanal(request):
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    professor = User2Professor(user)
        
    head='Informe setmana'
    
    grups = Grup.objects.filter( tutor__professor = professor )

    
    if request.method == "POST":
        form = informeSetmanalForm( data = request.POST, queryset = grups )
        if form.is_valid():
            grup = form.cleaned_data['grup']
            if grup is not None:
                data = form.cleaned_data['data']
                url_next = '/tutoria/informeSetmanalPrint/{0}/{1}/{2}/{3}/{4}'.format( grup.pk if grup else 'all', data.year, data.month, data.day,'html' )
                return HttpResponseRedirect(  url_next)
            else:
                msg = u"No has escollit un grup vàlid."
                url_next = 'javascript:window.close();'
                resultat = { 'errors': [ msg ],
                        'warnings':  [], 'infos':  [], 'url_next': url_next }
                return render_to_response(
                           'resultat.html',
                           {'head': u'Error preparant el llistat:' ,
                            'msgs': resultat },
                           context_instance=RequestContext(request))
        else:
            msg = u"Comprova que has seleccionat correctament el grup i la data."
            url_next = 'javascript:window.close();'
            resultat = { 'errors': [ msg ], 
                    'warnings':  [], 'infos':  [], 'url_next': url_next }
            return render_to_response(
                       'resultat.html', 
                       {'head': u'Error preparant el llistat:' ,
                        'msgs': resultat },
                       context_instance=RequestContext(request))    

    else:
        grupInicial = { 'grup': grups[0]} if grups else {}
        if not grups and professor.tutorindividualitzat_set.count()  == 0:
            return render_to_response(
                        'resultat.html', 
                        {'head': u'Justificador de faltes' ,
                         'msgs': { 'errors': [], 'warnings':  [u'Sembla ser que no tens grups assignats'], 'infos':  [] } },
                        context_instance=RequestContext(request)) 
        
        form = informeSetmanalForm(  queryset = grups, initial = grupInicial )


    return render_to_response(
                  "form.html",
                  {"form": form,
                   "head": head,
                   "target":"blank_"
                   },
                  context_instance=RequestContext(request))
    

@login_required
@group_required(['professors'])
def justificadorMKTable(request, year, month, day ):
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    professor = User2Professor(user)
    
    data = date( year = int(year), month= int(month), day = int(day) )
    grups = Grup.objects.filter( tutor__professor = professor )

    q_grups_tutorats = Q( grup__in =  [ t.grup for t in professor.tutor_set.all() ] )
    q_alumnes_tutorats = Q( pk__in = [ti.alumne.pk for ti in professor.tutorindividualitzat_set.all() ]  )
    alumnes = Alumne.objects.filter( q_grups_tutorats | q_alumnes_tutorats )
    
    #busco el dilluns i el divendres
    dia_de_la_setmana = data.weekday()
     
    delta = timedelta( days = (-1 * dia_de_la_setmana ) )
    dilluns = data + delta
        
    #marc horari per cada dia
    dades = tools.classebuida()
    dades.alumnes = alumnes.order_by('grup', 'cognoms', 'nom' )
    dades.c = []    #controls
    
    dades.dia_hores = tools.diccionari()
    dades.marc_horari = {}
    for delta in [0,1,2,3,4]:
        dia = dilluns + timedelta( days = delta )
        q_grups = Q(grup__in = grups )
        q_alumnes = Q(grup__alumne__in = alumnes )
        q_impartir = Q( impartir__controlassistencia__alumne__in = alumnes )
        q_dies = Q(impartir__dia_impartir = dia)
        
        #forquilla = Horari.objects.filter( ( q_grups | q_alumnes ) & q_dies                                               
        forquilla = Horari.objects.filter( q_impartir & q_dies                                               
                                ).aggregate( desde=Min( 'hora__hora_inici' ), finsa=Max( 'hora__hora_inici' )  )
        if forquilla['desde'] and forquilla['finsa']:
            dades.marc_horari[dia] = { 'desde':forquilla['desde'],'finsa':forquilla['finsa']}
            dades.dia_hores[dia] = llista()
            for hora in FranjaHoraria.objects.filter( hora_inici__gte = forquilla['desde'],
                                                      hora_inici__lte = forquilla['finsa'] ).order_by('hora_inici'):
                dades.dia_hores[dia].append(hora)            
        
    dades.quadre = tools.diccionari()
    
    for alumne in dades.alumnes:

        dades.quadre[unicode(alumne)] = []

        for dia, hores in dades.dia_hores.itemsEnOrdre():
            
            hora_inici = FranjaHoraria.objects.get( hora_inici = dades.marc_horari[dia]['desde'] )
            hora_fi    = FranjaHoraria.objects.get( hora_inici = dades.marc_horari[dia]['finsa'] )

            q_controls = Q( impartir__dia_impartir = dia ) & \
                         Q( impartir__horari__hora__gte = hora_inici) & \
                         Q( impartir__horari__hora__lte = hora_fi) & \
                         Q( alumne = alumne )

            controls = [ c for c in ControlAssistencia.objects.select_related(
                                'estat', 'impartir__assignatura','professor','estat_backup','professor_backup'
                                ).filter( q_controls ) ]

            for hora in hores:
     
                cella = tools.classebuida()
                cella.txt = ''
                hiHaControls = len( [ c for c in controls if c.impartir.horari.hora == hora] )>0
                haPassatLlista = hiHaControls and len( [ c for c in controls if c.estat is not None and c.impartir.horari.hora == hora] )>0
                
                cella.c = [ c for c in controls if c.impartir.horari.hora == hora]
                for item in cella.c:
                    item.professor2show = item.professor or ( item.impartir.horari.professor if item.impartir.horari else ' ' ) 
                    item.estat2show= item.estat or " "
                dades.c.extend(cella.c)

                if not hiHaControls:
                    cella.color = '#505050'
                else:
                    if not haPassatLlista:
                        cella.color = '#E0E0E0'
                    else:
                        cella.color = 'white'
                
                dades.quadre[unicode(alumne)].append( cella )
                
    return dades    
    
@login_required
@group_required(['professors'])
def justificaNext(request, pk):
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    professor = User2Professor(user)
    
    #--seg----
    control = ControlAssistencia.objects.get( pk = int(pk) )
    esTutor = professor in  control.alumne.tutorsDeLAlumne() 
    tePermis = l4 or esTutor
    if not tePermis:
        return Http404
        pass

    justificada = EstatControlAssistencia.objects.get( codi_estat = 'J' )
    
    ok = True
    errors = []
    jaEstaJustifiada = control.estat and control.estat == justificada
    if not jaEstaJustifiada or control.swaped:
        if control.swaped:
            control.estat, control.estat_backup = control.estat_backup, None
            control.professor, control.professor_backup = control.professor_backup, None
        else:
            control.estat_backup, control.estat = control.estat, justificada
            control.professor_backup, control.professor = control.professor, professor

        try:
            control.swaped = not control.swaped
            control.credentials = credentials
            control.save()

            #LOGGING
            Accio.objects.create( 
                    tipus = 'JF',
                    usuari = user,
                    l4 = l4,
                    impersonated_from = request.user if request.user != user else None,
                    text = u"""Justificades faltes de l'alumne {0} del dia {1}. """.format( control.alumne, control.impartir.dia_impartir )
                )                
        except ValidationError, e:
            ok=False
            import itertools
            errors = list( itertools.chain( *e.message_dict.values() )  )        

    resposta = {
        'ok' :  ok,
        'codi': control.estat.codi_estat if control.estat else ' ',
        'missatge': u'{0}:{1}  Prof.: {2}'.format( control.estat, control.impartir.horari.assignatura,  control.professor ),
        'errors':  errors,
        'swaped' : (control.swaped)
    }
    
    return HttpResponse( simplejson.dumps(resposta, ensure_ascii=False ) ,mimetype= 'application/json')

@login_required
@group_required(['professors'])
def justificador(request, year, month, day):
    credentials = tools.getImpersonateUser(request)
    (user, l4) = credentials
    professor = User2Professor(user)

    errorsTrobats = None

    dades = justificadorMKTable(request, year, month, day)

    #navegacio pel calendari:
    import datetime as t

    data = t.date(  int(year), int(month), int(day) )
    altres_moments = [
           [ professor.username, '<< mes passat'    , data + t.timedelta( days = -30 )],
           [ professor.username, '< setmana passada' , data + t.timedelta( days = -7 )],
           [ professor.username, '< avui >'    , t.date.today ],
           [ professor.username, 'setmana vinent >'  , data + t.timedelta( days = +7 ) ],
           [ professor.username, 'mes vinent >>'      , data + t.timedelta( days = +30 ) ],
        ]

    return render_to_response(
              "justificator.html",
              {"head": u'Justificar faltes de tutorats de {0}'.format( professor ),
               "dades": dades,
               "altres_moments": altres_moments
               },
              context_instance=RequestContext(request))

# @login_required
# @group_required(['professors'])
# def justificaFaltesPre(request):
#     credentials = tools.getImpersonateUser(request)
#     (user, l4) = credentials
#     professor = User2Professor(user)
#
#     #prefixes:
#     #https://docs.djangoproject.com/en/dev/ref/forms/api/#prefixes-for-forms
#     formset = []
#
#     head='Justificar faltes'
#
#     #---------------------------------Passar llista -------------------------------
#
#     q_grups_tutorats = Q( grup__in =  [ t.grup for t in professor.tutor_set.all() ] )
#     q_alumnes_tutorats = Q( pk__in = [ti.alumne.pk for ti in professor.tutorindividualitzat_set.all() ]  )
#     query = Alumne.objects.filter( q_grups_tutorats | q_alumnes_tutorats )
#
#
#     if request.method == "POST":
#
#         formPas1=justificaFaltesW1Form( request.POST, queryset = query )
#         if formPas1.is_valid():
#             alumne = formPas1.cleaned_data['alumne']
#             dia_impartir = formPas1.cleaned_data['data']
#             if alumne:
#                 url_next = '/tutoria/justificaFaltes/{0}/{1}/{2}/{3}'.format(alumne.pk, dia_impartir.year, dia_impartir.month, dia_impartir.day  )
#             else:
#                 url_next = '/tutoria/justificador/{0}/{1}/{2}'.format(dia_impartir.year, dia_impartir.month, dia_impartir.day  )
#             return HttpResponseRedirect( url_next )
#         else:
#             formset.append( formPas1 )
#     else:
#         form=justificaFaltesW1Form( queryset = query )
#         formset.append(form)
#
#     return render_to_response(
#                   "formset.html",
#                   {"formset": formset,
#                    "head": head,
#                    },
#                   context_instance=RequestContext(request))

@login_required
@group_required(['professors'])
def elsMeusAlumnesTutorats(request):

    credentials = tools.getImpersonateUser(request) 
    (user, _ ) = credentials
    
    professor = User2Professor( user )     
    
    report = elsMeusAlumnesTutoratsRpt( professor )
        
    return render_to_response(
                'report.html',
                    {'report': report,
                     'head': 'Els meus alumnes tutorats' ,
                    },
                    context_instance=RequestContext(request))            


@login_required
@group_required(['professors'])
def gestioCartes(request):
    
    #TODO: Vaig per aquí cartes absència

    credentials = tools.getImpersonateUser(request) 
    (user, l4 ) = credentials
    
    professor = User2Professor( user )     
    
    report = gestioCartesRpt( professor, l4 )
        
    return render_to_response(
                'report.html',
                    {'report': report,
                     'head': 'Els meus alumnes tutorats' ,
                    },
                    context_instance=RequestContext(request))  

@login_required
@group_required(['professors'])
def novaCarta(request, pk_alumne ):
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    professor = User2Professor(user)
    alumne = get_object_or_404(Alumne,  pk = pk_alumne )
                
    #seg-------------------
    te_permis = (l4 or 
                professor in alumne.tutorsDeLAlumne() )
    if  not te_permis:
        raise Http404() 

    carta = CartaAbsentisme( alumne = alumne , professor = professor )
    frmFact = modelform_factory(CartaAbsentisme, fields=('data_carta', ))
    if request.method == 'POST':
        form = frmFact( request.POST, instance = carta )
        if form.is_valid():
            form.save()
            url_next = r'/tutoria/gestioCartes/#{0}'.format( carta.pk )   
            return HttpResponseRedirect( url_next )
    else:
        form = frmFact(  instance = carta )
    
    form.fields['data_carta'].widget = DateTextImput()
    
    return render_to_response(
                'form.html', 
                {'form': form, 
                 'head': u'Carta absentisme'},
                context_instance=RequestContext(request))          

@login_required
@group_required(['professors'])        
def imprimirCarta(request, pk_carta, flag  ):        
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    professor = User2Professor(user)
    carta = get_object_or_404(CartaAbsentisme,  pk = pk_carta )
    carta.impresa = flag
    carta.save()
                
    #seg-------------------
    te_permis = (l4 or 
                professor in carta.alumne.tutorsDeLAlumne()
                or
                user.groups.filter(name__in= [u'direcció', ] ).exists()
                )
    if  not te_permis:
        raise Http404() 
    
    return report_cartaAbsentisme(   request, carta )
    
@login_required
@group_required(['direcció'])        
def esborraCarta(request, pk_carta ):        
    credentials = tools.getImpersonateUser(request) 
    (user, l4) = credentials
    professor = User2Professor(user)
    carta = get_object_or_404(CartaAbsentisme,  pk = pk_carta )
    carta.delete()
                
    #seg-------------------
    te_permis = (l4 or 
                professor in carta.alumne.tutorsDeLAlumne() and 1==2   #potser deixar-los esborrar cartes durant uns minuts ??
                )
    if  not te_permis:
        raise Http404() 
    
    url_next = r'/tutoria/gestioCartes/'
    return HttpResponseRedirect( url_next )
    

@login_required
@group_required(['direcció'])
def totesLesCartes(request):
    
    #TODO: Vaig per aquí cartes absència

    credentials = tools.getImpersonateUser(request) 
    (user, l4 ) = credentials
    
    professor = User2Professor( user )     
    
    report = totesLesCartesRpt(  )
        
    return render_to_response(
                'report.html',
                    {'report': report,
                     'head': 'Els meus alumnes tutorats' ,
                    },
                    context_instance=RequestContext(request))  



@login_required
@group_required(['professors'])
def elsMeusAlumnesTutoratsEntreDates(request):

    credentials = tools.getImpersonateUser(request) 
    (user, _ ) = credentials
    
    professor = User2Professor( user )     
    
    if user.groups.filter(name='direcció'):
        possibles_grups = [ ( t.pk, unicode( t) ) for t in   Grup.objects.all() ]
    else:
        possibles_grups = [ ( t.grup.pk, unicode( t.grup) ) for t in  Tutor.objects.filter( professor = professor )]
        
    possibles_grups.append( ( 'ElsMeusAlumnes', 'Els Meus Alumnes', ) )
    
    if request.method == 'POST':
        form = elsMeusAlumnesTutoratsEntreDatesForm( request.POST, grups = possibles_grups ) 
        
        if form.is_valid():
            parm_professor = None
            parm_grup = None
            if form.cleaned_data['grup'] == 'ElsMeusAlumnes':
                parm_professor = professor
            else:
                parm_grup = form.cleaned_data['grup']
            parm_dataDesDe = form.cleaned_data['dataDesDe']
            parm_dataFinsA = form.cleaned_data['dataFinsA']
            
            report = elsMeusAlumnesTutoratsRpt( parm_professor, parm_grup, parm_dataDesDe, parm_dataFinsA )
                
            return render_to_response(
                        'report.html',
                            {'report': report,
                             'head': 'Consulta Assistència Entre Dates' ,
                            },
                            context_instance=RequestContext(request))         
    else:
        form = elsMeusAlumnesTutoratsEntreDatesForm( grups = possibles_grups )
        
    return render_to_response(
                'form.html', 
                {'form': form, 
                 'head': 'Consulta Assistència Entre Dates'},
                context_instance=RequestContext(request))    



#---------------------  --------------------------------------------#

    
@login_required
@group_required(['professors',])
def detallTutoriaAlumne( request, pk , detall = 'all'):

    credentials = tools.getImpersonateUser(request) 
    (user, l4 ) = credentials
    
    professor = User2Professor( user )     
    
    alumne = Alumne.objects.get( pk = pk )
    
    esTutorat = l4 or \
                professor in alumne.tutorsDeLAlumne() or \
                user.groups.filter(name__in= [u'direcció', u'psicopedagog'] ).exists()  
    
    if not esTutorat:
        raise Http404 
    
    head = u'{0} ({1})'.format(alumne , unicode( alumne.grup ) )
    
    report = []

    #---dades alumne---------------------------------------------------------------------
    if detall in ['all','dades']:
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 200
        capcelera.contingut = u'Dades Alumne'
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)
    
        capcelera = tools.classebuida()
        capcelera.amplade = 400
        capcelera.contingut = u''
        taula.capceleres.append(capcelera)
        
        taula.fileres = []
    
            #----grup------------------------------------------
        filera = []
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'Grup'        
        filera.append(camp)
    
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'{0}'.format( alumne.grup )        
        filera.append(camp)
    
        taula.fileres.append( filera )
    
            #----data neix------------------------------------------
        filera = []
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'Data Neixement'        
        filera.append(camp)
    
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'{0}'.format( alumne.data_neixement.strftime( '%d/%m/%Y' ) )        
        filera.append(camp)
    
        taula.fileres.append( filera )
    
            #----telefons------------------------------------------
        filera = []
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'Telèfon'        
        filera.append(camp)
    
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'{0}'.format( alumne.telefons )        
        filera.append(camp)
    
        taula.fileres.append( filera )
    
            #----Pares------------------------------------------
        filera = []
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'Pares'        
        filera.append(camp)
    
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'{0}'.format( alumne.tutors )        
        filera.append(camp)
    
        taula.fileres.append( filera )
    
            #----adreça------------------------------------------
        filera = []
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'Adreça'        
        filera.append(camp)
    
        camp = tools.classebuida()
        camp.enllac = None
        camp.contingut = u'{0} ({1})'.format( alumne.adreca, alumne.localitat )        
        filera.append(camp)
    
        taula.fileres.append( filera )
    
        report.append(taula)
    
    #----Expulsions del centre --------------------------------------------------------------------   
    if detall in ['all', 'incidencies']:
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 200
        capcelera.contingut = u'Expulsions del Centre'
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)
    
        capcelera = tools.classebuida()
        capcelera.amplade = 400
        capcelera.contingut = u''
        taula.capceleres.append(capcelera)
                
        taula.fileres = []
            
        for expulsio in alumne.expulsiodelcentre_set.all().order_by( '-data_inici' ):
            filera = []
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'{0}'.format( expulsio.data_inici.strftime( '%d/%m/%Y' ) )          
            filera.append(camp)
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'{0}'.format( expulsio.motiu_expulsio )        
            filera.append(camp)
            #--
            taula.fileres.append( filera )
    
        report.append(taula)

    #----Expulsions --------------------------------------------------------------------
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 200
        capcelera.contingut = u'Expulsions'
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)
    
        capcelera = tools.classebuida()
        capcelera.amplade = 40
        capcelera.contingut = u''
        taula.capceleres.append(capcelera)
            
        capcelera = tools.classebuida()
        capcelera.amplade = 400
        capcelera.contingut = u''
        taula.capceleres.append(capcelera)
        
        taula.fileres = []
        
        for expulsio in alumne.expulsio_set.exclude( estat = 'ES' ).order_by( '-dia_expulsio', '-franja_expulsio' ):
            filera = []
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'{0} {1}'.format( expulsio.dia_expulsio.strftime( '%d/%m/%Y' ),
                                                u'''(per acumulació d'incidències)''' if expulsio.es_expulsio_per_acumulacio_incidencies else '')         
            filera.append(camp)
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'{0}, {1}'.format( u'No tramitada.' if expulsio.estat != 'TR' else u'Sí tramitada', 
                                                u'Sí vigent.' if expulsio.es_vigent else u'No vigent',)         
            filera.append(camp)            
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'Sr(a): {0} - {1}'.format(                                                
                                               expulsio.professor , 
                                               expulsio.motiu_expulsio )        
            filera.append(camp)
            #--
            taula.fileres.append( filera )
            
        report.append(taula)
        
            
    #----incidències --------------------------------------------------------------------
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 200
        capcelera.contingut = u'Incidències'
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)
    
        capcelera = tools.classebuida()
        capcelera.amplade = 400
        capcelera.contingut = u''
        taula.capceleres.append(capcelera)
        
        taula.fileres = []
    
        for incidencia in alumne.incidencia_set.filter( es_informativa = False ).order_by( '-dia_incidencia', '-franja_incidencia' ):
            filera = []
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'{0} {1}'.format( incidencia.dia_incidencia.strftime( '%d/%m/%Y' ), 
                                                'Vigent' if incidencia.es_vigent else '')        
            filera.append(camp)
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'Sr(a): {0} - {1}'.format(incidencia.professional , 
                                                        incidencia.descripcio_incidencia )        
            filera.append(camp)
    
            #--
            taula.fileres.append( filera )            
    
        report.append(taula)
        
        
        

    #----observacions --------------------------------------------------------------------
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 200
        capcelera.contingut = u'Observacions'
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)
    
        capcelera = tools.classebuida()
        capcelera.amplade = 400
        capcelera.contingut = u''
        taula.capceleres.append(capcelera)
        
        taula.fileres = []
    
        for incidencia in alumne.incidencia_set.filter( es_informativa = True ).order_by( '-dia_incidencia', '-franja_incidencia' ):
            filera = []
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'{0}'.format( incidencia.dia_incidencia.strftime( '%d/%m/%Y' ) )        
            filera.append(camp)
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'Sr(a): {0} - {1}'.format(incidencia.professional , 
                                                        incidencia.descripcio_incidencia )        
            filera.append(camp)
    
            #--
            taula.fileres.append( filera )
        
        report.append(taula)

    #----Assistencia --------------------------------------------------------------------
    if detall in ['all', 'assistencia']:
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        taula.fileres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 200
        capcelera.contingut = u'Faltes i retards' 
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)
    
        capcelera = tools.classebuida()
        capcelera.amplade = 400
        capcelera.contingut = u''
        taula.capceleres.append(capcelera)
        
        for control in alumne.controlassistencia_set.exclude( estat__codi_estat = 'P' 
                                                              ).filter(  
                                                        estat__isnull=False                                                          
                                                            ).order_by( '-impartir__dia_impartir' , '-impartir__horari__hora'):
            
            filera = []
            
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = unicode(control.impartir.dia_impartir)        
            filera.append(camp)
    
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'{0} a {1} ({2})'.format(
                                                 control.estat,
                                                 control.impartir.horari.assignatura,
                                                 control.impartir.horari.hora 
                                    )        
            filera.append(camp)
    
            #--
            taula.fileres.append( filera )
    
        report.append(taula)    

    #----Actuacions --------------------------------------------------------------------
    if detall in ['all', 'actuacions']:
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        taula.fileres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 200
        capcelera.contingut = u'Actuacions' 
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)
    
        capcelera = tools.classebuida()
        capcelera.amplade = 400
        capcelera.contingut = u''
        taula.capceleres.append(capcelera)
        
        for actuacio in alumne.actuacio_set.order_by('-moment_actuacio' ):
            
            filera = []
            
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = unicode(actuacio.moment_actuacio)        
            filera.append(camp)
    
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = '/tutoria/editaActuacio/{0}'.format(actuacio.pk)
            camp.contingut = u'{0} fa actuació amb {1}: '.format( 
                                    actuacio.get_qui_fa_actuacio_display(),
                                    actuacio.get_amb_qui_es_actuacio_display(),
                                    actuacio.assumpte
                                    )        
            filera.append(camp)
    
            #--
            taula.fileres.append( filera )
    
        report.append(taula)    

    #----Seguiment tutorial--------------------------------------------------------------------
    if detall in ['all', 'seguiment']:
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 200
        capcelera.contingut = u'Següiment tutorial' 
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)
        
        anys_seguiment_tutorial =  []
        txt_preguntes = []
        try:
                anys_seguiment_tutorial = SeguimentTutorialRespostes.objects.filter( 
                                                        seguiment_tutorial__alumne = alumne  
                                                                                   ).values_list('any_curs_academic', flat=True).distinct()
                txt_preguntes = SeguimentTutorialRespostes.objects.filter( 
                                                        seguiment_tutorial__alumne = alumne  
                                                                                   ).values_list('pregunta', flat=True).distinct()
        except:
                pass
    
        for un_any in anys_seguiment_tutorial:
            capcelera = tools.classebuida()
            capcelera.amplade = 200
            capcelera.contingut = u'{0}-{1}'.format( un_any, un_any+1 )
            taula.capceleres.append(capcelera)
        
        taula.fileres = []
    
        for txt_pregunta in txt_preguntes:
            filera = []
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = unicode(txt_pregunta)        
            filera.append(camp)            
            for un_any in anys_seguiment_tutorial:
                txt_resposta = ''
                try:
                        txt_resposta = SeguimentTutorialRespostes.objects.get( 
                                                                seguiment_tutorial__alumne = alumne,
                                                                pregunta = txt_pregunta,
                                                                any_curs_academic = un_any,
                                                                              ).resposta
                except:
                        pass                            
        
                #----------------------------------------------
                camp = tools.classebuida()
                camp.enllac = None
                camp.contingut = unicode(txt_resposta)        
                filera.append(camp)
    
            #--
            taula.fileres.append( filera )
    
        report.append(taula)    
        
        
    #----Històric --------------------------------------------------------------------
    if detall in ['all', 'historic']:
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        taula.fileres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 600
        capcelera.contingut = u'Històric' 
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)

        
        for h in ResumAnualAlumne.objects.filter(seguiment_tutorial__alumne = alumne  ).order_by( '-curs_any_inici' ):
            
            filera = []
            
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u"""\n-----------------------------{0}------------------------------------
            \n
            {1}
            """.format(  unicode(h.curs_any_inici) + '-' + unicode(h.curs_any_inici+1)  , h.text_resum)        
            filera.append(camp)
    
            #--
            taula.fileres.append( filera )
    
        report.append(taula)          

    #----Qualitatives--------------------------------------------------------------------
    if detall in ['all', 'qualitativa']:
        taula = tools.classebuida()
    
        taula.titol = tools.classebuida()
        taula.titol.contingut = ''
        taula.titol.enllac = None
    
        taula.capceleres = []
        
        capcelera = tools.classebuida()
        capcelera.amplade = 200
        capcelera.contingut = u'Qualitativa' 
        capcelera.enllac = ""
        taula.capceleres.append(capcelera)
    
        capcelera = tools.classebuida()
        capcelera.amplade = 400
        capcelera.contingut = u''
        taula.capceleres.append(capcelera)
        
        taula.fileres = []
    
        for resposta in alumne.respostaavaluacioqualitativa_set.all().order_by( 'qualitativa', 'assignatura' ) :
            
            filera = []
            
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = u'{0} {1}'.format( resposta.qualitativa.data_tancar_avaluacio.strftime( '%d/%m/%Y' ) ,
                                                resposta.assignatura )        
            filera.append(camp)
    
            #----------------------------------------------
            camp = tools.classebuida()
            camp.enllac = None
            camp.contingut = unicode(resposta.item)        
            filera.append(camp)
    
            #--
            taula.fileres.append( filera )
    
        report.append(taula)    
        

#----------------
    
    return render_to_response(
                'report.html',
                    {'report': report,
                     'head': u'Informació alumne {0}'.format( head ) ,
                    },
                    context_instance=RequestContext(request))            




@login_required
@group_required(['direcció'])        
def informeCompletFaltesIncidencies(request):
    
    formset = []
    totBe = True
    head = u"Tria alumnes i dates"
    
    OPCIONS = (
        ('s', u'Imprimir Informe'),
        ('n', u'No Imprimir'),
        ('r', u'Imprimir Recordatori')
    )

    if request.method == 'POST':
        
        form = dataForm( request.POST, prefix = 'data_ini', label = u'Data des de', help_text = u'Primer dia a incloure al llistat' )
        form.fields['data'].required = True
        formset.append( form )  
        dataInici = form.cleaned_data['data'] if form.is_valid() else None

        form = dataForm( request.POST, prefix = 'data_fi' , label = u'Data fins a', help_text = u'Darrer dia a incloure al llistat' )
        form.fields['data'].required = True
        formset.append( form )
        dataFi = form.cleaned_data['data'] if form.is_valid() else None
        
        alumnes_recordatori = []
        alumnes_informe = []
        grups = []
        for grup in Grup.objects.filter( alumne__isnull = False ).distinct():
            #http://www.ibm.com/developerworks/opensource/library/os-django-models/index.html?S_TACT=105AGX44&S_CMP=EDU
            formInclouGrup=ckbxForm(request.POST,
                                    prefix=str( grup.pk ),
                                    label = u'Incloure {0}'.format(grup),
                                    help_text = u"Marca aquesta casella per incloure al llistat els alumnes d'aquest grup"                          
                                     )
            formInclouGrup.formSetDelimited = True
            formset.append( formInclouGrup )
            if formInclouGrup.is_valid():
                if formInclouGrup.cleaned_data['ckbx']:
                    grups.append(grup)            
            else:
                totBe = False
            
            for alumne in grup.alumne_set.all():

                user_associat = alumne.get_user_associat()
                
                fa_15_dies = datetime.now() - timedelta( days = 15 )
                connexio_darrers_dies = LoginUsuari.objects.filter( exitos = True, usuari__pk = user_associat.pk, moment__gte =  fa_15_dies ).exists()
                
                darrera_connexio = LoginUsuari.objects.filter( exitos = True, usuari__pk = user_associat.pk ).order_by('-moment')[:1]
                darrera_notificacio = alumne.relacio_familia_darrera_notificacio 
                te_correus_associats = bool( alumne.get_correus_relacio_familia() )

                opcio = 's'
                help_text = u"No tenim els correus d'aquest alumne"
                if alumne.esBaixa() or connexio_darrers_dies or ( darrera_connexio and darrera_notificacio and darrera_connexio[0].moment > darrera_notificacio): 
                    opcio = 'n'
                    help_text = u'Aquest alumne és baixa' if alumne.esBaixa() else u"Els tutors d'aquest alumne no tenen dades pendents de revisar"
                elif te_correus_associats:
                    opcio = 'r'
                    help_text = u'Aquest alumne té correus associats: {0}'.format( ', '.join(alumne.get_correus_relacio_familia()) )

                    
                formAlumne = choiceForm( request.POST,
                                         prefix=str( 'almn-{0}'.format( alumne.pk ) ),
                                         label = u'{0}'.format(alumne),
                                         opcions = OPCIONS,
                                         help_text = help_text ,
                                         initial = { 'opcio':opcio}  )
                formset.append( formAlumne )
                
                if formAlumne.is_valid():
                    if formAlumne.cleaned_data['opcio'] == 's':
                        alumnes_informe.append(alumne)
                    elif formAlumne.cleaned_data['opcio'] == 'r':
                        alumnes_recordatori.append(alumne)
                else:
                    totBe = False
                
        if totBe and dataInici and dataFi:            
            import reports 
            return reports.reportFaltesIncidencies(dataInici, dataFi, alumnes_informe, alumnes_recordatori, grups, request)
    #--------FINS AQUÍ--------
    else:

        form = dataForm( request.POST, prefix = 'data_ini' , label = u'Data des de', help_text = u'Primer dia a incloure al llistat' )       
        formset.append( form )

        form = dataForm( request.POST, prefix = 'data_fi' , label = u'Data fins a', help_text = u'Darrer dia a incloure al llistat' )       
        formset.append( form )
        
        for grup in Grup.objects.filter( alumne__isnull = False ).distinct():
            #http://www.ibm.com/developerworks/opensource/library/os-django-models/index.html?S_TACT=105AGX44&S_CMP=EDU
            formInclouGrup=ckbxForm(
                prefix=str( grup.pk ),
                label = u'Incloure {0}'.format(grup),
                help_text = u"Marca aquesta casella per incloure al llistat els alumnes d'aquest grup"
                 )
            formInclouGrup.formSetDelimited = True
            formset.append( formInclouGrup )
            for alumne in grup.alumne_set.all():
                
                user_associat = alumne.get_user_associat()

                fa_15_dies = datetime.now() - timedelta( days = 15 )
                connexio_darrers_dies = LoginUsuari.objects.filter( exitos = True, usuari__pk = user_associat.pk, moment__gte =  fa_15_dies ).exists()
                
                darrera_connexio = LoginUsuari.objects.filter( exitos = True, usuari__pk = user_associat.pk ).order_by('-moment')[:1]
                darrera_notificacio = alumne.relacio_familia_darrera_notificacio 
                te_correus_associats = bool( alumne.get_correus_relacio_familia() )

                opcio = 's'
                help_text = u"No tenim els correus d'aquest alumne"
                if alumne.esBaixa() or connexio_darrers_dies or ( darrera_connexio and darrera_notificacio and darrera_connexio[0].moment > darrera_notificacio):
                    opcio = 'n'
                    help_text = u'Aquest alumne és baixa' if alumne.esBaixa() else u"Els tutors d'aquest alumne no tenen dades pendents de revisar"
                elif te_correus_associats:
                    opcio = 'r'
                    help_text = u'Aquest alumne té correus associats: {0}'.format( ', '.join(alumne.get_correus_relacio_familia()) )

                    
                formAlumne = choiceForm( prefix=str( 'almn-{0}'.format( alumne.pk ) ),
                                         label = u'{0}'.format(alumne),
                                         opcions = OPCIONS,
                                         help_text = help_text ,
                                         initial = { 'opcio':opcio}  )
                formset.append( formAlumne )
        
    return render_to_response(
                  "informeCompletFaltesIncidencies.html", 
                  {"formset": formset,
                   "head": head,
                   "formSetDelimited": True,
                   },
                  context_instance=RequestContext(request))        



    
@login_required
@group_required(['professors'])
def calendariCursEscolarTutor(request):    

    credentials = tools.getImpersonateUser(request) 
    (user, _ ) = credentials

    professor = User2Professor( user ) 
    
    reports = reportCalendariCursEscolarTutor( professor )

    return render_to_response(
                'calendariCursEscolarTutor.html', 
                {'reports': reports},
                context_instance=RequestContext(request))
    
    
    
@login_required
@group_required(['direcció'])        
def seguimentTutorialPreguntes(request):

    head=u'Preguntes de Seguiment Tutorial' 
    
    formset_f = modelformset_factory( SeguimentTutorialPreguntes , extra=10, can_delete=True )
    missatge = ''

    if request.method == 'POST':
        formset = formset_f(request.POST)
        if formset.is_valid():            
            formset.save()
            for form in formset.deleted_forms:
                instancia = form.save()
                instancia.delete()
            missatge = u'''Actualització realitzada.'''
            url_next = '/tutoria/seguimentTutorialPreguntes' 
            return HttpResponseRedirect( url_next )
        else:
            missatge = u'''Actualització no realitzada.'''
                                   
    else:
        formset = formset_f()
    
    for form in formset:
        form.fields['pregunta'].widget.attrs['size'] = 70
        form.fields['ajuda_pregunta'].widget.attrs['size'] = 70
        
    missatge =  u"""Atenció! Per mantenir un històric de respostes 
                    és important no modificar el redactat de les preguntes.
                    Un petit canvi en el redactat de la pregunta es cosidera
                    una pregunta diferent."""
        
    return render_to_response(
                'formset.html', 
                {'formset': formset, 
                 'head': head,
                 'missatge': missatge,
                 'formSetDelimited':True},
                context_instance=RequestContext(request))    


@login_required
@group_required(['professors'])        
def seguimentTutorialFormulari(request):
    
    credentials = tools.getImpersonateUser(request) 
    (user, _ ) = credentials
    
    professor = User2Professor( user )     
    
    any_curs_academic = date.today().year - ( 1 if date.today().month <=8 else 0 )
    missatge = u"Atenció! Deseu la feina sovint (amb el botó enviar dades del peu de la pàgina). Recordeu que hi ha un temps de desconnexió per innactivitat."
    head = u""
    formset = []
    
    grups = [ t.grup for t in  Tutor.objects.filter( professor = professor )]
    grups.append( 'Altres' )
    for grup in grups:

        if grup == 'Altres':
            consulta_alumnes = Q( pk__in = [ti.alumne.pk for ti in professor.tutorindividualitzat_set.all() ]  )
        else:
            consulta_alumnes = Q( grup =  grup ) 
            
        for alumne in Alumne.objects.filter( consulta_alumnes ):
            infoform_added = False
            
            if not hasattr( alumne, 'seguimenttutorial' ):
                s, is_new = SeguimentTutorial.objects.get_or_create(
                        nom = alumne.nom,
                        cognoms =   alumne.cognoms,
                        data_neixement = alumne.data_neixement     )
                if is_new:
                    s.datadarreraacttualitzacio = datetime.now()                
                s.alumne = alumne
                s.save()
                alumne = Alumne.objects.get( pk = alumne.pk )
                
                
            for pregunta in SeguimentTutorialPreguntes.objects.all():

                if request.method == 'POST':  #---------------------------------------------------------
                    form = seguimentTutorialForm(
                                request.POST,
                                prefix=str( alumne.pk )+'_'+str(  pregunta.pk ), 
                                pregunta = pregunta,
                                resposta_anterior = None,
                                tutor = professor,
                                alumne = alumne )  
                    if form.is_valid():
                        r, is_new = SeguimentTutorialRespostes.objects.get_or_create(
                                                                                any_curs_academic = any_curs_academic,
                                                                                pregunta = pregunta.pregunta,
                                                                                seguiment_tutorial = alumne.seguimenttutorial,
                                                                           )
                        r.resposta = form.cleaned_data[ form.q_valida ]
                        r.save()                                    
                              
                
                
                else:                         #---------------------------------------------------------                    
                    try:
                        resposta_anterior = SeguimentTutorialRespostes.objects.get(
                                                    seguiment_tutorial = alumne.seguimenttutorial ,
                                                    any_curs_academic = any_curs_academic ,
                                                    pregunta = pregunta.pregunta
                                                            )
                    except ObjectDoesNotExist:
                        resposta_anterior = None
                    form = seguimentTutorialForm(
                                prefix=str( alumne.pk )+'_'+str(  pregunta.pk ), 
                                pregunta = pregunta,
                                resposta_anterior = resposta_anterior,
                                tutor = professor,
                                alumne = alumne  )
                
#                if pregunta.es_pregunta_oberta:
#                    del form.fields['pregunta_select']
#                else:
#                    del form.fields['pregunta_oberta']

                if not infoform_added:
                    infoform_added = True
                    form.infoForm = [ (u'{0} - Alumne'.format(alumne.grup), u'{0} curs {1}'.format( alumne, any_curs_academic )  ) ]
                    form.formSetDelimited = True
                    
                formset.append(form)

                    
    return render_to_response(
                'formset.html', 
                {'formset': formset, 
                 'head': head,
                 'missatge': missatge,
                 'formSetDelimited':True},
                context_instance=RequestContext(request)) 
    
    
@login_required
@group_required(['direcció'])        
def calculaResumAnual(request):
    calculaResumAnualProcess()
    
    
@login_required
def blanc( request ):
    return render_to_response(
                'blanc.html',
                    {},
                    context_instance=RequestContext(request)) 
        