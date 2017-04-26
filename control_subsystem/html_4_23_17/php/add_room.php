<?php

	session_start();
	
	if(!isset($_SESSION['user']) || !isset($_SESSION['admin']))
		exit;
	
	if(!$_SESSION['admin'])
		exit;

	function changeDateFormat($wake_time){
		$temp = explode(":", $wake_time);
		echo count($temp);
		$wake_time = (intval($temp[0]) * 60 ) + intval($temp[1]);
		return $wake_time;
	}
	

	require_once('db_connect.php');
	$roomName       = $_POST['room_name'];
	$roomIp         = $_POST['room_ip'];
	$wakeTime       = $_POST['wake_time'];
	$threshold      = $_POST['threshold'];
	
	
	
	$db_query = "INSERT INTO sensor_settings(ip, wake_time, color_thres, light_thres, name) VALUES('". $roomIp."', '". $wakeTime ."', '". $threshold."', '". 0 . "', '". $roomName. "')";


	$sensor_port = "12348";

	if($con->query($db_query))
		echo "Data inserted successfully";
	else
		echo "Could not insert data";

	$con->close();

	$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
	$result = socket_connect($socket, $roomIp, $sensor_port);

	socket_close($socket);
	
?>
