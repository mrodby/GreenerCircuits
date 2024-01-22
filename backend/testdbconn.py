#!/usr/bin/python3
''' Component of Greener Circuits:
Test the database connection; report whether it works or not.
'''

from gcdatabase import GCDatabase

def main():
    try:
        gc_database = GCDatabase()
        print("Database connection succeeded")
    except:
        print("Database connection failed")

if __name__ == '__main__':
    main()
