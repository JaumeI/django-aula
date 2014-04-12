# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.forms.models import modelformset_factory
from django.template import RequestContext
from django.db.models import Q

from aula.utils.tools import getImpersonateUser
from models import SMS
from forms import smsForm
from aula.utils.decorators import group_required


@login_required
@group_required(['consergeria'])
def llistaSMS(request):

    credentials = getImpersonateUser(request)
    (user, l4 ) = credentials

    #TODO:
    # Cal fer un cron::
    #   Cada dia a les 00:00 tots els anulats: enviat = True
    #Treballar amb multiples formularis
    SmsFormset = modelformset_factory(SMS, form=smsForm, extra = 0)
    if request.method == 'POST':
        formset = SmsFormset(request.POST)
        if formset.is_valid():
            formset.save()

    formset = SmsFormset(queryset=SMS.objects.filter(~Q(estat='enviar'), enviat=False).order_by('dia', 'alumne__grup__curs', 'alumne__grup__nom_grup'))

    return render_to_response('mostraSMS.html', {'formset': formset, 'head': 'Envia SMS'}, context_instance=RequestContext(request))



def enviaSMS(request):
    username = 'jaumei@gmail.com'
    hash = 'antonio'
    numbers = ('34691250084')
    sender = 'ATAPIS'
    message = 'El seu fill ha faltat el dia 14 de abril'
    test_flag = 0
    values = {'test'    : test_flag,
          'uname'   : username,
          'hash'    : hash,
          'message' : message,
          'from'    : sender,
          'selectednums' : numbers }

    url = 'http://www.txtlocal.com/sendsmspost.php'

    # postdata = urllib.urlencode(values)
    # req = urllib2.Request(url, postdata)

    print 'Attempt to send SMS ...'
    # try:
    #     response = urllib2.urlopen(req)
    #     response_url = response.geturl()
    #     if response_url==url:
    #         print 'SMS sent!'
    # except urllib2.URLError, e:
    #     print 'Send failed!'
    #     print e.reason
    print hash
    return llistaSMS(request)

