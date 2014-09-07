from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('aula.apps.extSMS.views',

    # DAVID -- TOTO -- 2.0 -- URL per la nova pantalla
   url(r'^genera-telefons$', 'generaTelefons' ,
       name="genera-telefons"),
   url(r'^$', 'llistaSMS' ,
       name="llista-sms"),

)

