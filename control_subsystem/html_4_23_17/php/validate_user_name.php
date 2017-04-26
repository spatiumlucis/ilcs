<?php
	require_once('db_connect.php');
	
	$user_name = $_GET['username'];
	
	$db_query = "SELECT username FROM users WHERE username = '$user_name'";
	
	$result = $con->query($db_query);
	
	if($result->num_rows)
		echo "invalid";
	else
		echo "valid";

?>