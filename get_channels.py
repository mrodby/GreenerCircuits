#!/usr/bin/python3
import pymysql
import requests
from bs4 import BeautifulSoup

# get IP addresses or hostnames from eMonitors file
with open('eMonitors') as f:
  ips = f.read().splitlines()

# connect to database
db = pymysql.connect(host="localhost",
                     user="eMonitor",
#                     passwd="xxxxxxxx",
                     db="eMonitor",
                     read_default_file="~/.my.cnf")

cur = db.cursor()

# get web page from eMonitor
nonBreakSpace = u'\xa0'
for idx, ip in enumerate(ips):
  response = requests.get('http://' + ip)
  if response.status_code != 200:
    print ("Invalid HTTP response from" + ip + ": " + response.status_code)
    continue

# pass page through Beautiful Soup HTML parser, insert each row into database
# - for channel number, use 100 + index for second eMonitor unit
  soup = BeautifulSoup(response.content, "html5lib")
  table = soup.find("table", { "class" : "channel-data" })
  for row in table.findAll("tr"):
    cells = row.findAll("td")
    if len(cells) == 3:
      num = str(int(cells[0].find(text=True)) + 100 * idx)
      name = cells[1].find(text=True).strip(nonBreakSpace)
      watts = cells[2].find(text=True)
      cur.execute("DELETE FROM channel WHERE channum=" + num)
      cur.execute("INSERT INTO channel (channum, name) VALUES (" + num + ", '" + name + "')")

# print new channel contents
cur.execute("SELECT * FROM channel ORDER BY channum")
for row in cur.fetchall():
  print (row[0], "-->", row[1])

# all done - close and commit
cur.close()
db.commit()
db.close()

