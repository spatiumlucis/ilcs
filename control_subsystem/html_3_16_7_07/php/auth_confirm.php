<?php
	session_start();
	

	if(isset($_SESSION['user'])){
		if($_SESSION['admin'])
			echo "admin";
		else
			echo "user";
	}
?>