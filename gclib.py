'''Greener Circuits library routines'''

import datetime
import time
import sys
import pymysql
import pymysql.constants

def gc_host():
    '''Return host name'''
    return 'rodby.org'

def connect_db(database):
    '''Connect to database'''
    return pymysql.connect(db=database,
                           read_default_file='/home/mrodby/.my.cnf',
                           connect_timeout=30,
                           read_timeout=30,
                           write_timeout=30,
                           client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS)

def get_time_zone():
    '''Return time zone of local machine'''

    # TODO: Get directly from tzinfo
    while True:
        localnow = datetime.datetime.now().replace(microsecond=0)
        utcnow = datetime.datetime.utcnow().replace(microsecond=0)
        if localnow.second == utcnow.second:
            break
    return localnow - utcnow

def sync_secs(secs):
    '''Wait until a multiple of secs seconds'''

    # TODO: Calculate sleep interval rather than polling
    while True:
        utcnow = datetime.datetime.utcnow().replace(microsecond=0)
        if utcnow.timestamp() % secs == 0:
            break
        time.sleep(0.5)
    return utcnow

def log(message, stamp=None):
    '''Log message with optional external timestamp'''

    # TODO: Implement log with standard Python logger
    if stamp is None:
        stamp = datetime.datetime.utcnow()
    print(stamp.isoformat()[:19], message)
    sys.stdout.flush()
