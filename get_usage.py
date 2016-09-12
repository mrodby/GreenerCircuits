#!/usr/bin/python
import MySQLdb
import requests
from bs4 import BeautifulSoup
import cgi
import datetime
import time
import sys

ips = ['192.168.1.124', '192.168.1.120']
inc = 10  # update interval in seconds (max 60)

db = MySQLdb.connect(host="localhost",
                     user="eMonitor",
#                     passwd="xxxxxxxx",
                     db="eMonitor",
                     read_default_file="/home/mrodby/.my.cnf")

while True:
  while True:
    # wait for next time increment
    now = datetime.datetime.now()
    if now.second % inc == 0:
      break
    time.sleep(0.5)

  cur = db.cursor()
  # get web page(s) from eMonitor(s)
  nonBreakSpace = u'\xa0'
  for idx, ip in enumerate(ips):
    try:
      response = requests.get('http://' + ip, timeout=5)
      if response.status_code != 200:
        print "Invalid HTTP response from", ip + ": ", response.status_code
        continue
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
      print "Error reading page from " + ip
      continue

    # pass page through Beautiful Soup HTML parser, insert each row into database
    # - for channel number, use 100 + index for second eMonitor unit
    soup = BeautifulSoup(response.content, "html5lib")
    table = soup.find("table", { "class" : "channel-data" })
    for row in table.findAll("tr"):
      cells = row.findAll("td")
      if len(cells) == 3:
        num = str(int(cells[0].find(text=True)) + 100 * idx)
    #    name = cells[1].find(text=True).strip(nonBreakSpace)
        watts = cells[2].find(text=True)
        sql = "INSERT INTO used VALUES (" + num + ", " + watts + ", '" + now.isoformat() + "')"
        cur.execute(sql)

  # done with this pass - close and commit
  cur.close()
  db.commit()

  # print update time
  print now.isoformat()[:19]
  sys.stdout.flush()

db.close()

