<?php
	require_once("db_connect.php");
	
	$db_query = "SELECT * FROM sensor_ip WHERE is_paired = 0";
	$result = $con->query($db_query);

	$avail_ips = "";

	while($row = $result->fetch_assoc()){
		echo $row['ip'];
		echo "|";
	}
	
	echo $avail_ips;
	$con->close();
?>
