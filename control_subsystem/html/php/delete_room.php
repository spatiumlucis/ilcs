<?php

	session_start();
	require_once('db_connect.php');

	if(!isset($_SESSION['user']) || !isset($_SESSION['admin']))
		exit;
	
	if(!$_SESSION['admin'])
		exit;

	$roomIp         = $_POST['room_ip'];
	$connect        = $_POST['connect'];
	$sensor_port    = "12349";

	$db_query = "SELECT being_serviced FROM sensor_status where ip = '".$roomIp."'";
	$result = $con->query($db_query);
	
	$row = $result->fetch_assoc();
	
	if($row['being_serviced']){
		echo "2";
		exit;
	}

	if(!$connect){
		echo "not connecting";
		exit;
	}


	$time = date('Y-m-d H:i');
	$db_query = "INSERT INTO system_logs(time, message, user) VALUES('$time','Deleted room with ip: $roomIp', '$username')";
	$result = $con->query($db_query);
	$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
	$result = socket_connect($socket, $roomIp, $sensor_port);

	socket_write($socket, 'D', 1);
	socket_close($socket);

	echo "Done sending command";

?>
