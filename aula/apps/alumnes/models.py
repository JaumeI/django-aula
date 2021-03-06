# This Python file uses the following encoding: utf-8
from aula.apps.alumnes.abstract_models import AbstractNivell, AbstractCurs,\
    AbstractGrup, AbstractAlumne

class Nivell(AbstractNivell):
    pass

class Curs(AbstractCurs):
    pass

class Grup(AbstractGrup):
    pass
    
class Alumne(AbstractAlumne):
    pass

# ----------------------------- B U S I N E S S       R U L E S ------------------------------------ #
from django.db.models.signals import post_save  #, pre_save, pre_delete

from aula.apps.alumnes.business_rules.alumne import alumne_post_save
post_save.connect(alumne_post_save, sender = Alumne )
#for customising replace by:
#from customising.business_rules.alumne import alumne_post_save
#post_save.connect(alumne_post_save, sender = Alumne )

