#!/usr/bin/python3
import pymysql
import requests
from bs4 import BeautifulSoup
import datetime
import time
import sys
import os
import urllib.parse

# globals
fails = [0, 0]
max_fails = 90
inc = 10  # read web page from each eMonitor IP every inc seconds (max 60)

# function to send a notification via prowlapp.com
# - call with event = IP address, desc = what happened
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

print ('***** Starting Greener Circuits *****')
sys.stdout.flush()

# get IP addresses or hostnames from eMonitors file
with open('eMonitors') as f:
  ips = f.read().splitlines()

# connect to database
db = pymysql.connect(host="localhost",
                     user="eMonitor",
#                     passwd="xxxxxxxx", - will be filled in from .my.cnf
                     db="eMonitor",
                     read_default_file="/home/mrodby/.my.cnf")

# start main loop
while True:
  while True:
    # wait for next time increment
    now = datetime.datetime.now()
    if now.second % inc == 0:
      break
    time.sleep(0.5)

# get database cursor, start a transaction, and get the current list of channels
  cur = db.cursor()
  cur.execute("START TRANSACTION")
  cur.execute("SELECT channum, type FROM channel")
  chantypes = {}
  for row in cur.fetchall():
    chantypes[row[0]] = int(row[1])

# get web page(s) from eMonitor(s) - log and notify via Prowl when failures occur
  for idx, ip in enumerate(ips):
    try:
      response = requests.get('http://' + ip, timeout=5)
      if response.status_code != 200:
        print ('Invalid HTTP response from', ip +  ':', response.status_code)
        continue
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
      print ('Error reading page from', ip)
      fails[idx] += 1
      if fails[idx] == max_fails:
        msg = 'eMonitor DOWN: ' + str(max_fails) + ' read failures'
        prowl (ip, msg)
      continue
    if fails[idx] >= max_fails:
      msg = 'eMonitor UP after ' + str(fails[idx]) + ' read failures'
      prowl (ip, msg)
    if fails[idx] > 0:
      msg = ip + ': success after ' + str(fails[idx])
      if fails[idx] > 1:
        msg += ' consecutive'
      msg += ' failure'
      if fails[idx] > 1:
        msg += 's'
      print (now.isoformat()[:19], msg)
      sys.stdout.flush()
      fails[idx] = 0

    # pass page through Beautiful Soup HTML parser, insert each row into database
    # - for channel number, use 100 + index for second eMonitor unit
    # - massage values depending on channel type
    soup = BeautifulSoup(response.content, "html5lib")
    table = soup.find("table", { "class" : "channel-data" })
    prev_watts = 0
    for row in table.findAll("tr"):
      cells = row.findAll("td")
      if len(cells) == 3:
        channum = (int(cells[0].find(text=True)) + 100 * idx)
        watts = int(cells[2].find(text=True))
        # assumes channel exists in table - TODO: handle case where it is not
        chantype = chantypes[channum]
        # handle special types
        if chantype == -1:
          watts = -watts
        elif chantype == 2:
          watts *= 2
        elif chantype == 3:
          watts += prev_watts
        prev_watts = watts
        if chantype == 0:
          continue
        sql = "INSERT INTO used VALUES (" + str(channum) + ", " + str(watts) + ", '" + now.isoformat() + "')"
        cur.execute(sql)
        sql = "UPDATE channel SET watts=" + str(watts) + ", stamp='" + now.isoformat() + "' WHERE channum=" + str(channum)
        cur.execute(sql)

  # put sum of current values into channel 0, both in used table and channel table
  sql = "SELECT SUM(watts) FROM channel WHERE type > 0";
  cur.execute(sql)
  row = cur.fetchone()
  watts = row[0]
  sql = "INSERT INTO used VALUES(0, " + str(watts) + ", '" + now.isoformat() + "')"
  cur.execute(sql)
  sql = "UPDATE channel SET watts=" + str(watts) + ", stamp='" + now.isoformat() + "' WHERE channum=0"
  cur.execute(sql)

  #sql = "INSERT INTO used VALUES(0, (SELECT SUM(watts) FROM channel WHERE type > 0), '" + now.isoformat() + "')"
  #cur.execute(sql)
  cur.execute("COMMIT");

  # done with this pass - close and commit
  cur.close()
  db.commit() # TODO: is this necessary?

  # print update time
  print (now.isoformat()[:19])
  sys.stdout.flush()


