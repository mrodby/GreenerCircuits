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

from bs4 import BeautifulSoup

from gcdatabase import GCDatabase
import gclib
import prowl

def terminated(_signum, _frame):
    """Ctrl-C or other terminate signal intercepted, log and exit"""

    gclib.log('***** Stopping Greener Circuits Database Update *****')
    sys.exit()


def main():
    """Main gcupdate functionality"""

    max_fails = 90
    update_interval = 10  # Scrape each eMonitor every update_interval seconds (max 60)

    gclib.log('***** Starting Greener Circuits Database Update *****')

    # Set terminate handler
    signal.signal(signal.SIGTERM, terminated)
    signal.signal(signal.SIGINT, terminated)

    # Instantiate prowlapp.com interface object.
    my_prowl = prowl.Prowl()

    # Get IP addresses or hostnames from eMonitors file.
    with open('eMonitors', encoding="utf-8") as e_monitors_file:
        hosts = e_monitors_file.read().splitlines()

    # Init fails array with zeroes
    fails = [0] * len(hosts)

    gc_database = GCDatabase()

    while True:
        # Update database every update_interval seconds.
        utcnow = gclib.sync_secs(update_interval)

        try:

            # Log update time
            gclib.log('')

            # Get list of channel types to know how to handle special types
            channels = gc_database.get_channels()
            chantypes = {}
            for channel in channels:
                chantypes[channel.channum] = int(channel.type)

            # Get web page(s) from eMonitor(s) - log and notify via Prowl when failures occur
            updated = False

            for host_index, host in enumerate(hosts):
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
                    fails[host_index] += 1
                    if fails[host_index] == max_fails:
                        msg = 'eMonitor DOWN: ' + str(max_fails) + ' read failures'
                        my_prowl.notify(host, msg)
                    continue
                if fails[host_index] >= max_fails:
                    msg = 'eMonitor UP after ' + str(fails[host_index]) + ' read failures'
                    my_prowl.notify(host, msg)
                if fails[host_index] > 0:
                    msg = host + ': success after ' + str(fails[host_index])
                    if fails[host_index] > 1:
                        msg += ' consecutive'
                    msg += ' failure'
                    if fails[host_index] > 1:
                        msg += 's'
                    gclib.log(msg)
                    fails[host_index] = 0

                updated = True

                #gclib.log('Passing page through Beautiful Soup parser')

                # Pass page through Beautiful Soup HTML parser,
                # insert each row into database:
                # - For channel number, use 100 + index for second eMonitor unit
                # - Massage values depending on channel type
                soup = BeautifulSoup(response.content, 'html5lib')
                table = soup.find('table', { 'class' : 'channel-data' })
                prev_watts = 0
                sql_text = ''
                for row in table.findAll('tr'):
                    cells = row.findAll('td')
                    if len(cells) == 3:
                        channum = (int(cells[0].find(text=True)) + 100 * host_index)
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
                        gc_database.insert_usage(channum, watts, utcnow)
                #gclib.log('Finished inserting into database')

            if updated:
                # Put sum of current values into channel 0, in used and channel tables
                gc_database.update_total_watts(utcnow)
                #gclib.log('Finished inserting sum of current values into database')

            # Done with this pass - commit transaction
            gc_database.commit()  # TODO: is this necessary since we executed COMMIT?
            #gclib.log('Returned from commit')

        except:
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
