import pymysql
import datetime
import time
import sys

def gcBaseURL():
    # Note: Set this to an appropriate value
    return 'rodby.org'

def connect_db():
    # Connect to database.
    # Note: Set these to appropriate values
    db = pymysql.connect(db='mrodby_GC',
                         read_default_file='/home/mrodby/.my.cnf.rodby.org',
                         connect_timeout=20,
                         read_timeout=20,
                         write_timeout=20)
    return db

def get_time_zone():
    while True:
        localnow = datetime.datetime.now().replace(microsecond=0)
        utcnow = datetime.datetime.utcnow().replace(microsecond=0)
        if localnow.second == utcnow.second:
            break
    return localnow - utcnow

def sync_secs(secs):
    while True:
        utcnow = datetime.datetime.utcnow().replace(microsecond=0)
        if utcnow.timestamp() % secs == 0:
            break
        time.sleep(0.5)
    return utcnow

def log(message, stamp=None):
    if stamp is None:
        stamp = datetime.datetime.utcnow()
    print(stamp.isoformat()[:19], message)
    sys.stdout.flush()

