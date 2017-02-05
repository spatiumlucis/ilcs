<?php
	

	require_once('db_connect.php');
	$roomName       = $_POST['room_name'];
	$roomIp         = $_POST['room_ip'];
	$wakeHr         = $_POST['wake_hr'];
	$wakeMn         = $_POST['wake_mn'];
	$lightThreshold = $_POST['light_threshold'];
	$colorThreshold = $_POST['color_threshold'];
	
	
	$db_query = "INSERT INTO sensor_settings(ip, wake_time, color_thres, light_thres, name) VALUES('". $roomIp."', '1120', '". $colorThreshold."', '". $lightThreshold. "', '". $roomName. "')";

	if($con->query($db_query))
		echo "Data inserted successfully";
	else
		echo "Could not insert data";

	$con->close();

	$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
	$result = socket_connect($socket, "192.168.1.4", "12349");

	socket_write($socket, "A", 1);
	socket_close($socket);
	
?>
