<?php

	session_start();
	
	require_once('db_connect.php');
	$username = trim($_POST['username']);
	$password = trim($_POST['password']);



	//"Put validation code"

	$password = sha1($password);
	$db_query = "SELECT * FROM users WHERE username = '$username' and password = '$password'";

	$result = $con->query($db_query);

	if($result->num_rows == 0){
		echo "invalid";
		exit;
	}


	$row = $result->fetch_assoc();
	
	$_SESSION['user'] = $username;

	$time = date('Y-m-d H:i');
	$db_query = "INSERT INTO system_logs(time, message, user) VALUES('$time','Login', '$username')";
	$result = $con->query($db_query);
	

	if($row['is_admin']){
		echo "admin";
		$_SESSION['admin'] = 1;
	}
	else{
		echo "user";
		$_SESSION['admin'] = 0;
	}
		
	
?>
