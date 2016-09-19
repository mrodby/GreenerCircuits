#!/usr/bin/python
import MySQLdb
import datetime
import time
import sys

print '***** Starting Greener Circuits Database Daemon *****'
sys.stdout.flush()

# connect to database
db = MySQLdb.connect(host="localhost",
                     user="eMonitor",
#                     passwd="xxxxxxxx", - will be filled in from .my.cnf
                     db="eMonitor",
                     read_default_file="/home/mrodby/.my.cnf")

# start main loop
while True:

  # only do this loop once each minute
  time.sleep(60)

  now = datetime.datetime.now()

  # get database cursor
  cur = db.cursor()

  # get the timestamp of the most recent consolidation
  # if none, use oldest timestamp in used table
  # if none, use now
  consolidate_stamp = None
  cur.execute("SELECT consolidate_stamp FROM settings");
  row = cur.fetchone()
  if row == None:
    cur.execute("INSERT INTO settings VALUES(NULL)")
  else:
    consolidate_stamp = row[0]
  if consolidate_stamp == None:
    cur.execute("SELECT MIN(stamp) FROM used")
    row = cur.fetchone()
    if row != None:
      consolidate_stamp = row[0]
  if consolidate_stamp == None:
    consolidate_stamp = now

  # calculate start and end of consolidation period
  # - move back to start of hour
  start_stamp = consolidate_stamp.replace(minute=0, second=0, microsecond=0)
  # - set end_stamp to one our later
  end_stamp = start_stamp + datetime.timedelta(hours=1)
  # - if end_stamp is not earlier than 1 minute ago, don't do anything this time around
  if end_stamp >= now - datetime.timedelta(minutes=1):
    continue

  print "Consolidating from " + start_stamp.isoformat()[:19] + " to " + end_stamp.isoformat()[:19]
  sys.stdout.flush()

  # start a transaction to ensure nobody else sees inconsistent data from this consolidation
  cur.execute("START TRANSACTION")

  # consolidate rows from this time period into 1-minute intervals
  # - clear scratchpad table
  cur.execute("DELETE FROM scratchpad")
  # - consolidate appropriate rows into scratchpad table
  sql = "INSERT INTO scratchpad " +\
          "SELECT " +\
             "channum, " +\
             "AVG(watts) AS watts, " +\
             "FROM_UNIXTIME(UNIX_TIMESTAMP(stamp) DIV 60 * 60 ) AS stamp " +\
          "FROM used " +\
          "WHERE stamp >= '" + start_stamp.isoformat() + "' AND stamp < '" + end_stamp.isoformat() + "' " +\
          "GROUP BY channum, UNIX_TIMESTAMP(stamp) DIV 60"
  cur.execute(sql)
  # - delete original rows
  sql = "DELETE FROM used "+\
          "WHERE stamp >= '" + start_stamp.isoformat() + "' AND stamp < '" + end_stamp.isoformat() + "' "
  cur.execute(sql)
  # - copy from scratchpad table to original table
  sql = "INSERT INTO used SELECT * FROM scratchpad"
  cur.execute(sql)

  # update consolidate_stamp in settings
  cur.execute("UPDATE settings SET consolidate_stamp='" + end_stamp.isoformat() + "'")

  # all done - commit transaction
  cur.execute("COMMIT");

  print "Done: " + now.isoformat()[:19]

  # Once an hour delete rows older than number of days specified in settings table
  cur.execute("SELECT history_days FROM settings");
  row = cur.fetchone()
  if row == None:
    days = 0
  else:
    days = row[0]
  if days == None:
    days = 0
  if days != 0:
    sql = "DELETE FROM used WHERE stamp < DATE_ADD(now, INTERVAL -" + str(days) + " DAY)"
    print sql
    cur.execute(sql)

  # done with this pass - close and commit
  cur.close()
  db.commit() # TODO: is this necessary?

