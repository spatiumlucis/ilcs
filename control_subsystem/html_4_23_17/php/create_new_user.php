<?php

	session_start();
	
	if(!isset($_SESSION['user']) || !isset($_SESSION['admin']))
		exit;
	
	if(!$_SESSION['admin'])
		exit;
	
	require_once('db_connect.php');

	$username = trim($_POST['user']);
	$password = trim($_POST['pass']);
	$priviledge = trim($_POST['priv']);

	if(strlen($priviledge))
		$db_query = "INSERT INTO users VALUES ('$username', '$password', 1)";
	else
		$db_query = "INSERT INTO users VALUES ('$username', '$password', 0)";

	$result = $con->query($db_query);

	if($result)
		echo "success";

	else
		echo "failed";

	
	


?>
