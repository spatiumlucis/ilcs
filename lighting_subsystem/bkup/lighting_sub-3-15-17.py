"""
File Name: lighting_sub.py

Version Number: v1.0

Target Device: Raspberry Pi 3

Dependencies:
-Control Subsystem database is online and connected to the same network

Authors:
-Zach Simpson
-Terry So
-Jeremy Trammell
-Chukwuebuka Nwankwo

Code Description:

Sources:
-Python socket code:
https://www.tutorialspoint.com/python/python_networking.html
http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/25850698#25850698

-Python MySQL code:
https://www.tutorialspoint.com/python/python_database_access.htm

-Python thread code:
https://www.tutorialspoint.com/python/python_multithreading.htm
"""
"""
Global Variables
"""
import time
import socket
import threading
import RPi.GPIO as GPIO
import MySQLdb
import wiringpi
import sys
import os
import signal

"""
Establish GPIO paramters for the LEDs
Red uses BCM pin 17
Green uses BCM pin 27
Blue uses BCM pin 22
Relay uses BCM pin 4
"""
GPIO.setmode(GPIO.BCM) #choose BCM or BOARD numbering schemes
GPIO.setup(17, GPIO.OUT) #set GIPO 17 as red led
GPIO.setup(27, GPIO.OUT) #set GIPO 27 as green led
GPIO.setup(22, GPIO.OUT) #set GIPO 22 as blue led
pinRelay = 4
GPIO.setup(pinRelay, GPIO.OUT)

"""
Set up PWM information for the LEDs
"""
red = GPIO.PWM(17, 100) #create object red for PWM on port 17 at 100Hz
green = GPIO.PWM(27, 100) #create object red for PWM on port 27 at 100Hz
blue = GPIO.PWM(22, 100) #create object red for PWM on port 22 at 100Hz

"""
Start the LED PWMs
"""
red.start(0)
green.start(0)
blue.start(0)

pause_time = 0.02

THREADS = []
"""
Mutex locks are used to protect shared variables
that can be read or written from multiple threads.
"""
keyboard_Event_mutex = threading.Lock()

"""
Establish database connection
"""
print "Connecting to database in Lighting Subsystem..."
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
cursor = db.cursor()

def get_ip():
    """
    This function is used to get the local IP of the Raspberry Pi.
    :return: The local IP address as a string
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 0))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def boot_up():
    """
    This is the main boot up function for the lighting subsystem.
    It will look into the DB to see if its IP address exists in the
    lighting_ip table. If the IP DOES exist, then the code will begin
    waiting for brightness commands. If the IP DOES NOT exist, the IP
    will be added to the end of the of the lighting_ip table and begin
    waiting for brightness commands from the sensor subsystem.
    :return: None.
    """
    """
    Import global vars
    """
    global cursor
    global db

    print "Booting up..."
    local_ip = get_ip()

    """
    Check DB for the local IP
    """
    sql = """SELECT * FROM lighting_ip WHERE ip = %s"""
    cursor.execute(sql, (local_ip))
    temp = cursor.fetchall()
    if len(temp) == 0:
        """
        If the local IP doesn't exist in the DB,
        then add it
        """

        sql = """INSERT INTO lighting_ip(ip) VALUES(%s)"""
        try:
            cursor.execute(sql, (local_ip))
            db.commit()
        except:
            db.rollback()
    """
    If the IP does exist, then create threads
    """
    print "Initializing threads..."
    begin_threading()

def begin_threading():
    """
    This function creates the threads for the lighting subsystem.
    The pir_thread is used to listen for sleep mode commands from
    the sensor subsystem. The main thread waits for normal brightness
    commands.
    :return: None.
    """
    """
    Import global vars
    """
    global THREADS

    """
    This event is useless
    """
    keyboard_Event = threading.Event()
    keyboard_Event.set()
    print "Trying to create PIR thread..."
    try:
        pir_thread=threading.Thread(name='pir_thread', target=PIR_cmd, args=(keyboard_Event,))
        pir_thread.start()
        THREADS.append(pir_thread)
    except:
        print "Error: unable to start thread"
    
    light_cmd(keyboard_Event)

def PIR_cmd(keyboard_Event):
    """
    This is the init function for the pir_thread. It listens
    for sleep mode commands from the sensor subsystem. If a
    sleep mode command is received, then the relay is triggered
    and the lights are turned off. If a wake up command is received,
    then the lights are turned back on.
    :param keyboard_Event: This event is useless and will be removed
    :return: None.
    """

    """
    Import global vars
    """
    global red
    global green
    global blue
    global pinRelay
    global local_ip
    global cursor
    global db
    print "PIR thread created successfully.\nPlease activate the Sensor Subsystem."

    """
    Set up server socket for sensor subsystem to connect to
    """
    lighting_pir_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    lighting_pir_svr_sock_host = ''
    lighting_pir_svr_sock_port = 12346
    lighting_pir_svr_sock.bind((lighting_pir_svr_sock_host, lighting_pir_svr_sock_port))

    lighting_pir_svr_sock.listen(5)

    while True and keyboard_Event.isSet():
        keyboard_Event_mutex.acquire()
        try:
            keyboard = keyboard_Event.isSet()
        finally:
            keyboard_Event_mutex.release()
        if not keyboard:
            break
        """
        Receive connection from sensor sub and get
        command values
        """
        lighting_pir_svr_sock_connection, lighting_pir_svr_sock_connection_addr = lighting_pir_svr_sock.accept()  # * Establish connection w
        print 'Got connection from', lighting_pir_svr_sock_connection_addr

        light_intensity = lighting_pir_svr_sock_connection.recv(1024)
        brightness_values = light_intensity.split('|')
        print "Received command on PIR thread: ", brightness_values

        if brightness_values[0] == 'D':
            """
            If command was 'D', then kill the
            script
            """
            GPIO.output(pinRelay, GPIO.LOW)
            pid = os.getpid()
            os.kill(pid, signal.SIGKILL)
        elif float(brightness_values[0]) == 0 and float(brightness_values[1]) == 0 and float(brightness_values[2]) == 0:
            """
            If command is all 0s then turn lights off
            """
            print "Entering sleep mode..."
            GPIO.output(pinRelay, GPIO.LOW)
        else:
            print "Exiting sleep mode..."
            GPIO.output(pinRelay, GPIO.HIGH)
            red.ChangeDutyCycle(float(brightness_values[0]) / 2)
            green.ChangeDutyCycle(float(brightness_values[1]) / 2)
            blue.ChangeDutyCycle(float(brightness_values[2]) / 2)
        time.sleep(1)

        lighting_pir_svr_sock_connection.close()

def light_cmd(keyboard_Event):
    global red
    global green
    global blue
    global pinRelay
    global THREADS

    lighting_lightCmd_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    lighting_lightCmd_svr_sock_host = ''
    lighting_lightCmd_svr_sock_port = 12347
    lighting_lightCmd_svr_sock.bind((lighting_lightCmd_svr_sock_host, lighting_lightCmd_svr_sock_port))

    lighting_lightCmd_svr_sock.listen(5)
    print "listening on light_cmd socket...."
    try:
        while True:
            lighting_lightCmd_svr_sock_connection, lighting_lightCmd_svr_sock_connection_addr = lighting_lightCmd_svr_sock.accept()  # * Establish connection w
            print '\nGot connection from', lighting_lightCmd_svr_sock_connection_addr, "\n"

            light_intensity = lighting_lightCmd_svr_sock_connection.recv(1024)
            brightness_values = light_intensity.split('|')
            print "GOT on light_cmd thread: ", brightness_values
            if float(brightness_values[0]) == 0 and float(brightness_values[1]) == 0 and float(brightness_values[2]) == 0:
                print "turning lights off"
                GPIO.output(pinRelay, GPIO.LOW)
            else:
                GPIO.output(pinRelay, GPIO.HIGH)
                red.ChangeDutyCycle(float(brightness_values[0]) / 2)
                green.ChangeDutyCycle(float(brightness_values[1]) / 2)
                blue.ChangeDutyCycle(float(brightness_values[2]) / 2)
            time.sleep(1)

            lighting_lightCmd_svr_sock_connection.close()
    except KeyboardInterrupt:
        keyboard_Event.clear()
        time.sleep(1)
        for thread in THREADS:
            thread.join()
        sys.exit()


boot_up()

