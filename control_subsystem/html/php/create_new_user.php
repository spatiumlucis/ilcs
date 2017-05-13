<?php

	session_start();

	function checkString($data){
		$valid = true;
		for($i = 0; $i < strlen($data); $i++){
			$code = ord($data[$i]);
			if(($code > 96 && $code < 123) || ($code > 47 && $code < 58) || ($code > 64 && $code < 91))
				continue;
			else{
				$valid = false;
				break;
			}
		}
		return $valid;

	}



	if(!isset($_SESSION['user']) || !isset($_SESSION['admin']))
		exit;
	
	if(!$_SESSION['admin'])
		exit;
	
	require_once('db_connect.php');

	
	
	

	$username = trim($_POST['user']);
	$password = trim($_POST['pass']);
	$priviledge = trim($_POST['priv']);


	if(!checkString($username) || !checkString($password)){
		echo "failed";
		exit;
	}
	



	
	$password = sha1($password);

	if($priviledge == "true")
		$db_query = "INSERT INTO users VALUES ('$username', '$password', 1)";
	else
		$db_query = "INSERT INTO users VALUES ('$username', '$password', 0)";

	$result = $con->query($db_query);

	if($result)
		echo "success";

	else
		echo "failed";

	$time = date('Y-m-d H:i');
	$user = $_SESSION['user'];
	$db_query = "INSERT INTO system_logs(time, message, user) VALUES('$time','Created new user: $username', '$user')";
	$result = $con->query($db_query);

	

	
	


?>
