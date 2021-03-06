# This Python file uses the following encoding: utf-8
from django.utils.datetime_safe import datetime
import datetime as dt
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


def clean_sortida( instance ):
    
    ( user, l4)  = instance.credentials if hasattr( instance, 'credentials') else (None,None,)

    instance.instanceDB = None   #Estat a la base de dades
    if instance.pk:    
        instance.instanceDB = instance.__class__.objects.get( pk = instance.pk )
    
    errors = []
    
    #si passem a proposat
    if instance.estat in (  'P', 'R', 'G', ):
        if ( instance.data_inici < dt.date.today() or
             instance.data_fi < instance.data_inici 
             ):
            errors.append( u"Comprova les dates i franges de la sortida" )

    
    #si passem a revisada 
    if instance.estat in ( 'R', ):
        
        if not User.objects.filter( pk=user.pk, groups__name = 'sortides').exists():
            errors.append( u"Només el coordinador de sortides pot Revisar Una Sortida" )
            
        if not bool(instance.instanceDB) or instance.instanceDB.estat not in [ 'P', 'R' ]:
            errors.append( u"Només es pot Revisar una sortida ja Proposada" )

        if bool(instance.instanceDB) and instance.instanceDB.estat in [ 'G' ]:             
            errors.append( u"Aquesta sortida ja ha estat gestionada." )
        
        if not instance.esta_aprovada_pel_consell_escolar:
            errors.append( u"Cal que la Sortida estigui aprovada pel consell escolar per poder-la donar per revisada." )
    
    #si passem a gestionada pel cap d'estudis
    if instance.estat in ( 'G', ):

        if not User.objects.filter( pk=user.pk, groups__name = 'direcció').exists():
            errors.append( u"Només el Direcció pot Gestionar una Sortida." )
                
        if not bool(instance.instanceDB) or instance.instanceDB.estat not in [ 'P', 'R' ]:
            errors.append( u"Només es pot Gestionar una Sortida Revisada" )
        
    
    if l4:
        pass
    elif bool(errors):
        raise ValidationError( errors  )
    



    