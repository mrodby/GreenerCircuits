#!/usr/bin/python3

import gclib

# Connect to database.
db = gclib.connect_db('mrodby_gc')

cur = db.cursor()

# Create tables
cur.execute("CREATE TABLE channel (" \
            "channum INT PRIMARY KEY," \
            "name TEXT," \
            "type INTEGER," \
            "watts DOUBLE," \
            "stamp DATETIME" \
        ")")

cur.execute("CREATE TABLE used (" \
            "channum INT, INDEX(channum)," \
            "watts INT," \
            "stamp DATETIME, INDEX(stamp)" \
        ")")

cur.execute("CREATE TABLE alert(" \
            "id INT NOT NULL PRIMARY KEY," \
            "channum INT," \
            "greater TINYINT," \
            "watts INT," \
            "minutes INT," \
            "start TIME," \
            "end TIME," \
            "message TEXT," \
            "alerted TINYINT DEFAULT 0" \
        ")")

cur.execute("CREATE TABLE settings(" \
            "consolidate_stamp DATETIME," \
            "history_days INT DEFAULT 365" \
       ")")

cur.execute("CREATE TABLE scratchpad LIKE used")


