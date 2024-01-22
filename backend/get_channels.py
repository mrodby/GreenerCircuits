#!/usr/bin/python3
''' Component of Greener Circuits:
Query eMonitor(s) for the name of each channel and write to database
Note: try/catch intentionally not used here because this is intended
to only be used interactively, and only once, so any exceptions should
be visible and obvious.
'''

import requests

import pymysql
from bs4 import BeautifulSoup

def main():
    '''Get IP addresses or hostnames from eMonitors file'''

    with open('eMonitors', encoding="utf-8") as e_monitors_file:
        ips = e_monitors_file.read().splitlines()

    # Connect to database and get cursor.
    database = pymysql.connect(host='localhost',
                        user='eMonitor',
    #                     passwd='xxxxxxxx', - will be filled in from .my.cnf
                        db='eMonitor',
                        read_default_file='~/.my.cnf')
    cur = database.cursor()

    cur.execute('INSERT INTO channel (channum, name) VALUES (0, "-Whole House-")')

    # Get web page(s) from eMonitor(s).
    non_break_space = u'\xa0'
    for idx, ip_address in enumerate(ips):
        response = requests.get('http://' + ip_address)
        if response.status_code != 200:
            print('Invalid HTTP response from', ip_address + ':', response.status_code)
            continue

        # Pass page through Beautiful Soup HTML parser, insert each row into
        # database:
        # - For channel number, use 100 + index for second eMonitor unit.
        soup = BeautifulSoup(response.content, 'html5lib')
        table = soup.find('table', { 'class' : 'channel-data' })
        for row in table.findAll('tr'):
            cells = row.findAll('td')
            if len(cells) == 3:
                num = str(int(cells[0].find(text=True)) + 100 * idx)
                name = cells[1].find(text=True).strip(non_break_space)
                cur.execute('DELETE FROM channel WHERE channum=' + num)
                cur.execute('INSERT INTO channel (channum, name) VALUES ('
                            + num + ', "' + name + '")')

    # Print new channel contents.
    cur.execute('SELECT * FROM channel ORDER BY channum')
    for row in cur.fetchall():
        print(row[0], '-->', row[1])

    # All done - close and commit.
    cur.close()
    database.commit()
    database.close()


if __name__ == '__main__':
    main()
