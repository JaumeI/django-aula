# This Python file uses the following encoding: utf-8
from aula.utils import tools
from aula.apps.alumnes.models import Alumne
from django.db.models.aggregates import Count
from django.db.models import Q
from itertools import chain
from aula.apps.presencia.models import ControlAssistencia

def alertaAssitenciaReport( data_inici, data_fi, nivell, tpc , ordenacio ):
    report = []

    
    taula = tools.classebuida()
    
    taula.titol = tools.classebuida()
    taula.titol.contingut = u'Ranking absència alumnes nivell {0}'.format( nivell )
    taula.capceleres = []
    taula.recompte = dict()
    
    capcelera = tools.classebuida()
    capcelera.amplade = 300
    capcelera.contingut = u'Alumne'
    taula.capceleres.append( capcelera )

    capcelera = tools.classebuida()
    capcelera.amplade = 70
    capcelera.contingut = u'hores absent no justificat'
    taula.capceleres.append( capcelera )

    capcelera = tools.classebuida()
    capcelera.amplade = 70
    capcelera.contingut = u'hores docència'
    taula.capceleres.append( capcelera )

    capcelera = tools.classebuida()
    capcelera.amplade = 100
    capcelera.contingut = u'%absència no justificada (absènc.no.justif./docència)'
    taula.capceleres.append( capcelera )

    capcelera = tools.classebuida()
    capcelera.amplade = 70
    capcelera.contingut = u'hores present'
    taula.capceleres.append( capcelera )

    capcelera = tools.classebuida()
    capcelera.amplade = 70
    capcelera.contingut = u'hores absènc. justif.'
    taula.capceleres.append( capcelera )

    capcelera = tools.classebuida()
    capcelera.amplade = 70
    capcelera.contingut = u'% assistència'
    taula.capceleres.append( capcelera )


    taula.fileres = []

    q_alumnes = Alumne.objects.filter( grup__curs__nivell = nivell )

    q_data_inici = Q( impartir__dia_impartir__gte = data_inici  )
    q_data_fi = Q( impartir__dia_impartir__lte = data_fi  )
    q_filtre = q_data_inici & q_data_fi
    q_controls = ControlAssistencia.objects.filter( alumne__in = q_alumnes ).filter( q_filtre )

    # 30/11/2016 - Afegit el Q(estat__codi_estat__isnull=True) per tal de retornar també aquelles assistencies sense passar llista
    q_p = q_controls.filter( Q(estat__codi_estat__in = ('P','R' )) | Q(estat__codi_estat__isnull=True) ).order_by().values_list( 'id','alumne__id' ).distinct()
    q_j = q_controls.filter( estat__codi_estat = 'J' ).order_by().values_list( 'id','alumne__id' ).distinct()
    q_f = q_controls.filter( estat__codi_estat = 'F' ).order_by().values_list( 'id','alumne__id' ).distinct()

    from itertools import groupby
    dict_p = {}
    data = sorted(q_p, key=lambda x: x[1])
    for k, g in groupby( data, lambda x: x[1] ):
        dict_p[k] = len( list(g) )

    dict_j = {}
    data = sorted(q_j, key=lambda x: x[1])
    for k, g in groupby( data, lambda x: x[1] ):
        dict_j[k] = len( list(g) )

    dict_f = {}
    data = sorted(q_f, key=lambda x: x[1])
    for k, g in groupby( data, lambda x: x[1] ):
        dict_f[k] = len( list(g) )



    alumnes = []
    for alumne in q_alumnes.select_related( 'grup', 'grup__curs' ).order_by().distinct():
        alumne.p = dict_p.get( alumne.id, 0)
        alumne.j = dict_j.get( alumne.id, 0)
        alumne.f = dict_f.get( alumne.id, 0)
        alumne.ca = alumne.p + alumne.j + alumne.f or 0.0
        alumne.tpc = ( float( alumne.f ) / float( alumne.ca ) ) * 100.0 if alumne.ca > 0 else 0
        alumne.tpc_assist =  ( float( alumne.p )  / float( alumne.ca ) ) * 100.0 if alumne.ca > 0 else 0

        if alumne.grup.curs.nom_curs_complert in taula.recompte:
            taula.recompte[alumne.grup.curs.nom_curs_complert]['total'] += 1
        else:
            taula.recompte[alumne.grup.curs.nom_curs_complert] = {
                'total' : 1,
                'total_tpc' : 0,
                'percent' : 0
            }
            print taula.recompte[alumne.grup.curs.nom_curs_complert]

        if alumne.tpc > tpc:
            taula.recompte[alumne.grup.curs.nom_curs_complert]['total_tpc'] += 1


        alumnes.append(alumne)
    #----------------------
    #choices = ( ('a', u'Nom alumne',), ('ca', u'Curs i alumne',),('n',u'Per % Assistència',), ('cn',u'Per Curs i % Assistència',),
    order_a = lambda a: ( a.cognoms,  a.nom)
    order_ca = lambda a: ( a.grup.curs.nom_curs, a.grup.nom_grup, a.cognoms, a.nom )
    order_n = lambda a: ( -1 * a.tpc, -1 * a.f )
    order_cn = lambda a: ( a.grup.curs.nom_curs, a.grup.nom_grup  , -1 * a.tpc)
    order = order_ca if ordenacio == 'ca' else order_n if ordenacio == 'n' else order_cn if ordenacio == 'cn' else order_a

    for rcurs, robject in taula.recompte.items():
        robject['percent'] = (float(robject['total_tpc']) / float(robject['total'])) * 100

    
    for alumne in  sorted( [ a for a in alumnes if a.tpc > tpc ] , key=order  ):   
                
        filera = []
        
        #-nom--------------------------------------------
        camp = tools.classebuida()
        camp.enllac = '/tutoria/detallTutoriaAlumne/{0}/all'.format(alumne.pk )
        camp.contingut = unicode(alumne) + ' (' + unicode(alumne.grup) + ')'
        filera.append(camp)

        #-docència--------------------------------------------
        camp = tools.classebuida()
        camp.contingut = unicode(alumne.f) 
        filera.append(camp)

        #-present--------------------------------------------
        camp = tools.classebuida()
        camp.contingut = unicode(alumne.ca) 
        filera.append(camp)

        #-%--------------------------------------------
        camp = tools.classebuida()
        camp.contingut =u'{0:.2f}%'.format(alumne.tpc ) 
        filera.append(camp)
        
        #-absent--------------------------------------------
        camp = tools.classebuida()
        camp.contingut = unicode(alumne.p) 
        filera.append(camp)

        #-justif--------------------------------------------
        camp = tools.classebuida()
        camp.contingut = unicode(alumne.j) 
        filera.append(camp)

        #-assist--------------------------------------------
        camp = tools.classebuida()
        camp.contingut = u'{0:.2f}%'.format(alumne.tpc_assist) 
        filera.append(camp)



        taula.fileres.append( filera )

    report.append(taula)

    return report