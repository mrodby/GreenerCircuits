#!/usr/bin/python3

# Component of Greener Circuits:
# Once every 10 seconds retrieve web page(s) from each eMonitor, scrape
# current usage numbers from the page(s), and store them in the database.
# If too many read errors occur when retrieving data from an eMonitor,
# send an alert via prowlapp.com.

import requests
import datetime
import sys
import signal

from bs4 import BeautifulSoup

import gclib
import prowl

def Terminate(signum, frame):
    gclib.Log('***** Stopping Greener Circuits Database Update *****')
    sys.exit()

# globals
fails = []
max_fails = 90
inc = 10  # Read web page from each eMonitor IP every inc seconds (max 60).

gclib.Log('***** Starting Greener Circuits Database Update *****')

# Set terminate handler
signal.signal(signal.SIGTERM, Terminate)
signal.signal(signal.SIGINT, Terminate)

# Connect to database.
db = gclib.ConnectDB()

# Instantiate prowlapp.com interface object.
prowl = prowl.Prowl()

# Get IP addresses or hostnames from eMonitors file.
with open('eMonitors') as f:
    ips = f.read().splitlines()
for idx, ip in enumerate(ips):
    fails.append(0)

while True:
    # Update database every 10 seconds.
    utcnow = gclib.SyncSecs(10)

    # Get database cursor, start a transaction, and get current channel list.
    cur = db.cursor()
    cur.execute('START TRANSACTION')
    cur.execute('SELECT channum, type FROM channel')
    chantypes = {}
    for row in cur.fetchall():
        chantypes[row[0]] = int(row[1])

    # Get web page(s) from eMonitor(s) - log and notify via Prowl when
    # failures occur.
    updated = False
    for idx, ip in enumerate(ips):
        try:
            response = requests.get('http://' + ip, timeout=5)
            if response.status_code != 200:
                print('Invalid HTTP response from', ip + ':',
                       response.status_code)
                continue
        except(requests.exceptions.ConnectTimeout,
               requests.exceptions.ReadTimeout,
               requests.exceptions.ConnectionError):
            print('Error reading page from', ip)
            fails[idx] += 1
            if fails[idx] == max_fails:
                msg = 'eMonitor DOWN: ' + str(max_fails) + ' read failures'
                prowl.notify(ip, msg)
            continue
        if fails[idx] >= max_fails:
            msg = 'eMonitor UP after ' + str(fails[idx]) + ' read failures'
            prowl.notify(ip, msg)
        if fails[idx] > 0:
            msg = ip + ': success after ' + str(fails[idx])
            if fails[idx] > 1:
                msg += ' consecutive'
            msg += ' failure'
            if fails[idx] > 1:
                msg += 's'
            gclib.Log(msg)
            fails[idx] = 0

        updated = True

        # Pass page through Beautiful Soup HTML parser,
        # insert each row into database:
        # - For channel number, use 100 + index for second eMonitor unit.
        # - Massage values depending on channel type.
        soup = BeautifulSoup(response.content, 'html5lib')
        table = soup.find('table', { 'class' : 'channel-data' })
        prev_watts = 0
        for row in table.findAll('tr'):
            cells = row.findAll('td')
            if len(cells) == 3:
                channum = (int(cells[0].find(text=True)) + 100 * idx)
                watts = int(cells[2].find(text=True))
                # Assume channel exists in table. TODO: handle when it is not
                chantype = chantypes[channum]
                # Handle special types.
                if chantype == -1:
                    watts = -watts
                elif chantype == 2:
                    watts *= 2
                elif chantype == 3:
                    watts += prev_watts
                prev_watts = watts
                if chantype == 0:
                    continue
                sql = ('INSERT INTO used VALUES (' + str(channum) + ', '
                       + str(watts) + ', "' + utcnow.isoformat() + '")')
                cur.execute(sql)
                sql = ('UPDATE channel SET watts=' + str(watts)
                       + ', stamp="' + utcnow.isoformat()
                       + '" WHERE channum=' + str(channum))
                cur.execute(sql)

    if updated:
        # Put sum of current values into channel 0, in used and channel tables.
        sql = 'SELECT SUM(watts) FROM channel WHERE type > 0';
        cur.execute(sql)
        row = cur.fetchone()
        watts = row[0]
        sql = ('INSERT INTO used VALUES(0, ' + str(watts)
               + ', "' + utcnow.isoformat() + '")')
        cur.execute(sql)
        sql = ('UPDATE channel SET watts=' + str(watts)
               + ', stamp="' + utcnow.isoformat() + '" WHERE channum=0')
        cur.execute(sql)

    # Done with this pass - commit transaction, close cursor,
    # and commit changes to database.
    cur.execute('COMMIT');
    cur.close()
    db.commit()  # TODO: is this necessary since we executed COMMIT?

    # Print update time.
    gclib.Log('', utcnow)

