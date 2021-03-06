# This Python file uses the following encoding: utf-8

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

import collections

class AbstractMissatge(models.Model):

    data = models.DateTimeField( auto_now_add = True, db_index = True )
    remitent = models.ForeignKey( User, db_index = True )    
    text_missatge = models.TextField("Missatge", help_text=u"Escriu el missatge")
    enllac = models.URLField(blank = True)    
    class Meta:
        abstract = True
        verbose_name = u'Missatge'
        verbose_name_plural = u'Missatges'
    def __unicode__(self):
        return self.text_missatge
    
    def envia_a_usuari(self, usuari, importancia='IN'):
        self.desa()        
        self.destinatari_set.create( destinatari = usuari, importancia= importancia )

    def envia_a_grup(self, grup, importancia='IN'):
        self.desa()              
        for usuari in grup.user_set.all():
            self.destinatari_set.create( destinatari = usuari, importancia = importancia )

    def envia_a_tothom(self, importancia='IN'):
        self.desa()        
        for usuari in User.objects.all():
            self.destinatari_set.create( destinatari = usuari, importancia = importancia )
    
    def afegeix_error(self, liniaDetall):
        if liniaDetall:
            self.desa()        
            self.detallmissatge_set.create( detall = liniaDetall, tipus = 'E' )

    def afegeix_warning(self, liniaDetall):
        if liniaDetall:
            self.desa()        
            self.detallmissatge_set.create( detall = liniaDetall, tipus = 'W' )

    def afegeix_info(self, liniaDetall):
        if liniaDetall:
            self.desa()        
            self.detallmissatge_set.create( detall = liniaDetall, tipus = 'I' )
        
    def afegeix_errors(self, liniesDetall):
        if isinstance(liniesDetall, collections.Iterable):
            self.desa()        
            for liniaDetall in liniesDetall:
                self.afegeix_error(liniaDetall)
            
    def afegeix_warnings(self, liniesDetall):
        if isinstance(liniesDetall, collections.Iterable):
            self.desa()        
            for liniaDetall in liniesDetall:
                self.afegeix_warning(liniaDetall)

    def afegeix_infos(self, liniesDetall):
        if isinstance(liniesDetall, collections.Iterable):
            self.desa()        
            for liniaDetall in liniesDetall:
                self.afegeix_info(liniaDetall)
    
    def errors(self):
        return self.detallmissatge_set.filter( tipus = 'E' )   

    def warnings(self):
        return self.detallmissatge_set.filter( tipus = 'W' )   

    def infos(self):
        return self.detallmissatge_set.filter( tipus = 'I' )   
    
    def desa(self):
        if not self.pk:
            self.save()
    

class AbstractDetallMissatge(models.Model):
    TIPUS_CHOICES = (
        ('E', 'Error'),
        ('W', 'Avís' ),
        ('I', 'Info' ),
                     )
    
    missatge = models.ForeignKey( 'missatgeria.Missatge' )   
    detall = models.TextField("detall")
    tipus = models.CharField(max_length=2, choices=TIPUS_CHOICES, default = 'I')
    class Meta:
        abstract = True
        verbose_name = u'Detall del missatge'
        verbose_name_plural = u'Detalls del missatge'
    def __unicode__(self):
        return self.detall


class AbstractDestinatari(models.Model):
    
    importancia_VI, importancia_IN, importancia_PI = 'VI', 'IN', 'PI'
    IMPORTANCIA_CHOICES = (
        (importancia_VI,'Molt important'),
        (importancia_IN,'Informatiu'),
        (importancia_PI,'Poc important'),
                           )
    missatge = models.ForeignKey( 'missatgeria.Missatge' )
    importancia = models.CharField(max_length=2, choices=IMPORTANCIA_CHOICES, default = 'IN')
    destinatari = models.ForeignKey( User, db_index = True )
    moment_lectura = models.DateTimeField( blank=True, null=True, db_index = True )
    followed = models.BooleanField( default = False )
    class Meta:
        abstract = True
        verbose_name = u'Lectura de missatge'
        verbose_name_plural = u'Lectures de missatges'
    def __unicode__(self):
        return 'Missatge llegit' if self.moment_lectura else 'Missatge no llegit'
    
    def llegit(self):
        return (self.moment_lectura != None)
    
    def llegitAraMateix(self):
        araMateix = False
        try:
            araMateix =                                                         \
                not self.moment_lectura or                                      \
                0 <= (datetime.now() - self.moment_lectura ).seconds <= 2
        except:
            araMateix = True
        return araMateix
    
    def inportanciaCSS(self):
        if self.importancia == self.importancia_VI:
            return 'danger'
        elif self.importancia == self.importancia_IN:
            return 'info'
        elif self.importancia == self.importancia_IN:
            return 'success'

