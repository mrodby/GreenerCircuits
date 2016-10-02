
<?php
error_reporting(E_ALL);
ini_set('display_errors', true);
ini_set('html_errors', false);

$servername = "localhost";
$username = $_SERVER["DB_USER"];
$password = $_SERVER["DB_PASSWORD"];
$dbname = "eMonitor";

// Create database connection
$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error)
    die("Database connection failed: " . $conn->connect_error);
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <title>Greener Circuits Alerts</title>
  <link rel="stylesheet" type="text/css" href="main.css">
</head>
<body>

  <?php
    include 'nav.php';
  ?>

  <h1><br/>Greener Circuits Alerts</h1>

  <h2><br/>Active Alerts</h2>

  <?php
    $result = $conn->query("SELECT alert.channum, greater, alert.watts, minutes, message, alerted, name " .
      "FROM alert INNER JOIN channel ON alert.channum=channel.channum " .
      "ORDER BY alerted DESC, name");

    echo('<table border=1>');
    echo('<tr>');
    echo('<th style="text-align:left">Channel</th>');
    echo('<th style="text-align:left">Current Condition</th>');
    echo('</tr>');

    $in_inactive = False;
    while($row = mysqli_fetch_array($result)){
      $channum = $row['channum'];
      $greater = $row['greater'];
      $watts = $row['watts'];
      $minutes = $row['minutes'];
      $message = $row['message'];
      $alerted = $row['alerted'];
      $name = $row['name'];

      if($message != '')
        $message = " -- " . $message;

      if((!$alerted) && (!$in_inactive)){
        echo('</table><h2><br/>Inactive Alerts</h2>');
        echo('<table border=1>');
        echo('<tr>');
        echo('<th style="text-align:left">Channel</th>');
        echo('<th style="text-align:left">Current Condition</th>');
        echo('</tr>');
        $in_inactive = True;
      }

      echo '<tr><td>' . $name . '</td>';
      $msg = "";
      if(!$alerted){
        $msg = "not ";
        $message = "";
      }
      if($greater)
        $msg .= "above ";
      else
        $msg .= "below ";
      $msg .= $watts . ' watts for more than ' . $minutes . ' minute';
      if($minutes != 1)
        $msg .= 's';
      $msg .= $message;

      echo('<td>' . ucfirst($msg) . '</td>');
      echo('</tr>');

    }
    echo('</table>');
  ?>

</body>
</html>

