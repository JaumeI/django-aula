#!/usr/bin/python
import urllib
import urllib2
import MySQLdb
import time
from datetime import datetime
print "Entro al sleep: " + str(datetime.now())
time.sleep(30) #Aixo a 30 despres ehh
print "Surto dl sleep: " + str(datetime.now())
db = MySQLdb.connect(
    host="localhost",
    user="userdjangoaula",
    passwd="i",
    db="djangoaula"
    )

#configuracio de txtlocal
username = 'jaumei@gmail.com'
hash = '1653ccf5b03b41d6f98bc5ebd8b77b1e0201417b'
test_flag = 1 #Canviar per enviar! 1 == no enviar 0 == enviar
sender = 'ATAPIS'

cur = db.cursor()

cur.execute("SELECT * FROM extsms_SMS WHERE enviat = 0 AND estat = 'enviar' AND telefon <> 'CAP'")

for sms in cur:
    cur2 = db.cursor()
    cur2.execute("SELECT telefon FROM extsms_telefonsms WHERE id = "+sms[4]+";")
    telf = cur2.fetchone()[0]
    dia = str(sms[2].day) + "/" + str(sms[2].month)
    textbase = "Us informem que el/la vostre/a fill/a ha faltat a classe el dia "+dia+". Per qualsevol dubte truqueu a l\'institut"


    #Comensa la party hard amb dj TXTLOCAL
    numbers = ("+34"+telf)
    message = textbase

    values = {'test'    : test_flag,
          'uname'   : username,
          'hash'    : hash,
          'message' : message,
          'from'    : sender,
          'selectednums' : numbers }

    url = 'http://www.txtlocal.com/sendsmspost.php'

    postdata = urllib.urlencode(values)
    req = urllib2.Request(url, postdata)

    print 'Attempt to send SMS ...'
    try:
        cur3 = db.cursor()
        response = urllib2.urlopen(req)
        response_url = response.geturl()
        if response_url==url:
            print 'SMS sent!'
            cur3.execute("UPDATE extsms_sms SET enviat = 1 WHERE id =  "+str(sms[0])+";")
            db.commit()
            #TODO:
            # Canviar 'enviat' de 0 a 1 per marcar-lo com enviat
    except urllib2.URLError, e:
        cur3.execute("UPDATE extsms_sms SET intents = "+str(sms[3]+1)+", estat = 'res' WHERE id = "+str(sms[0])+";")
        db.commit()
        print 'Send failed!'
        print e.reason

print "Fi del script chupiguay"