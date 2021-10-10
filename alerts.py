#!/usr/bin/python3
'''
Component of Greener Circuits:
Once each minute check each entry in the alert table to see if its
conditions have been met.  When a condition is met (or when a
condition had previously been met but is now resolved), send an alert
via prowlapp.com.
'''

from datetime import datetime
import time
import sys
import signal
import traceback

import gclib
from gcdatabase import GCDatabase
import prowl

def channel_url(channum):
    '''Return URL for channel channum'''

    return 'http://' + gclib.gc_host() + '/power.php?channel=' + str(channum)


def new_alert(event, desc, prowlapp, info_url=None):
    '''Log event and notify Prowl, optionally include a URL for more info'''

    gclib.log(event + ' ' + desc)
    prowlapp.notify(event, desc, info_url)


def check_alert(gc_database, alert, prowlapp):
    '''Check this alert'''

    # Set msg_still to indicate current state and msg_newly to indicate a change
    if alert.greater:
        msg_still = 'above'
        msg_newly = 'fallen below'
    else:
        msg_still = 'below'
        msg_newly = 'risen above'

    # Only perform alert check if localtime is inside the time range
    localnow = datetime.now().time()
    if alert.end > alert.start: # Interval doesn't span midnight
        outside_interval = not alert.start <= localnow < alert.end
    else:   # Interval spans midnight or empty interval
        outside_interval = alert.end <= localnow < alert.start
    if outside_interval:
        if alert.alerted:
            name = gc_database.get_channel_name(alert.channum)
            message = name + '" still ' + msg_still + ' ' + str(alert.watts) + \
                ' watts and it is now outside the monitoring time - clearing alert'
            new_alert(message, 'power alert', prowlapp, channel_url(alert.channum))
            gc_database.set_alerted(alert.id, False)
        return

    # alert_triggered() returns 1 if triggered, 0 if not, -1 if no records in interval
    alert_triggered = gc_database.alert_triggered(alert)

    if alert_triggered == -1:
        # No records in interval, so don't issue alert
        return

    # If alert is newly triggered or newly cleared, send alert via prowlapp
    if alert_triggered != alert.alerted:
        name = gc_database.get_channel_name(alert.channum)
        if not alert.alerted:
            message = name + ' has been ' + msg_still + ' ' \
                       + str(alert.watts) + ' watts for more than ' \
                       + str(alert.minutes) + ' minutes'
            if alert.message:
                message += ': ' + alert.message
            new_alert(message, 'POWER ALERT', prowlapp, channel_url(alert.channum))
        else:
            message = (name + ' has ' + msg_newly + ' '
                       + str(alert.watts) + ' watts')
            if alert.message:
                message += ': ' + alert.message
            new_alert(message, 'power alert', prowlapp, channel_url(alert.channum))
        gc_database.set_alerted(alert.id, alert_triggered)


def terminated(_signum, _frame):
    '''Called when program terminates'''

    gclib.log('***** Stopping Greener Circuits Alerts *****')
    sys.exit()


def main():
    '''Main Greener Circuits Alerts function'''

    gclib.log('***** Starting Greener Circuits Alerts *****')

    # Set terminate handler
    signal.signal(signal.SIGTERM, terminated)
    signal.signal(signal.SIGINT, terminated)

    # Instantiate prowlapp.com interface object
    prowlapp = prowl.Prowl()

    # Create GCDatabase object to communicate with database
    gc_database = GCDatabase()

    # Main loop
    while True:
        # Check alerts once per minute
        gclib.sync_secs(60)

        try:
            # Log update time
            gclib.log('')

            # Verify database has been updated recently
            if gc_database.updating_changed():
                if gc_database.updating:
                    new_alert('***** updates resumed *****',
                        'Database updates have resumed', prowlapp)
                else:
                    new_alert('***** UPDATES STOPPED *****',
                        'Last database update more than 1 minute ago', prowlapp)

            if gc_database.updating:
                # Check each alert in the alert table
                alerts = gc_database.get_alerts()
                for alert in alerts:
                    check_alert(gc_database, alert, prowlapp)

        except:     #pylint: disable=bare-except
            traceback.print_exc(file=sys.stdout)

        time.sleep(2)  # Ensure we don't go through this loop multiple times per cycle


if __name__ == '__main__':
    main()
