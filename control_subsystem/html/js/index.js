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
var canDelete = 0;


var room_prop = {};
room_prop['degrade_notification'] = 0;
room_prop['sleep_notification'] = 0;
room_prop['service_count'] = 0;
room_prop['distance_notification'] = 0;


var sleep_sound = 0;
var degrade_sound = 0;
var distance_sound = 0;
var service_sound = 0;


/*
	This function is called to turn on/off the 
	blinking white led. The blinking white led
	will be turned on when the lumens degrades
	and off when it is okay.
	
	parameters - 2 required
		ip : this is used to identify the room to turn on/off the blinking led
		state: identifies whether the blinking led should be turned on or off
*/

function whiteLed(ip,state){
	ip = ip.split('.');
	ip = ip.join('_');
	
	var target = '#white_led_' + ip;
	
	if(state){
		
		$(target).css({
			'-webkit-animation': 'blinkYellow 0.5s infinite',
			'-moz-animation': 'blinkYellow 0.5s infinite',
			'-ms-animation': 'blinkYellow 0.5s infinite',
			'-o-animation': 'blinkYellow 0.5s infinite',
			'animation': 'blinkYellow 0.5s infinite'
		});
	}
	
	else{
		
		$(target).css({
			'-webkit-animation': '',
			'-moz-animation': '',
			'-ms-animation': '',
			'-o-animation': '',
			'animation': ''
		});
	}
}


/*
	This function is called to turn on/off the 
	blinking red led. The blinking red led
	will be turned on when the red led degrades
	and off when it is okay.
	
	parameters - 2 required
		ip : this is used to identify the room to turn on/off the blinking led
		state: identifies whether the blinking led should be turned on or off
*/

function redLed(ip,state){
	ip = ip.split('.');
	ip = ip.join('_');
	
	var target = '#red_led_' + ip;
	if(state){
		//alert("if " + ip);
		$(target).css({
			'-webkit-animation': 'blinkRed 0.5s infinite',
			'-moz-animation': 'blinkRed 0.5s infinite',
			'-ms-animation': 'blinkRed 0.5s infinite',
			'-o-animation': 'blinkRed 0.5s infinite',
			'animation': 'blinkRed 0.5s infinite'
		});
	}
	
	else{
		//alert("else " + ip);
		$(target).css({
			'-webkit-animation': '',
			'-moz-animation': '',
			'-ms-animation': '',
			'-o-animation': '',
			'animation': ''
		});
	}
}


/*
	This function is called to turn on/off the 
	blinking green led. The blinking green led
	will be turned on when the red led degrades
	and off when it is okay.
	
	parameters - 2 required
		ip : this is used to identify the room to turn on/off the blinking led
		state: identifies whether the blinking led should be turned on or off
*/
function greenLed(ip,state){
	ip = ip.split('.');
	ip = ip.join('_');
	
	var target = '#green_led_' + ip;
	if(state){
		
		$(target).css({
			'-webkit-animation': 'blinkGreen 0.5s infinite',
			'-moz-animation': 'blinkGreen 0.5s infinite',
			'-ms-animation': 'blinkGreen 0.5s infinite',
			'-o-animation': 'blinkGreen 0.5s infinite',
			'animation': 'blinkGreen 0.5s infinite'
		});
	}
	
	else{
	
		$(target).css({
			'-webkit-animation': '',
			'-moz-animation': '',
			'-ms-animation': '',
			'-o-animation': '',
			'animation': ''
		});
	}
}


/*
	This function is called to turn on/off the 
	blinking blue led. The blinking red led
	will be turned on when the blue led degrades
	and off when it is okay.
	
	parameters - 2 required
			ip : this is used to identify the room to turn on/off the blinking led
			state: identifies whether the blinking led should be turned on or off
*/
function blueLed(ip,state){
	ip = ip.split('.');
	ip = ip.join('_');
	
	var target = '#blue_led_' + ip;
	if(state){
		
		$(target).css({
			'-webkit-animation': 'blinkBlue 0.5s infinite',
			'-moz-animation': 'blinkBlue 0.5s infinite',
			'-ms-animation': 'blinkBlue 0.5s infinite',
			'-o-animation': 'blinkBlue 0.5s infinite',
			'animation': 'blinkBlue 0.5s infinite'
		});
	}
	
	else{
	
		$(target).css({
			'-webkit-animation': '',
			'-moz-animation': '',
			'-ms-animation': '',
			'-o-animation': '',
			'animation': ''
		});
	}
}


/*
	This function is used to display the current time 
	and date on the banner (well class- bootstrap)
	
	paremeters - none
		
*/

function getDateTime(){
	var currentDate = new Date();
	$('#current_time').text(currentDate.toLocaleTimeString());
	$('#current_date').text(currentDate.toLocaleDateString());
	
}


/* 
	This function is used to render/update a donut chart for the read in lumens reading
	
	parameters - 3 required
		intensity: this is the read in lumens reading from the database 
		colorLabel: this text is displayed within the donut chart.
		roomIp: this is used to identify the donut chart to render or update

*/

function graphWhiteLight(intensity, colorLabel, roomIp){
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');


	var elem = "white_"+id_ip;
	var target = $('#'+elem);
	
	if(intensity > 514)
		intensity = 514;

	target.html('');
	
	
	var whiteDonut = Morris.Donut({
		element: elem,
		colors: ['#2a2a2a','#e0e0f4'],
  		data: [
				{value: 514 - intensity, label: ''},
    			{value: intensity, label: colorLabel}
    			
 			],
		resize: true
		});

	whiteDonut.select(1);
}


/* 
	This function is used to render/update a donut chart for the read in red sensor reading
	
	parameters - 3 required
		intensity: this is the read in red sensor reading from the database 
		colorLabel: this text is displayed within the donut chart.
		roomIp: this is used to identify the donut chart to render or update

*/


function graphRedLight(intensity, colorLabel, roomIp){
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');

	colorLabel += ' (%)';
	var elem = "red_"+id_ip;
	var target = $('#'+elem);

	target.html('');
	
	var redDonut = Morris.Donut({
		element: elem,
		colors: ['#2a2a2a','#ff0000'],
  		data: [
				{value: (100 - intensity), label: ''},
    			{value: intensity, label: colorLabel}
    			
 			],
		resize: true
		});

	redDonut.select(1);

	
	/*var firstTarget  = $('#roomIp svg text tspan:eq(0)');
	var secondTarget = $('#roomIp svg text tspan:eq(1)');
	var thirdTarget  = $('#roomIp svg path:eq(1)');

	alert(firstTarget.html() + "  " + secondTarget.html() + "  "  + thirdTarget.html());

	
	//firstTarget.text("" + colorLabel);
	//secondTarget.text("" + intensity);*/


}

/* 
	This function is used to render/update a donut chart for the read in green sensor reading
	
	parameters - 3 required
		intensity: this is the read in green sensor reading from the database 
		colorLabel: this text is displayed within the donut chart.
		roomIp: this is used to identify the donut chart to render or update

*/

function graphGreenLight(intensity, colorLabel, roomIp){
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');
	colorLabel += ' (%)';

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


/* 
	This function is used to render/update a donut chart for the read in blue sensor reading
	
	parameters - 3 required
		intensity: this is the read in blue sensor reading from the database 
		colorLabel: this text is displayed within the donut chart.
		roomIp: this is used to identify the donut chart to render or update

*/
function graphBlueLight(intensity, colorLabel, roomIp){
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');
	colorLabel += ' (%)';

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


/* 
	This function is used to ensure that menu options and tags are responsive to user's screen
	size. 
	
	parameters - none

*/


function checkScreen(){
	if(canEdit){	
		if(window.innerWidth <= 769){
			$('.desktop_submenu').hide();
			$('.mobile_submenu').show();
		}
	
		else{
			$('.mobile_submenu').hide();
			$('.desktop_submenu').show();
			$('.desktop_submenu').css('display','inline-block');
		}
	}

	else{
		$('.mobile_submenu').hide();
		$('.desktop_submenu').hide();
	}
	
	if(!canDelete && canEdit){
		
		if(window.innerWidth <= 769){
			$('#room_delete_btn').hide();
			$('#room_edit_btn').show();
		}
		else{
			$('.desktop_submenu').hide();
			$('#room_edit_btn_lg').show();
		}
	}
}


/*
	This function sends the new user information to the backend scripts
	when new a new user is created
	
	parameters - 4 required
		username : the new user's username (a required field when the user needs to log in)
		password : the new user's password (a required field when the user needs to log in)
		priviledge: this is used to state wheather the user gets admin priviledge or not
		serverPage: the location of the backend script that will process this information
 
*/


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
			else{
		
				$('#create_user_error').show();
			}
		});

}



/*
	This function is used to load room and sensor information from the database when 
	the page is loaded for the first time. It is also used to update the information of
	a room when a user makes any changes
	
	parameters - 1 required, 1 optional
		serverPage: the location of the backend script that will process this information (required)
		userAction: this is used to identify if the functionis called to load data from the database
					or to update information of a room (optional)
*/
function loadSensorData(serverPage, userAction = true){

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
			
			if(data[0] in room_prop)
				continue;
			waketime = minutesToTime(data[1]);
			
			CreateRoom(data[4], data[0], waketime, data[2], 1, userAction);
			
		} 
	  }
	});	
}


/*
	This function goes through the room_prop global variable checking if any room has degraded
	
	parameters - none

*/

function checkForDegradation(){
	var degradation_found = 0;
	for(var ip in room_prop){
		  
		if(ip != 'degrade_notification' && ip != 'sleep_notification' && ip != 'service_count' && ip != 'distance_notification'){
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
	}
	
	if(degradation_found){
		//soundAlarm();
		//setTimeout(silentAlarm, 1500);

		degrade_sound = 1;
		
	}
	
}



/*
	This function goes through the room_prop global variable checking if any room is in sleep mode
	
	parameters - none

*/
function checkForSleepMode(){
	var sleep_mode_found = 0;
	
	for(ip in room_prop){
		if(ip != 'degrade_notification' && ip != 'sleep_notification' && ip != 'service_count' && ip != 'distance_notification'){
			if(room_prop[ip]['sleep'] && !room_prop[ip]['sleep_show']){
				room_prop[ip]['sleep_show'] = 1;
				sleep_mode_found = 1;
			}
		}
	}
	
	if(sleep_mode_found){
		//soundAlarm();
		//setTimeout(silentAlarm, 1500);

		sleep_sound = 1;
		
	}
}


/*
	This function goes through the room_prop global variable checking if any room lighing fixture is below 8 feets
	
	parameters - none

*/


function checkForDistance(){
	var distance_error_found = 0;
	
	for(ip in room_prop){
		if(ip != 'degrade_notification' && ip != 'sleep_notification' && ip != 'service_count' && ip != 'distance_notification'){
			if(room_prop[ip]['distance'] && !room_prop[ip]['distance_show']){
				room_prop[ip]['distance_show'] = 1;
				distance_error_found = 1;
			}
		}
	}
	
	if(distance_error_found){
		//soundAlarm();
		//setTimeout(silentAlarm, 1500);

		distance_sound = 1;
		
	}
	
}

/* 
	This function is to reset the signal delete variable that checks if a room was deleted from a different device
	
	parameters - none
*/

function resetDeleteStat(){
	for(var ip in room_prop){
		if(ip != 'degrade_notification' && ip != 'sleep_notification' && ip != 'service_count' && ip != 'distance_notification')
			room_prop[ip]['delete_stat'] = 0;
	}
}

/* 
	This function is to set the signal delete variable that checks if a room was deleted from a different device
	
	parameters - none
*/

function checkDeleteStat(){
	
	for(var ip in room_prop){
		if(ip != 'degrade_notification' && ip != 'sleep_notification' && ip != 'service_count' && ip != 'distance_notification'){
			if(room_prop[ip]['delete_stat'] == 0){
				DeleteRoom(room_prop[ip]['name'], ip);
			}
		}			
	}

	var result;
	result = $('.notification .distance_list').html().trim();	
	if(result == ""){
		$('.distance_divider').css({'display': 'none'});
		$('.distance_header').css({'display': 'none'});
	}


	result = $('.notification .sleep_mode_list').html().trim();
	if(result == ""){
		$('.sleep_divider').css({'display': 'none'});
		$('.sleep_mode_header').css({'display': 'none'});
	}
}


/*
	This function reads all sensor values from the database and updates the web page if any changes was made
	parameters - none
*/

function readValuesFromAllSensors(){
	$.get(ALL_ROOM_DEGRADE,
		function(data, status){
			data = data.split("|");
			var service_count = 0;
			
			for(var i = 0; i < data.length - 1; i++){
				var temp = data[i].split(",");
				room_prop[temp[0]]['name'] = temp[1];
				if(temp[0]){
					room_prop[temp[0]]['delete_stat'] = 1;
					
				}
				
				if(parseInt(temp[9])){
					var current = '#sensors .rooms:not(:hidden) .service_message';
					$(current).show();
				}
				
				else{
					var current = '#sensors .rooms:not(:hidden) .service_message';
					$(current).hide();
				}

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
					
					if(parseInt(temp[2])){
						room_prop[temp[0]]['red_color_degrade'] = 1;
						redLed(temp[0], 1);
					}
					else{
						redLed(temp[0], 0);
					}
					
					if(parseInt(temp[3])){
						room_prop[temp[0]]['green_color_degrade'] = 1;
						greenLed(temp[0], 1);
					}
					else{
						greenLed(temp[0], 0);
					}
					
					if(parseInt(temp[4])){
						room_prop[temp[0]]['blue_color_degrade'] = 1;
						blueLed(temp[0], 1);
					}
					else{
						blueLed(temp[0], 0);
					}

						
					
					
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
						redLed(temp[0], 0);
					}
					
					if(!parseInt(temp[3])){
						room_prop[temp[0]]['green_color_degrade'] = 0;
						room_prop[temp[0]]['green_color_degrade_show'] = 0;
						
						greenLed(temp[0], 0);
					}
					
					if(!parseInt(temp[4])){
						room_prop[temp[0]]['blue_color_degrade'] = 0;
						room_prop[temp[0]]['blue_color_degrade_show'] = 0;
						
						blueLed(temp[0], 0);
					}
					
					room_prop[temp[0]]['color_degrade'] = 0;
					if(room_prop[temp[0]]['color_degrade_show']){
						$('.notification #color_degrade_'+ temp[1]).remove();
						
						room_prop[temp[0]]['color_degrade_show'] = 0;
						if(room_prop['degrade_notification'] > 0)
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
						whiteLed(temp[0], 1);
					}
					
				}
				else{
					room_prop[temp[0]]['light_degrade'] = 0;
					if(room_prop[temp[0]]['light_degrade_show']){
						$('.notification #light_degrade_'+ temp[1]).remove();
						
						room_prop[temp[0]]['light_degrade_show'] = 0;
						if(room_prop['degrade_notification'] > 0)
							room_prop['degrade_notification'] -= 1;
						
					}
					
					var result = $('.notification .degradation_list').html().trim();
					if(result == "")
						$('.degradation_header').css({'display': 'none'});
					whiteLed(temp[0], 0);
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
						
						//room_prop[temp[0]]['sleep_show'] = 1;
						room_prop['sleep_notification'] += 1;
					}
				}
				else{
					room_prop[temp[0]]['sleep'] = 0;
					if(room_prop[temp[0]]['sleep_show']){
						$('.notification #sleep_'+ temp[1]).remove();
						room_prop[temp[0]]['sleep_show'] = 0;
						if(room_prop['sleep_notification'] > 0)
							room_prop['sleep_notification'] -= 1;
					}
					
					var result = $('.notification .sleep_mode_list').html().trim();
					if(result == ""){
						$('.sleep_divider').css({'display': 'none'});
						$('.sleep_mode_header').css({'display': 'none'});
					}
					
				}
				

				if(parseInt(temp[8]) != 8){
					room_prop[temp[0]]['distance'] = 1;
					if(!room_prop[temp[0]]['distance_show']){
						var elem = '<li class="room_distance_warning" id ="distance_' + temp[1] + '">' + 
										'<strong> Room ' + temp[1] + ' is below 8ft </strong>'+ 
									'</li>';
									
						$('.notification .distance_list').append(elem);
						$('.distance_divider').css({'display': 'block'});
						$('.distance_header').css({'display': 'block'});
						
						//room_prop[temp[0]]['distance_show'] = 1;
						room_prop['distance_notification'] += 1;
						
					}
				}
				
				else{
					room_prop[temp[0]]['distance'] = 0;
					if(room_prop[temp[0]]['distance_show']){
						$('.notification #distance_'+ temp[1]).remove();
						room_prop[temp[0]]['distance_show'] = 0;
						if(room_prop['distance_notification'] > 0)
							room_prop['distance_notification'] -= 1;
					}
					
					var result = $('.notification .distance_list').html().trim();
				
					if(result == ""){
					
						$('.distance_divider').css({'display': 'none'});
						$('.distance_header').css({'display': 'none'});
					}
					
				}
				
				
				
			}
			
			
		checkDeleteStat();
		resetDeleteStat();
			
		});
		
		
		$('.notification_count').text(parseInt(room_prop['degrade_notification']) + parseInt(room_prop['sleep_notification']) + parseInt(room_prop['service_count']) + parseInt(room_prop['distance_notification']));
		$('.degrade_notification_count').text(room_prop['degrade_notification']);
		$('.sleep_notification_count').text(room_prop['sleep_notification']);
		$('.service_notification_count').text(room_prop['service_count']);
		$('.distance_notification_count').text(room_prop['distance_notification']);
		
}

/*
	This function reads the current sensor values from the database and updates the web page if any changes was made
	
	parameters - none
*/

function readSensorsValues(){
	
	getDateTime();
	getUnpairedIp();
	loadSensorData(LOAD_DATA, false);
	
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

		  for(var i = 1; i < data.length - 2; i ++)
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
			 
			  $('.chart').show();
			  graphWhiteLight(temp[4], "Brightness\n\n(Lumens)", ip);
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
			 	
				
			 	
			 	if((whiteLight != temp[4]) && temp[8] && isWhiteDegraded){  
					isWhiteDegraded = 1
					graphWhiteLight(temp[4], "Brightness Degraded\n(Lumens)",ip);
				}

				else if((whiteLight != temp[4]) && temp[8] && !isWhiteDegraded){  //turns on degraded sign
					isWhiteDegraded = 1
					graphWhiteLight(temp[4], "Brightness Degraded\n(Lumens)",ip);
				}

				else if((whiteLight != temp[4]) && !temp[8] && isWhiteDegraded){  //turns off degraded sign
					isWhiteDegraded = 0
					graphWhiteLight(temp[4], "Brightness\n\n(Lumens)",ip);
				}

				else if((whiteLight != temp[4]) && !temp[8] && !isWhiteDegraded){  //turns off degraded sign
					isWhiteDegraded = 0
					graphWhiteLight(temp[4], "Brightness\n\n(Lumens)",ip);
				}

				else if(temp[8] && !isWhiteDegraded){
					isWhiteDegraded = 1;
			  		graphWhiteLight(temp[4], "Brightness Degraded\n(Lumens)",ip);
				}

				else if(!temp[8] && isWhiteDegraded){
					isWhiteDegraded = 0;
			  		graphWhiteLight(temp[4], "Brightness\n\n(Lumens)",ip);
				}
			 	whiteLight = temp[4];
				room_prop[ip]['white'] = temp[4];   /////////
			  
		   }




		  	if((redLight != temp[1]) || (temp[5] != isRedDegraded)){
			 	
				
			 	
			 	if((redLight != temp[1]) && temp[5] && isRedDegraded){  
					isRedDegraded = 1
					graphRedLight(temp[1], "Red Led\nDegraded",ip);
				}

				else if((redLight != temp[1]) && temp[5] && !isRedDegraded){  //turns on degraded sign
					isRedDegraded = 1
					graphRedLight(temp[1], "Red Led\nDegraded",ip);
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
			  		graphRedLight(temp[1], "Red Led\nDegraded",ip);
				}

				else if(!temp[5] && isRedDegraded){
					isRedDegraded = 0;
			  		graphRedLight(temp[1], "Red",ip);
				}
			 	redLight = temp[1];
				room_prop[ip]['red'] = temp[1];   /////////
			  
		   }


		   if((greenLight != temp[2]) || (temp[6] != isGreenDegraded)){
			 	
			 	
			 	if((greenLight != temp[2]) && temp[6] && isGreenDegraded){  
					isGreenDegraded = 1;
					graphGreenLight(temp[2], "Green Led\nDegraded",ip);
				}

				else if((greenLight != temp[2]) && temp[6] && !isGreenDegraded){  //turns on degraded sign
					isGreenDegraded = 1;
					graphGreenLight(temp[2], "Green Led\nDegraded",ip);
				}

				else if((greenLight != temp[2]) && !temp[6] && isGreenDegraded){  //turns off degraded sign
					isGreenDegraded = 0;
					graphGreenLight(temp[2], "Green",ip);
				}

				else if((greenLight != temp[2]) && !temp[6] && !isGreenDegraded){  //turns off degraded sign
					isGreenDegraded = 0;
					graphGreenLight(temp[2], "Green",ip);
				}

				else if(temp[6] && !isGreenDegraded){
					isGreenDegraded = 1;
			  		graphGreenLight(temp[2], "Green Led\nDegraded",ip);
				}

				else if(!temp[6] && isGreenDegraded){
					isGreenDegraded = 0;
			  		graphGreenLight(temp[2], "Green",ip);
				}
			 	greenLight = temp[2]; 
				room_prop[ip]['green'] = temp[2];   /////////
		   }

		   if((blueLight != temp[3]) || (temp[7] != isBlueDegraded)){
			 	
				
			 	
			 	if((blueLight != temp[3]) && temp[7] && isBlueDegraded){  
					isBlueDegraded = 1
					graphBlueLight(temp[3], "Blue Led\nDegraded",ip);
				}

				else if((blueLight != temp[3]) && temp[7] && !isBlueDegraded){  //turns on degraded sign
					isBlueDegraded = 1
					graphBlueLight(temp[3], "Blue Led\nDegraded",ip);
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
			  		graphBlueLight(temp[3], "Blue Led\nDegraded",ip);
				}

				else if(!temp[7] && isBlueDegraded){
					isBlueDegraded = 0;
			  		graphBlueLight(temp[3], "Blue",ip);
				}
			 	blueLight = temp[3]; wake_value
				room_prop[ip]['blue'] = temp[3];   /////////
		   }
			
		 }
	
		
		var room_showing = '#sensors .rooms:not(:hidden)';
		
		
		
		
		$(room_showing + ' #waketime_lg').text("" + minutesToTime(parseInt(data[12])));
		$(room_showing + ' #wake_value').text('Wake Time: ' + minutesToTime(parseInt(data[12])));
		
		$(room_showing + ' #threshold_lg').text("" + data[13] + "%");
		$(room_showing + ' #thresh_value').text('Intensity Threshold: ' + data[13] + '%' );
		
		
		
	  });	
	  
	  readValuesFromAllSensors();
	  checkForDegradation();
	  checkForSleepMode();
	  checkForDistance();

	if(sleep_sound || degrade_sound || distance_sound || service_sound){
		soundAlarm();
		setTimeout(silentAlarm, 1500);
		sleep_sound = 0;
		degrade_sound = 0;
		distance_sound = 0;
		service_sound = 0;
	}
	   
}

/* 
	This function is used to render menus meant for logged in users
	
	parameters - none

*/

function loginSuccess(){
	$.get(AUTH_CONFIRMATION,
	  function(data, stat){
	
		if(data == "admin" || data == "user"){
			if(data == "admin"){
				canEdit = 1;
				canDelete = 1;
			}
			
			else if(data == "user"){
				canEdit = 1;
				canDelete = 0;
			}
			
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
				$('#room_edit_btn_lg').show();
			}
		}
	});
	
}

/* 
	This function is used to display error messages for invalid login entries
	
	parameters - none

*/

function loginFail(){
	$('.login_error').css({'display': 'inline'});

}


/*
	This function communicates with the backend script and ensures that all
	session variables are destroyed
*/
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
	canDelete = 0;
	checkScreen();
}

/*
	This function sends the user entered login entries to a backend script that 
	verifies that the entries are valid
	
	paremeters - 3 required
		user: user's userName
		pass: user's password
		serverPage: location of backend script that will process the sent data
*/

function login(user, pass, serverPage){
	$.post(serverPage,
	{
		username : user,
		password : pass
	},
		function(data, status){
			
			if(data == 'admin' || data == "user"){
				if(data == "admin"){
					canEdit = 1;
					canDelete = 1;
				}
				userLogin = 1;
				checkScreen();
				loginSuccess();
			}

			else
				loginFail();
	});

}

/*
	This function is used to turn on the alert sound when degradtion is detected, a room is in sleep mode or
	when a lighting fixture is below 8 feet.

	parameters - none
*/

function soundAlarm(){
	
	var target = $('#alert_sound');
	target[0].currentTime = 0;
	target[0].volume = 1;
}


/*
	This function is used to turn off the alert sound
	
	parameters - none

*/

function silentAlarm(){	
	var target = $('#alert_sound');
	target[0].volume = 0;
}

/*
	This function is used to check if an unpaired lighting ip address is in the database. If there is, the 
	unpaired lighting ip will be used when a user adds a roomIp
	
	parameters - none
*/

function getUnpairedIp(){
	$.get(AVAILABLE_IP,
	  function(data, stat){
		  if(data.length > 5){
			  
			  UNPAIRED_IP = data.trim();
		  }
	  });
}

/*
	This function is used to set the select option values for the add room wake time
	
	parameters -  none
*/

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

/*
	This function is used to set the select option values for the add room intensity values
	
	parameters -  none
*/
function loadLightIntensityValues(){
	var target = $('#threshold');

	var options = "";

	var temp = "";
	for(var i = 0; i <= 100; i += 10){
		temp = "<option value = '" + i + "'> " + i + "</option>"; 
		options += temp;
	}

	target.append(options);
	

}

/*
	This function is used to send sensor settings data to a script running on the serverPage
	
	parameters - 4 required
		roomName: Entered room name
		roomIp: Hidden ip field data
		wakeTime: Entered wake time for the lighting system
		thresh: Entered threshold value for the lighting system
		serverPage: location of script that receives the data

*/
	
function sendData(roomName, roomIp, wakeTime, thresh, serverPage){
	$.post(serverPage,
	{
		room_name : roomName,
		room_ip   : roomIp,
		wake_time : wakeTime,
		threshold : thresh,
	},
		function(data, status){
			
	});
}

/*
	This function is used to notify a script running on the serverpage that a delete	
	command has been issued
	
	parameters - 2 required
		serverPage: location of script that receives the notification
		roomIp: the ip of the room to be deleted

*/

function sendDeleteCommand(serverPage, roomIp){
	$.post(serverPage,
	{
		room_ip : roomIp
	},

	function(data, status){
		console.log("delete");	
	});
}

/*
	This function is used to send edit notification to a script running on the web server
	
	6 parameters - required
		serverPage: this is the script running on the web server that recieves the command
		roomName: the name of the room being edited
		roomIp: the ip of the room being edited
		waketime: the waketime of the room being edited
		thresh: the threshold of the room being edited
		code: this signals what data was changed
	
*/

function sendEditCommand(serverPage, roomName, roomIp, wakeTime, thresh, code){
	$.ajaxSetup({async: false});
	$.post(serverPage, 
	{
		room_name      : roomName,
		room_ip        : roomIp,
		wake_time      : wakeTime,
		threshold: thresh,
		edit_code      : code
	},
		function(data, status){
			stat =  data;

			
		});
	return stat;

}

/*
	After a user makes changes to a sensor settings, this function runs
	and checks if there is any difference between the previous setting
	and the current one. if there is, it sends the new data to  the 
	sendEditCommand function.
	
	parameters - 4 required
		roomName: room name being changed
		roomIp: the ip of the room being modified
		wakeTime: the entered new wake time of the room be modified
		threshold: the entered new threshold value of the room being modified
*/

function SaveRoom(roomName, roomIp, wakeTime, threshold){

	var current = '#sensors .rooms:not(:hidden) ';

	var prev_room_name   = $(current +'.aroom_name').text().trim();

	//var prevWakeTime = $(current + ' .aroom_wake_time').text().split(":");

	var prevWakeTime = $(current +  ' #waketime_lg').text().split(":");
	

	var wakeHr = prevWakeTime[0].trim();
	
	
	prevWakeTime = prevWakeTime[1].split(" ");
	var wakeMn = prevWakeTime[0];
	var meridiem = prevWakeTime[1];


	prevWakeTime = timeToMinutes(wakeHr, wakeMn, meridiem);
	var prev_thresh = $(current +'.aroom_light_threshold').text().split(":")[1].trim();
	prev_thresh = prev_thresh.slice(0, -1);


	var code = "";

	if(prevWakeTime != wakeTime)
		code += wakeTime + "|";
	else
		code += "N|";


	if(prev_thresh !=  threshold)
		code += threshold + "|";
	else
		code += "N|";

	
	
	if(code == "N|N|")
		return;

	var status = sendEditCommand(EDIT_ROOM_PAGE, roomName, roomIp, wakeTime, threshold, code);
	

	
	status = parseInt(status);
	if(status == 1){
		wakeTime = minutesToTime(wakeTime);
		$(current + '.aroom_name').text(roomName);

		$(current + ' #waketime_lg').text(wakeTime);
		$(current + ' #threshold_lg').text(threshold + "%");
		$(current + ' #thresh_value').text('User Set Intensity Threshold: ' + threshold);
		$(current + ' #wake_value').text('User Set Wake Time: ' + wakeTime );
		
		
		
		
		var target = $('#room_select');
		var value = target.val();
		
		value = value.split('_');
		var oldval = value[1];
		var newval = value[0] + '_' +  roomName;
		
		
		$('#room_select option:contains(' + oldval + ')').val(newval);
		$('#room_select option:contains(' + oldval + ')').text(roomName);
		
		$(current).attr('id', "Div_" + roomName);
	
		target.val(newval);
		var status_info = "Room changes Saved"
	}
	else if(status == 2)
		var status_info = "Can not make changes when room is in service";
	else
		var status_info = "Room could not be updated";
	
	message = $('#alert');
	message.fadeIn()
	message.text(status_info);
	message.fadeOut(3000);
}






function CreateRoom(roomName, roomIp, wakeTime, threshold, isPageLoading, userAction){
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
	room_prop[roomIp]['delete_stat'] = 0;
	room_prop[roomIp]['distance_show'] = 0;
	
	
	if(sensorCount == 0){
		$('#sensor_container').show();
		$('#room_title h4').show();
		var newRoomTag = '<option value = "Room_' + roomName + '">' + roomName + '</option>'
						
		$('#room_select').append(newRoomTag).show();
		$('.btn_container').show();
		$('#no_room').hide(); 
		$('.acknowledgement').show();
	}
	
	else{
		var newRoomTag = '<option value = "Room_' + roomName + '">' + roomName + '</option>';
		if(userAction)
			$('#room_select').append(newRoomTag).val("Room_" + roomName);
		else
			$('#room_select').append(newRoomTag);
	}
	
	
	
	var div  = "Div_" + roomName;
	var id_ip = roomIp.split('.');
	id_ip = id_ip.join('_');
	

	var newDivTag  =  
		'<div class = "container-fluid rooms" id = "' + div + '">' +
			'<div class = "service_message container col-sm-6 col-sm-offset-3 col-xs-9 col-lg-4 col-lg-offset-4">' + 
				'<h3> Room is being serviced!!! </h3>' + 
			'</div>' + 
			'<div class = "row" id = "all_sensor_values">' +  
					
				'<div class = "user_set_values">' + 
					'<span id = "aroom_name" class = "aroom_name">' + roomName +'</span>' + 
					'<input type = "hidden"  class = "aroom_ip" value = "' + roomIp + '" />' + 

					'<h3 class = "aroom_wake_time col-xs-4 col-xs-offset-2 large_screen_view first"> Wake Time</h3>' + 
					'<h3 class = "aroom_light_threshold col-xs-4 large_screen_view"> Intensity Threshold</h3>' +
 
					'<h3 class = "aroom_wake_time col-xs-12 small_screen_view" id = "wake_value" > Wake Time: ' + wakeTime + '</h3>' + 
					'<h3 class = "aroom_light_threshold col-xs-12 small_screen_view" id = "thresh_value"> Intensity Threshold: ' + threshold + '%</h3>' + 
				'</div>' + 
					
			'</div>' + 

			'<div class = "row large_screen_view" id = "set_values">' + 
				'<h3 class = "aroom_wake_time_value col-xs-4 col-xs-offset-2 first" id = "waketime_lg">' + wakeTime + '</h3>' + 
				'<h3 class = "aroom_light_threshold_value col-xs-4" id = "threshold_lg">' + threshold + '%</h3>' + 
			'</div>' + 
			
			'<div class = "row chart blink_led">' + 
				'<div class = "col-md-3 col-sm-6">' + 
					'<div id = "white_' + id_ip + '"></div>' + 
					'<div class="led-box">' + 
						'<div class="led-yellow" id = "white_led_' + id_ip + '"></div>' + 
					'</div>' + 
				'</div>' +

				'<div class = "col-md-3 col-sm-6">' + 
					'<div id = "red_' + id_ip + '"></div>' +
					'<div class="led-box">' + 
						'<div class="led-red" id = "red_led_' + id_ip + '"></div>' + 
					'</div>' + 
				'</div>' + 

				'<div class = "col-md-3 col-sm-6">' + 
					'<div id = "green_' + id_ip + '"></div>' +
					'<div class="led-box">' + 
						'<div class="led-green" id = "green_led_' + id_ip + '"></div>' + 
					'</div>' +
				'</div>' + 

				'<div class = "col-md-3 col-sm-6">' + 
					'<div id = "blue_' + id_ip + '"></div>' + 
					'<div class="led-box">' + 
						'<div class="led-blue" id = "blue_led_' + id_ip + '"></div>' + 
					'</div>' + 
				'</div>' + 
			'</div>' +

			
		'</div>';

	
	
	
	
	var room_showing = $('#sensors .rooms:not(:hidden)');

	if(userAction || sensorCount == 0){
		room_showing.hide();
		$('#sensors').append(newDivTag);
	}

	else{
		$('#sensors').append(newDivTag);
		$('#'+div).hide();
	}
	

	if(!isPageLoading){
		message.fadeIn();
		message.text("Room Created Successfully");
		message.fadeOut(3000);
	}
	

	sensorCount ++;
	$('#sensor_count').val(sensorCount);
}

function deleteNotificationValue(room_ip, room_name){
	////
	

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
		if(room_prop['degrade_notification'] < 0)
			room_prop['degrade_notification'] = 0;
		
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
		if(room_prop['sleep_notification'] < 0)
			room_prop['sleep_notification'] = 0;
	}
	
	var result = $('.notification .sleep_mode_list').html().trim();
	if(result == "")
		$('.sleep_divider').css({'display': 'none'});
	
	
	//////////
	room_prop[room_ip]['sleep'] = 0;
	if(room_prop[room_ip]['distance_show']){
		$('.notification #distance_'+ room_name).remove();
		room_prop[room_ip]['distance_show'] = 0;
		room_prop['distance_notification'] -= 1;
		if(room_prop['distance_notification'] < 0)
			room_prop['distance_notification'] = 0;
	}
	
	var result = $('.notification .distance_list').html().trim();
	if(result == "")
		$('.distance_divider').css({'display': 'none'});
	

	
	$('.notification_count').text(parseInt(room_prop['degrade_notification']) + parseInt(room_prop['sleep_notification']) + parseInt(room_prop['service_count']) + parseInt(room_prop['distance_notification']));
	$('.degrade_notification_count').text(room_prop['degrade_notification']);
	$('.sleep_notification_count').text(room_prop['sleep_notification']);
	$('.service_notification_count').text(room_prop['service_count']);
	$('.distance_notification_count').text(room_prop['distance_notification']);
	delete room_prop[room_ip];
	
}



function DeleteRoom(name, ip){
	
	if(name && ip){
		var div  = "#Div_" + name;
		var room_tag = '#sensors ' + div;
		var room = $(room_tag);
		var room_ip = ip;
		var room_name = name;
		
	}
	else{
		var room_tag = '#sensors .rooms:not(:hidden)';
		var room = $(room_tag);
		var room_ip = $(room_tag + ' input[type = "hidden"]').val();
		var room_name = $(room_tag + ' .aroom_name').text().trim();	
	}
	sendDeleteCommand(DELETE_ROOM_PAGE, room_ip);
	deleteNotificationValue(room_ip, room_name);
	

	room.remove();
	//var target = $('#room_select :selected');

	var target = $('#room_select option[value = "Room_' + room_name + '"');
	var chart_target = "Div_" + room_name;

	var message = $('#alert');
	var opt = target.next();
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
			$('#room_title h4').hide();
			$('.acknowledgement').hide();
			graphLoaded = 0;
			$('.btn_container').hide();
			message.fadeOut(3000);
			$('#delete_room_container').modal('hide');
			
			return;
		}
	}
	target.remove();
	$('#' + chart_target + ' .chart').remove();
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

	else if(meridiem == 'AM' && hour == 12){
		totalTime = 0;
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
	
	if(wakeHr >= 0 || wakeHr <= 12){

		if(wakeHr == 0)
			wakeHr = 12;

		if(waketime < 720)
			wakeMeridiem = "AM";
		else
			wakeMeridiem = "PM";
	}


	if(wakeHr > 12){
		wakeMeridiem = "PM";
		wakeHr = parseInt(wakeHr % 12);
	}

	
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
	
	var threshold = $('#threshold').val().trim();
	
	
	
	if(action == ADD_ACTION){
		var wakeTime = timeToMinutes(wakeTimeHr, wakeTimeMin, wakeTimeMeridiem);
		sendData(roomName, roomIp, wakeTime, threshold, ADD_ROOM_PAGE);
		wakeTime = minutesToTime(wakeTime);
		CreateRoom(roomName, roomIp, wakeTime, threshold, 0);
	}
		
	else{
		var target = '.rooms:not(:hidden)';
		var wakeTime = timeToMinutes(wakeTimeHr, wakeTimeMin, wakeTimeMeridiem);
		roomIp = $(target + ' .aroom_ip').val();
		SaveRoom(roomName, roomIp, wakeTime, threshold);

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
		var wakeHr = "07";
		var wakeMn = "00";
		var meridiem = "AM";
		var threshold = "100";
	}
	
	else{
		var target = '#sensors .rooms:not(:hidden)';
		var roomName = $(target + ' .aroom_name').text()
		if(roomName)
			roomName = roomName.trim();	
		else
			roomName = "";

		var wakeTime = $(target + ' #waketime_lg').text().split(":");
		var wakeHr = wakeTime[0].trim();
		

		wakeTime = wakeTime[1].split(" ");
		
		var wakeMn = wakeTime[0];
		var meridiem = wakeTime[1];

		
		
		var threshold = $(target + ' #thresh_value').text().split(":")[1].trim();
		
		threshold = threshold.split("%");
		threshold = threshold[0];
		
	
	}
	
	$('#room_name').val(roomName);
	
	$('#room_wake_hr').val(wakeHr);
	$('#room_wake_min').val(wakeMn);
	$('#room_wake_meridiem').val(meridiem);
	
	$('#threshold').val(threshold);
	
	
}


function checkRoomName(roomName, serverPage){
	$('.room_name_container').removeClass('has-success');
	$('.room_name_container').removeClass('has-error');
	$('.room_name_container .glyphicon-ok, .room_name_container .error_msg_a').hide()
	$('.room_name_container .error_msg_b, .room_name_container .error_msg_b, .room_name_container .glyphicon-remove').hide();
	
	if(roomName.length <= 4){
		$('.room_name_container').addClass('has-error');
		$('.room_name_container .glyphicon-remove').show();
		$('.room_name_container .error_msg_b').show();	
		return false;
	}


	var code;
	var valid = true;
	var temp = roomName.toLowerCase();

	for(var i = 0; i < temp.length; i++){
		code  = temp.charCodeAt(i);
		if((code > 96 && code < 123) || (code > 47 && code < 58))
			continue;
		else{
			valid = false;
			break;
		}
	}


	if(!valid){
		$('.room_name_container').addClass('has-error');
		$('.room_name_container .glyphicon-remove').show();
		$('.room_name_container .error_msg_c').show();	
		return false;
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
	
	return true;
}




function checkUserName(userName, serverPage){
	$('.user_name_container').removeClass('has-success');
	$('.user_name_container').removeClass('has-error');
	$('.user_name_container .glyphicon-ok, .user_name_container .error_msg_a').hide()
	$('.user_name_container .error_msg_b, .user_name_container .error_msg_c,.user_name_container .glyphicon-remove').hide();
	
	if(userName.length <= 4){
		$('.user_name_container').addClass('has-error');
		$('.user_name_container .glyphicon-remove').show();
		$('.user_name_container .error_msg_b').show();	
		return false;
	}
	
	var code;
	var valid = true;


	var temp = userName.toLowerCase();

	for(var i = 0; i < temp.length; i++){
		code  = temp.charCodeAt(i);
		if((code > 96 && code < 123) || (code > 47 && code < 58))
			continue;
		else{
			valid = false;
			break;
		}
	}

	if(!valid){
		$('.user_name_container').addClass('has-error');
		$('.user_name_container .glyphicon-remove').show();
		$('.user_name_container .error_msg_c').show();	
		return false;
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
		});
	
	return true;
}


$(document).ready(function(){
	//This function runs when the the body finish loading
	
		
	checkScreen();
	loadWakeTimeValues();
    loadLightIntensityValues();
	
	loginSuccess();

	$(window).resize(function(){
		checkScreen();
		
		var target = '.rooms:not(:hidden)';
		var ip = $(target + ' .aroom_ip').val();

		if(!ip || !graphLoaded)
			return;

		if(isWhiteDegraded)
			graphWhiteLight(whiteLight, "Brightness Degraded\n(Lumens)",ip);
		else
			graphWhiteLight(whiteLight, "Brightness\n\n(Lumens)",ip);

		
		if(isRedDegraded)
			graphRedLight(redLight, "Red\nDegraded",ip);
		else
			graphRedLight(redLight, "Red",ip);


		if(isGreenDegraded)
			graphGreenLight(greenLight, "Green\nDegraded",ip);
		else
			graphGreenLight(greenLight, "Green",ip);

		
		if(isBlueDegraded)
			graphBlueLight(blueLight, "Blue\nDegraded",ip);
		else
			graphBlueLight(blueLight, "Blue",ip);

	});
	
	
	$(".admin_view").click(function(evt){
		evt.preventDefault()  //prevents navigational links from following the default 
	});
	
	$('#menu_add_room').click(function(evt){
			evt.preventDefault();
			setDialogValues(true);
			$('.room_name_container').removeClass('has-error');
			$('.room_name_container').removeClass('has-success');
			$('.room_name_container .glyphicon-ok, .room_name_container .glyphicon-remove').hide();
			$('.room_name_container .error_msg_a, .room_name_container .error_msg_b').hide();
			if(!UNPAIRED_IP){
				var message = $('#alert');
				message.fadeIn();
				message.text("No available IP in the database");
				message.fadeOut(3000);
				return;
			}
			$('#room_form_main_container').modal('show');
	});
	
	$('#add_room_btn').click(function(evt){
		
		$('#room_name').removeAttr('disabled');
		var temp = $('#add_room_btn').text().trim();
		if (temp == ADD_ROOM){
			if(!checkRoomName($('#room_name').val(), CHECK_ROOM_NAME))
				return;
			$('#room_form_main_container').modal('hide');
			CreateSaveRoom(ADD_ACTION);		
			
		}
		
			
		else{ //important this is for saving user changes. It is a continuation of the room_edit_btn event
			$('#room_form_main_container').modal('hide');
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
		var val = $(this).val();
		val = val.split('_');
		val = '#Div_' + val[1];
		var room_showing = $('#sensors .rooms:not(:hidden)');
		room_showing.hide();
		$(val).show();
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
		$('#room_name').attr('disabled','disabled');
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
		
		username = username.toLowerCase();
		if($('#menu').hasClass('in'))
			$('.top_menu .navbar-toggle').click();

		var code;
		var valid = true;
		for(var i = 0; i < username.length; i++){
			code  = username.charCodeAt(i);
			if((code > 96 && code < 123) || (code > 47 && code < 58))
				continue;
			else
				valid = false;
		}


		if(valid)
			login(username, password, AUTH_USER);
		else
			loginFail();
	});



	$('#menu_add_user').click(function(){
		$('#create_user_error').hide();
		$('.user_name_container').removeClass('has-error');true
		$('.user_name_container').removeClass('has-success');
		$('.user_name_container .glyphicon-ok, .user_name_container .glyphicon-remove').hide();
		$('.user_name_container .error_msg_a, .user_name_container .error_msg_b, .user_name_container .error_msg_b').hide();
	
		$('#adduser_form_container').modal('show');
		
	
	});


	$('#create_user_btn').click(function(){

		var new_username = $('#new_username').val();
		var new_password = $('#new_password').val();
		var priviledge = $('#admin_priveledge').is(':checked');


		
		if(!new_username.length || !new_password.length)
			$('#create_user_invalid').show();	
		else if(checkUserName(new_username))
			createUser(new_username, new_password, priviledge, CREATE_USER);
	});

	$('#user_logout_btn').click(function(){
		logout();
	});


	/*$(window).resize(function(){
		checkScreen();
	});*/
	
	
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
	
	
	// The below if statement initializes the audio sound when the page loads for the first time
	if(window.innerWidth >= 1200){
		var target = $('#alert_sound');
		target[0].volume = 0;
		target[0].play();
		
	}

	

	
}); //end of ready function
