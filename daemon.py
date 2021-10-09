#!/usr/bin/python3
'''
Component of Greener Circuits:
Once per hour consolidate rows in the database into 1-minute averages
and delete rows older than 30 days old.
'''

from datetime import datetime, timedelta
import time
import sys
import signal
import traceback

from gcdatabase import GCDatabase
import gclib

def consolidate(gc_database, utcnow):
    '''Get the timestamp of the most recent consolidation.
    If none, use oldest timestamp in used table.
    If none, use utcnow.
    '''

    consolidate_stamp = gc_database.consolidate_stamp

    # If we've never consolidated before, set consolidate_stamp to an appropriate value
    if consolidate_stamp is None:
        consolidate_stamp = gc_database.get_min_used_stamp()
        if consolidate_stamp is None:
            consolidate_stamp = utcnow

    # Calculate start and end of consolidation period:
    # - Set start_stamp to start of hour
    start_stamp = consolidate_stamp.replace(minute=0, second=0, microsecond=0)
    # - Set end_stamp to one hour later
    end_stamp = start_stamp + timedelta(hours=1)
    # - If end_stamp is not earlier than 1 minute ago, don't do anything
    if end_stamp >= utcnow - timedelta(minutes=1):
        return end_stamp

    # Perform consolidation
    print('Consolidating from', start_stamp.isoformat()[:19], 'to', end_stamp.isoformat()[:19])
    sys.stdout.flush()
    gc_database.consolidate(start_stamp, end_stamp)

    return end_stamp


def terminated(_signum, _frame):
    '''Called when the program is terminated'''
    gclib.log('***** Stopping Greener Circuits Database Daemon *****')
    sys.exit()


def main():
    '''Main function'''

    gclib.log('***** Starting Greener Circuits Database Daemon *****')

    # Set terminate handler
    signal.signal(signal.SIGTERM, terminated)
    signal.signal(signal.SIGINT, terminated)

    gc_database = GCDatabase()

    while True:

        utcnow = datetime.utcnow().replace(microsecond=0)

        try:
            # Log update time
            gclib.log('')

            # Perform consolidation
            end_stamp = consolidate(gc_database, utcnow)

            # Once an hour delete rows older than number of days specified in settings
            if utcnow.minute == 0:
                gc_database.cull(end_stamp)

        except:     #pylint: disable=bare-except
            traceback.print_exc(file=sys.stdout)

        # Only do this loop about once each minute, but no need to sync with a minute boundary
        time.sleep(60)


if __name__ == '__main__':
    main()
