<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Michael Rodby</title>
  <link rel="stylesheet" type="text/css" href="main.css">
</head>
<body>

<h1 align='center'><br/>Michael Rodby</h1>

<table>
  <tr>
    <td>
      <img src='images/headshot.jpg' height='200' alt='Michael Rodby in suit and tie'>
    </td>
    <td style='text-align:justify'>
      <p>
        My background spans a wide variety of software development skills, from
        individual development to managing multiple teams, from individual
        device drivers to distributed cooperating programs, from assembly
        language to Ruby on Rails.
      </p>
      <p>
        With my degrees in Electrical Engineering (BSEE) and Computer Science
        (MSCS), my sweet spot is in embedded software, especially where
        detailed knowledge of the hardware it runs on is required for good
        performance, optimal features, or both.
      </p>
    </td>
    <td>
      <img src='images/cartoonized.jpg' height='200' alt='Michael Rodby cartoonized'>
    </td>
  </tr>
</table>

<p>
  <br/>My projects have included:
  <ul>
    <li>
      <a href='http://98.151.142.85/power.php'>Greener Circuits:</a>
      Python programs and PHP web
      pages that monitor the power used by each circuit of my house, keep
      track of that usage in a database, graphs usage over time, and notify
      me when something happens that I am interested in. Except for the actual
      monitoring device itself, all of the software (including the database
      and web server) runs in a <a href='https://www.adafruit.com/products/2885'>
      Raspberry Pi Zero</a>, a tiny $5 computer that runs Linux. You can see
      the results <a href='http://98.151.142.85/power.php'>here</a>, and the
      source code is available on GitHub
      <a href='https://github.com/mrodby/GreenerCircuits'>here</a>.
      I wrote all of the custom software for this
      project. The web pages are so simple that I didn’t bother with a more
      powerful framework. If this were to turn into something real, I would
      convert it to a real web framework, such as Ruby on Rails.<br/>
      <img src='images/gcpower.png'
      alt='Sample Greener Circuits display' width='90%'><br/>
      This example shows the electricity used by my refrigerator over a 24 hour
      period. Note that around mealtimes the compressor is on for longer than it
      is at night, since that is when we open its door and put warmer things in
      it. Some of the narrow spikes are the light that turns on when we open it,
      others are the ice maker warming its ice tray so that the ice cubes will
      slide out. The wider and taller spike is the self-defrosting feature of
      the freezer doing its thing. The compressor cycle after the defrost cycle
      is much wider than usual to remove the extra heat added by the defrost
      cycle.<br/>
      Though the monitor itself cost about $2,000 including installation, by
      analyzing graphs similar to the one above,
      <a href='http://www.energyconsultingassociates.com'>Willy Bennett</a>
      showed me how to reduce my energy usage, saving over $100 each month.
      When I installed solar panels on my roof, the cost was about $5,000
      lower because of the reduce usage, making the $2,000 a very good
      investment indeed!
    </li>
    <li>
      APMI Ballots: A C++/MFC Windows program to maintain a database of condo
      associations and condo owners to support annual meetings of those
      associations. This software interfaces directly with an optical ballot
      reader and does the unexpectedly complex calculations to tally votes
      that are weighted by percentage of ownership for each condo. I wrote all
      of the custom software for this project.
    </li>
    <li>
      More to come...
    </li>
  </ul>
</p>

  </body>
</html>

