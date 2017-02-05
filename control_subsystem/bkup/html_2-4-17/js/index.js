var ADD_ACTION = 1;
var SAVE_ACTION = 2;
var ADD_ROOM = "Add Room";
var SAVE_ROOM = "Save Room";
var UNPAIRED_IP;

// SERVER PAGES
var ADD_ROOM_PAGE = "php/add_room.php";
var DELETE_ROOM_PAGE =  "php/delete_room.php";
var EDIT_ROOM_PAGE = "php/edit_room.php";
var AVAILABLE_IP  = "php/available_ip.php";
var AUTH_USER= "php/auth_user.php";
var ROOM_UPDATE = "php/room_update.php";


var SENSOR_PORT = "12349";
var alarm_on = 0;





function readSensorsValues(){
	$.get(ROOM_UPDATE,
	  function(data, stat){
		  data = data.split('|');
		  data = data[0].split(',');
		  $('#takeout').text(data);
		  if(parseInt(data[9]) == 1)
				$('#sleep_alert').css({'display':'block'});
		  else
				$('#sleep_alert').css({'display':'none'});
	  });	
}



function loginSuccess(user){
	$('#login_form_container').modal('hide');
	$('#menu_items').css({'display': 'inline-block'});
	$('.sub_menu').css({'display': 'inline'});
	$('#user_logout_btn').css({'display': 'block'});
	$('#user_login_btn').css({'display': 'none'});
	

}

function logout(){
	$('#menu_items').css({'display': 'none'});
	$('.sub_menu').css({'display': 'none'});
	$('#user_login_btn').css({'display': 'block'});
	$('#user_logout_btn').css({'display': 'none'});
}



function login(user, pass, serverPage){
	$.post(serverPage,
	{
		username : user,
		password : pass
	},
		function(data, status){
			if(data == 'pass'){
				loginSuccess(user);
			}
	});

}


function soundAlarm(){
	var target = $('#alert_sound');
	target[0].play();
}


//Not needed...audio stops when dismissable link in clicked
function silentAlarm(){
	var target = $('#alert_sound');
	target[0].pause();
	target[0].currentTime = 0;
}

//This code runs before body document loads
$.get(AVAILABLE_IP,
	  function(data, stat){
		  var temp =  data;
		  UNPAIRED_IP = temp.trim();
	  });


function loadWakeTimeValues(){
	var target = $('#room_wake_time');
	var options = "";

	var temp = "";
	for(var i = 0; i < 24; i ++){
		if(i < 10){
			temp = "<option value = '0" + i + ":00' > 0" + i + ":00 </option>"; 
			temp += "<option value = '0" + i + ":30' > 0" + i + ":30 </option>"; 
		}

		else{
			temp = "<option value = '" + i + ":00' > " + i + ":00 </option>"; 
			temp += "<option value = '" + i + ":30' > " + i + ":30 </option>"; 
		}

		options += temp;
	}

	target.append(options);
}


function loadLightIntensityValues(){
	var target = $('#room_light_threshold');

	var options = "";

	var temp = "";
	for(var i = 0; i <= 100; i += 10){
		temp = "<option selected value = '" + i + "'> " + i + "</option>"; 
		options += temp;
	}

	target.append(options);

}


function loadColorIntensityValues(){
	var target = $('#room_color_threshold');

	var options = "";

	var temp = "";
	for(var i = 0; i <= 100; i += 10){
		temp = "<option value = '" + i + "'>" + i + "</option>"; 
		options += temp;
	}

	target.append(options);

}

	
function sendData(roomName, roomIp, wakeTime, lightThreshold, colorThreshold, serverPage){
	alert("in here  " + wakeTime);
	$.post(serverPage,
	{
		room_name : roomName,
		room_ip   : roomIp,
		wake_time : wakeTime,
		light_threshold : lightThreshold,
		color_threshold : colorThreshold
	},
		function(data, status){
			alert(roomIp);
			alert("Done with PHP1");
			alert(data);
			alert(status);
	});
}

function sendDeleteCommand(serverPage, roomIp){
	alert(roomIp);
	$.post(serverPage,
	{
		room_ip : roomIp
	},

	function(data, status){
			alert("Done with PHP2");
			alert(data);
			alert(status);
	});
}


function sendEditCommand(serverPage, roomName, roomIp, wakeTime, lightThres, colorThres, code){
	alert("in edit");
	$.post(serverPage, 
	{
		room_name      : roomName,
		room_ip        : roomIp,
		wake_time      : wakeTime,
		light_threshold: lightThres,
		color_threshold: colorThres, 
		edit_code      : code
	},
		function(data, status){
			alert(data);
			alert(status);
			alert("Done with PHP3");
	});

}

function SaveRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold){

	var current = '#sensors .rooms:not(:hidden) ';

	var prev_room_name   = $(current +'.aroom_name').text().split(":")[1].trim();
	var prev_wake_time   = $(current +'.aroom_wake_time').text().split(":");
	prev_wake_time       = prev_wake_time[1].trim() + ":" + prev_wake_time[2].trim();
	var prev_light_thres = $(current +'.aroom_light_threshold').text().split(":")[1].trim();
	var prev_color_thres = $(current +'.aroom_color_threshold').text().split(":")[1].trim();


	var code = "";
	
	if(prev_room_name != roomName)
		code += "R|";

	if(prev_wake_time != wakeTime)
		code += "W|";


	if(prev_light_thres !=  lightThreshold)
		code += "L|";

	if(prev_color_thres != colorThreshold)
		code += "C|";

	sendEditCommand(EDIT_ROOM_PAGE, roomName, roomIp, wakeTime, lightThreshold, colorThreshold, code);
	
	$(current + '.aroom_name').text('Room Name: ' + roomName);
	$(current +'.aroom_wake_time').text('Room Wake Time: ' + wakeTime);
	$(current +'.aroom_light_threshold').text('Room Light Threshold: ' + lightThreshold);
	$(current +'.aroom_color_threshold').text('Room Color Threshold: ' + colorThreshold);
	
	
	
	var target = $('#room_select');
	var value = target.val();
	
	value = value.split('_');
	var oldval = value[1];
	var newval = value[0] + '_' +  roomName;
	
	
	$('#room_select option:contains(' + oldval + ')').val(newval);
	$('#room_select option:contains(' + oldval + ')').text(roomName);
	
	$(current).attr('id', "Div_" + roomName);
	
	target.val(newval);
	message = $('#alert');
	message.fadeIn()
	message.text("Room Changes Saved");
	message.fadeOut(3000);
}



function CreateRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold){
	var sensorCount = $('#sensor_count').val();
	sensorCount = parseInt(sensorCount);

	
	var message = $('#alert');
	//Include validity function
	
	if(sensorCount == 0){
		$('#sensor_container').show();
		var newRoomTag = '<option value = "Room_' + roomName + '">' + roomName + '</option>'
						
		$('#room_select').append(newRoomTag).show();
		$('#no_room').hide(); 
	}
	
	else{
		var newRoomTag = '<option value = "Room_' + roomName + '">' + roomName + '</option>';
		$('#room_select').append(newRoomTag).val("Room_" + roomName);
	}
	
	
	var div  = "Div_" + roomName;
	
	var newDivTag  =    '<div class = "row" >\
							<div class ="rooms col-md-8 col-md-offset-2" id = "' + div + '"> \
								<div class = "row">\
									<div class = "submenu_container col-md-4 pull-right">\
										<nav class = "navbar">\
											<div class = "container-fluid">\
												<div class = "navbar-header">\
													<button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#sub_menu_' + roomName + '">\
														Action <span class="glyphicon glyphicon-option-vertical"></span>\
													</button>\
												</div>\
												<div class="collapse navbar-collapse sub_menu" id="sub_menu_' + roomName +'">\
													<ul class = "nav navbar-nav" id = "action_sub_menu"> \
														<li><button type="button" class="btn btn-primary btn-sm" id = "room_edit_btn">Edit</button></li> \
														<li><button type="button" class="btn btn-primary btn-sm" id = "room_delete_btn" data-toggle = "modal" data-target = "#delete_room_container" data-keyboard = "true">Delete</button></li>\
													</ul>\
												</div>\
											</div>\
										</nav>\
									</div>\
								</div>\
								<div id = "room_info">\
									<h2 class = "aroom_name"> Room Name: ' + roomName + '</h2>\
									<input type = "hidden" class = "aroom_ip" value = "' + roomIp + '" />\
									<p class = "aroom_wake_time"> Room Wake Time: ' + wakeTime + '</p>\
									<p class = "aroom_light_threshold"> Room Light Threshold: ' + lightThreshold + '</p>\
									<p class = "aroom_color_threshold"> Room Color Threshold: ' + colorThreshold + '</p>\
									<p id="takeout"></p>\
								</div>\
								<div class = "row">\
									<div id = "sleep_alert" class = "container-fluid alert alert-info alert-dismissable">\
										<h6>Room is in sleep mode</h6>\
									</div>\
								</div>\
								<div class = "row">\
									<div id = "degrade_alert" class = "container-fluid alert alert-danger alert-dismissable">\
										<h6></h6>\
									</div>\
								</div>\
							</div>\
						</div>';

	
	
	sensorCount ++;
	$('#sensor_count').val(sensorCount);
	var room_showing = $('#sensors .rooms:not(:hidden)');
	room_showing.hide();
	$('#sensors').append(newDivTag);

	message.fadeIn();
	message.text("Room Created");
	message.fadeOut(3000);
	
}

function DeleteRoom(){
	var room = $('#sensors .rooms:not(:hidden)');
	var room_ip = $('#sensors .rooms:not(:hidden) input[type = "hidden"]').val();
	
	//Create socket connection to send notification to the control subsystem
	sendDeleteCommand(DELETE_ROOM_PAGE, room_ip);

	room.remove();
	var target = $('#room_select :selected');
	var message = $('#alert');
	var opt = target.next()
	if(!opt.text()){
		opt = target.prev();
		if(!opt.text()){
			$('#room_select').hide();
			$('#sensor_count').val(0);
			target.remove();
			
			message.fadeIn();
			message.text("Room Deleted Successfully");
			$('#no_room').show();
			message.fadeOut(3000);
			$('#delete_room_container').modal('hide');
			
			return;
		}
	}
	target.remove();
	opt.prop('selected',true);
	$('#room_select').change();
	
	message.fadeIn();
	message.text("Room Deleted Successfully");
	message.fadeOut(3000);
	$('#delete_room_container').modal('hide');
	
	
}

function CreateSaveRoom(action){
	alert(roomIp);
	var roomName = $('#room_name').val().trim();
	var roomIp = UNPAIRED_IP;
	var wakeTime = $('#room_wake_time').val().trim();
	var lightThreshold = $('#room_light_threshold').val().trim();
	var colorThreshold = $('#room_color_threshold').val().trim();
	
	if(action == ADD_ACTION){
		alert(roomIp);
		sendData(roomName, roomIp, wakeTime, lightThreshold, colorThreshold, ADD_ROOM_PAGE);
		CreateRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold);
	}
		
	else
		SaveRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold);
	
	
}

/*
	This function sets the values of the form by 
	copying the previous entered values for the room
	into the form fields. 
*/

function setDialogValues(isDefault){
	
	if(isDefault){
		var roomName = "";
		var wakeHr = "12";
		var wakeMn = "00";
		var lightThreshold = "00";
		var colorThreshold = "00";
	}
	
	else{
		var target = '#room_info:not(:hidden)';
		var roomName = $(target + ' .aroom_name').text().split(":")[1].trim();		
		var wakeTime = $(target + ' .aroom_wake_time').text().split(":");
		var wakeTime = wakeTime[1].trim() + ":" + wakeTime[2].trim();
		var lightThreshold = $(target + ' .aroom_light_threshold').text().split(":")[1].trim();
		var colorThreshold = $(target + ' .aroom_color_threshold').text().split(":")[1].trim();
	}
	
	$('#room_name').val(roomName);
	$('#room_wake_time').val(wakeTime);
	$('#room_light_threshold').val(lightThreshold);
	$('#room_color_threshold').val(colorThreshold);
	
	
}


$(document).ready(function(){
	
	//This function runs when the the body finish loading
	loadWakeTimeValues();
    loadLightIntensityValues();
    loadColorIntensityValues();

	$("nav a").click(function(evt){
		evt.preventDefault()  //prevents navigational links from following the default 
		//$('#alarm_switch').click();
	});
	
	$('#menu_add_room').click(function(evt){
			evt.preventDefault();
			setDialogValues(true);
		
			$('#room_form_main_container').modal('show');
	});
	
	$('#add_room_btn').click(function(evt){
		$('#room_form_main_container').modal('hide');
		var temp = $('#add_room_btn').text().trim();
		if (temp == ADD_ROOM)
			CreateSaveRoom(ADD_ACTION);		
			
		else{ //important this is for saving user changes. It is a continuation of the room_edit_btn event
			CreateSaveRoom(SAVE_ACTION);
			$('#add_room_btn:contains(Save Changes)').text('Add Room');
		}
	}); // end of click event
	
	
	
	$('#room_select').change(function(){
		var value = $(this).val();
		value = value.split('_');
		value = '#Div_' + value[1];
		var room_showing = $('#sensors .rooms:not(:hidden)');
		room_showing.hide();
		$(value).show();		
	}); //end of change event
	
	
	$('#delete_btn').click(function(evt){
		DeleteRoom();
	});
	
	
	$('#sensors').on('click', '#room_edit_btn',(function(evt){
		$('#add_room_btn:contains(Add Room)').text('Save Changes');
		setDialogValues(false);
		$('#room_form_main_container').modal('show');
		
	}));

	$('#turn_off_alarm').click(function(){
			var target = $('#alarm_switch');
			target.removeClass( "alarm_on");
			target.addClass( "alarm_off");
			alarm_on = 0;
	});

	$('#alarm_switch').click(function(){
		var action = $(this).attr("class");
		if(action ==  "alarm_on"){
			$(this).removeClass( "alarm_on");
			$(this).addClass( "alarm_off");
			alarm_on = 0;
			silentAlarm();
		}

		else{
			$(this).removeClass( "alarm_off");
			$(this).addClass( "alarm_on");
			alarm_on = 1;
			soundAlarm();
		}
	});

	$('#login_btn').click(function(){
		var username = $('#username').val();
		var password = $('#password').val();


		login(username, password, AUTH_USER);
	});


	$('#user_logout_btn').click(function(){
		logout();
	});
	

	
}); //end of ready function
