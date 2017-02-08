var ADD_ACTION = 1;
var SAVE_ACTION = 2;
var ADD_ROOM = "Add Room";
var SAVE_ROOM = "Save Room";
var UNPAIRED_IP = "";

// SERVER PAGES
var ADD_ROOM_PAGE = "php/add_room.php";
var DELETE_ROOM_PAGE =  "php/delete_room.php";
var EDIT_ROOM_PAGE = "php/edit_room.php";
var AVAILABLE_IP  = "php/available_ip.php";
var AUTH_USER= "php/auth_user.php";
var ROOM_UPDATE = "php/room_update.php";
var LOAD_DATA = "php/load_sensor_data.php";


var SENSOR_PORT = "12349";
var alarm_on = 0;



function loadSensorData(serverPage){
	$.get(serverPage,
	  function (data, status){
	  if(data.length == 0)
			return;
	  else{
		var rooms = data.split('|');
		var data;
		var waketime;
		for(var i = 0; i < rooms.length - 1; i++){
			data = rooms[i].split(',');
			var temp = parseInt(data[1]/60);
			waketime = temp + ":" + (parseInt(data[1]) % 60);
			CreateRoom(data[4], data[0], waketime, data[3], data[2]);
		} 
	  }
	
	});	
}



function readSensorsValues(){
	getUnpairedIp();
	$.get(ROOM_UPDATE,
	  function(data, stat){
		  data = data.split('|');
		  data = data[0].split(',');
		  $('#takeout').text(data);

		  if(parseInt(data[6]) == 1){
				$('#sleep_alert').css({'display':'block'});
				$('#alarm_switch').click();
		  }

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

function getUnpairedIp(){
	$.get(AVAILABLE_IP,
	  function(data, stat){
		  if(data.length > 5){
			  
			  UNPAIRED_IP = data.trim();
		  }
	  });
}


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
	$.post(serverPage,
	{
		room_name : roomName,
		room_ip   : roomIp,
		wake_time : wakeTime,
		light_threshold : lightThreshold,
		color_threshold : colorThreshold
	},
		function(data, status){
			alert("Done with PHP1");
	});
}

function sendDeleteCommand(serverPage, roomIp){
	$.post(serverPage,
	{
		room_ip : roomIp
	},

	function(data, status){
			alert("Done with PHP2");
	});
}


function sendEditCommand(serverPage, roomName, roomIp, wakeTime, lightThres, colorThres, code){
	alert(roomIp);
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
			alert("Done with PHP3");
	});

}

function SaveRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold){

	var current = '#sensors .rooms:not(:hidden) ';

	var prev_room_name   = $(current +'.aroom_name').text().trim();
	var prev_wake_time   = $(current +'.aroom_wake_time').text().split(":");
	prev_wake_time       = prev_wake_time[1].trim() + ":" + prev_wake_time[2].trim();
	var prev_light_thres = $(current +'.aroom_light_threshold').text().split(":")[1].trim();
	var prev_color_thres = $(current +'.aroom_color_threshold').text().split(":")[1].trim();


	var code = "";

	/*if(prev_wake_time != wakeTime)
		code += wakeTime + "|";
	else
		code += "N|";*/

	if(prev_color_thres != colorThreshold)
		code += colorThreshold + "|";
	else
		code += "N|";


	if(prev_light_thres !=  lightThreshold)
		code += lightThreshold + "|";
	else
		code += "N|";

	

	sendEditCommand(EDIT_ROOM_PAGE, roomName, roomIp, wakeTime, lightThreshold, colorThreshold, code);
	
	$(current + '.aroom_name').text(roomName);
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
		$('.btn_container').show();
		$('#no_room').hide(); 
	}
	
	else{
		var newRoomTag = '<option value = "Room_' + roomName + '">' + roomName + '</option>';
		$('#room_select').append(newRoomTag).val("Room_" + roomName);
	}
	
	
	
	var div  = "Div_" + roomName;
	
	var newDivTag  =  
		'<div class = "container rooms" id = "' + div + '">' +
			'<div class = "row">' + 
				'<div class = "col-sm-12">' + 
					'<div class = "col-sm-6 col-xs-12">' + 
						'<div class = "user_set_values room_info">' + 
							'<span id = "aroom_name" class = "aroom_name">' + roomName +'</span>' + 
							'<input type = "hidden"  class = "aroom_ip" value = "' + roomIp + '" />' + 
							'<h2 class = "aroom_wake_time"> Set Wake Time: ' + wakeTime + '</h2>' + 
							'<h2 class = "aroom_light_threshold"> Set Light Threshold: ' + lightThreshold + '</h2>' + 
							'<h2 class = "aroom_color_threshold"> Set Color Threshold: ' + colorThreshold + '</h2>' + 

						'</div>' + 
					'</div>' + 
					
					'<div class = "col-sm-6 col-xs-12">' + 
						'<div class = "sensor_values">' + 
							'<h2> Read Wake Time </h2>' + 
							'<h2> Read Light Threshold </h2>' + 
							'<h2> Read Color Threshold </h2>' + 
						'</div>' + 
					'</div>' + 
				'</div>' + 
			'</div>' + 
			
			'<div class = "row">' +
				'<div class = "col-sm-4 col-sm-offset-4 col-xs-12">' + 
					'<div id = "sleep_alert" class = "alert alert-info alert-dismissable">' + 
						'<a href ="#" class = "close" data-dismiss = "alert" aria-label = "close"> &times; </a>' + 
						'<span>Room is in sleep mode</span>' + 
					'</div>' + 
				'</div>' + 
			'</div>' + 
			
			'<div class = "row">' + 
				'<div class = "col-sm-4 col-sm-offset-4 col-xs-12">' + 
					'<div id = "sleep_alert" class = "alert alert-danger alert-dismissable">' + 
						'<a href ="#" class = "close" data-dismiss = "alert" aria-label = "close"> &times; </a>' + 
						'<span>Light degraded</span>' + 
					'</div>' + 
				'</div>' + 
			'</div>' + 
		'</div>';

	
	
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
			$('.btn_container').hide();
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
	
	var roomName = $('#room_name').val().trim();
	var roomIp = UNPAIRED_IP;
	var wakeTime = $('#room_wake_time').val().trim();
	var lightThreshold = $('#room_light_threshold').val().trim();
	var colorThreshold = $('#room_color_threshold').val().trim();
	
	if(action == ADD_ACTION){
		sendData(roomName, roomIp, wakeTime, lightThreshold, colorThreshold, ADD_ROOM_PAGE);
		CreateRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold);
	}
		
	else{
		var target = '.rooms:not(:hidden)';
		roomIp = $(target + ' .aroom_ip').val();
		SaveRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold);

	}
	
	
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
		var target = '.rooms:not(:hidden)';
		var roomName = $(target + ' .aroom_name').text().trim();		
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
		$('#alarm_switch').click();
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
	
	
	$('#room_edit_btn').click(function(evt){
		$('#add_room_btn:contains(Add Room)').text('Save Changes');
		setDialogValues(false);
		$('#room_form_main_container').modal('show');
		
	});


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


	$(window).resize(function(){
		if(window.innerWidth < 992){
			var target = $('#sensor_selection');
			target.removeClass('col-sm-6 col-sm-offset-2');
			target.addClass('col-xs-12');

			target = $('#btn_container');
			target.removeClass("col-sm-4");
			target.addClass("col-xs-8 col-xs-offset-4");

		
		}

		else{
			var target = $('#sensor_selection');
			target.removeClass('col-xs-12');
			target.addClass('col-sm-6 col-sm-offset-2');

			target = $('#btn_container');
			target.removeClass("col-sm-4");
			target.addClass("col-xs-8 col-xs-offset-4");

		}
	

	});
	

	
}); //end of ready function
