#!/usr/bin/python3
''' Component of Greener Circuits:
Test the ability to issue an alert using Prowl.
'''

import prowl

def main():
    prowlapp = prowl.Prowl()
    prowlapp.notify('Testing', 'Notification works')

if __name__ == '__main__':
    main()
