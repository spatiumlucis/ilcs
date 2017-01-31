<?php

	$roomIp         = $_POST['room_ip'];
	$sensor_port    = "12349";

//	$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
//	$result = socket_connect($socket, $roomIp, $sensor_port);

//	socket_write($socket, 'D', 1);
//	socket_close($socket);

	echo "Done sending command";

?>
