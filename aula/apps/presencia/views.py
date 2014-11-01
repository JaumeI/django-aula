# This Python file uses the following encoding: utf-8

#templates
from django.template import RequestContext

#formularis
from aula.apps.presencia.forms import regeneraImpartirForm,ControlAssistenciaForm,\
    alertaAssistenciaForm, faltesAssistenciaEntreDatesForm,\
    marcarComHoraSenseAlumnesForm, passaLlistaGrupDataForm
from aula.apps.presencia.forms import afegeixTreuAlumnesLlistaForm, afegeixAlumnesLlistaExpandirForm
from aula.apps.presencia.forms import afegeixGuardiaForm, calculadoraUnitatsFormativesForm

#models
from aula.apps.horaris.models import FranjaHoraria
from aula.apps.presencia.models import Impartir, ControlAssistencia
from aula.apps.alumnes.models import Alumne     , Grup
from aula.apps.usuaris.models import User2Professor, Accio

#helpers
from aula.apps.presencia.regeneraImpartir import regeneraThread
from aula.utils.tools import getImpersonateUser, getSoftColor
from django.utils.safestring import SafeText

#consultes
from django.db.models import Q

#auth
from django.contrib.auth.decorators import login_required
from aula.utils.decorators import group_required

#workflow
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404

#excepcions
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.http import Http404

#other
from django.utils.datetime_safe import datetime, date
from django import forms
from aula.apps.assignatures.models import Assignatura
from aula.apps.presencia.reports import alertaAssitenciaReport
from aula.apps.presencia.rpt_faltesAssistenciaEntreDatesProfessor import faltesAssistenciaEntreDatesProfessorRpt
from django.forms.models import modelformset_factory
from django.forms.widgets import RadioSelect
from aula.apps.BI.utils import dades_dissociades
from aula.apps.BI.prediccio_assistencia import predictTreeModel
from aula.apps.presencia.business_rules.impartir import impartir_despres_de_passar_llista

#template filters
from django.template.defaultfilters import date as _date
from django.contrib import messages
from django.core.urlresolvers import reverse


#vistes -----------------------------------------------------------------------------------
@login_required
@group_required(['direcció'])
def regeneraImpartir(request):

    head=u'Reprogramar classes segons horari actual'

    if request.method == 'POST':
        form = regeneraImpartirForm(request.POST)
        if form.is_valid():

            r=regeneraThread(
                            data_inici=form.cleaned_data['data_inici'],
                            franja_inici = form.cleaned_data['franja_inici'],
                            user = request.user
                            )
            r.start()
            errors=[]
            warnings=[]
            infos=[u'Iniciat procés regeneració']
            resultat = {   'errors': errors, 'warnings':  warnings, 'infos':  infos }
            return render_to_response(
                    'resultat.html',
                    {'head': head ,
                     'msgs': resultat },
                    context_instance=RequestContext(request))
    else:
        form = regeneraImpartirForm()
    return render_to_response(
                'form.html',
                {'form': form,
                 'head': head},
                context_instance=RequestContext(request))


#------------------------------------------------------------------------------------------
#
#@login_required
#def mostraImpartir( request, user=None, year=None, month=None, day=None ):
#    
#    import datetime as t
#    
#    professor = None
#    #si usuari arriba a none posem l'actual
#    if not user:
#        professor = User2Professor( request.user ) 
#        user = request.user.username
#    else:
#        professor = get_object_or_404( Professor, username = user )
#        
#    if professor is None:
#        HttpResponseRedirect( '/' )

@login_required
@group_required(['professors'])
def mostraImpartir( request, year=None, month=None, day=None ):

    import datetime as t

    credentials = getImpersonateUser(request)
    (user, _ ) = credentials

    professor = User2Professor( user )

    if professor is None:
        HttpResponseRedirect( '/' )

    #si la data arriba a none posem la data d'avui    
    if not ( year and month and day):
        today = t.date.today()
        year = today.year
        month = today.month
        day = today.day
    else:
        year= int( year)
        month = int( month )
        day = int( day)

    #no es tracta del dia d'avui, sino la data amb la que treballem
    data_actual = t.date( year, month, day)

    #busquem el primer dilluns    
    dia_de_la_setmana = data_actual.weekday()
    delta = t.timedelta( days = (-1 * dia_de_la_setmana ) )
    data = data_actual + delta

    #per cada dia i franja horaria fem un element.
    impartir_tot=[]             #això són totes les franges horàries
    impartir_pendents=[]        #aquí les que potser no posarem (si estan buides i no hi ha més)
    dies_calendari=[]
    unDia = t.timedelta( days = 1)
    primera_franja_insertada = False
    for f in FranjaHoraria.objects.all():
        impartir_franja=[ [ [( unicode(f),'','','' )]  ] ]
        te_imparticions = False
        for d in range(0,5):
            dia = data + d * unDia
            if dia not in dies_calendari : dies_calendari.append( dia )
            franja_impartir = Q(horari__hora = f)
            dia_impartir = Q( dia_impartir = dia )
            user_impartir = Q( horari__professor = professor )
            guardia = Q( professor_guardia  = professor )

            #TODO: Passar només la impartició i que el template faci la resta de feina.
            imparticions = [
                            (x.horari.assignatura.nom_assignatura,          #
                             x.horari.grup if  x.horari.grup else '',       #
                             x.horari.nom_aula,                             #
                             x.pk,                                          #
                             getSoftColor( x.horari.assignatura ),    #
                             x.color(),
                             x.resum(),
                             (x.professor_guardia  and x.professor_guardia.pk == professor.pk),
                            )
                            for x in Impartir.objects.filter( franja_impartir & dia_impartir & (user_impartir | guardia)   ) ]

            impartir_franja.append( (imparticions, dia==data_actual) )
            te_imparticions = te_imparticions or imparticions   #miro si el professor ha d'impartir classe en aquesta franja

        if te_imparticions:                     #si ha d'impartir llavors afageixo la franja
            primera_franja_insertada = True
            impartir_tot += impartir_pendents   #afegeixo franges buides entre franges "plenes"
            impartir_pendents = []
            impartir_tot.append( impartir_franja )
        else:
            if primera_franja_insertada:
                impartir_pendents.append( impartir_franja ) #franges buides que potser caldrà afegir a l'horari

    nomProfessor = unicode( professor )

    #navegacio pel calencari:
    altres_moments = [
           # text a mostrar, data de l'enllaç, mostrar-ho a mòbil, mostrar-ho a tablet&desktop
           [ '<< mes passat'    , data + t.timedelta( days = -30 ), False, True ],
           [ '< setmana passada' , data + t.timedelta( days = -7 ), False, True ],
           [ '< dia passat' , data_actual + t.timedelta( days = -1 ), True, False ],
           [ '< avui >'    , t.date.today, True, True ],
           [ 'dia vinent >' , data_actual + t.timedelta( days = +1 ), True, False ],
           [ 'setmana vinent >'  , data + t.timedelta( days = +7 ), False, True ],
           [ 'mes vinent >>'      , data + t.timedelta( days = +30 ), False, True ],
        ]

    calendari = [ (_date( d, 'D'), d.strftime('%d/%m/%Y'), d==data_actual) for d in dies_calendari]

    return render_to_response(
                'mostraImpartir.html',
                {
                 'calendari': calendari,
                 'impartir_tot': impartir_tot,
                 'professor': nomProfessor,
                 'altres_moments': altres_moments,
                 } ,
                context_instance=RequestContext(request))


#------------------------------------------------------------------------------------------


#http://streamhacker.com/2010/03/01/django-model-formsets/    
@login_required
@group_required(['professors'])
def passaLlista( request, pk ):
    credentials = getImpersonateUser(request)
    (user, l4) = credentials

    #prefixes:
    #https://docs.djangoproject.com/en/dev/ref/forms/api/#prefixes-for-forms    
    formset = []
    impartir = Impartir.objects.get(pk=pk)

    #seg-------------------------------
    pertany_al_professor = user.pk in [ impartir.horari.professor.pk,       \
                                        impartir.professor_guardia.pk if impartir.professor_guardia else -1]
    if not ( l4 or pertany_al_professor):
        raise Http404()

    head=''
    info={}
    info['old'] = unicode(impartir)
    info['professor'] = unicode(impartir.horari.professor)
    info['dia_setmana'] = unicode(impartir.horari.dia_de_la_setmana)
    info['dia_complet'] = impartir.dia_impartir.strftime( "%d/%m/%Y")
    info['hora'] = unicode(impartir.horari.hora)
    info['assignatura'] = unicode(impartir.horari.assignatura)
    info['nom_aula'] = unicode(impartir.horari.nom_aula)
    info['grup'] = unicode(impartir.horari.grup)

    url_next = '/presencia/mostraImpartir/%d/%d/%d/'% (
                                    impartir.dia_impartir.year,
                                    impartir.dia_impartir.month,
                                    impartir.dia_impartir.day )




    #---------------------------------Passar llista -------------------------------
    if request.method == "POST":
        #un formulari per cada alumne de la llista
        totBe = True
        quelcomBe = False
        hiHaRetard = False
        form0 = forms.Form()
        formset.append( form0 )
        for control_a in impartir.controlassistencia_set.order_by( 'alumne__grup', 'alumne' ):
            control_a.currentUser = user
            form = ControlAssistenciaForm(
                                    request.POST,
                                    prefix=str( control_a.pk ),
                                    instance=control_a )
            control_a.professor = User2Professor(user)
            control_a.credentials = credentials
            justificat = False
            control_antic = ControlAssistencia.objects.get(id=control_a.id)
            control_aux = None
            if form.is_valid():
                if control_antic.estat is not None:
                    if control_antic.estat.codi_estat != "J":
                        control_aux = form.save()
                else:
                    control_aux = form.save()
                if control_aux is not None:
                    hiHaRetard |= control_aux.estat.codi_estat == "R"
                quelcomBe |= True
                justificat = True
            else:
                totBe = False
                #torno a posar el valor que hi havia ( per si el tutor l'ha justificat )
                errors_formulari = form._errors
                form=ControlAssistenciaForm(
                                    prefix=str( control_a.pk ),
                                    instance=ControlAssistencia.objects.get( id= control_a.pk)  )
                form._errors =  errors_formulari
            if justificat:
                form.fields['estat'].label = unicode(control_a.alumne) + ' (justificat)'
            else:
                form.fields['estat'].label = unicode(control_a.alumne)
            formset.append( form )

            #----------------CODI ANTIC ENDS----------------------

        if quelcomBe:
            impartir.dia_passa_llista = datetime.now()
            impartir.professor_passa_llista = User2Professor( request.user )
            impartir.currentUser = user

            try:
                impartir.save()

                #si hi ha retards, recordar que un retard provoca una incidència.
                if hiHaRetard:
                    url_incidencies = reverse( "aula__horari__posa_incidencia" , kwargs={'pk': pk})
                    msg =  u"""Has posat 'Retard', recorda que els retards provoquen incidències,
                    s'hauran generat automàticament, valora si cal 
                    <a href="{url_incidencies}">gestionar les faltes</a>.""".format( url_incidencies = url_incidencies)
                    messages.warning(request,  SafeText(msg ) )
                #LOGGING
                Accio.objects.create(
                        tipus = 'PL',
                        usuari = user,
                        l4 = l4,
                        impersonated_from = request.user if request.user != user else None,
                        text = u"""Passar llista: {0}.""".format( impartir )
                    )

                impartir_despres_de_passar_llista( impartir )
                if totBe:
                    return HttpResponseRedirect( url_next )
            except ValidationError, e:
                #Com que no és un formulari de model cal tractar a mà les incidències del save:
                for _, v in e.message_dict.items():
                    form0._errors.setdefault(NON_FIELD_ERRORS, []).extend(  v  )

    else:
        for control_a in impartir.controlassistencia_set.order_by( 'alumne' ):
            form=ControlAssistenciaForm(
                                    prefix=str( control_a.pk ),
                                    instance=control_a )
            avui_es_anivesari = ( control_a.alumne.data_neixement.month == impartir.dia_impartir.month and
                                  control_a.alumne.data_neixement.day == impartir.dia_impartir.day )


            form.fields['estat'].label = unicode( control_a.alumne ) + ( '(fa anys en aquesta data)' if avui_es_anivesari else '')
            if control_a.estat is not None:
                form.fields['estat'].label += (' (justificat)' if control_a.estat.codi_estat == "J" else '')


            formset.append( form )


    for form in formset:
        if hasattr(form, 'instance'):
            #0 = present #1 = Falta
            d = dades_dissociades(  form.instance )
            form.hora_anterior = ( 0 if d['assistenciaaHoraAnterior'] == 'Present' else
                                   1 if d['assistenciaaHoraAnterior'] == 'Absent' else None )
            prediccio, pct  = predictTreeModel( d)
            form.prediccio = ( 0 if prediccio == 'Present' else
                               1 if prediccio == 'Absent' else  None )

            form.avis = None
            form.avis_pct = ( u"{0:.2f}%".format( pct * 100  )  ) if pct else ''
            if pct < 0.8:
                form.bcolor = '#CC0000'
                form.avis = 'danger'
            elif pct < 0.9:
                form.bcolor = '#CC9900'
                form.avis = 'warning'
            else:
                form.bcolor = '#66FFCC'
                form.avis = 'info'


    return render_to_response(
                  "passaLlista.html",
                  {"formset": formset,
                   "id_impartir":  pk ,
                   "horariUrl": url_next,
                   "pot_marcar_sense_alumnes": not impartir.pot_no_tenir_alumnes ,
                   "impartir": impartir,
                   "head": head,
                   "info": info,
                   "feelLuckyEnabled": True,
                   },
                  context_instance=RequestContext(request))


#------------------------------------------------------------------------------------------

@login_required
@group_required(['direcció'])
def passaLlistaGrupDataTriaGrupDia(request):


    if request.method == "POST":
        frm = passaLlistaGrupDataForm( request.POST  )

        if frm.is_valid():
            return HttpResponseRedirect( '/presencia/passaLlistaGrupData/{0}/{1}/{2}/{3}/'.format(
                                                            frm.cleaned_data['grup'].pk,
                                                            frm.cleaned_data['dia'].day,
                                                            frm.cleaned_data['dia'].month,
                                                            frm.cleaned_data['dia'].year,
                                                                                                  ) )
    else:
        frm = passaLlistaGrupDataForm(  )

    return render_to_response(
                  "form.html",
                  {"form": frm,
                   "head": u"Passa llista a grup. Tria grup i data",
                   },
                  context_instance=RequestContext(request))




@login_required
@group_required(['direcció'])
def passaLlistaGrupData(request, grup, dia, mes, year):

    credentials = getImpersonateUser(request)
    (user, l4) = credentials

    data = date( year = int(year), month = int(mes), day = int(dia) )
    controls = ( ControlAssistencia.objects
                 .filter( alumne__grup = grup,  impartir__dia_impartir = data  )
                 .order_by( 'alumne', 'impartir__horari__hora__hora_inici' )
               )

    pendents = controls.filter(  estat__isnull = True )

    frmFact = modelformset_factory(
                    ControlAssistencia,
                    extra = 0,
                    fields = ( 'estat', ) ,
                    #widgets={'estat': RadioSelect( attrs={'class':'presenciaEstat'} ), }
                    )

    if request.method == "POST":
        formSet = frmFact( request.POST , queryset = controls  )

        for f in formSet.forms:
            f.instance.credentials = credentials

        if formSet.is_valid():
            formSet.save()
            return HttpResponseRedirect( '/' )
    else:
        formSet = frmFact( queryset = controls  )

    if bool(formSet.forms):
        f_prev = formSet.forms[0]
        for f in formSet:
            f.fields['estat'].widget = RadioSelect(
                                                choices = [x for x in f.fields['estat'].choices][1:],
                                                attrs={'class':'presenciaEstat'},
                                                 )

            f.fields['estat'].label = u'{0} {1}'.format(  f.instance.alumne, f.instance.impartir.horari.hora )
            if f.instance.alumne != f_prev.instance.alumne:
                f_prev = f
                f.formSetDelimited = True

    return render_to_response(
                  "passaLlistaGrup.html",
                  {"formset": formSet,
                   "head": u"Passa llista a grup",
                   'pendents': pendents,
                   },
                  context_instance=RequestContext(request))


#---


@login_required
@group_required(['professors'])
def marcarComHoraSenseAlumnes(request, pk):
    credentials = getImpersonateUser(request)
    (user, l4) = credentials

    head=u'Afegir alumnes a la llista'

    pk = int(pk)
    impartir = Impartir.objects.get ( pk = pk )

    #seg-------------------------------
    pertany_al_professor = user.pk in [ impartir.horari.professor.pk,   \
                                        impartir.professor_guardia.pk if impartir.professor_guardia else -1 ]
    if not ( l4 or pertany_al_professor):
        raise Http404()


    if request.method == "POST":
        form = marcarComHoraSenseAlumnesForm( request.POST  )
        if form.is_valid() and form.cleaned_data['marcar_com_hora_sense_alumnes']:
            expandir = form.cleaned_data['expandir_a_totes_les_meves_hores']

            from aula.apps.presencia.afegeixTreuAlumnesLlista import marcaSenseAlumnesThread
            afegeix=marcaSenseAlumnesThread(expandir = expandir, impartir=impartir )
            afegeix.start()

            #LOGGING
            Accio.objects.create(
                    tipus = 'LL',
                    usuari = user,
                    l4 = l4,
                    impersonated_from = request.user if request.user != user else None,
                    text = u"""Marcar classe sense alumnes {0}""".format(
                                impartir )
                        )

            import time
            while afegeix and not afegeix.primerDiaFet(): time.sleep(  0.5 )

            url_next = '/presencia/mostraImpartir/%d/%d/%d/'% (
                                    impartir.dia_impartir.year,
                                    impartir.dia_impartir.month,
                                    impartir.dia_impartir.day )

            return HttpResponseRedirect(url_next )
    else:
        form = marcarComHoraSenseAlumnesForm( initial= { 'marcar_com_hora_sense_alumnes': True, }  )

    return render_to_response(
                  "form.html",
                  {"form": form,
                   "head": head,
                   },
                  context_instance=RequestContext(request))


@login_required
@group_required(['professors'])
def afegeixAlumnesLlista(request, pk):
    credentials = getImpersonateUser(request)
    (user, l4) = credentials

    head=u'Afegir alumnes a la llista'

    pk = int(pk)
    impartir = Impartir.objects.get ( pk = pk )

    #seg-------------------------------
    pertany_al_professor = user.pk in [ impartir.horari.professor.pk,   \
                                        impartir.professor_guardia.pk if impartir.professor_guardia else -1 ]
    #if not ( l4 or pertany_al_professor):
    if not (l4):
        return render_to_response("no-access.html", context_instance=RequestContext(request))

    alumnes_pk = [ ca.alumne.pk for ca in impartir.controlassistencia_set.all()]
    #http://www.ibm.com/developerworks/opensource/library/os-django-models/index.html?S_TACT=105AGX44&S_CMP=EDU

    #un formulari per cada grup
    grups_a_mostrar = impartir.horari.grupsPotencials()

    formset = []
    if request.method == "POST":

        expandir = False
        alumnes = []

        totBe = True

        #
        #primer form: expandir
        #
        formExpandir=afegeixAlumnesLlistaExpandirForm( request.POST, prefix='tots')
        formset.append( formExpandir )
        if formExpandir.is_valid():
            expandir = formExpandir.cleaned_data['expandir_a_totes_les_meves_hores']
            matmulla = formExpandir.cleaned_data['matmulla']
        else:
            totBe = False
        #
        #altres forms: grups d'alumnes        
        #
        for grup in grups_a_mostrar:
            form=afegeixTreuAlumnesLlistaForm(
                                    request.POST,
                                    prefix=str( grup.pk ),
                                    queryset =  grup.alumne_set.exclude( pk__in = alumnes_pk )  ,
                                    etiqueta = unicode(grup)
                                     )
            formset.append( form )
            if form.is_valid():
                alumnes += form.cleaned_data['alumnes']
            else:
                totBe = False

        #TODO: afegir error a mà


        if totBe:
            from aula.apps.presencia.afegeixTreuAlumnesLlista import afegeixThread
            afegeix=afegeixThread(expandir = expandir, alumnes=alumnes, impartir=impartir, usuari = user, matmulla = matmulla)
            afegeix.start()

            #LOGGING
            Accio.objects.create(
                    tipus = 'LL',
                    usuari = user,
                    l4 = l4,
                    impersonated_from = request.user if request.user != user else None,
                    text = u"""Posar alumnes de la classe {0} (Forçat:{1}, Expandir:{2}): {3}""".format(
                                impartir,
                                u'Sí' if matmulla else 'No',
                                u'Sí' if expandir else 'No',
                                u', '.join( [ unicode(a) for a in alumnes  ] )
                                  )
                )

            #espero a que estigui fet el primer dia: abans de mostrar la pantalla de passar llista
            import time
            while afegeix and not afegeix.primerDiaFet(): time.sleep(  0.5 )

            return HttpResponseRedirect('/presencia/passaLlista/%s/'% pk )

    else:

        #primer form: expandir
        formExpandir=afegeixAlumnesLlistaExpandirForm(
                                            prefix='tots',
                                            initial={'expandir_a_totes_les_meves_hores':False})
        formset.append( formExpandir )

        #altres forms: grups d'alumnes        
        for grup in grups_a_mostrar:
            #http://www.ibm.com/developerworks/opensource/library/os-django-models/index.html?S_TACT=105AGX44&S_CMP=EDU
            form=afegeixTreuAlumnesLlistaForm(
                                    prefix=str( grup.pk ),
                                    queryset =  grup.alumne_set.exclude( pk__in = alumnes_pk )  ,
                                    etiqueta = unicode( grup )
                                     )
            formset.append( form )

    return render_to_response(
                  "formset.html",
                  {"formset": formset,
                   "head": head,
                   },
                  context_instance=RequestContext(request))

#------------------------------------------------------------------------------------------


@login_required
@group_required(['professors'])
def treuAlumnesLlista(request, pk):
    credentials = getImpersonateUser(request)
    (user, l4) = credentials

    head=u'Treure alumnes de la llista'

    pk = int(pk)
    impartir = Impartir.objects.get ( pk = pk )

    #seg-------------------------------
    pertany_al_professor = user.pk in [ impartir.horari.professor.pk,   \
                                       impartir.professor_guardia.pk if impartir.professor_guardia else -1]
    #if not ( l4 or pertany_al_professor):
    if not (l4):
        return render_to_response("no-access.html", context_instance=RequestContext(request))



    formset = []
    alumnes = []
    if request.method == "POST":

        expandir = False

        #
        #primer form: expandir
        #
        formExpandir=afegeixAlumnesLlistaExpandirForm( request.POST, prefix='tots')
        formExpandir.fields["matmulla"].help_text = u'''Marca aquesta opció per treure alumnes tot i que hagi passat llista (només els absents)'''
        formExpandir.fields["matmulla"].label = u'Força treure'


        #
        #altres forms: grups d'alumnes        
        #
        form=afegeixTreuAlumnesLlistaForm(
                                request.POST,
                                prefix=str( 'alumnes' ),
                                queryset =  Alumne.objects.filter( pk__in = [ ca.alumne.pk for ca in impartir.controlassistencia_set.all()  ] )   ,
                                etiqueta = 'Alumnes a treure:'
                                 )

        if form.is_valid() and formExpandir.is_valid():
            alumnes += form.cleaned_data['alumnes']
            expandir = formExpandir.cleaned_data['expandir_a_totes_les_meves_hores']
            matmulla = formExpandir.cleaned_data['matmulla']

            from aula.apps.presencia.afegeixTreuAlumnesLlista import treuThread
            treu=treuThread(expandir = expandir, alumnes=alumnes, impartir=impartir, matmulla=matmulla)
            treu.start()

            #LOGGING
            Accio.objects.create(
                    tipus = 'LL',
                    usuari = user,
                    l4 = l4,
                    impersonated_from = request.user if request.user != user else None,
                    text = u"""Treure alumnes de la classe {0} (Forçat:{1}, Expandir:{2}): {3}""".format(
                                impartir,
                                u'Sí' if matmulla else 'No',
                                u'Sí' if expandir else 'No',
                                u', '.join( [ unicode(a) for a in alumnes  ] )
                                  )
                )

            #espero que estigui fet el primer dia abans de mostrar la pantalla de passar llista
            import time
            while treu and not treu.primerDiaFet(): time.sleep(  0.5 )

            #afegeix.join()      #todo: missatge i redirecció!!!  
            #(' procés d'insertar alumnes engegat, pot trigar una estona. si no apareixen els alumnes prem el butó 'refrescar' del navegador' 
            #'/presencia/passaLlista/%s/' )

            return HttpResponseRedirect('/presencia/passaLlista/%s/'% pk )

    else:

        #primer form: expandir
        formExpandir=afegeixAlumnesLlistaExpandirForm(
                                            prefix='tots',
                                            initial={'expandir_a_totes_les_meves_hores':False})
        formExpandir.fields["matmulla"].help_text = u'''Marca aquesta opció per treure alumnes tot i que hagi passat llista (només els absents)'''
        formExpandir.fields["matmulla"].label = u'Força treure'

        formset.append( formExpandir )

        #altres forms: grups d'alumnes               
        form=afegeixTreuAlumnesLlistaForm(
                                prefix=str( 'alumnes' ),
                                queryset =  Alumne.objects.filter( pk__in = [ ca.alumne.pk for ca in impartir.controlassistencia_set.all()  ] )  ,
                                etiqueta = 'Alumnes a treure:'
                                 )
        formset.append( form )

    return render_to_response(
                  "formset.html",
                  {"formset": formset,
                   "head": head,
                   "missatge":u"""Atenció, no s'esborraran els alumnes que ja s'hagi passat llista o els que tinguin
                                   alguna incidència o expulsió""",
                   },
                  context_instance=RequestContext(request))


@login_required
@group_required(['professors'])
def afegeixGuardia(request, dia=None, mes=None, year=None):

    credentials = getImpersonateUser(request)
    (user, _ ) = credentials

    head=u'Fer guardia'

    url_next = '/presencia/mostraImpartir/%d/%d/%d/'% (
                                    int(year),
                                    int(mes),
                                    int(dia ) )
    if request.method == 'POST':
        form = afegeixGuardiaForm(request.POST)

        if form.is_valid():

            professor = form.cleaned_data['professor']
            franges = form.cleaned_data['franges']
            dia_impartir = date( int(year), int(mes), int(dia)  )
            professor_guardia = User2Professor( user )
            Impartir.objects.filter( dia_impartir = dia_impartir,
                                     horari__professor = professor,
                                     horari__hora__in = franges
                                    ).update( professor_guardia = professor_guardia  )

            return HttpResponseRedirect( url_next )


    else:
        form = afegeixGuardiaForm()
    return render_to_response(
                'form.html',
                {'form': form,
                 'head': head},
                context_instance=RequestContext(request))


@login_required
@group_required(['professors'])
def esborraGuardia(request, pk):
    credentials = getImpersonateUser(request)
    (user, l4) = credentials

    impartir = get_object_or_404( Impartir, pk = pk )

    url_next = '/presencia/mostraImpartir/%d/%d/%d/'% (
                                    impartir.dia_impartir.year,
                                    impartir.dia_impartir.month,
                                    impartir.dia_impartir.day )

    #seg-------------------------------
    pertany_al_professor = ( impartir.professor_guardia is not None) and (  user.pk == impartir.professor_guardia.pk )
    if not ( l4 or pertany_al_professor):
        return HttpResponseRedirect( url_next )

    if impartir.professor_guardia == User2Professor(user):
        impartir.professor_guardia = None
        impartir.currentUser = user
        impartir.save()

    return HttpResponseRedirect( url_next )


@login_required
@group_required(['professors'])
def calculadoraUnitatsFormatives(request):

    credentials = getImpersonateUser(request)
    (user, _ ) = credentials

    professor = User2Professor( user )

    head=u'Calculadora Unitats Formatives'
    infoForm = []

    grupsProfessor = Grup.objects.filter( horari__professor = professor  ).order_by('curs').distinct()
    assignaturesProfessor = Assignatura.objects.filter(
                                        horari__professor = professor,
                                        horari__grup__isnull = False ).order_by('curs','nom_assignatura').distinct()

    if request.method == 'POST':
        form = calculadoraUnitatsFormativesForm( request.POST, assignatures = assignaturesProfessor, grups = grupsProfessor )

        if form.is_valid():
            grup = form.cleaned_data['grup']
            assignatures = form.cleaned_data['assignatura']
            dataInici = form.cleaned_data['dataInici']
            hores = form.cleaned_data['hores']
            imparticionsAssignatura = Impartir.objects.filter( dia_impartir__gte = dataInici,
                                                               horari__assignatura__in = assignatures,
                                                               horari__grup = grup,
                                                               horari__professor = professor
                                                               ).order_by( 'dia_impartir', 'horari__hora'  )
            if imparticionsAssignatura.count() < hores:
                form._errors.setdefault(NON_FIELD_ERRORS, []).extend(
                           [ u'''A partir de la data {0} només hi ha {1} hores,
                                   comprova que has triat bé el curs.
                                   '''.format(
                                                dataInici,
                                                imparticionsAssignatura.count()
                                                ) ] )
            else:
                try:
                    darreraImparticio = imparticionsAssignatura[hores-1]
                    infoForm = [ ('Darrera classe', u'dia {0} a les {1}'.format( darreraImparticio.dia_impartir, darreraImparticio.horari.hora.hora_inici )), ]
                except Exception, e:
                    form._errors.setdefault(NON_FIELD_ERRORS, []).extend(  [e]  )



    else:
        form = calculadoraUnitatsFormativesForm( assignatures = assignaturesProfessor , grups = grupsProfessor)
    return render_to_response(
                'form.html',
                {'form': form,
                 'infoForm': infoForm,
                 'head': head},
                context_instance=RequestContext(request))


#------------------------------------------------------------------------------------------

@login_required
@group_required(['direcció'])
def alertaAssistencia(request):
    credentials = getImpersonateUser(request)
    (user, l4) = credentials

    head=u'''Alerta alumnes'''

    if request.method == 'POST':
        form = alertaAssistenciaForm(request.POST)
        if form.is_valid():
            report = alertaAssitenciaReport(
                            data_inici = form.cleaned_data['data_inici'],
                            data_fi = form.cleaned_data['data_fi'],
                            nivell = form.cleaned_data['nivell'],
                            tpc = form.cleaned_data['tpc']  ,
                            ordenacio = form.cleaned_data['ordenacio']  ,
                                             )

            return render_to_response(
                        'report.html',
                            {'report': report,
                             'head': 'Informació alumnes' ,
                            },
                            context_instance=RequestContext(request))

    else:
        form = alertaAssistenciaForm()

    return render_to_response(
            'alertaAbsentisme.html',
            {'head': head ,
             'form': form },
            context_instance=RequestContext(request))

@login_required
@group_required(['professors'])
def faltesAssistenciaEntreDates(request):

    credentials = getImpersonateUser(request)
    (user, _ ) = credentials

    professor = User2Professor( user )

    head=u'Calculadora %assistència entre Dates'
    infoForm = []

    grupsProfessor = Grup.objects.filter( horari__professor = professor  ).order_by('curs').distinct()
    assignaturesProfessor = Assignatura.objects.filter(
                                        horari__professor = professor,
                                        horari__grup__isnull = False ).order_by('curs','nom_assignatura').distinct()

    if request.method == 'POST':
        form = faltesAssistenciaEntreDatesForm( request.POST, assignatures = assignaturesProfessor, grups = grupsProfessor )

        if form.is_valid():

            report = faltesAssistenciaEntreDatesProfessorRpt(
                professor = professor,
                grup = form.cleaned_data['grup'],
                assignatures = form.cleaned_data['assignatura'],
                dataDesDe = form.cleaned_data['dataDesDe'],
                horaDesDe = form.cleaned_data['horaDesDe'],
                dataFinsA = form.cleaned_data['dataFinsA'],
                horaFinsA = form.cleaned_data['horaFinsA']
                                         )
            return render_to_response(
                    'reportTabs.html',
                        {'report': report,
                         'head': 'Informació alumnes' ,
                        },
                        context_instance=RequestContext(request))
#            except Exception, e:
#                form._errors.setdefault(NON_FIELD_ERRORS, []).extend(  [e]  )



    else:
        form = faltesAssistenciaEntreDatesForm( assignatures = assignaturesProfessor , grups = grupsProfessor)
    return render_to_response(
                'form.html',
                {'form': form,
                 #'infoForm': [],
                 'head': head},
                context_instance=RequestContext(request))
    


    
    
    

