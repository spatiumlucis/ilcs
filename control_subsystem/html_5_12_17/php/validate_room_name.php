<?php
	require_once('db_connect.php');
	
	$room_name = $_GET['roomname'];
	
	$db_query = "SELECT name FROM sensor_settings WHERE name = '$room_name'";
	
	$result = $con->query($db_query);
	
	if($result->num_rows)
		echo "invalid";
	else
		echo "valid";

?>