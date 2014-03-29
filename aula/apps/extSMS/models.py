from django.contrib import messages
from django.db import models

# Create your models here.
from aula.apps.alumnes.models import Alumne
from aula.apps.horaris.models import FranjaHoraria

OPCIONS = (
    ('enviar','enviar'),
    ('anular','anular'),
    ('res','res')
)

class SMS(models.Model):
    alumne = models.ForeignKey(Alumne)
    dia = models.DateField(db_index=True)
    intents = models.IntegerField(default=0)
    enviat = models.BooleanField(default=False)
    estat = models.CharField(max_length=20, choices=OPCIONS, default='res')


    def __unicode__(self):
        return str(self.alumne) + " " + str(self.dia) + " " + \
               " Estat: " + self.estat + " Intents: " + str(self.intents) + \
               ". Ha estat enviat: " + str(self.enviat)




#Es possible que necessitem una altra taula amb totes les faltes
#Si no te SMS, creem SMS i la primera falta
# Si te SMS i la falta per aquella hora no existeix, creem falta
class FaltaSMS(models.Model):
    sms = models.ForeignKey(SMS)
    hora = models.ForeignKey(FranjaHoraria)

    def __unicode__(self):
        return str(self.sms.alumne) + " " + str(self.sms.dia) + " " + str(self.hora)