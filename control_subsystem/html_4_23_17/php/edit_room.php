<?php

	session_start();
	
	if(!isset($_SESSION['user']) || !isset($_SESSION['admin']))
		exit;
	
	if(!$_SESSION['admin'])
		exit;



	require_once('db_connect.php');
	
	$roomName       = $_POST['room_name'];
	$roomIp         = $_POST['room_ip'];
	$wakeTime         = $_POST['wake_time'];
	$lightThreshold = 0;
	$threshold = $_POST['threshold'];
	$code           = $_POST['edit_code'];


	$sensor_port = "12349";





	$db_query =  "UPDATE sensor_settings SET name = '".$roomName."', light_thres = '".$lightThreshold."', color_thres = '".$threshold."', wake_time = '" .$wakeTime ."' WHERE ip = '".$roomIp."'";

	

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
