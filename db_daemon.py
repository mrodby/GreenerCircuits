#!/usr/bin/python3

# Component of Greener Circuits:
# Once an hour consolidate rows in the database into 1-minute averages
# and delete rows older than 30 days old.

import datetime
import time
import sys
import signal

import pymysql

import gclib

def Consolidate(cur, utcnow):
    # Get the timestamp of the most recent consolidation.
    # If none, use oldest timestamp in used table.
    # If none, use utcnow.
    consolidate_stamp = None
    cur.execute('SELECT consolidate_stamp FROM settings')
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
            consolidate_stamp = utcnow

    # Calculate start and end of consolidation period:
    # - Move back to start of hour.
    start_stamp = consolidate_stamp.replace(minute=0, second=0, microsecond=0)
    # - Set end_stamp to one our later.
    end_stamp = start_stamp + datetime.timedelta(hours=1)
    # - If end_stamp is not earlier than 1 minute ago, don't do anything.
    if end_stamp >= utcnow - datetime.timedelta(minutes=1):
        return end_stamp

    print('Consolidating from '
          + start_stamp.isoformat()[:19] + ' to '
          + end_stamp.isoformat()[:19])
    sys.stdout.flush()
    start = datetime.datetime.utcnow()

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
    print('Done consolidating,',
          (datetime.datetime.utcnow() - start).total_seconds(), 'seconds')
    sys.stdout.flush()

    # Update consolidate_stamp in settings.
    cur.execute('UPDATE settings SET consolidate_stamp="'
                + end_stamp.isoformat() + '"')
    return end_stamp

def Cull(cur, end_stamp):
    cur.execute('SELECT history_days FROM settings')
    row = cur.fetchone()
    if row is None:
        days = 0
    else:
        days = row[0]
    if days is None:
        days = 0
    if days != 0:
        start = datetime.datetime.utcnow()
        cull_start = end_stamp - datetime.timedelta(days=days)
        print('Culling records before', cull_start.isoformat())
        sql = ('DELETE FROM used WHERE stamp < "' + cull_start.isoformat() + '"')
        cur.execute(sql)
        print('Done culling,',
              (datetime.datetime.utcnow() - start).total_seconds(), 'seconds')
        sys.stdout.flush()

def Terminate(signum, frame):
    gclib.Log('***** Stopping Greener Circuits Database Daemon *****')
    sys.exit()


gclib.Log('***** Starting Greener Circuits Database Daemon *****')

# Set terminate handler
signal.signal(signal.SIGTERM, Terminate)
signal.signal(signal.SIGINT, Terminate)

# Connect to database.
db = gclib.ConnectDB()

# Start main loop.
while True:

    utcnow = datetime.datetime.utcnow()

    # Get database cursor.
    cur = db.cursor()

    # Start a transaction to ensure nobody else sees inconsistent data.
    cur.execute('START TRANSACTION')

    # Perform consolidation.
    end_stamp = Consolidate(cur, utcnow)

    # Once an hour delete rows older than number of days specified in settings.
    if utcnow.minute == 0:
        Cull(cur, end_stamp)

    # Done with this pass - close and commit.
    cur.execute('COMMIT')

    cur.close()
    db.commit()

    # Only do this loop once each minute.
    time.sleep(60)

