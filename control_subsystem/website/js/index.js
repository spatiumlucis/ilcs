var ADD_ACTION = 1;
var SAVE_ACTION = 2;
var ADD_ROOM = "Add Room";
var SAVE_ROOM = "Save Room";
var UNPAIRED_IPS = [];

// SERVER PAGES
var ADD_ROOM_PAGE = "php/add_room.php";
var AVAILABLE_IP  = "php/available_ip.php";


var SENSOR_PORT = "12349";

//This code runs before body document loads

$.get(AVAILABLE_IP,
	  function(data, stat){
		  var temp =  data.split("|");
		  for(var i = 0; i < temp.length - 1; i++){
			  UNPAIRED_IPS.push(temp[i].trim());
			}
	  });

	

function createIpOptions(){
	var parent = $('#room_ip');
	var element;
	for (var i = 0; i < UNPAIRED_IPS.length; i++){
		element = "<option value = '" + UNPAIRED_IPS[i] + "'>" + UNPAIRED_IPS[i] + "</option>";
		parent.append(element);
	}
}

function sendData(roomName, roomIp, wakeHr, wakeMn, lightThreshold, colorThreshold, serverPage){
	$.post(serverPage,
	{
		room_name : roomName,
		room_ip   : roomIp,
		wake_hr   : wakeHr,
		wake_mn   : wakeMn,
		light_threshold : lightThreshold,
		color_threshold : colorThreshold
	},
	function(data, stat){
		var index = UNPAIRED_IPS.indexOf(roomIp);
		UNPAIRED_IPS.pop(index);
		$("#room_ip option[value = '" + roomIp + "']").remove();
	});
}


function SaveRoom(roomName, roomIp, wakeHr, wakeMn, lightThreshold, colorThreshold){
	var current = '#sensors .rooms:not(:hidden) ';
	//previous values 
	//var prev_wake_time   = $(current +'.aroom_wake_time').text().split(":")[1].trim();   has  two ":"
	var prev_light_thres = $(current +'.aroom_light_threshold').text().split(":")[1].trim();
	var prev_color_thres = $(current +'.aroom_color_threshold').text().split(":")[1].trim();


	if(prev_light_thres !=  lightThreshold)
		alert("Light changed");
	if(prev_color_thres != colorThreshold)
		alert("Color changed");

	
	$(current + '.aroom_name').text('Room Name: ' + roomName);
	$(current +'.aroom_ip').text('Room IP: ' + roomIp);
	$(current +'.aroom_wake_time').text('Room Wake Time: ' + wakeHr + ':' + wakeMn);
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



function CreateRoom(roomName, roomIp, wakeHr, wakeMn, lightThreshold, colorThreshold){
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
									<p class = "aroom_ip"> Room IP: ' + roomIp + '</p>\
									<p class = "aroom_wake_time"> Room Wake Time: ' + wakeHr + ':' + wakeMn + '</p>\
									<p class = "aroom_light_threshold"> Room Light Threshold: ' + lightThreshold + '</p>\
									<p class = "aroom_color_threshold"> Room Color Threshold: ' + colorThreshold + '</p>\
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
	var room_text= $('.aroom_ip:not(:hidden)').text();
	var ip = room_text.split(":")[1].trim();
	UNPAIRED_IPS.push(ip);
	var element = "<option value = '" + ip + "' id = '" + ip + "'>" + ip + "</option>";
	$('#room_ip').append(element);

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
	var roomName = $('#room_name').val().trim();
	var roomIp = $('#room_ip').val().trim();
	var wakeHr = $('#room_wake_time_hr').val().trim();;
	var wakeMn = $('#room_wake_time_min').val().trim();;
	var lightThreshold = $('#room_light_threshold').val().trim();
	var colorThreshold = $('#room_color_threshold').val().trim();
	
	if(action == ADD_ACTION){
		sendData(roomName, roomIp, wakeHr, wakeMn, lightThreshold, colorThreshold, ADD_ROOM_PAGE);
		CreateRoom(roomName, roomIp, wakeHr, wakeMn, lightThreshold, colorThreshold);
	}
		
	else
		SaveRoom(roomName, roomIp, wakeHr, wakeMn, lightThreshold, colorThreshold);
	
	
}

/*
	This function sets the values of the form by 
	copying the previous entered values for the room
	into the form fields. 
*/

function setDialogValues(isDefault){
	
	if(isDefault){
		var roomName = "";
		var roomIp = "";
		var wakeHr = "12";
		var wakeMn = "00";
		var lightThreshold = "00";
		var colorThreshold = "00";
	}
	
	else{
		var target = '#room_info:not(:hidden)';
		var roomName = $(target + ' .aroom_name').text().split(":")[1].trim();		
		var roomIp =   $(target + ' .aroom_ip').text().split(":")[1].trim();
		var wakeTime = $(target + ' .aroom_wake_time').text().split(":");
		var wakeHr = wakeTime[1].trim();
		var wakeMn = wakeTime[2].trim();
		var lightThreshold = $(target + ' .aroom_light_threshold').text().split(":")[1].trim();
		var colorThreshold = $(target + ' .aroom_color_threshold').text().split(":")[1].trim();
	}
	
	$('#room_name').val(roomName);
	$('#room_ip').val(roomIp);
	$('#room_wake_time_hr').val(wakeHr);
	$('#room_wake_time_min').val(wakeMn);
	$('#room_light_threshold').val(lightThreshold);
	$('#room_color_threshold').val(colorThreshold);
	
	
}


$(document).ready(function(){
	
	//This function runs when the the body finish loading
	createIpOptions();
	

	$("nav a").click(function(evt){
		evt.preventDefault()  //prevents navigational links from following the default 
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
	

	
}); //end of ready function
