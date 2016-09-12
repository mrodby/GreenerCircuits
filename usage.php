
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
    <title>Greener Circuits Usage</title>
    <link rel="stylesheet" type="text/css" href="main.css">

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
            if (isset($_GET["channel"])) {
              $chan = $_GET["channel"];
              if (!ctype_digit($chan))
                die("Invalid channel number: " . $chan);
            }
            else
              $chan = "11";
            if (isset($_GET["interval"])) {
              $interval = $_GET["interval"];
              if (!ctype_digit($interval))
                die("Invalid interval: " . $interval);
            }
            else
              $interval = "300";

            // get channel name and multiplier
            $sql = "SELECT * FROM channel WHERE channum = " . $chan;
            $result = $conn->query($sql);
            if ($result->num_rows <= 0)
              die("Invalid channel: " . $chan);
            $row = $result->fetch_assoc();
            $name = $row["name"];
            $mult = $row["mult"];

            $sql = "SELECT FROM_UNIXTIME(UNIX_TIMESTAMP(stamp) DIV " . $interval . " * " . $interval . ") AS Time, ROUND(AVG(watts)) * " . $mult . " AS Power " .
                   "FROM used " .
                   "WHERE channum = " . $chan . " AND stamp > DATE_ADD(CURRENT_TIMESTAMP, INTERVAL -24 HOUR) " .
                   "GROUP BY UNIX_TIMESTAMP(stamp) DIV " . $interval;
            $result = $conn->query($sql);
            if ($result->num_rows <= 0)
              die("No results for channel " . $chan . ", interval " . $interval);

            while($row = mysqli_fetch_array($result)){
              $time = $row['Time'];
              $power = $row['Power'];
              echo "[new Date('".$row['Time']."Z'),".$row['Power']."],";
            }
          ?>
        ]);

        var options = {
          title: "<?php echo $name ?>"
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

    <h1>
      Greener Circuits Usage
    </h1>
    <br/>

    <!--Div that will hold the chart-->
    <div id="chart_div" style="height:400px"></div>

  </body>
</html>
