#PIR code from: modmypi.com/blog/raspberry-pi-gpio-sensing-motion-detection
#Socket code: tutorialspoint.com/python/python_networking.html
import time
import socket
import threading
import RPi.GPIO as GPIO
import MySQLdb #Required for MySQL stuff
import wiringpi
import sys
import os
import signal

#PWM Stuff
lightIntensity = -5

#*Set up PWM for lights
# pinPWM = 18
# pinRelay = 7
#
# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(pinRelay, GPIO.OUT)
#
# wiringpi.wiringPiSetupGpio()
# wiringpi.pinMode(pinPWM, 2)
# wiringpi.pwmSetClock(5000)
pinRelay = 4
pinRelayS = 5

wiringpi.wiringPiSetupGpio()
GPIO.setmode(GPIO.BCM) #choose BCM or BOARD numbering schemes
GPIO.setup(17, GPIO.OUT) #set GIPO 17 as red led
GPIO.setup(27, GPIO.OUT) #set GIPO 27 as green led
GPIO.setup(22, GPIO.OUT) #set GIPO 22 as blue led
GPIO.setup(pinRelay, GPIO.OUT)

red = GPIO.PWM(17, 100) #create object red for PWM on port 17 at 100Hz
green = GPIO.PWM(27, 100) #create object red for PWM on port 27 at 100Hz
blue = GPIO.PWM(22, 100) #create object red for PWM on port 22 at 100Hz

red.start(0)
green.start(0)
blue.start(0)

GPIO.setup(29, GPIO.OUT) #set GIPO 17 as red led
GPIO.setup(31, GPIO.OUT) #set GIPO 27 as green led
GPIO.setup(33, GPIO.OUT) #set GIPO 22 as blue led
GPIO.setup(pinRelayS, GPIO.OUT) #secondary relay

redS = GPIO.PWM(29, 100) #create object red for PWM on port 17 at 100Hz
greenS = GPIO.PWM(31, 100) #create object red for PWM on port 27 at 100Hz
blueS = GPIO.PWM(33, 100) #create object red for PWM on port 22 at 100Hz

redS.start(0)
greenS.start(0)
blueS.start(0)

#GPIO.output(pinRelay, GPIO.LOW)

pause_time = 0.02

THREADS = []

GPIO.setwarnings(False)
keyboard_Event_mutex = threading.Lock()
red_mutex = threading.Lock()
green_mutex = threading.Lock()
blue_mutex = threading.Lock()

redS_mutex = threading.Lock()
greenS_mutex = threading.Lock()
blueS_mutex = threading.Lock()

comp_Event_mutex = threading.Lock()
# Open database connection
print "connecting to database..."
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
# prepare a cursor object using cursor() method
cursor = db.cursor()

def get_ip():
    # source:
    # http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/25850698#25850698
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
    print "entered"
    global cursor
    # get local ip
    local_ip = get_ip()
    sql = """SELECT * FROM lighting_ip WHERE ip = %s"""
    cursor.execute(sql, (local_ip))
    temp = cursor.fetchall()
    if len(temp) == 0:
        print "empty tuple"
        #insert into DB
        sql = """INSERT INTO lighting_ip(ip) VALUES(%s)"""
        try:
            cursor.execute(sql, (local_ip))
            db.commit()
        except:
            db.rollback()
        begin_threading()
    else:
        begin_threading()

def begin_threading():
    global THREADS
    keyboard_Event = threading.Event()
    keyboard_Event.set()
    comp_Event = threading.Event()
    comp_Event.set()

    # Create two threads as follows
    try:
        pir_thread=threading.Thread(name='pir_thread', target=PIR_cmd, args=(keyboard_Event,comp_Event,))
        pir_thread.start()
        THREADS.append(pir_thread)
    except:
        print "Error: unable to start sleep mode thread"
    try:
        delete_thread=threading.Thread(name='delete_thread', target=delete_cmd, args=())
        delete_thread.start()
        THREADS.append(pir_thread)
    except:
        print "Error: unable to start delete thread"
    try:
        comp_thread=threading.Thread(name='comp_thread', target=comp_cmd, args=(comp_Event,))
        comp_thread.start()
        THREADS.append(pir_thread)
    except:
        print "Error: unable to start delete thread"
    
    light_cmd(keyboard_Event,comp_Event)
def delete_cmd():
    global pinRelay
    global pinRelayS
    lighting_del_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
    lighting_del_svr_sock_host = ''  # * Get local machine name
    lighting_del_svr_sock_port = 12355  # delete port.
    lighting_del_svr_sock.bind((lighting_del_svr_sock_host, lighting_del_svr_sock_port))  # * Bind to the port

    lighting_del_svr_sock.listen(5)  # * Now wait for client connection.
    print "listening on light_pir socket...."
    lighting_del_svr_sock_connection, lighting_del_svr_sock_connection_addr = lighting_del_svr_sock.accept()  # * Establish connection w
    print '\nGot connection from', lighting_del_svr_sock_connection_addr, "\n"

    GPIO.output(pinRelay, GPIO.LOW)
    GPIO.output(pinRelayS, GPIO.LOW)

    pid = os.getpid()
    os.kill(pid, signal.SIGKILL)
def comp_cmd(comp_Event):
    global red
    global redS
    global green
    global greenS
    global blue
    global blueS

    lighting_comp_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
    lighting_comp_svr_sock_host = ''  # * Get local machine name
    lighting_comp_svr_sock_port = 12356  # comp port.
    lighting_comp_svr_sock.bind((lighting_comp_svr_sock_host, lighting_comp_svr_sock_port))  # * Bind to the port
    lighting_comp_svr_sock.listen(5)
    while True:

        lighting_comp_svr_sock_connection, lighting_comp_svr_sock_connection_addr = lighting_comp_svr_sock.accept()  # * Establish connection w
        print '\nGot connection from', lighting_comp_svr_sock_connection_addr, "\n"

        light_intensity = lighting_comp_svr_sock_connection.recv(1024)
        cmd = light_intensity.split('|')
        print "GOT on pir_cmd thread: ", cmd
        comp_Event_mutex.acquire()
        try:
            comp_Event.clear()
        finally:
            comp_Event_mutex.release()

        if cmd[0] != "N":
            red_mutex.acquire()
            try:
                red.ChangeDutyCycle(float(cmd[0]) / 2)
            finally:
                red_mutex.release()
        if cmd[1] != "N":
            redS_mutex.acquire()
            try:
                redS.ChangeDutyCycle(float(cmd[1]) / 2)
            finally:
                redS_mutex.release()
        if cmd[2] != "N":
            green_mutex.acquire()
            try:
                green.ChangeDutyCycle(float(cmd[2]) / 2)
            finally:
                green_mutex.release()
        if cmd[3] != "N":
            greenS_mutex.acquire()
            try:
                greenS.ChangeDutyCycle(float(cmd[3]) / 2)
            finally:
                greenS_mutex.release()
        if cmd[4] != "N":
            blue_mutex.acquire()
            try:
                blue.ChangeDutyCycle(float(cmd[4]) / 2)
            finally:
                blue_mutex.release()
        if cmd[5] != "N":
            blue_mutex.acquire()
            try:
                blue.ChangeDutyCycle(float(cmd[5]) / 2)
            finally:
                blue_mutex.release()
        comp_Event_mutex.acquire()
        try:
            comp_Event.set()
        finally:
            comp_Event_mutex.release()
        lighting_comp_svr_sock_connection.close()

def PIR_cmd(keyboard_Event, comp_Event):
    global red
    global green
    global blue
    global pinRelay
    global pinRelayS
    global local_ip
    global cursor
    global db
    # *establish server socket for Control subsystem to connect to for LI send
    lighting_pir_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
    lighting_pir_svr_sock_host = ''  # * Get local machine name
    lighting_pir_svr_sock_port = 12346  # PIR port.
    lighting_pir_svr_sock.bind((lighting_pir_svr_sock_host, lighting_pir_svr_sock_port))  # * Bind to the port

    lighting_pir_svr_sock.listen(5)  # * Now wait for client connection.
    print "listening on light_pir socket...."
    # print s.recv(1024)
    # s.close                     #* Close the socket when done

    while True and keyboard_Event.isSet():
        keyboard_Event_mutex.acquire()
        try:
            keyboard = keyboard_Event.isSet()
        finally:
            keyboard_Event_mutex.release()
        if not keyboard:
            break
        lighting_pir_svr_sock_connection, lighting_pir_svr_sock_connection_addr = lighting_pir_svr_sock.accept()  # * Establish connection w
        print '\nGot connection from', lighting_pir_svr_sock_connection_addr, "\n"

        light_intensity = lighting_pir_svr_sock_connection.recv(1024)
        brightness_values = light_intensity.split('|')
        print "GOT on pir_cmd thread: ", brightness_values

        if float(brightness_values[0]) == 0 and float(brightness_values[1]) == 0 and float(brightness_values[2]) == 0:
            # * turn lights off
            comp_Event_mutex.acquire()
            try:
                comp_status = comp_Event.isSet()
            finally:
                comp_Event_mutex.release()
            if not comp_status:
                comp_Event.wait()
            print "entering sleep mode..."
            GPIO.output(pinRelay, GPIO.LOW)
            GPIO.output(pinRelayS, GPIO.LOW)
            #red.stop()
            #green.stop()
            #blue.stop()
            #GPIO.cleanup()
            #GPIO.output(pinRelay, GPIO.LOW)
        else:
            #sepatate into red, green, blue values
            comp_Event_mutex.acquire()
            try:
                comp_status = comp_Event.isSet()
            finally:
                comp_Event_mutex.release()
            if not comp_status:
                comp_Event.wait()
            print "exiting sleep mode"
            GPIO.output(pinRelay, GPIO.HIGH)
            red.ChangeDutyCycle(float(brightness_values[0]) / 2)
            green.ChangeDutyCycle(float(brightness_values[1]) / 2)
            blue.ChangeDutyCycle(float(brightness_values[2]) / 2)
            #GPIO.output(pinRelay, GPIO.HIGH)
            #dutyCycle = (float(light_intensity) / 100) * 1024
            #wiringpi.pwmWrite(pinPWM, int(dutyCycle))
        time.sleep(1)

        lighting_pir_svr_sock_connection.close()

def light_cmd(keyboard_Event, comp_Event):
    global red
    global green
    global blue
    global redS
    global greenS
    global blueS
    global pinRelay
    global pinRelayS
    global THREADS
    # *establish server socket for Control subsystem to connect to for LI send
    lighting_lightCmd_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
    lighting_lightCmd_svr_sock_host = ''  # * Get local machine name
    lighting_lightCmd_svr_sock_port = 12347  # PIR port.
    lighting_lightCmd_svr_sock.bind((lighting_lightCmd_svr_sock_host, lighting_lightCmd_svr_sock_port))  # * Bind to the port

    lighting_lightCmd_svr_sock.listen(5)  # * Now wait for client connection.
    print "listening on light_cmd socket...."
    # print s.recv(1024)
    # s.close                     #* Close the socket when done
    try:
        while True:
            lighting_lightCmd_svr_sock_connection, lighting_lightCmd_svr_sock_connection_addr = lighting_lightCmd_svr_sock.accept()  # * Establish connection w
            print '\nGot connection from', lighting_lightCmd_svr_sock_connection_addr, "\n"

            light_intensity = lighting_lightCmd_svr_sock_connection.recv(1024)
            brightness_values = light_intensity.split('|')
            print "GOT on light_cmd thread: ", brightness_values

            if float(brightness_values[0]) == 0 and float(brightness_values[1]) == 0 and float(brightness_values[2]) == 0:
                # * turn lights off
                comp_Event_mutex.acquire()
                try:
                    comp_status = comp_Event.isSet()
                finally:
                    comp_Event_mutex.release()
                if not comp_status:
                    comp_Event.wait()
                print "turning lights off"
                GPIO.output(pinRelay, GPIO.LOW)
                # red.stop()
                # green.stop()
                # blue.stop()
                # GPIO.cleanup()
            else:
                comp_Event_mutex.acquire()
                try:
                    comp_status = comp_Event.isSet()
                finally:
                    comp_Event_mutex.release()
                if not comp_status:
                    comp_Event.wait()
                GPIO.output(pinRelay, GPIO.HIGH)
                # brightness_values = light_intensity.split('|')
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

