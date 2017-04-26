<?php

	session_start();
	
	if(!isset($_SESSION['user']) || !isset($_SESSION['admin']))
		exit;
	



	require_once('db_connect.php');
	
	$roomName       = $_POST['room_name'];
	$roomIp         = $_POST['room_ip'];
	$wakeTime         = $_POST['wake_time'];
	$lightThreshold = 0;
	$threshold      = $_POST['threshold'];
	$code           = $_POST['edit_code'];


	$sensor_port = "12349";


	$db_query = "SELECT being_serviced FROM sensor_status where ip = '".$roomIp."'";
	$result = $con->query($db_query);
	
	$row = $result->fetch_assoc();
	
	if($row['being_serviced']){
		echo "2";
		exit;
	}
		


	$db_query =  "UPDATE sensor_settings SET name = '".$roomName."', light_thres = '".$lightThreshold."', color_thres = '".$threshold."', wake_time = '" .$wakeTime ."' WHERE ip = '".$roomIp."'";

	

	if($con->query($db_query)){
		echo "1";

		$time = date('Y-m-d H:i');
		$user = $_SESSION['user'];
		$db_query = "INSERT INTO system_logs(time, message, user) VALUES('$time','Edited room with ip: $roomIp', '$user')";
		$result = $con->query($db_query);

		$con->close();

		$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
		$result = socket_connect($socket, $roomIp, $sensor_port);

		socket_write($socket, $code, strlen($code));
		socket_close($socket);
	}
	else
		echo "0";

?>
