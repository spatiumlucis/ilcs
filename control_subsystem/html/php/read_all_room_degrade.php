<?php	
	
	require_once('db_connect.php');
	
	$db_query = "SELECT ss.ip, st.name, ss.red_degraded, ss.green_degraded, ss.blue_degraded, ss.lumens_degraded, ss.sleep_mode_status, ss.service
				 FROM sensor_status AS ss, sensor_settings AS st
				 WHERE ss.ip = st.ip";
	
	$result = $con->query($db_query);
	
	$length = $result->num_rows;
	
	if(!$length){
		echo "Could not get data";
		return;
	}
	
	
	for($i = 0; $i < $length; $i++ ){
		$row = $result->fetch_assoc();
		echo $row['ip'].",".$row['name'].",".$row['red_degraded'].",".$row['green_degraded'].",".$row['blue_degraded'].",".$row['lumens_degraded'].",".$row['sleep_mode_status'].",".$row['service'];
		echo "|";
	}
		
		
?>
