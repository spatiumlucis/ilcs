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
var CREATE_USER = "php/create_new_user.php";
var CHECK_ROOM_NAME = "php/validate_room_name.php";
var CHECK_USERNAME = "php/validate_user_name.php";
var ALL_ROOM_DEGRADE = "php/read_all_room_degrade.php";
var ALL_ROOM_SLEEP = "php/read_all_room_sleep.php";
var LOGOUT = "php/logout.php";
var AUTH_CONFIRMATION = "php/auth_confirm.php";


var SENSOR_PORT = "12349";
var alarm_on = 0;

var whiteLight = 0;
var redLight = 0;
var greenLight = 0;
var blueLight = 0;
var graphLoaded = 0;

var isRedDegraded = 0;
var isGreenDegraded = 0;
var isBlueDegraded = 0;
var isWhiteDegraded = 0;

var userLogin = 0;
var canEdit = 0;



var room_prop = {};
room_prop['degrade_notification'] = 0;
room_prop['sleep_notification'] = 0;
room_prop['service_count'] = 0;


function sensorValues(white, red, green, blue){
	
	var current = '#sensors .rooms:not(:hidden) ';
	var target = $(current +'.sensor_values');
	var element =   "<h3> Current Light Intensity: " + white + " lumens" + "</h3>" + 
					"<h3> Current Red Led Intensity: " + red + "%</h3>" + 
					"<h3> Current Green Led Intensity: " + green + "%</h3>" + 
					"<h3> Current Blue Led Intensity: " + blue + "%</h3>";
	target.html(element);

}




function graphWhiteLight(intensity, colorLabel, roomIp){
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');

	var elem = "white_"+id_ip;
	var target = $('#'+elem);;
	target.html('');
	
	var whiteDonut = Morris.Donut({
		element: elem,
		colors: ['#2a2a2a','#e0e0f4'],
  		data: [
				{value: 100 - intensity, label: ''},
    			{value: intensity, label: colorLabel}
    			
 			],
		resize: true
		});

	whiteDonut.select(1);
}


function graphRedLight(intensity, colorLabel, roomIp){
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');

	var elem = "red_"+id_ip;
	var target = $('#'+elem);

	target.html('');
	
	var redDonut = Morris.Donut({
		element: elem,
		colors: ['#2a2a2a','#ff0000'],
  		data: [
				{value: 100 - intensity, label: ''},
    			{value: intensity, label: colorLabel}
    			
 			],
		resize: true
		});

	redDonut.select(1);


	/*var firstTarget  = $('#red svg text tspan:eq(0)');
	var secondTarget = $('#red svg text tspan:eq(1)');
	var thirdTarget  = $('#red svg path:eq(1)');


	firstTarget.text("" + colorLabel);
	secondTarget.text("" + intensity);*/


}


function graphGreenLight(intensity, colorLabel, roomIp){
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');

	var elem = "green_"+id_ip;
	var target = $('#'+elem);

	target.html('');
	var greenDonut = Morris.Donut({
		element: elem,
		colors: ['#2a2a2a','#00ff00'],
  		data: [
				{value: 100 - intensity, label: ''},
    			{value: intensity, label: colorLabel}
    			
 			],
		resize: true
		});

	greenDonut.select(1);
}


function graphBlueLight(intensity, colorLabel, roomIp){
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');

	var elem = "blue_"+id_ip;
	var target = $('#'+elem);

	target.html('');
	var blueDonut = Morris.Donut({
		element: elem,
		colors: ['#2a2a2a','#0000ff'],
  		data: [
				{value: 100 - intensity, label: ''},
    			{value: intensity, label: colorLabel}
    			
 			],

		resize: true
		});
	blueDonut.select(1);
}


function checkScreen(){
	if(canEdit){	
		if(window.innerWidth < 768){
			$('.desktop_submenu').hide();
			$('.mobile_submenu').show();
		}
	
		else{
			$('.desktop_submenu').show();
			$('.desktop_submenu').css('display','inline-block');
			$('.mobile_submenu').hide();
		}
	}

	else{
		$('.mobile_submenu').hide();
		$('.desktop_submenu').hide();
	}
	
}


function createUser(username, password, priviledge, serverPage){
	$.post(serverPage,
		{user: username,
		 pass: password,
		priv: priviledge},
		function(data, status){
			if(data == "success"){
				$('#create_user_error').hide();
				$('#adduser_form_container').modal('hide');
			}
			else
				$('#create_user_error').show();
		});

}


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
			
			waketime = minutesToTime(data[1]);
			
			CreateRoom(data[4], data[0], waketime, data[3], data[2], 1);
			
		} 
	  }
	});	
}


function checkForDegradation(){
	var degradation_found = 0;
	for(var ip in room_prop){
		if(room_prop[ip]['light_degrade'] || room_prop[ip]['color_degrade']){
			if(room_prop[ip]['red_color_degrade'] && !room_prop[ip]['red_color_degrade_show']){
				room_prop[ip]['red_color_degrade_show'] = 1;
				degradation_found = 1;
			}
			
			if(room_prop[ip]['green_color_degrade'] && !room_prop[ip]['green_color_degrade_show']){
				room_prop[ip]['green_color_degrade_show'] = 1;
				degradation_found = 1;
			}
			
			if(room_prop[ip]['blue_color_degrade'] && !room_prop[ip]['blue_color_degrade_show']){
				room_prop[ip]['blue_color_degrade_show'] = 1;
				degradation_found = 1;
			}
			
			if(room_prop[ip]['light_degrade'] && !room_prop[ip]['light_degrade_show']){
				room_prop[ip]['light_degrade_show'] = 1;
				degradation_found = 1;
			}
		}	
	}
	
	if(degradation_found){
		soundAlarm();
		setTimeout(silentAlarm, 1000);
	}
	

}


function readValuesFromAllSensors(){
	$.get(ALL_ROOM_DEGRADE,
		function(data, status){
			data = data.split("|");
			var service_count = 0;
			for(var i = 0; i < data.length - 1; i++){
				var temp = data[i].split(",");
				room_prop[temp[0]]['name'] = temp[1];

				if(parseInt(temp[7]) && !parseInt(room_prop[temp[0]]['service_show'])){
					room_prop['service_count'] += 1;
					room_prop[temp[0]]['room_service'] = 1;
					room_prop[temp[0]]['service_show'] = 1;

					var elem = 	'<li class="room_service_warning" id ="room_service_' + temp[1] + '">' + 
										'<strong> Room ' + temp[1] + ' needs service</strong>'+ 
								'</li>';

					$('.notification .service_list').append(elem);
					$('.service_divider').css({'display': 'block'});
					$('.service_header').css({'display': 'block'});
				}

				else if(parseInt(room_prop[temp[0]]['service_show']) && !parseInt(temp[7])){
					room_prop['service_count'] -= 1;
					room_prop[temp[0]]['room_service'] = 0;
					room_prop[temp[0]]['service_show'] = 0;
					$('.notification #room_service_'+ temp[1]).remove();
					
					var result = $('.notification .service_list').html().trim();
					if(result == ""){
						$('.service_divider').css({'display': 'none'});
						$('.service_header').css({'display': 'none'});
					}
				}

				if(parseInt(temp[2]) || parseInt(temp[3]) || parseInt(temp[4])){
					if(parseInt(temp[2]))
						room_prop[temp[0]]['red_color_degrade'] = 1;
					
					if(parseInt(temp[3]))
						room_prop[temp[0]]['green_color_degrade'] = 1;
					
					if(parseInt(temp[4]))
						room_prop[temp[0]]['blue_color_degrade'] = 1;

						
					
					
					room_prop[temp[0]]['color_degrade'] = 1;
					
					if(!room_prop[temp[0]]['color_degrade_show']){	
						var elem = 	'<li class="room_degrade_warning" id ="color_degrade_' + temp[1] + '">' + 
										'<strong> Color degraded in ' + temp[1] + ' </strong>'+ 
									'</li>';
					
								
						$('.notification .degradation_list').append(elem);
						
						$('.degradation_header').css({'display': 'block'});
						room_prop[temp[0]]['color_degrade_show'] = 1;
						room_prop['degrade_notification'] += 1;
					}
				}
				else{
					
					if(!parseInt(temp[2])){
						room_prop[temp[0]]['red_color_degrade'] = 0;
						room_prop[temp[0]]['red_color_degrade_show'] = 0;
					}
					
					if(!parseInt(temp[3])){
						room_prop[temp[0]]['green_color_degrade'] = 0;
						room_prop[temp[0]]['green_color_degrade_show'] = 0;
					}
					
					if(!parseInt(temp[4])){
						room_prop[temp[0]]['blue_color_degrade'] = 0;
						room_prop[temp[0]]['blue_color_degrade_show'] = 0;
					}
					
					room_prop[temp[0]]['color_degrade'] = 0;
					if(room_prop[temp[0]]['color_degrade_show']){
						$('.notification #color_degrade_'+ temp[1]).remove();
						
						room_prop[temp[0]]['color_degrade_show'] = 0;
						room_prop['degrade_notification'] -= 1;
					}
					
					var result = $('.notification .degradation_list').html().trim();
					if(result == "")
						$('.degradation_header').css({'display': 'none'});
				}
				
				
				
				
				if(parseInt(temp[5])){
					room_prop[temp[0]]['light_degrade'] = 1;
					if(!room_prop[temp[0]]['light_degrade_show']){	
						var elem = 	'<li class="room_degrade_warning" id ="light_degrade_' + temp[1] + '">' + 
										'<strong> Light degraded in ' + temp[1] + ' </strong>'+ 
									'</li>';
					
								
						$('.notification .degradation_list').append(elem);
						$('.degradation_header').css({'display': 'block'});
						
						//room_prop[temp[0]]['light_degrade_show'] = 1;
						room_prop['degrade_notification'] += 1;
					}
				}
				else{
					room_prop[temp[0]]['light_degrade'] = 0;
					if(room_prop[temp[0]]['light_degrade_show']){
						$('.notification #light_degrade_'+ temp[1]).remove();
						
						room_prop[temp[0]]['light_degrade_show'] = 0;
						room_prop['degrade_notification'] -= 1;
						
					}
					
					var result = $('.notification .degradation_list').html().trim();
					if(result == "")
						$('.degradation_header').css({'display': 'none'});
					
				}

				if(parseInt(temp[6])){
					room_prop[temp[0]]['sleep'] = 1;
					if(!room_prop[temp[0]]['sleep_show']){
						var elem = '<li class="room_sleep_warning" id ="sleep_' + temp[1] + '">' + 
										'<strong> Room ' + temp[1] + ' is in sleep mode </strong>'+ 
									'</li>';
									
						$('.notification .sleep_mode_list').append(elem);
						$('.sleep_divider').css({'display': 'block'});
						$('.sleep_mode_header').css({'display': 'block'});
						
						room_prop[temp[0]]['sleep_show'] = 1;
						room_prop['sleep_notification'] += 1;
					}
				}
				else{
					room_prop[temp[0]]['sleep'] = 0;
					if(room_prop[temp[0]]['sleep_show']){
						$('.notification #sleep_'+ temp[1]).remove();
						room_prop[temp[0]]['sleep_show'] = 0;
						room_prop['sleep_notification'] -= 1;
					}
					
					var result = $('.notification .sleep_mode_list').html().trim();
					if(result == ""){
						$('.sleep_divider').css({'display': 'none'});
						$('.sleep_mode_header').css({'display': 'none'});
					}
					
				}
			}

			
		});
		
		$('.notification_count').text(parseInt(room_prop['degrade_notification']) + parseInt(room_prop['sleep_notification']) + parseInt(room_prop['service_count']));
		$('.degrade_notification_count').text(room_prop['degrade_notification']);
		$('.sleep_notification_count').text(room_prop['sleep_notification']);
		$('.service_notification_count').text(room_prop['service_count']);
}



function readSensorsValues(){
	getUnpairedIp();
	
	var current = '#sensors .rooms:not(:hidden) ';
	var ip = $(current + 'input.aroom_ip').val();
	
	if(!ip)
		return;

	
	var id_ip = ip.split('.');
	id_ip = id_ip.join('_');

	$.get(ROOM_UPDATE,
		{room_ip: ip},
	  function(data, stat)
	   {
		
		  if(data.length == 0)
				return;
		  data = data.split('|');
		  data = data[0].split(',');

			
		  temp = [];
		  for(var i = 1; i < data.length - 1; i ++)
			temp[i] = parseInt(data[i]);

		  room_prop[ip]['name'] = data[11];    /////////
		  room_prop[ip]['sleep'] = temp[9];    /////////
		  
		  if(temp[9] == 1){
				$('#sleep_alert_' + id_ip).css({'display':'block'});
		  }

		  else{
				$('#sleep_alert_' + id_ip).css({'display':'none'});				
		  }

		  
		  // Degradation code
		  if(temp[5] || temp[6] || temp[7] || temp[8]){
		  		$('#degrade_alert_' + id_ip).css({'display':'block'});
				room_prop[ip]['degrade'] = 1;   /////////
		  }

		  else{
				$('#degrade_alert_' + id_ip).css({'display':'none'});
				room_prop[ip]['degrade'] = 0;   /////////
		  }




		 if(graphLoaded == 0){
			  sensorValues(data[4], data[1], data[2], data[3]);
			  $('.chart').show();
			  graphWhiteLight(temp[4], "Light", ip);
			  graphRedLight(temp[1], "Red",ip);
			  graphGreenLight(temp[2], "Green",ip);
			  graphBlueLight(temp[3], "Blue",ip);

			  graphLoaded = 1;
			  whiteLight = temp[4];
			  redLight = temp[1];
			  greenLight = temp[2];
			  blueLight = temp[3];
			  
		  }

		  else{

			
			if((whiteLight != temp[4]) || (temp[8] != isWhiteDegraded)){
			 	sensorValues(data[4], data[1], data[2], data[3]);
				
			 	
			 	if((whiteLight != temp[4]) && temp[8] && isWhiteDegraded){  
					isWhiteDegraded = 1
					graphWhiteLight(temp[4], "Light Degraded",ip);
				}

				else if((whiteLight != temp[4]) && temp[8] && !isWhiteDegraded){  //turns on degraded sign
					isWhiteDegraded = 1
					graphWhiteLight(temp[4], "Light Degraded",ip);
				}

				else if((whiteLight != temp[4]) && !temp[8] && isWhiteDegraded){  //turns off degraded sign
					isWhiteDegraded = 0
					graphWhiteLight(temp[4], "White Light",ip);
				}

				else if((whiteLight != temp[4]) && !temp[8] && !isWhiteDegraded){  //turns off degraded sign
					isWhiteDegraded = 0
					graphWhiteLight(temp[4], "White Light",ip);
				}

				else if(temp[8] && !isWhiteDegraded){
					isWhiteDegraded = 1;
			  		graphWhiteLight(temp[4], "Light Degraded",ip);
				}

				else if(!temp[8] && isWhiteDegraded){
					isWhiteDegraded = 0;
			  		graphWhiteLight(temp[4], "White Light",ip);
				}
			 	whiteLight = temp[4];
				room_prop[ip]['white'] = temp[4];   /////////
			  
		   }




		  	if((redLight != temp[1]) || (temp[5] != isRedDegraded)){
			 	sensorValues(data[4], data[1], data[2], data[3]);
				
			 	
			 	if((redLight != temp[1]) && temp[5] && isRedDegraded){  
					isRedDegraded = 1
					graphRedLight(temp[1], "Red Led Degraded",ip);
				}

				else if((redLight != temp[1]) && temp[5] && !isRedDegraded){  //turns on degraded sign
					isRedDegraded = 1
					graphRedLight(temp[1], "Red Led Degraded",ip);
				}

				else if((redLight != temp[1]) && !temp[5] && isRedDegraded){  //turns off degraded sign
					isRedDegraded = 0
					graphRedLight(temp[1], "Red",ip);
				}

				else if((redLight != temp[1]) && !temp[5] && !isRedDegraded){  //turns off degraded sign
					isRedDegraded = 0
					graphRedLight(temp[1], "Red",ip);
				}

				else if(temp[5] && !isRedDegraded){
					isRedDegraded = 1;
			  		graphRedLight(temp[1], "Red Led Degraded",ip);
				}

				else if(!temp[5] && isRedDegraded){
					isRedDegraded = 0;
			  		graphRedLight(temp[1], "Red",ip);
				}
			 	redLight = temp[1];
				room_prop[ip]['red'] = temp[1];   /////////
			  
		   }


		   if((greenLight != temp[2]) || (temp[6] != isGreenDegraded)){
			 	sensorValues(data[4], data[1], data[2], data[3]);
				
			 	
			 	if((greenLight != temp[2]) && temp[6] && isGreenDegraded){  
					isGreenDegraded = 1
					graphGreenLight(temp[2], "Green Led Degraded",ip);
				}

				else if((greenLight != temp[2]) && temp[6] && !isGreenDegraded){  //turns on degraded sign
					isGreenDegraded = 1
					graphGreenLight(temp[2], "Green Led Degraded",ip);
				}

				else if((greenLight != temp[2]) && !temp[6] && isGreenDegraded){  //turns off degraded sign
					isGreenDegraded = 0
					graphGreenLight(temp[2], "Green",ip);
				}

				else if((greenLight != temp[2]) && !temp[6] && !isGreenDegraded){  //turns off degraded sign
					isGreenDegraded = 0
					graphGreenLight(temp[2], "Green",ip);
				}

				else if(temp[6] && !isGreenDegraded){
					isGreenDegraded = 1;
			  		graphGreenLight(temp[2], "Green Led Degraded",ip);
				}

				else if(!temp[6] && isGreenDegraded){
					isGreenDegraded = 0;
			  		graphGreenLight(temp[2], "Green",ip);
				}
			 	greenLight = temp[2]; 
				room_prop[ip]['green'] = temp[2];   /////////
		   }

		   if((blueLight != temp[3]) || (temp[7] != isBlueDegraded)){
			 	sensorValues(data[4], data[1], data[2], data[3]);
				
			 	
			 	if((blueLight != temp[3]) && temp[7] && isBlueDegraded){  
					isBlueDegraded = 1
					graphBlueLight(temp[3], "Blue Led Degraded",ip);
				}

				else if((blueLight != temp[3]) && temp[7] && !isBlueDegraded){  //turns on degraded sign
					isBlueDegraded = 1
					graphBlueLight(temp[3], "Blue Led Degraded",ip);
				}

				else if((blueLight != temp[3]) && !temp[7] && isBlueDegraded){  //turns off degraded sign
					isBlueDegraded = 0
					graphBlueLight(temp[3], "Blue",ip);
				}

				else if((blueLight != temp[3]) && !temp[7] && !isBlueDegraded){  //turns off degraded sign
					isBlueDegraded = 0
					graphBlueLight(temp[3], "Blue",ip);
				}

				else if(temp[7] && !isBlueDegraded){
					isBlueDegraded = 1;
			  		graphBlueLight(temp[3], "Blue Led Degraded",ip);
				}

				else if(!temp[7] && isBlueDegraded){
					isBlueDegraded = 0;
			  		graphBlueLight(temp[3], "Blue",ip);
				}
			 	blueLight = temp[3]; 
				room_prop[ip]['blue'] = temp[3];   /////////
		   }
			
		 }


	  });	
	  
	  readValuesFromAllSensors();
	  checkForDegradation();
	 

	   
}



function loginSuccess(isUser){
	
	$.get(AUTH_CONFIRMATION,
	  function(data, stat){
		
		if(data == "admin" || data == "user"){
			if(data == "admin")
				canEdit = 1;
			userLogin = 1;
			
		
			
			$('#login_form_container').modal('hide');
			$('#menu_items').css({'display': 'inline-block'});
			
			$('#user_logout_btn').css({'display': 'block'});
			$('#user_login_btn').css({'display': 'none'});
			$('.login_error').css({'display': 'none'});

			if(data == "admin"){
				
				$('.admin_view').css({'display': 'inline-block'});
				$('.user_view').css({'display': 'none'});
				
				if(window.innerWidth < 768){
					$('.desktop_submenu').hide();
					$('.mobile_submenu').show();
				}
			
				else{
					$('.desktop_submenu').show();
					$('.desktop_submenu').css('display','inline-block');
					$('.mobile_submenu').hide();
				}
			}
			
			else{	
				$('.mobile_submenu').hide();
				$('.desktop_submenu').hide();
				$('.admin_view').css({'display': 'none'});
				$('.user_view').css({'display': 'inline-block'});
			}
		}
	});
	
}

function loginFail(){
	$('.login_error').css({'display': 'inline'});

}

function logout(){
	$('#menu_items').css({'display': 'none'});
	$('.sub_menu').css({'display': 'none'});
	$('#user_login_btn').css({'display': 'block'});
	$('#user_logout_btn').css({'display': 'none'});
	
	$.post(LOGOUT,
	  function(data, stat){
		 

	 });
	  
	userLogin = 0;
	canEdit = 0;
	checkScreen();
}



function login(user, pass, serverPage){
	$.post(serverPage,
	{
		username : user,
		password : pass
	},
		function(data, status){
			if(data == 'admin' || data == "user"){
				if(data == "admin")
					canEdit = 1;
				userLogin = 1;
				checkScreen();
				loginSuccess(data);
			}

			else
				loginFail();
	});

}


function soundAlarm(){
	
	var target = $('#alert_sound');
	target[0].currentTime = 0;
	target[0].volume = 1;
}


//Not needed...audio stops when dismissable link in clicked
function silentAlarm(){	
	var target = $('#alert_sound');
	target[0].volume = 0;
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
	var target = $('#room_wake_hr');
	var options = "";

	var temp = "";
	for(var i = 1; i <= 12; i++){
		if(i < 10){
			temp = "<option value = '0" + i + "'> 0" + i + "</option>"; 
		}

		else{
			temp = "<option value = '" + i + "'> " + i + "</option>"; 
		}

		options += temp;
	}

	target.append(options);
	
	
	
	target = $('#room_wake_min');
	options = "";

	temp = "";
	for(var i = 0; i <= 59; i ++){
		if(i < 10){
			temp = "<option value = '0" + i + "'> 0" + i + "</option>"; 
		}

		else{
			temp = "<option value = '" + i + "'> " + i + "</option>"; 
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
			//alert("Done with PHP1");
	});
}

function sendDeleteCommand(serverPage, roomIp){
	$.post(serverPage,
	{
		room_ip : roomIp
	},

	function(data, status){
			
	});
}


function sendEditCommand(serverPage, roomName, roomIp, wakeTime, lightThres, colorThres, code){
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
	
	});

}

function SaveRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold){

	var current = '#sensors .rooms:not(:hidden) ';

	var prev_room_name   = $(current +'.aroom_name').text().trim();

	var prevWakeTime = $(current + ' .aroom_wake_time').text().split(":");
	
	

	var wakeHr = prevWakeTime[1].trim();
	
	
	prevWakeTime = prevWakeTime[2].split(" ");
	var wakeMn = prevWakeTime[0];
	var meridiem =prevWakeTime[1];


	prevWakeTime = timeToMinutes(wakeHr, wakeMn, meridiem);
	var prev_light_thres = $(current +'.aroom_light_threshold').text().split(":")[1].trim();
	prev_light_thres = prev_light_thres.slice(0, -1);

	var prev_color_thres = $(current +'.aroom_color_threshold').text().split(":")[1].trim();
	prev_color_thres = prev_color_thres.slice(0, -1);


	var code = "";

	if(prevWakeTime != wakeTime)
		code += wakeTime + "|";
	else
		code += "N|";

	if(prev_color_thres != colorThreshold)
		code += colorThreshold + "|";
	else
		code += "N|";


	if(prev_light_thres !=  lightThreshold)
		code += lightThreshold + "|";
	else
		code += "N|";

	
	alert(code);
	sendEditCommand(EDIT_ROOM_PAGE, roomName, roomIp, wakeTime, lightThreshold, colorThreshold, code);
	
	wakeTime = minutesToTime(wakeTime);
	$(current + '.aroom_name').text(roomName);
	$(current +'.aroom_wake_time').text('Room Wake Time: ' + wakeTime);
	$(current +'.aroom_light_threshold').text('Room Light Threshold: ' + lightThreshold + "%");
	$(current +'.aroom_color_threshold').text('Room Color Threshold: ' + colorThreshold + "%");
	
	
	
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



function CreateRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold, isPageLoading){
	var sensorCount = $('#sensor_count').val();
	sensorCount = parseInt(sensorCount);
	var message = $('#alert');
	
	room_prop[roomIp] = {};
	room_prop[roomIp]['red_color_degrade_show'] = 0;
	room_prop[roomIp]['green_color_degrade_show'] = 0;
	room_prop[roomIp]['blue_color_degrade_show'] = 0;
	
	room_prop[roomIp]['red_color_degrade'] = 0;
	room_prop[roomIp]['green_color_degrade'] = 0;
	room_prop[roomIp]['blue_color_degrade'] = 0;
	
	room_prop[roomIp]['color_degrade_show'] = 0;
	room_prop[roomIp]['light_degrade_show'] = 0;
	room_prop[roomIp]['sleep_show'] = 0;

	room_prop[roomIp]['room_service'] = 0;
	room_prop[roomIp]['service_show'] = 0;
	
	
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
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');
	
	
	var newDivTag  =  
		'<div class = "container-fluid rooms" id = "' + div + '">' +
			'<div class = "row" id = "all_sensor_values">' + 
				'<div class = "col-md-6 col-sm-12 values_container" >' + 
					
					'<div class = "user_set_values">' + 
						'<span id = "aroom_name" class = "aroom_name">' + roomName +'</span>' + 
						'<input type = "hidden"  class = "aroom_ip" value = "' + roomIp + '" />' + 
						'<h3 class = "aroom_wake_time"> User Set Wake Time: ' + wakeTime + '</h3>' + 
						'<h3 class = "aroom_light_threshold"> User Set Light Threshold: ' + lightThreshold + '%</h3>' + 
						'<h3 class = "aroom_color_threshold"> User Set Color Threshold: ' + colorThreshold + '%</h3>' + 
					'</div>' + 
				'</div>	' +
				
				'<div class = "col-md-6 col-sm-12">' + 
					'<div class = "sensor_values">' + 
					'</div>' + 
				'</div>' + 	
			'</div>' + 
			
			'<div class = "row chart">' + 
				'<div class = "col-md-3">' + 
					'<div id = "white_' + id_ip + '"></div>' + 
				'</div>' +

				'<div class = "col-md-3">' + 
					'<div id = "red_' + id_ip + '"></div>' + 
				'</div>' + 

				'<div class = "col-md-3">' + 
					'<div id = "green_' + id_ip + '"></div>' +
				'</div>' + 

				'<div class = "col-md-3">' + 
					'<div id = "blue_' + id_ip + '"></div>' + 
				'</div>' + 
			'</div>' +

			
		'</div>';

	
	
	sensorCount ++;
	$('#sensor_count').val(sensorCount);
	var room_showing = $('#sensors .rooms:not(:hidden)');
	room_showing.hide();
	$('#sensors').append(newDivTag);

	if(!isPageLoading){
		message.fadeIn();
		message.text("Room Created Successfully");
		message.fadeOut(3000);
	}
	
}

function deleteNotificationValue(room_ip, room_name){
	////
	
	alert(room_prop[room_ip]['service_show'])
	if(parseInt(room_prop[room_ip]['service_show'])){
		room_prop['service_count'] -= 1;
		room_prop[room_ip]['room_service'] = 0;
		room_prop[room_ip]['service_show'] = 0;
		$('.notification #room_service_'+ room_name).remove();
		
		var result = $('.notification .service_list').html().trim();
		if(result == ""){
			$('.service_divider').css({'display': 'none'});
			$('.service_header').css({'display': 'none'});
		}
	
	}
	
	
	////
	
	
	room_prop[room_ip]['red_color_degrade'] = 0;
	room_prop[room_ip]['red_color_degrade_show'] = 0;



	room_prop[room_ip]['green_color_degrade'] = 0;
	room_prop[room_ip]['green_color_degrade_show'] = 0;



	room_prop[room_ip]['blue_color_degrade'] = 0;
	room_prop[room_ip]['blue_color_degrade_show'] = 0;
	
	
	room_prop[room_ip]['color_degrade'] = 0;
	if(room_prop[room_ip]['color_degrade_show']){
		$('.notification #color_degrade_'+ room_name).remove();
		
		room_prop[room_ip]['color_degrade_show'] = 0;
		room_prop['degrade_notification'] -= 1;
	}
	
	var result = $('.notification .degradation_list').html().trim();
	if(result == "")
		$('.degradation_header').css({'display': 'none'});
	
	////////
	
	room_prop[room_ip]['light_degrade'] = 0;
	if(room_prop[room_ip]['light_degrade_show']){
		$('.notification #light_degrade_'+ room_name).remove();
		
		room_prop[room_ip]['light_degrade_show'] = 0;
		room_prop['degrade_notification'] -= 1;
		
	}
	
	var result = $('.notification .degradation_list').html().trim();
	if(result == "")
		$('.degradation_header').css({'display': 'none'});
					
	
	/////////
	
	room_prop[room_ip]['sleep'] = 0;
	if(room_prop[room_ip]['sleep_show']){
		$('.notification #sleep_'+ room_name).remove();
		room_prop[room_ip]['sleep_show'] = 0;
		room_prop['sleep_notification'] -= 1;
	}
	
	var result = $('.notification .sleep_mode_list').html().trim();
	if(result == "")
		$('.sleep_divider').css({'display': 'none'});

	
	$('.notification_count').text(parseInt(room_prop['degrade_notification']) + parseInt(room_prop['sleep_notification']) + parseInt(room_prop['service_count']));
	$('.degrade_notification_count').text(room_prop['degrade_notification']);
	$('.sleep_notification_count').text(room_prop['sleep_notification']);
	$('.service_notification_count').text(room_prop['service_count']);
	delete room_prop[room_ip];
	alert("done");
}



function DeleteRoom(){


	var room_tag = '#sensors .rooms:not(:hidden)';
	var room = $(room_tag);
	var room_ip = $(room_tag + ' input[type = "hidden"]').val();
	var room_name = $(room_tag + ' .aroom_name').text().trim();	
	
	sendDeleteCommand(DELETE_ROOM_PAGE, room_ip);
	deleteNotificationValue(room_ip, room_name);
	

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
			$('.chart').remove();
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
	$('.chart').remove();
	opt.prop('selected',true);
	$('#room_select').change();
	
	message.fadeIn();
	message.text("Room Deleted Successfully");
	message.fadeOut(3000);
	$('#delete_room_container').modal('hide');
	
	
	
	
	
}

function timeToMinutes(hour, minute, meridiem){
	var totalTime;
	
	if(meridiem == 'PM' && hour != 12){
		totalTime = parseInt(hour) + 12;
	}
	else{
		totalTime = parseInt(hour);
	}
	
	totalTime *= 60;
	totalTime += parseInt(minute);
	
	return totalTime;
}


function minutesToTime(waketime){
	var wakeHr, wakeMin, wakeMeridiem;
	
	waketime = parseInt(waketime);
	
	wakeHr = parseInt(waketime / 60);

	if(wakeHr > 12){
		wakeMeridiem = "PM";
		wakeHr = parseInt(wakeHr % 12);
	}
	
	else
		wakeMeridiem = "AM";
	
	wakeMin = waketime % 60;
	
	if(wakeHr < 10)
		wakeHr = "0" + wakeHr;
	
	if(wakeMin < 10)
		wakeMin = "0" + wakeMin;
	
	var str_time = "" + wakeHr + ":" + wakeMin + " " + wakeMeridiem;
	return str_time
	
}


function CreateSaveRoom(action){
	
	var roomName = $('#room_name').val().trim();
	var roomIp = UNPAIRED_IP;
	var wakeTimeHr = $('#room_wake_hr').val().trim();
	

	var wakeTimeMin = $('#room_wake_min').val().trim();
	var wakeTimeMeridiem = $('#room_wake_meridiem').val().trim();
	
	var lightThreshold = $('#room_light_threshold').val().trim();
	var colorThreshold = $('#room_color_threshold').val().trim();
	
	
	
	if(action == ADD_ACTION){
		var wakeTime = timeToMinutes(wakeTimeHr, wakeTimeMin, wakeTimeMeridiem);
		sendData(roomName, roomIp, wakeTime, lightThreshold, colorThreshold, ADD_ROOM_PAGE);
		wakeTime = minutesToTime(wakeTime);
		CreateRoom(roomName, roomIp, wakeTime, lightThreshold, colorThreshold, 0);
	}
		
	else{
		var target = '.rooms:not(:hidden)';
		var wakeTime = timeToMinutes(wakeTimeHr, wakeTimeMin, wakeTimeMeridiem);
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
		var meridiem = "AM";
		var lightThreshold = "00";
		var colorThreshold = "00";
	}
	
	else{
		var target = '.rooms:not(:hidden)';
		var roomName = $(target + ' .aroom_name').text().trim();		
		var wakeTime = $(target + ' .aroom_wake_time').text().split(":");
		var wakeHr = wakeTime[1].trim();
		
		
		wakeTime = wakeTime[2].split(" ");
		var wakeMn = wakeTime[0];
		var meridiem = wakeTime[1];
		
		
		var lightThreshold = $(target + ' .aroom_light_threshold').text().split(":")[1].trim();
		lightThreshold = lightThreshold.split("%");
		lightThreshold = lightThreshold[0];
		
		var colorThreshold = $(target + ' .aroom_color_threshold').text().split(":")[1].trim();
		colorThreshold = colorThreshold.split("%");
		colorThreshold = colorThreshold[0];
	}
	
	$('#room_name').val(roomName);
	
	


	
	$('#room_wake_hr').val(wakeHr);
	$('#room_wake_min').val(wakeMn);
	$('#room_wake_meridiem').val(meridiem);
	
	$('#room_light_threshold').val(lightThreshold);
	$('#room_color_threshold').val(colorThreshold);
	
	
}


function checkRoomName(roomName, serverPage){
	$('.room_name_container').removeClass('has-success');
	$('.room_name_container').removeClass('has-error');
	$('.room_name_container .glyphicon-ok, .room_name_container .error_msg_a').hide()
	$('.room_name_container .error_msg_b, .room_name_container .glyphicon-remove').hide();
	
	if(roomName.length <= 4){
		$('.room_name_container').addClass('has-error');
		$('.room_name_container .glyphicon-remove').show();
		$('.room_name_container .error_msg_b').show();	
		return;
	}
	
	$.get(serverPage,
		{
		roomname : roomName
		},
	
		function(data, status){
			if(data == "valid"){
				$('.room_name_container').addClass('has-success');
				$('.room_name_container .glyphicon-ok').show();
			}
			
			else{
				$('.room_name_container').addClass('has-error');
				$('.room_name_container .glyphicon-remove').show();
				$('.room_name_container .error_msg_a').show();
			}
		}
	);
	
}




function checkUserName(userName, serverPage){
	$('.user_name_container').removeClass('has-success');
	$('.user_name_container').removeClass('has-error');
	$('.user_name_container .glyphicon-ok, .user_name_container .error_msg_a').hide()
	$('.user_name_container .error_msg_b, .user_name_container .glyphicon-remove').hide();
	
	if(userName.length <= 4){
		$('.user_name_container').addClass('has-error');
		$('.user_name_container .glyphicon-remove').show();
		$('.user_name_container .error_msg_b').show();	
		return;
	}
	
	$.get(serverPage,
		{
		username : userName
		},
	
		function(data, status){
			if(data == "valid"){
				$('.user_name_container').addClass('has-success');
				$('.user_name_container .glyphicon-ok').show();
			}
			
			else{
				$('.user_name_container').addClass('has-error');
				$('.user_name_container .glyphicon-remove').show();
				$('.user_name_container .error_msg_a').show();
			}
		}
	);
	
}


$(document).ready(function(){
	//This function runs when the the body finish loading
	
		
	checkScreen();
	loadWakeTimeValues();
    loadLightIntensityValues();
    loadColorIntensityValues();
	loginSuccess();
	
	


	$(window).resize(function(){
		checkScreen();
		var target = '.rooms:not(:hidden)';
		var ip = $(target + ' .aroom_ip').val();

		if(!ip)
			return;

		if(isWhiteDegraded)
			graphWhiteLight(whiteLight, "White Degraded",ip);
		else
			graphWhiteLight(whiteLight, "White",ip);

		
		if(isRedDegraded)
			graphRedLight(redLight, "Red Degraded",ip);
		else
			graphRedLight(redLight, "Red",ip);


		if(isGreenDegraded)
			graphGreenLight(greenLight, "Green Degraded",ip);
		else
			graphGreenLight(greenLight, "Green",ip);

		
		if(isBlueDegraded)
			graphBlueLight(blueLight, "Blue Degraded",ip);
		else
			graphBlueLight(blueLight, "Blue",ip);

	});
	
	
	$("nav a").click(function(evt){
		evt.preventDefault()  //prevents navigational links from following the default 
	});
	
	$('#menu_add_room').click(function(evt){
			evt.preventDefault();
			setDialogValues(true);
			$('.room_name_container').removeClass('has-error');
			$('.room_name_container').removeClass('has-success');
			$('.room_name_container .glyphicon-ok, .room_name_container .glyphicon-remove').hide();
			$('.room_name_container .error_msg_a, .room_name_container .error_msg_b').hide();
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
			var elem = '<span class = "glyphicon glyphicon-plus"></span> Add New Room';
			$('#dynammic_title').html(elem);
		}
	}); // end of click event
	
	
	
	$('#room_name').blur(function(){
		checkRoomName($(this).val(), CHECK_ROOM_NAME);
		
	});
	
	$('#new_username').blur(function(){
		checkUserName($(this).val(), CHECK_USERNAME);
	});
	
	$('#room_select').change(function(){
		var value = $(this).val();
		value = value.split('_');
		value = '#Div_' + value[1];
		var room_showing = $('#sensors .rooms:not(:hidden)');
		room_showing.hide();
		$(value).show();
		//$(window).resize();		
	}); //end of change event
	
	
	$('#delete_btn').click(function(evt){
		DeleteRoom();
	});
	
	
	$('#room_edit_btn, #room_edit_btn_lg').click(function(evt){
		$('#add_room_btn:contains(Add Room)').text('Save Changes');
		setDialogValues(false);
		var elem = '<span class = "glyphicon glyphicon-edit"></span> Edit Room';
		$('#dynammic_title').html(elem);
		$('#room_form_main_container').modal('show');
		
	});


	$('#alarm_turn_off').click(function(){
			var target = $('#alarm_switch');
			target.removeClass( "alarm_on");
			target.addClass( "alarm_off");
			alarm_on = 0;
	});



	$('#login_btn').click(function(){
		var username = $('#username').val().trim();
		var password = $('#password').val().trim();
		login(username, password, AUTH_USER);
	});



	$('#menu_add_user').click(function(){
		$('#create_user_error').hide();
		$('.user_name_container').removeClass('has-error');
		$('.user_name_container').removeClass('has-success');
		$('.user_name_container .glyphicon-ok, .user_name_container .glyphicon-remove').hide();
		$('.user_name_container .error_msg_a, .user_name_container .error_msg_b').hide();
		
		$('#adduser_form_container').modal('show');
		
	
	});


	$('#create_user_btn').click(function(){

		var new_username = $('#new_username').val();
		var new_password = $('#new_password').val();
		var priviledge = $('#admin_priveledge').val();

		createUser(new_username, new_password, priviledge, CREATE_USER);
	});

	$('#user_logout_btn').click(function(){
		logout();
	});


	$(window).resize(function(){
		checkScreen();
	});
	
	
	$('.mobile_modal_close').click(function(){
		var target = $('#alert_sound');
		target[0].volume = 0;
		target[0].play();
		
	});
	
	

	
	$('.dropdown').on('show.bs.dropdown', function(){
        $('.glyphicon-menu-down').toggle();
		$('.glyphicon-menu-up').toggle();
    });
	
	$('.dropdown_btn').on('hidden.bs.dropdown', function(){
        $('.glyphicon-menu-down').toggle();
		$('.glyphicon-menu-up').toggle();
    });
	
	
	$('.dropdown-header').click(function(evt){
		evt.preventDefault();
		$(this).next('ul').toggle();
	});
	
	if(window.innerWidth >= 992){
		var target = $('#alert_sound');
		target[0].volume = 0;
		target[0].play();
		
	}

	

	
}); //end of ready function
