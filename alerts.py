#!/usr/bin/python3

# Component of Greener Circuits:
# Once each minute check each entry in the alerts table to see if its
# conditions have been met.  When a condition is met (or when a
# condition had previously been met but is now resolved), send an alert
# via prowlapp.com.

import datetime
import time
import sys
import signal

import gclib
import prowl

def ChannelURL(channum):
    return 'http://' + gclib.GcIP() + '/power.php?channel=' + str(channum)

def Alert(event, desc, info_url=None):
    print(event, desc)
    sys.stdout.flush()
    prowl.notify(event, desc, info_url)

def DatabaseUpdating(cur):
    global updating
    # If database has not been updated in the last 60 seconds, send alert.
    cur.execute('SELECT MAX(stamp) FROM used')
    row = cur.fetchone()
    stamp = row[0]
    if (utcnow - stamp).total_seconds() > 60:
        if updating:
            Alert('***** UPDATES STOPPED *****',
                  'Last database update more than 1 minute ago')
            updating = False
    else:
        if not updating:
            Alert('***** updates resumed *****',
                  'Database updates have resumed')
            updating = True
    return updating

def TestAlert(cur, row, localnow):
    id = row[0]
    channum = row[1]
    # Set "compare" to the opposite of the condition we are looking
    # for, since our trigger is zero occurrences of "compare" being
    # true and set msgzero and msgnonzero to appropriate values to
    # use in prowlapp messages.
    if row[2] == 1:
        compare = '<'
        msgzero = 'above'
        msgnonzero = 'fallen below'
    else:
        compare = '>'
        msgzero = 'below'
        msgnonzero = 'risen above'
    watts = row[3]
    minutes = row[4]
    # In the next 2 lines, the value comes from MySQL as datetime.timedelta
    # - convert to time by adding any date to it and calling time().
    start = (datetime.datetime.combine(localnow.date(), datetime.time())
             + row[5]).time()
    end = (datetime.datetime.combine(localnow.date(), datetime.time())
           + row[6]).time()
    message = row[7]
    if message != '':
        message = ' -- ' + message
    alerted = (row[8] != 0)

    localtime = (utcnow + timezone).time()
    # Only perform alert check if localtime is inside the time range.
    if ((end > start and (localtime < start or localtime >= end)) or
        (end < start and (localtime >= end and localtime < start))):
        if alerted:
            message = ('Circuit "' + name + '" is still ' + msgzero + ' '
                       + str(watts) + ' watts and it is now outside the '
                       'monitoring time - clearing alert')
            Alert('power alert', message, ChannelURL(channum))
            cur.execute('UPDATE alert SET alerted=0 WHERE id=' + str(id))
        return
    sql = ('SELECT COUNT(*) FROM used WHERE channum=' + str(channum) +\
           ' AND stamp >= DATE_ADD("' + utcnow.isoformat() + '", INTERVAL -'
               + str(minutes) + ' MINUTE)' +\
           ' AND watts ' + compare + str(watts))
    cur.execute(sql)
    countrow = cur.fetchone()
    # If all rows meet the criteria (i.e. no rows meet the
    # reverse of the criteria), the alert is active - check to see
    # if that condition has changed.
    if (countrow[0] == 0) != alerted:
        cur.execute('SELECT name FROM channel WHERE channum='
                    + str(channum))
        # This assumes channel exists. TODO: handle case where it does not
        name=cur.fetchone()[0]
        if not alerted:
            message = ('Circuit "' + name + '" has been ' + msgzero + ' '
                       + str(watts) + ' watts for more than '
                       + str(minutes) + ' minutes' + message)
            Alert('POWER ALERT', message, ChannelURL(channum))
            cur.execute('UPDATE alert SET alerted=1 WHERE id=' + str(id))
        else:
            message = ('Circuit "' + name + '" has ' + msgnonzero + ' '
                       + str(watts) + ' watts')
            Alert('power alert', message, ChannelURL(channum))
            cur.execute('UPDATE alert SET alerted=0 WHERE id=' + str(id))

def Terminate(signum, frame):
    gclib.Log('***** Stopping Greener Circuits Alerts *****')
    sys.stdout.flush()
    sys.exit()

gclib.Log('***** Starting Greener Circuits Alerts *****')
sys.stdout.flush()

# Set terminate handler
signal.signal(signal.SIGTERM, Terminate)
signal.signal(signal.SIGINT, Terminate)

# Connect to database.
db = gclib.ConnectDB()

# Instantiate prowlapp.com interface object.
prowl = prowl.Prowl()

# Global to issue only one alert when db updates stop or restart.
updating = True

# Get time zone.
timezone = gclib.GetTimeZone()

# Start main loop.
while True:
    # Wait until the start of a minute (only check alerts once per minute).
    utcnow = gclib.SyncSecs(60)
    localnow = utcnow + timezone

    # Call db.commit() to renew our view of the database.
    db.commit()

    # Get database cursor.
    cur = db.cursor()

    # Verify database is being updated.
    if DatabaseUpdating(cur):

        # Test each alert in the alert table.
        cur.execute('SELECT id, channum, greater, watts, minutes, start, '
                    'end, message, alerted from alert')
        for row in cur.fetchall():
            TestAlert(cur, row, localnow)

    # Done with this pass - close cursor.
    cur.close()

    # Print update time.
    gclib.Log('', utcnow)

    # Ensure this loop is not done more often than once per second.
    time.sleep(1)

