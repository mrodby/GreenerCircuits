<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>Greener Circuits</title>
    <link rel="stylesheet" type="text/css" href="main.css">
  </head>
  <body>

<?php
  include 'nav.php';
?>
    <h1>
      Greener Circuits
    </h1>
    <br/>

    <p>
      Welcome to Greener Circuits.
    </p>
    <p>
      My house has two 24-circuit Powerhouse Dynamics eMonitor power line monitors.
    </p>
    <p style="text-align: center">
      <img src="http://www.energycircle.com/sites/default/files/images/stories/1124/onthetable.jpg" alt="eMonitor">
    </p>
    <p>
      Each monitor contains a web server that will show the current power
      usage of one circuit. Powerhouse Dynamics offers an annual subscription
      to provide history, and lets me analyze that history in many ways. I
      thought it might be fun to write software to periodically retrieve data
      from these monitors, store it in a database, and analyze it in ways that
      Power Dynamics does not offer. For example, I wanted it to notify me if
      the ceiling fan in our unused bedroom was left on when nobody was in the
      room. This project is the result.<br/>
      The original Powerhouse Dynamics system cost about $2,000 to install,
      but analysis of electricity usage enabled by that system allowed us to
      reduce our electricity usage by about $100 per month, and allowed us to
      reduce the size of the PV system we installed by about $5,000. That's
      a very nice payback of the investment.<br/> 
    </p>
    <p>
      This project uses PHP, CSS, HTML, MySQL, Python, and third party
      libraries such as Beautiful Soup and Google Charts. All of the HTML,
      CSS, and PHP is hand-crafted. Three Python programs continually run in
      the background:
    </p>
    <ul>
      <li>get_usage.py: This retrieves a page from the web server embedded in
          each eMonitor once every 10 seconds. The web page contains a table
          of the current power usage for each channel. Each power measurement
          is stored in a database. If retrieving the page fails too many times
          in a row, an alert is sent to my cell phone via prowlapp.com.</li>
      <li>db_daemon.py: Once each hour this consolidates 10-second records
          into 1-minute records in the database, and deletes data older than
          30 days.</li>
      <li>alerts.py: Once each minute this checks each alert in the alert
          table. If an alert is newly raised, or if a previously raised alert
          is resolved, a message is sent to my cell phone via prowlapp.com.
          It also checks to make sure the database is being updated by
          verifying that the most recent time stamp in the database is less
          than 1 minute old.</li>
    </ul>
    <p style="text-align: center">
      <img src="images/PiZero.jpg" alt="Raspberry Pi Zero">
    </p>
    <p>
      This whole project runs on a Raspberry Pi Zero with an 8 GB Micro-SD card.
      <br/>
    </p>
    <p>
      Click on a channel name to see how usage has varied for that circuit over
      the past 24 hours. You can change the interval (in seconds) or the time
      span (in hours) by changing the corresponding parameter in the URL.
    </p>

  </body>
</html>

