# This Python file uses the following encoding: utf-8
from aula.utils import tools
from aula.apps.alumnes.models import Alumne
from django.db.models.aggregates import Count
from django.db.models import Q
from itertools import chain

def alertaAssitenciaReport( data_inici, data_fi, nivell, tpc , ordenacio ):
    report = []

    
    taula = tools.classebuida()
    
    taula.titol = tools.classebuida()
    taula.titol.contingut = u'Ranking absència alumnes nivell {0}'.format( nivell )
    taula.capceleres = []
    
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
    

    q_nivell = Q( grup__curs__nivell = nivell )
    q_data_inici = Q(  controlassistencia__impartir__dia_impartir__gte = data_inici  )
    q_data_fi = Q(  controlassistencia__impartir__dia_impartir__lte = data_fi  )
    q_filte = q_nivell & q_data_inici & q_data_fi
    q_alumnes = Alumne.objects.filter( q_filte )

    q_p = q_alumnes.filter( controlassistencia__estat__codi_estat__in = ('P','R' ) ).order_by().distinct().annotate( x=Count('controlassistencia__estat') ).values_list( 'id', 'x' )
    q_j = q_alumnes.filter( controlassistencia__estat__codi_estat = 'J' ).order_by().distinct().annotate( x=Count('controlassistencia__estat') ).order_by().distinct().values_list( 'id', 'x' )
    q_f = q_alumnes.filter( controlassistencia__estat__codi_estat = 'F' ).order_by().distinct().annotate( x=Count('controlassistencia__estat') ).values_list( 'id', 'x' )
    
    dict_p, dict_j, dict_f = dict( q_p ), dict( q_j ), dict( q_f )
    
    #ajuntar dades diferents fonts
    alumnes = []
    for alumne in q_alumnes.select_related( 'grup', 'grup__curs' ).order_by().distinct():
        alumne.p = dict_p.get( alumne.id, 0)
        alumne.j = dict_j.get( alumne.id, 0)
        alumne.f = dict_f.get( alumne.id, 0)
        alumne.ca = alumne.p + alumne.j + alumne.f or 0.0
        alumne.tpc = ( float( alumne.f ) / float( alumne.ca ) ) * 100.0 if alumne.ca > 0 else 0
        alumne.tpc_assist =  ( float( alumne.p )  / float( alumne.ca ) ) * 100.0 if alumne.ca > 0 else 0
        alumnes.append(alumne)
    #----------------------
    #choices = ( ('a', u'Nom alumne',), ('ca', u'Curs i alumne',),('n',u'Per % Assistència',), ('cn',u'Per Curs i % Assistència',),
    order_a = lambda a: ( a.cognoms,  a.nom)
    order_ca = lambda a: ( a.grup.curs.nom_curs, a.grup.nom_grup, a.cognoms, a.nom )
    order_n = lambda a: ( -1 * a.tpc, -1 * a.f )
    order_cn = lambda a: ( a.grup.curs.nom_curs, a.grup.nom_grup  , -1 * a.tpc)
    order = order_ca if ordenacio == 'ca' else order_n if ordenacio == 'n' else order_cn if ordenacio == 'cn' else order_a
    
    
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