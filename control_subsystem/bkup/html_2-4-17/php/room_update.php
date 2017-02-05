<?php
	require_once('db_connect.php');

	$db_query = "SELECT * FROM sensor_status";

	$result = $con->query($db_query);
	
	if(!$result)
		echo "Could not get data";

	else{
		
		$record_count = $result->num_rows;

		while($row =  $result->fetch_assoc()){
			echo $row['ip'].",".$row['red'].",".$row['green'].",".$row['blue'].",".$row['lumens'].",".$row['red_degraded'].",".$row['green_degraded'].",".$row['blue_degraded'].",".$row['lumens_degraded'].",".$row['sleep_mode_status'].",".$row['distance'];
			echo "|";
		}
	}
?>
