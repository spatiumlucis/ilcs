<?php
	
	session_start();
	require_once('php/db_connect.php');
	if(!$_SESSION['admin']){
		echo "you are not authorized to view this page";
		exit;
	}


	$db_query = "SELECT time, message, user from system_logs ORDER BY id DESC";
	$result = $con->query($db_query);


	$length = $result->num_rows;
?>


<!doctype html>
<html>
	<head>
		<title> Welcome - ITS </title>
		<meta name = "viewport" content = "width=device-width, initial-scale = 1" >
		<!-- Latest compiled and minified CSS -->
		<link rel="stylesheet" href="lib/bootstrap/css/bootstrap.min.css">

		<!-- jQuery library -->
		<script src="lib/jquery/jquery.min.js"></script>
		
		<!-- Latest compiled JavaScript -->
		<script src="lib/bootstrap/js/bootstrap.min.js"></script>
				
	</head>

	<body>
		<div class = "container">
			<h2> Logs</h2>
				<table class = "table table-striped">
					<thead>
						<tr>
							<th>Time</th>
							<th>Message</th>
							<th>User</th>		
						</tr>
					</thead>
					<tbody>
						
					<?php
						for($i = 0; $i < $length; $i++ ){
							$row = $result->fetch_assoc();
							echo "<tr>";
							echo "<td>".$row['time']."</td>";
							echo "<td>".$row['message']."</td>";
							echo "<td>".$row['user']."</td>";
							echo "</tr>";
						}

					?> 



					</tbody>
				</table>
		</div>	
		
	</body>

</html>
