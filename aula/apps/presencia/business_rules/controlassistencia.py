# This Python file uses the following encoding: utf-8
import datetime as dt
from datetime import timedelta
import re

from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db.models import get_model
from django.http import request
from aula.apps.extSMS.models import TelefonTutors

from aula.apps.usuaris.models import User2Professor, User2Professional
from aula.apps.tutoria.models import CartaAbsentisme
from aula.apps.incidencies.business_rules.incidencia import incidencia_despres_de_posar


#INSRM DEBUG:: Això es pel try catch

#-------------ControlAssistencia-------------------------------------------------------------      

def controlAssistencia_clean( instance ):

    (user, l4) = instance.credentials if hasattr(instance, 'credentials') else (None, None,)

    if l4: return

    isUpdate = instance.pk is not None #Si estem editant un control d'assistencia
    instance.instanceDB = None if not isUpdate else instance.__class__.objects.get( pk = instance.pk ) #Objecte de la base de dades si estem editant

    errors = {}

    tutors = [ tutor for tutor in instance.alumne.tutorsDeLAlumne() ]
    if user:
        instance.professor = User2Professor( user ) #Guardem l'usuari que esta fent els canvis
    else: #Si no hi ha usuari donem per suposat que es L4... (temporal)
        maybel4 = True

    #
    # Només es poden modificar assistències 
    #
    nMaxDies = 30*3
    if isUpdate and instance.impartir.dia_impartir < ( dt.date.today() - dt.timedelta( days = nMaxDies) ):
        errors.setdefault(NON_FIELD_ERRORS, []).append( u'''Aquest controll d'assistència és massa antic per ser modificat (Té més de {0} dies)'''.format(nMaxDies) )

    #todo: altres controls:
    daqui_2_hores = dt.datetime.now() + dt.timedelta( hours = 2)
    if isUpdate and instance.impartir.diaHora() > daqui_2_hores :
        errors.setdefault(NON_FIELD_ERRORS, []).append( u'''Encara no es pot entrar aquesta assistència 
                                    (Falta {0} per poder-ho fer )'''.format(
            instance.impartir.diaHora()  - daqui_2_hores ) )

    #Una falta justificada pel tutor no pot ser matxacada per un professor
    socTutor = hasattr(instance, 'professor') and instance.professor and instance.professor in tutors
    justificadaDB = instance.instanceDB and instance.instanceDB.estat and instance.instanceDB.estat.codi_estat.upper() == 'J'
    justificadaAra = instance.estat and instance.estat.codi_estat.upper() == 'J'
    posat_pel_tutor = instance.instanceDB and instance.instanceDB.professor and instance.instanceDB.professor in tutors

    if not socTutor and justificadaDB and posat_pel_tutor and not justificadaAra:
        errors.setdefault(NON_FIELD_ERRORS, []).append( u'''
                                  La falta d'en {0} no es pot modificar. El tutor Sr(a) {1} ha justificat la falta.  
                                                            '''.format(
            instance.alumne, instance.instanceDB.professor ) )

    #Una falta justificada per consergeria o administracio o direccio no pot ser matxacada per ningú que no siguin ells
    if maybel4:
        es_super = True
    else:
        es_super = user.groups.filter(name__in=['consergeria', ]) != None \
                   or user.groups.filter(name__in=['administradors', ]) != None \
                   or user.groups.filter(name__in=['direcció', ]) != None


    if not es_super and justificadaDB:
        errors.setdefault(NON_FIELD_ERRORS, []).append( u'''
                                  La falta d'en {0} no es pot modificar. Parla amb el/la cap d'estudis.
                                                            '''.format(instance.alumne))


    #No es poden justificar faltes si s'ha enviat una carta.
    if not justificadaDB and justificadaAra:
        data_control_mes_3 = instance.impartir.dia_impartir + timedelta( days = 3 )
        dins_ambit_carta = ( CartaAbsentisme
                             .objects
                             .exclude( carta_esborrada_moment__isnull = False )
                             .filter( alumne = instance.alumne,
                                      data_carta__gte = data_control_mes_3
        )
                             .exists()
        )
        if dins_ambit_carta:
            errors.setdefault(NON_FIELD_ERRORS, []).append( u'''
                                  La falta d'en {0} no es pot modificar. El tutor ha inclòs la falta en una Carta.  
                                                            '''.format(
                instance.alumne ) )

    #Només el tutor, el professor de guardia o el professor titular pot modificar un control d'assistència:
    if user:
        professors_habilitats = tutors
        if instance.professor: professors_habilitats.append( instance.professor.pk )
        if instance.impartir.horari.professor: professors_habilitats.append( instance.impartir.horari.professor.pk )
        if instance.impartir.professor_guardia: professors_habilitats.append( instance.impartir.professor_guardia.pk )

        #TODO: Falta mirar aixo
        # Si es direcció o consergeria OK
        # else ko
        es_conserge = user.groups.filter(name__in=['consergeria', ]) != None



        if user.pk not in professors_habilitats and not es_conserge and not es_admin and not es_direc:
            errors.setdefault(NON_FIELD_ERRORS, []).append( u'''Només el professor de l'assignatura, 
                                            el professor de guardia que ha passat llista o el tutor poden variar una assistència. 
                                                            ''' )

    if len( errors ) > 0:
        raise ValidationError(errors)

    #Justificada: si el tutor l'havia justificat deixo al tutor com el que ha desat la falta:
    if justificadaDB and posat_pel_tutor:
        instance.professor = instance.instanceDB.professor


def controlAssistencia_pre_delete( sender, instance, **kwargs):
    pass

def controlAssistencia_pre_save(sender, instance,  **kwargs):
    instance.clean()

def controlAssistencia_post_save(sender, instance, created, **kwargs):
    frase = u'Ha arribat tard a classe.'

    if instance.estat and instance.estat.codi_estat == 'R':
        Incidencia = get_model('incidencies','Incidencia')
        ja_hi_es = Incidencia.objects.filter(
            alumne = instance.alumne,
            control_assistencia = instance,
            descripcio_incidencia = frase,
            es_informativa = False ,).exists()

        if not ja_hi_es:
            try:
                i = Incidencia.objects.create(
                    professional = User2Professional( instance.professor ),
                    alumne = instance.alumne,
                    control_assistencia = instance,
                    descripcio_incidencia = frase,
                    es_informativa = False ,)
                incidencia_despres_de_posar( i )                                       #TODO: Passar-ho a post-save!!!!
            except:
                pass

    else:
        try:
            Incidencia.objects.filter(
                alumne = instance.alumne,
                control_assistencia = instance,
                descripcio_incidencia = frase,
                es_informativa = False ,).delete()
        except:
            pass

    #Executar això només si està activada l'app de extSMS



    # DAVID -- TODO -- 2.0 -- Ja no es creen telefons

    try:
        #Els SMS estàn activats
        SMS = get_model('extSMS', 'SMS')
        FaltaSMS = get_model('extSMS', 'FaltaSMS')
        #TelefonSMS = get_model('extSMS', 'TelefonSMS')

        sms = SMS.objects.filter(alumne = instance.alumne, dia = instance.impartir.dia_impartir)
        hora = instance.impartir.horari.hora
        falta = FaltaSMS.objects.filter(sms = sms, hora = hora)
        telefons = TelefonTutors.objects.filter(alumne=instance.alumne)
        camp_telefon = ""
        separator = ""
        for telf in telefons:
            camp_telefon += separator + "34"+telf.telefon
            separator = ","
        if instance.estat and instance.estat.codi_estat == 'F':
            if not sms.exists(): #Crear SMS nou
                if camp_telefon is not "":
                    sms = SMS.objects.create(alumne = instance.alumne,dia = instance.impartir.dia_impartir,telefon = camp_telefon)
                    sms.save()
                else:
                    print "No es crea el SMS perque no hi han telefons"
                # regex = re.compile("\d{9}\d*")
                #telefons = re.findall("\d{9}\d*", instance.alumne.telefons)

                # for telefon in telefons:
                #     tel = telefon[-9:]
                #     if tel[0] == '6' or tel[0] == '7':
                #         print tel
                #         TelefonSMS.objects.create(telefon = tel, sms = sms)
            else:
                sms = sms[0]

            if not falta.exists():
                falta = FaltaSMS.objects.create(sms = sms, hora = hora)
                falta.save()

        elif instance.estat:
            if falta.exists():
                falta.delete()
            faltes = FaltaSMS.objects.filter(sms = sms)
            if len(faltes) == 0:
                sms.delete()
    except TypeError as e:
        print "TypeError: " + e.message
        pass
    except:
        pass


 
