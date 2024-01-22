'''Greener Circuits library routines'''

from datetime import datetime, timezone
import time
import sys


def gc_host():
    '''Return host name'''

    return 'rodby.org'


def sync_secs(secs):
    '''Wait until time is a multiple of secs seconds'''

    utcnow = datetime.now()
    microsecond = utcnow.microsecond
    utcnow = utcnow.replace(microsecond=0)  # Truncate to even second
    timestamp = utcnow.timestamp()
    sleep_secs = secs - timestamp % secs - microsecond / 1000000
    time.sleep(sleep_secs)
    return datetime.now(timezone.utc).replace(microsecond=0)


def log(message, stamp=None):
    '''Log message with optional external timestamp'''

    # TODO: Implement log with standard Python logger
    if stamp is None:
        stamp = datetime.now(timezone.utc)
    print(stamp.isoformat()[:19], message)
    sys.stdout.flush()
