import pymysql
import datetime
import time
import sys

def GcIP():
    return '66.75.74.92'

def ConnectDB():
    # Connect to database.
    db = pymysql.connect(host='localhost',
                         user='eMonitor',
#                         passwd='xxxxxxxx', - will be filled in from .my.cnf
                         db='eMonitor',
                         read_default_file='/home/mrodby/.my.cnf')
    return db

def GetTimeZone():
    while True:
        localnow = datetime.datetime.now().replace(microsecond=0)
        utcnow = datetime.datetime.utcnow().replace(microsecond=0)
        if localnow.second == utcnow.second:
            break
    return localnow - utcnow

def SyncSecs(secs):
    while True:
        utcnow = datetime.datetime.utcnow().replace(microsecond=0)
        if utcnow.timestamp() % secs == 0:
            break
        time.sleep(0.5)
    return utcnow

def Log(message, stamp=None):
    if stamp is None:
        stamp = datetime.datetime.utcnow()
    print(stamp.isoformat()[:19], message)
    sys.stdout.flush()

