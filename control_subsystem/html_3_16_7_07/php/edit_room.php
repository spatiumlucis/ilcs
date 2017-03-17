<?php

	session_start();
	
	if(!isset($_SESSION['user']) || !isset($_SESSION['admin']))
		exit;
	
	if(!$_SESSION['admin'])
		exit;

	/*function changeDateFormat($wake_time){
		$wake_time = explode(":", $wake_time);
		$wake_time = (intval($wake_time[0]) * 60 ) + intval($wake_time[1]);
		return $wake_time;
	}*/


	require_once('db_connect.php');
	
	$roomName       = $_POST['room_name'];
	$roomIp         = $_POST['room_ip'];
	$wakeTime         = $_POST['wake_time'];
	$lightThreshold = $_POST['light_threshold'];
	$colorThreshold = $_POST['color_threshold'];
	$code           = $_POST['edit_code'];


	$sensor_port = "12349";





	$db_query =  "UPDATE sensor_settings SET name = '".$roomName."', light_thres = '".$lightThreshold."', color_thres = '".$colorThreshold."', wake_time = '" .$wakeTime ."' WHERE ip = '".$roomIp."'";

	

	if($con->query($db_query))
		echo "Data updated";
	else
		echo "Could not update data";

	$con->close();

	$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
	$result = socket_connect($socket, $roomIp, $sensor_port);

	socket_write($socket, $code, strlen($code));
	socket_close($socket);

?>
