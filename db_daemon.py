#!/usr/bin/python3

# Component of Greener Circuits:
# Once an hour consolidate rows in the database into 1-minute averages
# and delete rows older than 30 days old.

import datetime
import time
import sys

import pymysql

print('***** Starting Greener Circuits Database Daemon *****')
sys.stdout.flush()

# Connect to database.
db = pymysql.connect(host='localhost',
                     user='eMonitor',
#                     passwd='xxxxxxxx', - will be filled in from .my.cnf
                     db='eMonitor',
                     read_default_file='/home/mrodby/.my.cnf')

# Start main loop.
while True:

    # Only do this loop once each minute.
    time.sleep(60)

    now = datetime.datetime.now()

    # Get database cursor.
    cur = db.cursor()

    # Get the timestamp of the most recent consolidation.
    # If none, use oldest timestamp in used table.
    # If none, use now.
    consolidate_stamp = None
    cur.execute('SELECT consolidate_stamp FROM settings');
    row = cur.fetchone()
    if row is None:
        cur.execute('INSERT INTO settings VALUES(NULL)')
    else:
        consolidate_stamp = row[0]
    if consolidate_stamp is None:
        cur.execute('SELECT MIN(stamp) FROM used')
        row = cur.fetchone()
        if row is not None:
            consolidate_stamp = row[0]
        if consolidate_stamp is None:
            consolidate_stamp = now  # TODO: change to oldest stamp in used

    # Calculate start and end of consolidation period:
    # - Move back to start of hour.
    start_stamp = consolidate_stamp.replace(minute=0, second=0, microsecond=0)
    # - Set end_stamp to one our later.
    end_stamp = start_stamp + datetime.timedelta(hours=1)
    # - If end_stamp is not earlier than 1 minute ago, don't do anything.
    if end_stamp >= now - datetime.timedelta(minutes=1):
      continue

    print('Consolidating from '
          + start_stamp.isoformat()[:19] + ' to '
          + end_stamp.isoformat()[:19])
    sys.stdout.flush()

    # Start a transaction to ensure nobody else sees inconsistent data.
    cur.execute('START TRANSACTION')

    # Consolidate rows from this time period into 1-minute intervals:
    # - Clear scratchpad table.
    cur.execute('DELETE FROM scratchpad')
    # - Consolidate appropriate rows into scratchpad table.
    sql = ('INSERT INTO scratchpad '
           'SELECT '
               'channum, '
               'AVG(watts) AS watts, '
               'FROM_UNIXTIME(UNIX_TIMESTAMP(stamp) DIV 60 * 60 ) AS stamp '
           'FROM used '
           'WHERE stamp >= "' + start_stamp.isoformat() + '" '
               'AND stamp < "' + end_stamp.isoformat() + '" '
           'GROUP BY channum, UNIX_TIMESTAMP(stamp) DIV 60')
    cur.execute(sql)
    # - Delete original rows.
    sql = ('DELETE FROM used '
           'WHERE stamp >= "' + start_stamp.isoformat()
           + '" AND stamp < "' + end_stamp.isoformat() + '" ')
    cur.execute(sql)
    # - Copy from scratchpad table to original table.
    cur.execute('INSERT INTO used SELECT * FROM scratchpad')

    # Update consolidate_stamp in settings.
    cur.execute('UPDATE settings SET consolidate_stamp="'
                + end_stamp.isoformat() + '"')

    # All done - commit transaction.
    cur.execute('COMMIT');

    print('Done:', now.isoformat()[:19])

    # Once an hour delete rows older than number of days specified in settings.
    cur.execute('SELECT history_days FROM settings');
    row = cur.fetchone()
    if row is None:
        days = 0
    else:
        days = row[0]
    if days is None:
        days = 0
    if days != 0:
        sql = ('DELETE FROM used WHERE stamp < DATE_ADD("'
               + end_stamp.isoformat() + '", INTERVAL -' + str(days) + ' DAY)')
        cur.execute(sql)

    # Done with this pass - close and commit.
    cur.close()
    db.commit() # TODO: is this necessary?

