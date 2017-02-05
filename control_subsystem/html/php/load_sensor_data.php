<?php
	
	require_once('db_connect.php');

	$db_query = "SELECT * FROM sensor_settings";

	$result = $con->query($db_query);

	$data = "";

	if(!$result){
		echo "could not get data";
		exit;
	}

	else{
		while ($row = $result->fetch_assoc()){
			$temp  =  $row['ip'].','.$row['wake_time'].','.$row['color_thres'].','.$row['light_thres'].','.$row['name'].'|';
			$data .= $temp;
		}

	}

	echo $data;
	


?>
