<?php
	session_start();
	
	if(!isset($_SESSION['user']) || !isset($_SESSION['admin']))
		exit;
	
	unset($_SESSION['user']);
	unset($_SESSION['admin']);
	
	session_destroy();


?>