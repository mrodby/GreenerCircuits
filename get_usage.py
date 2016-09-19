#!/usr/bin/python
import MySQLdb
import requests
from bs4 import BeautifulSoup
import cgi
import datetime
import time
import sys
import os

# globals
fails = [0, 0]
max_fails = 30
inc = 10  # read web page from each eMonitor IP every inc seconds (max 60)

# function to send a notification via prowl.com
# - call with event = IP address, desc = what happened
def prowl(event, desc):
  app = cgi.escape('Greener Circuits')
  url = 'http://api.prowlapp.com/publicapi/add?' + \
    'apikey=' + prowl_key + \
    '&application=' + cgi.escape("Greener Circuits") + \
    '&event=' + cgi.escape(event) + \
    '&description=' + cgi.escape(desc)
  requests.get(url)

print '***** Starting Greener Circuits *****'
sys.stdout.flush()

# if prowl_key is set, copy to global; if not, complain and exit
if not 'prowl_key' in os.environ:
  print 'prowl_key not set in environment'
  quit()
prowl_key = os.environ['prowl_key']
if prowl_key[-1] == ':':      # TODO: when started from /etc/init.d a colon is appended - find out why
  prowl_key = prowl_key[:-1]

# get IP addresses or hostnames from eMonitors file
with open('eMonitors') as f:
  ips = f.read().splitlines()

# connect to database
db = MySQLdb.connect(host="localhost",
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

# get database cursor and start a transaction
  cur = db.cursor()
  cur.execute("START TRANSACTION")

# get web page(s) from eMonitor(s) - log and notify via Prowl when failures occur
  for idx, ip in enumerate(ips):
    try:
      response = requests.get('http://' + ip, timeout=5)
      if response.status_code != 200:
        print "Invalid HTTP response from", ip + ": ", response.status_code
        continue
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
      print "Error reading page from " + ip
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
      print now.isoformat()[:19] + ' ' + msg
      sys.stdout.flush()
      fails[idx] = 0

    # pass page through Beautiful Soup HTML parser, insert each row into database
    # - for channel number, use 100 + index for second eMonitor unit
    soup = BeautifulSoup(response.content, "html5lib")
    table = soup.find("table", { "class" : "channel-data" })
    for row in table.findAll("tr"):
      cells = row.findAll("td")
      if len(cells) == 3:
        num = str(int(cells[0].find(text=True)) + 100 * idx)
        watts = cells[2].find(text=True)
        sql = "INSERT INTO used VALUES (" + num + ", " + watts + ", '" + now.isoformat() + "')"
        cur.execute(sql)
        sql = "UPDATE channel SET last=" + watts + ", stamp='" + now.isoformat() + "' WHERE channum=" + num
        cur.execute(sql)
  cur.execute("COMMIT");

  # done with this pass - close and commit
  cur.close()
  db.commit() # TODO: is this necessary?

  # print update time
  print now.isoformat()[:19]
  sys.stdout.flush()


