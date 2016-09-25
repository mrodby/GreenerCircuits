#!/usr/bin/python3

# Component of Greener Circuits:
# Once each minute check each entry in the alerts table to see if its conditions have been met.
# When a condition is met (or when a condition had previously been met but is now resolved),
# send an alert via prowl.com

import pymysql
import requests
import datetime
import time
import sys
import os
import urllib.parse

# function to send a notification via prowl.com
# - call with event = title, desc = what happened
def prowl(event, desc):
  app = urllib.parse.quote('Greener Circuits')
  url = 'http://api.prowlapp.com/publicapi/add?' + \
    'apikey=' + prowl_key + \
    '&application=' + urllib.parse.quote("Greener Circuits") + \
    '&event=' + urllib.parse.quote(event) + \
    '&description=' + urllib.parse.quote(desc)
  requests.get(url)

# if prowl_key is set, copy to global; if not, complain and exit
if not 'prowl_key' in os.environ:
  print ('prowl_key not set in environment')
  quit()
prowl_key = os.environ['prowl_key']
if prowl_key[-1] == ':':      # TODO: when started from /etc/init.d a colon is appended - find out why
  prowl_key = prowl_key[:-1]

print ('***** Starting Greener Circuits Alerts *****')
sys.stdout.flush()

# connect to database
db = pymysql.connect(host="localhost",
                     user="eMonitor",
#                     passwd="xxxxxxxx", - will be filled in from .my.cnf
                     db="eMonitor",
                     read_default_file="/home/mrodby/.my.cnf")

# main loop
while True:
  while True:
    timezone = datetime.timedelta(hours=-10)   # TODO: get time zone from pytz
    # check alerts once per minute
    now = datetime.datetime.now() + timezone
    if now.second % 60 == 0:
      break
    time.sleep(0.5)

  # get database cursor
  cur = db.cursor()

  # test each alert
  cur.execute("SELECT id, channum, greater, watts, minutes, start, end, message, alerted from alert")
  for row in cur.fetchall():
    id = row[0]
    channum = row[1]
    # set "compare" to the opposite of the condition we are looking for,
    # since our trigger is zero occurrences of "compare" being true
    # and set msgcomp to the same as the condition we are looking for,
    # so we can use that in a prowl message.
    if row[2] == 1:
      compare = '<'
      msgcomp = '>'
    else:
      compare = '>'
      msgcomp = '<'
    watts = row[3]
    minutes = row[4]
    start = datetime.datetime.combine(now.date(), datetime.time()) + row[5]
    end = datetime.datetime.combine(now.date(), datetime.time()) + row[6]
    message = row[7]
    alerted = (row[8] != 0)

    # if now is outside of the effective time range of this alert, don't check
    if end > start and (now < start or now >= end):
      continue
    if end < start and (now > start or now <= end):
      continue
    sql = 'SELECT COUNT(*) FROM used WHERE channum=' + str(channum) +\
            ' AND stamp >= DATE_ADD(CURRENT_TIMESTAMP, INTERVAL -' + str(minutes) + ' MINUTE)' +\
            ' AND watts ' + compare + str(watts)
    cur.execute(sql)
    countrow = cur.fetchone()
    if countrow[0] == 0:  # if all used rows meet the criteria (i.e. no rows meet the reverse of the criteria), alert!
      if not alerted:
        cur.execute('SELECT name FROM channel WHERE channum=' + str(channum))
        # assumes channel exists -- TODO: handle case where it does not
        name=cur.fetchone()[0]
        if message != '':
          message = '-- ' + message
        message = name + ': power ' + msgcomp + ' ' + str(watts) + ' watts for more than ' + str(minutes) + ' minutes' + message
        print ('***** POWER ALERT ******', message)
        prowl ('POWER ALERT', message)
        cur.execute('UPDATE alert SET alerted=1 WHERE id=' + str(id))
    else:
      if alerted:
        cur.execute('SELECT name FROM channel WHERE channum=' + str(channum))
        # assumes channel exists -- TODO: handle case where it does not
        name=cur.fetchone()[0]
        if message != '':
          message = '-- ' + message
        message = name + ': power ' + msgcomp + ' ' + str(watts) + ' watts for more than ' + str(minutes) + ' minutes' + message
        print ('***** power alert resolved *****', message)
        prowl ('power alert resolved', message)
        cur.execute('UPDATE alert SET alerted=0 WHERE id=' + str(id))

  # done with this pass - close cursor
  cur.close()
  db.commit() # without this our view of the database would be static, even for SELECT statements

  # print update time
  print (now.isoformat()[:19])
  sys.stdout.flush()

  # ensure this loop is not done more often than once per second
  time.sleep(1)

