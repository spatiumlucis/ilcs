<?php
	ini_set('display_errors', 1);

	$host = "localhost";
	$port       = 3306;
	$socket     = "";
	$username   = "spatiumlucis";
	$password   = "spatiumlucis";
	$database   = "ilcs";
	
	

	$con = new mysqli($host, $username, $password, $database, $port, $socket); 
	
	//$con = new mysqli($host, "root", "", "ilcs");
	

	if($con->connect_error)
		echo "Connection failed";



?>
