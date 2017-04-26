<?php
	session_start();
?>

<!doctype html>
<html>
	<head>
		<title> Welcome - ITS </title>
		<meta name = "viewport" content = "width=device-width, initial-scale = 1" >
		<link rel = "shortcut icon" href = "">
		<!-- Latest compiled and minified CSS -->
		<link rel="stylesheet" href="lib/bootstrap/css/bootstrap.min.css">
		<link href = "css/index.css"  rel = "stylesheet">
		<link href = "css/form.css" rel = "stylesheet">
		<!-- jQuery library -->
		<script src="lib/jquery/jquery.min.js"></script>
		<script src = "lib/morris/raphael.min.js"></script>
		<script src = "lib/morris/morris.js"></script>
		
		<!-- Latest compiled JavaScript -->
		<script src="lib/bootstrap/js/bootstrap.min.js"></script>
		<script src = "js/index.js"></script>
		<script>
			loadSensorData(LOAD_DATA);
		</script>
				
	</head>
	
	<body onload="setInterval(readSensorsValues,1000);">
	
		<nav class = "navbar navbar-inverse">
			<div class = "container-fluid top_menu">
				<div class = "navbar-header">
					<button class="navbar-toggle" data-toggle = "collapse" data-target = "#menu" >
						<span class = "icon-bar"></span>
						<span class = "icon-bar"></span>
						<span class = "icon-bar"></span>
					</button>
					
					<a class="navbar-brand" href="index.html"> ILCS </a>
				</div>
				
				<div class = "collapse navbar-collapse" id = "menu">
					<ul class = "nav navbar-nav" id = "menu_items">
						<li><a href = "#" id = "menu_add_room" class = "admin_view"> Add New Room </a></li>
						<li><a href = "#" id = "menu_add_user" class = "admin_view"> Add New User </a></li>
						<li><a href = "#" id = "menu_view_log" class = "admin_view"> Logs </a></li>
						<li><a href = "#" class = "admin_view"> Help </a></li>
					</ul>
					
					<ul class = "nav navbar-nav navbar-right" id = "user_login_btn">
						<li><a href ="#" data-toggle = "modal" data-target = "#login_form_container" data-keyboard = "true" data-backdrop="static"><span class ="glyphicon glyphicon-log-in"></span> Login</a></li>
					</ul>
					
					<ul class = "nav navbar-nav navbar-right" id = "user_logout_btn">
						<li><a href = "#" class = "user_view"> Help </a></li>
						<button class= "btn btn-primary navbar-btn" > <span class ="glyphicon glyphicon-log-out"> Logout</button>
					</ul>
					
				</div>
			</div>
		</nav>
		

		<div class =  "container-fluid title">
			<div  class = "well">
				<h1>Intelligent Lighting Control System </h1>
			</div>
		</div>
		
		<div class = "container-fluid notification">
			<div class = "row">
				<div class = "col-sm-4 col-sm-offset-4 col-xs-12">
					<div class="dropdown dropdown_btn">
						<button class="btn btn-primary btn-block dropdown-toggle" type="button" data-toggle="dropdown">Notification
							<span class="badge notification_count">0</span>
							<span class="glyphicon glyphicon-menu-down"></span>
							<span class="glyphicon glyphicon-menu-up"></span>
						</button>
						
						<ul class="dropdown-menu dropdown_notification" style = "width: 100%;">
							<li class="dropdown-header degradation_header">Degradation <span class="badge degrade_notification_count">0</span>
								<ul class = "degradation_list">
								
								</ul>
							</li>
							<li class="divider sleep_divider"></li>
							<li class="dropdown-header sleep_mode_header">Sleep Mode <span class="badge sleep_notification_count">0</span>
								<ul class = "sleep_mode_list">
								
								</ul>
							</li>
							<li class="divider service_divider"></li>
							<li class="dropdown-header service_header">Urgent Room Service <span class="badge service_notification_count">0</span>
								<ul class = "service_list">
								
								</ul>
							</li>
						</ul>
					</div>
					
					
					
				</div>
			</div>
			
			<div  id = "alert" class = "alert alert-success col-xs-8 col-xs-offset-2 col-sm-4 col-sm-offset-4">
				<p></p>
			</div>
		</div>

	
		
		<div class = "container-fluid items content">
			<div id = "sensor_container" class = "row">
				<div id = "sensor_selection" class = "col-sm-6 col-sm-offset-3 col-xs-9 col-lg-4 col-lg-offset-4">
					<select name = "room_select" id = "room_select" class="form-control">
					</select>
				</div>
                
                
				 <div id = "btn_container" class = "btn_container" >
					
				
                	<div class="dropdown mobile_submenu col-xs-2">
                		<button class="btn btn-primary dropdown-toggle" data-toggle = "dropdown">
                        	Action <span class="caret"></span>
                        </button> 
                        
                        <ul class="dropdown-menu">
                            <li><a href="#" id = "room_edit_btn"><span class = "glyphicon glyphicon-edit"></span> Edit</a></li>
                            <li class = "divider"></li>
                            <li><a href="#" data-toggle = "modal" data-target = "#delete_room_container" data-keyboard = "true"><span class = "glyphicon glyphicon-trash"></span> Delete</a></li>
                        </ul>
    			                
                    </div>
                    
					<button class = "btn btn-primary desktop_submenu"  id = "room_edit_btn_lg"><span class = "glyphicon glyphicon-edit"></span> Edit Room </button>
					<button class = "btn btn-primary desktop_submenu" data-toggle = "modal" data-target = "#delete_room_container" data-keyboard = "true"><span class = "glyphicon glyphicon-trash"></span> Delete Room </button>
				</div>
            </div>
			<div class="row">
				<div id = "sensors">
					<input type = "hidden" id = "sensor_count" value = "0" />
				</div>
				
			</div>
		</div>
		
		<div class = "container-fluid content" id = "no_room">
			<h2> No Room Readings Available!!!</h2>
			<h3><small>Add a Sensor Subsystem to view room readings </small></h3>
		</div>
		
		
		<div id = "log_container content">
		
		</div>
		
		<div id = "help_container content"> 
		
		</div>
		
		
		
		<div id = "room_form_main_container" class = "modal fade" role = "dialog">
			<div id = "room_form_container" class = "modal-dialog modal-sm">
				
				<div class = "modal-content">
				
					<div class = "modal-header">
						<button type="button" class="close" data-dismiss="modal">&times;</button>
						<h4 class = "modal-title" id = "dynammic_title"><span class = "glyphicon glyphicon-plus"></span> Add New Room </h4>
					</div>
					
					<div class = "modal-body">
						<div class="form-group has-feedback room_name_container">
							<label for="room_name" class = "main_label control-label"> Room Name </label>
							<input type = "text" id = "room_name" name = "room_name"  class="form-control" />
							<span class="glyphicon glyphicon-ok form-control-feedback"></span>
							<span class="glyphicon glyphicon-remove form-control-feedback"></span>
							<span class = "error_msg_a">Room name already exist</span>
							<span class = "error_msg_b">Room name must contain at least 5 character</span>
						</div>
					

		
						<div class="form-group">
							
							<label for="room_wake_time" class = "main_label"> Wake-up Time </label>
							<div class = "row">
								<label for = "room_wake_hr" class = "col-xs-3 col-xs-offset-1">Hour </label>
								<label for = "room_wake_min" class = "col-xs-3">Minutes </label>
								
							</div>
							
							<div class = "row">	
								<select name = "wake_time_hr" id = "room_wake_hr" class="col-xs-3 col-xs-offset-1">
				
								</select>
								
								<select name = "wake_time_min" id = "room_wake_min" class="col-xs-3">
				
								</select>
								
								<select name = "wake_time_meridiem" id = "room_wake_meridiem" class="col-xs-3">
									<option value = "AM"> AM </option>
									<option value = "PM"> PM </option>
								</select>
							</div>
						</div>
					
						<div class="form-group">
							<label for="threshold" class = "main_label">Intensity Threshold </label>
							<select name = "threshold" id = "threshold" class="form-control">
							
							</select> 
						</div>
					

					</div>
					
					<div class = "modal-footer">
						<button  id = "add_room_btn" class="btn btn-default"> Add Room </button>
						<button  data-dismiss="modal" class="btn btn-default">Cancel</button>
					</div>
				</div>
			</div>
		</div>  <!-- end of add room form -->
		
		
		<div id = "login_form_container" class = "modal fade" role = "dialog">
			<div class = "modal-dialog modal-sm">
				<div class = "modal-content">	
					<div class = "modal-header">
						<button type="button" class="close" data-dismiss="modal">&times;</button>
						<h4 class = "modal-title"><span class = "glyphicon glyphicon-user"></span> Login </h4>
					</div>
					
					<div class = "modal-body">
						<span class = "login_error">Invalid Username and/or Password </span>
						<div class = "form-group">
							<label for = "username" class="control-label">Username </label>
							<input type = "text" name = "username" id = "username" class="form-control" placeholder = "Enter Username" />
					
						</div>
					
						<div class = "form-group">
							<label for = "password">Password </label>
							<input type = "password" name = "password" id = "password" class="form-control" placeholder = "Enter Password"/>
						</div>
					</div>
					
					<div class = "modal-footer">
						<button  id = "login_btn" class="btn btn-default"> Login </button>
						<button  data-dismiss="modal" class="btn btn-default">Cancel</button>
					</div>
					
				</div>
			</div>
		</div> <!-- end of login container -->





		<div id = "adduser_form_container" class = "modal fade" role = "dialog">
			<div class = "modal-dialog modal-sm">
				<div class = "modal-content">	
					<div class = "modal-header">
						<button type="button" class="close" data-dismiss="modal">&times;</button>
						<h4 class = "modal-title"><span class = "glyphicon glyphicon-plus"></span>  Add New User </h4>
					</div>
					
					<div class = "modal-body">
						<span id = "create_user_error" class = "error"> Error: Could not create user </span>
						
						<div class="form-group has-feedback user_name_container"> 
							<label for = "new_username">Username </label>
							<input type = "text" name = "username" id = "new_username" class="form-control"/>
							<span class="glyphicon glyphicon-ok form-control-feedback"></span>
							<span class="glyphicon glyphicon-remove form-control-feedback"></span>
							<span class = "error_msg_a">Username already exist</span>
							<span class = "error_msg_b">Username must contain at least 5 character</span>
						</div>
						
					
						<div class="form-group"> 
							<label for = "new_password">Password </label>
							<input type = "password" name = "password" id = "new_password" class="form-control"/>
						</div>
						
						
						<div class="form-group"> 
							<div class="checkbox">
								<label for = "admin_priveledge"><input type = "checkbox" name = "admin_priveledge" id = "admin_priveledge" value = "true" /> Grant Admin Priviledge </label>
								 
							</div>
						</div>
					</div>
					
					<div class = "modal-footer">
						<button  id = "create_user_btn" class="btn btn-default"> Create User </button>
						<button  data-dismiss="modal" class="btn btn-default">Cancel</button>
					</div>
					
				</div>
			</div>
		</div> <!-- end of add user container -->

		
		<div class = "container-fluid modal fade" role = "dialog" id = "delete_room_container" >
			<div class = "modal-dialog modal-sm">
				<div class = "modal-content">
				
					<div class = "modal-header">
						<h4> Delete Room</h4>
					</div>
					
					<div class = "modal-body">
						<h6> Are you sure you want to delete this room? </h6>
					</div>
					
					<div class = "modal-footer">
						<button  id = "delete_btn" class="btn btn-default">Delete </button>
						<button  data-dismiss="modal" class="btn btn-default">Cancel</button>
					</div>
				</div>
			</div>
		</div>
		
		
		

		<div id = "alert_danger" class = "container-fluid alert alert-danger alert-dismissable" style = "display: none;">
			<a href="#" class="close" data-dismiss="alert" aria-label="close" id = "alarm_turn_off">&times;Close</a>
            <audio id = "alert_sound" loop class = "off" controls>
            	<source src="media/lightdegraded.mp3" type = "audio/mpeg">
                <p>Browser does not support audio </p>
            </audio>
			<h6></h6>
		</div>		
		
		
		
		
		
		
		<div class="container">

			<button type="button" class="btn btn-info btn-lg" data-toggle="modal" data-target="#myModal" id = "mobile_modal" data-backdrop="static" style = "display:none">Open Small Modal</button>

  <!-- Modal -->
			<div class="modal fade" id="myModal" role="dialog">
				<div class="modal-dialog modal-sm">
					<div class="modal-content">
						<div class="modal-header">
							<button type="button" class="close mobile_modal_close" data-dismiss="modal">&times;</button>
							<h4 class="modal-title"> <span class="glyphicon glyphicon-warning-sign"></span> Intelligent Lighting Control System</h4>
						</div>
						<div class="modal-body">
							<p>In order to reduce data usage, browser vendors disabled media auto-play for mobile devices. Due to this
								reason, when you pause and close the degradation alarm sound in the notification panel, you will not receive
								the degradation alert until you reload the page 
							</p>
						</div>
					<div class="modal-footer">
						<button type="button" class="btn btn-default mobile_modal_close" data-dismiss="modal" >Close</button>
					</div>
				</div>
			</div>
		</div>

		<script>
			if(window.innerWidth < 992 && performance.navigation.type != 1){
				$('#mobile_modal').click();
			}
				
		</script>
		
		
		
	</body>

</html>


