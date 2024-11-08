<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<!-- Component of Greener Circuits
Shows power usage both in text and graphically.
Parameters include which circuit (default 0, whole house), time interval
per bar (default 60 seconds), and time span (default 24 hours) -->

<?php
error_reporting(E_ALL);
ini_set('display_errors', true);
ini_set('html_errors', false);

// set variables to connect with database
include 'db.php';

// Create database connection
$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error)
    die("Database connection failed: " . $conn->connect_error);
?>

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <title>Greener Circuits Power Usage</title>
  <link rel="stylesheet" type="text/css" href="main.css">
  <link rel="icon" href="/images/GreenerCircuits.png" type="image/png" />
  <link rel="shortcut icon" href="/images/GreenerCircuits.ico" />
  <style>
    ul {
      margin: 0;
      padding: 0;
    }
    ul li {
      color: #fff;
    }
  </style>
  <script type="text/javascript" src="https://www.google.com/jsapi"></script>
  <script type="text/javascript">

    // Load the Visualization API and the corechart package.
    google.load("visualization", "1", {packages:["corechart"]});

    // Set a callback to run when the Google Visualization API is loaded.
    google.setOnLoadCallback(drawChart);

    // The callback itself
    function drawChart() {
      var data = google.visualization.arrayToDataTable([
        ['Time', 'Watts'],
        <?php
          function number_parm($name, $default) {
            if (isset($_GET[$name]))
              $ret = $_GET[$name];
            else
              $ret = $default;
            if (!ctype_digit($ret))
              die('Invalid ' . $name);
            return $ret;
          }
          $chan = number_parm("channel", "0");
          $hours = number_parm("hours", "24");
          $interval = number_parm("interval", "60");
          $page = number_parm("page", "0");
          $time = time() - date('Z');
	  $end = $time - $page * $hours * 3600;
	  $start = $end - $hours * 3600;
          $end = date('Y-m-d', $end) . 'T' . date('H:i:s', $end) . 'Z';
          $start = date('Y-m-d', $start) . 'T' . date('H:i:s', $start) . 'Z';

          // get channel name and type
          $sql = "SELECT * FROM channel WHERE channum = " . $chan;
          $result = $conn->query($sql);
          if ($result->num_rows <= 0)
            die("Invalid channel: " . $chan);
          $row = $result->fetch_assoc();
          $name = $row["name"];

          $sql = "SELECT FROM_UNIXTIME(UNIX_TIMESTAMP(stamp) DIV " .
                     $interval . " * " . $interval . ") AS Time, " .
                     "ROUND(AVG(watts)) AS Power " .
                 "FROM used " .
                 "WHERE channum = " . $chan .
                      " AND stamp BETWEEN DATE_ADD('" . $end .
                      "', INTERVAL -" . $hours . " HOUR) AND '" . $end . "' " .
                 "GROUP BY Time";
	  $result = $conn->query($sql);
          $total = 0;
          if ($result->num_rows > 0){
            while($row = mysqli_fetch_array($result)){
              $time = $row[0];
              $power = $row[1];
              # note: $time is in the format YYYY-MM-DD HH:MM:SS
              # - to work in Safari and IE a T needs to be between date and time,
              #   and for proper time zone adjustment, a 'Z' needs to be appended
              echo "[new Date('" . substr($time,0,10) . "T" . substr($time,11,5) . "Z')," . $power . "],";
	      $total += $power;
	    }
	  }
	  else {
	    echo "[new Date('" . $start . "'), 0],";
	    echo "[new Date('" . $end . "'), 0],";
	  }
        ?>
      ]);

      var options = {
        title: "<?php echo $name; $kWh = round($total/(3600/$interval)/1000,3);
            echo " (Total: " . $kWh . " kWh)"; /* note: do not call htmlspecialchars here */ ?>",
        chartArea:{left:50,top:30,right:10,bottom:40,width:"100%",height:"100%"},
        legend: { position: "none" }
      };
      var chart = new google.visualization.ColumnChart(document.getElementById("chart_div"));
      chart.draw(data, options);
    }
  </script>
</head>
<body>

  <?php
    include 'nav.php';
  ?>
  <h1><br/>Greener Circuits Power Usage</h1>
  Last updated 
  <?php
    $time = time() - date('Z');
    echo date('Y-m-d', $time) . ' ' . date('H:i:s', $time);
  ?>        
  <br/>

  <table width='100%'>
    <tr>
      <td style='white-space:nowrap'>
        <?php
          // populate first column with names and current usage
          $sql = "SELECT channum, name, watts FROM channel WHERE type<>0 ORDER BY name";
          $result = $conn->query($sql);

          if ($result->num_rows > 0) {
            echo "<table>";
            while($row = $result->fetch_assoc()) {
              echo "<tr><td align='right'>" . $row["watts"] . "</td><td>" .
                "<a href='power.php?" .
                "channel=" . $row["channum"] .
                "&interval=" . $interval .
                "&hours=" . $hours .
                "'>" . htmlspecialchars($row["name"]) . "</a></td></tr>";
            }
            echo "</table>";
          } else {
            echo "No channels in database";
          }
          echo "</td>";
        ?>
        <?php
          echo "<td><a href='power.php?" .
              "channel=" . $chan .
              "&interval=" . $interval .
              "&hours=" . $hours .
              "&page=" . ($page + 1) .
              "'>&lt;&lt;</a></td>";
        ?>
      <td style='width:99%; vertical-align:top'>
        <div id="chart_div" style='height:500px'></div>
      </td>
        <?php
          if ($page > 0)
            echo "<td><a href='power.php?" .
              "channel=" . $chan .
              "&interval=" . $interval .
              "&hours=" . $hours .
              "&page=" . ($page - 1) .
              "'>&gt;&gt;</a></td>";
          else
            echo "<td>&gt;&gt;</td>";
        ?>
    </tr>
  </table>

</body>
</html>

