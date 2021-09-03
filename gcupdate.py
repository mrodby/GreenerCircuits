#!/usr/bin/python3
"""Greener Circuits Database Update

Once every N seconds (default 10) retrieve web page(s) from each eMonitor,
scrape current usage numbers from the page(s), and store them in the
database. If too many read errors occur when retrieving data from an
eMonitor, send an alert via prowlapp.com.
"""

import time
import sys
import signal
import traceback
import requests
import pymysql

from bs4 import BeautifulSoup

import gclib
import prowl

def terminate(_signum, _frame):
    """Ctrl-C or other terminate signal intercepted, log and exit"""
    gclib.log('***** Stopping Greener Circuits Database Update *****')
    sys.exit()


def main():
    """Main gcupdate functionality"""
    fails = []
    max_fails = 90
    update_interval = 10  # Scrape each eMonitor every update_interval seconds (max 60).

    gclib.log('***** Starting Greener Circuits Database Update *****')

    # Set terminate handler
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)

    # Instantiate prowlapp.com interface object.
    my_prowl = prowl.Prowl()

    # Get IP addresses or hostnames from eMonitors file.
    with open('eMonitors', encoding="utf-8") as e_monitors_file:
        hosts = e_monitors_file.read().splitlines()

    # Init fails array with zeroes
    for host in hosts:
        fails.append(0)

    database = None

    while True:
        # Update database every update_interval seconds.
        utcnow = gclib.sync_secs(update_interval)

        try:

            # Print update time.
            gclib.log('', utcnow)

            # Connect or reconnect to database.
            if database is None:
                gclib.log('(Re)Connecting to database...')
                database = gclib.connect_db('mrodby_gc')

            # Get database cursor, start a transaction, and get current channel list.
            cur = database.cursor()
            cur.execute('START TRANSACTION')
            cur.execute('SELECT channum, type FROM channel')
            chantypes = {}
            for row in cur.fetchall():
                chantypes[row[0]] = int(row[1])

            # Get web page(s) from eMonitor(s) - log and notify via Prowl when
            # failures occur.
            updated = False

            for idx, host in enumerate(hosts):
                #gclib.log('Getting page from ' + ip)
                try:
                    response = requests.get('http://' + host, timeout=5)
                    if response.status_code != 200:
                        gclib.log('Invalid HTTP response from ' + host + ': ' +
                            response.status_code)
                        continue
                    #gclib.log('Got page from ' + ip)

                except(requests.exceptions.ConnectTimeout,
                    requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectionError):
                    gclib.log('Error reading page from ' + host)
                    fails[idx] += 1
                    if fails[idx] == max_fails:
                        msg = 'eMonitor DOWN: ' + str(max_fails) + ' read failures'
                        my_prowl.notify(host, msg)
                    continue
                if fails[idx] >= max_fails:
                    msg = 'eMonitor UP after ' + str(fails[idx]) + ' read failures'
                    my_prowl.notify(host, msg)
                if fails[idx] > 0:
                    msg = host + ': success after ' + str(fails[idx])
                    if fails[idx] > 1:
                        msg += ' consecutive'
                    msg += ' failure'
                    if fails[idx] > 1:
                        msg += 's'
                    gclib.log(msg)
                    fails[idx] = 0

                updated = True

                #gclib.log('Passing page through Beautiful Soup parser')

                # Pass page through Beautiful Soup HTML parser,
                # insert each row into database:
                # - For channel number, use 100 + index for second eMonitor unit.
                # - Massage values depending on channel type.
                soup = BeautifulSoup(response.content, 'html5lib')
                table = soup.find('table', { 'class' : 'channel-data' })
                prev_watts = 0
                sql = ''
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
                        sql = sql + ('INSERT INTO used VALUES (' + str(channum) + ', '
                            + str(watts) + ', "' + utcnow.isoformat() + '");')
                        sql = sql + ('UPDATE channel SET watts=' + str(watts)
                            + ', stamp="' + utcnow.isoformat()
                            + '" WHERE channum=' + str(channum) + ';')
                gclib.log('Inserting into database: ' + sql)
                cur.execute(sql)
                #gclib.log('Finished inserting into database')

            if updated:
                #gclib.log('Inserting sum of current values into database')
                # Put sum of current values into channel 0, in used and channel tables.
                sql = 'SELECT SUM(watts) FROM channel WHERE type > 0'
                cur.execute(sql)
                row = cur.fetchone()
                watts = row[0]
                sql = ('INSERT INTO used VALUES(0, ' + str(watts)
                    + ', "' + utcnow.isoformat() + '")')
                cur.execute(sql)
                sql = ('UPDATE channel SET watts=' + str(watts)
                    + ', stamp="' + utcnow.isoformat() + '" WHERE channum=0')
                cur.execute(sql)
                #gclib.log('Finished inserting sum of current values into database')

            # Done with this pass - commit transaction, close cursor,
            # and commit changes to database.
            #gclib.log('Committing changes')
            cur.execute('COMMIT')
            #gclib.log('Closing cursor')
            cur.close()
            #gclib.log('Calling db.commit')
            database.commit()  # TODO: is this necessary since we executed COMMIT?
            #gclib.log('Returned from db.commit')

        except(pymysql.err.OperationalError, pymysql.err.InternalError, ConnectionResetError):
            print('Writing stack trace to stderr')
            print('Writing stack trace to stderr', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)   # default, but just to be explicit
            print('Writing stack trace to stdout')
            print('Writing stack trace to stdout', file=sys.stderr)
            traceback.print_exc(file=sys.stdout)   # TODO: remove this one when sufficiently tested
            time.sleep(2)  # Ensure we don't get multiple exceptions per update cycle
            database = None

if __name__ == '__main__':
    main()
