#!/usr/bin/python3
'''
Component of Greener Circuits:

'''

from datetime import time

from gcdatabase import GCDatabase

def main():
    '''Create default set of alerts'''
    gc_database = GCDatabase()

    print('Deleting alerts')
    gc_database.delete_alerts()

    print('Creating alerts')

    guest_bedroom = 6
    gc_database.create_alert(channum=guest_bedroom, greater=True, watts=50, minutes=10,
        start=time(0, 0, 0), end=time(23, 59, 59), message='')

    hall = 8
    gc_database.create_alert(channum=hall, greater=True, watts=10, minutes=10,
        start=time(0, 0, 0), end=time(23, 59, 59), message='Hall lights')

    master_bedroom = 9
    gc_database.create_alert(channum=master_bedroom, greater=True, watts=50, minutes=10,
        start=time(8, 0, 0), end=time(20, 0, 0), message='')

    refrigerator = 11
    gc_database.create_alert(channum=refrigerator, greater=False, watts=50, minutes=120,
        start=time(8, 0, 0), end=time(20, 0, 0), message='')

    garage_refrigerator = 17
    gc_database.create_alert(channum=garage_refrigerator, greater=False, watts=50, minutes=120,
        start=time(8, 0, 0), end=time(20, 0, 0), message='')

if __name__ == '__main__':
    main()
