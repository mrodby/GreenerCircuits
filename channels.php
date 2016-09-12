<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>Greener Circuits Channels</title>
    <link rel="stylesheet" type="text/css" href="main.css">
  </head>
  <body>

    <?php
      include 'nav.php';
    ?>

    <h1>
      Greener Circuits Channels
    </h1>
    <br/>

<?php

$servername = "localhost";
$username = $_SERVER["DB_USER"];
$password = $_SERVER["DB_PASSWORD"];
$dbname = "eMonitor";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Database connection failed: " . $conn->connect_error);
}

$sql = "SELECT channum, name FROM channel WHERE inuse=1 ORDER BY name";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    echo "<table>";
    while($row = $result->fetch_assoc()) {
        echo "<tr>";
    //    echo "<td align='right'>". $row["channum"] . "</td>";
        echo "<td>" . "<a href='usage.php?channel=" . $row["channum"] . "&interval=60'>" . $row["name"] . "</a></td>";
        echo "</tr>";
    }
    echo "</table>";
} else {
    echo "0 results";
}

$conn->close();
?>

  </body>
</html>
