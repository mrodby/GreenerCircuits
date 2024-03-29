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


def get_response(host):
    '''Ask for and retrieve a response from host'''

    #gclib.log('Getting page from ' + ip)
    try:
        response = requests.get('http://' + host, timeout=5)
        if response.status_code != 200:
            gclib.log('Invalid HTTP response from ' + host + ': ' +
                response.status_code)
            return ''
        #gclib.log('Got page from ' + ip)

    except(requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectionError):
        gclib.log('Error reading page from ' + host)
        return ''
    return response


def validate_response(host_index, host, response, fails, my_prowl):
    '''Check host response, notify via prowl if appropriate'''

    max_fails = 90
    if not response:
        fails[host_index] += 1
        if fails[host_index] == max_fails:
            msg = 'eMonitor DOWN: ' + str(max_fails) + ' read failures'
            my_prowl.notify(host, msg)
        return False

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
    return True


def parse_page_and_update_database(response, host_index, chantypes, gc_database, utcnow):
    '''Pass page through Beautiful Soup HTML parser, insert each row into database:
        - For channel number, use 100 + index for second eMonitor unit
        - Massage values depending on channel type
    '''

    soup = BeautifulSoup(response.content, 'html5lib')
    table = soup.find('table', { 'class' : 'channel-data' })
    prev_watts = 0
    for row in table.findAll('tr'):
        cells = row.findAll('td')
        if len(cells) == 3:
            channum = (int(cells[0].find(text=True)) + 100 * host_index)
            watts = int(cells[2].find(text=True))
            if channum not in chantypes:
                continue
            chantype = chantypes[channum]
            # Handle special types.
            if chantype == -1:
                watts = -watts
            elif chantype == 2:
                watts *= 2
            elif chantype == 3:
                watts += prev_watts
            prev_watts = watts
            gc_database.insert_usage(channum, watts, utcnow)
    #gclib.log('Finished inserting into database')


def update_from_hosts(gc_database, hosts, fails, my_prowl, utcnow):
    '''Get web page(s) from eMonitor(s) - log and notify via Prowl when failures occur'''

    updated = False

    # Get list of channel types to know how to handle special types
    channels = gc_database.get_channels()
    chantypes = {}
    for channel in channels:
        chantypes[channel.channum] = int(channel.type)

    for host_index, host in enumerate(hosts):

        response = get_response(host)
        if not validate_response(host_index, host, response, fails, my_prowl):
            continue

        updated = True

        #gclib.log('Passing page through Beautiful Soup parser')

        parse_page_and_update_database(response, host_index, chantypes, gc_database, utcnow)

    if updated:
        # Put sum of current values into channel 0, in used and channel tables
        gc_database.update_total_watts(utcnow)
        #gclib.log('Finished inserting sum of current values into database')


def main():
    """Main gcupdate functionality"""

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

            # Perform update
            update_from_hosts(gc_database, hosts, fails, my_prowl, utcnow)

        except:     #pylint: disable=bare-except
            traceback.print_exc(file=sys.stdout)

        time.sleep(2)  # Ensure we don't go through this loop multiple times per update cycle


if __name__ == '__main__':
    main()
