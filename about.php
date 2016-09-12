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
      (eMonitor photo here)
    </p>
    <p>
      Each monitor contains a web server that will show the current power usage of one circuit. Powerhouse Dynamics
      offers an annual subscription to provide history, and lets me analyze that history in many ways.
      I thought it might be fun to write software to periodically retrieve data from these monitors, store it
      in a database, and analyze it in ways that Power Dynamics does not offer. For example, I wanted it to
      notify me if the ceiling fan in our unused bedroom was left on when nobody was in the room. This project
      is the result.
      <br/>
    </p>
    <p>
      To implement this project I had to learn or brush up on PHP, CSS, HTML, MySQL, Python, Linux system administration,
      and third party libraries such as Beautiful Soup and Google Charts. All of the HTML, CSS, and PHP is hand-crafted.
    </p>
    <p style="text-align: center">
      (Raspberry Pi Zero photo here)
    </p>
    <p>
      This whole project runs on a Raspberry Pi Zero with an 8 GB Micro-SD card.
      <br/>
    </p>
    <p>
      Choose Channels from the menu bar to see a list of the available channels, then click on a channel name to see how
      usage has varied for that circuit over the past 24 hours.
    </p>

  </body>
</html>

