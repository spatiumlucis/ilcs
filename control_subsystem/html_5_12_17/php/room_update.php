<?php
	
	
	

	require_once('db_connect.php');
	
	$ip = $_GET['room_ip'];

	$db_query = "SELECT * FROM sensor_status WHERE ip = '$ip'";
	
	$db_query_b = "SELECT name, wake_time, color_thres FROM sensor_settings where ip = '$ip'";


	$result = $con->query($db_query);
	$result_b = $con->query($db_query_b);
	
	if(!$result || !$result_b)
		echo "Could not get data";

	else{

		$row =  $result->fetch_assoc();
		$row_b = $result_b->fetch_assoc();
		echo $row['ip'].",".$row['red'].",".$row['green'].",".$row['blue'].",".$row['lumens'].",".$row['red_degraded'].",".$row['green_degraded'].",".$row['blue_degraded'].",".$row['lumens_degraded'].",".$row['sleep_mode_status'].",".$row['distance'];
		echo ",".$row_b['name'].",".$row_b['wake_time'].",".$row_b['color_thres'];
		echo "|";
	}
?>
