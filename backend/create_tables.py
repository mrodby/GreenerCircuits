#!/usr/bin/python3
'''Create all database tables'''

from gcdatabase import GCDatabase

gc_database = GCDatabase()

gc_database.create_tables()
