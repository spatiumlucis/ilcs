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

#GPIO.output(pinRelay, GPIO.LOW)

pause_time = 0.02

THREADS = []

keyboard_Event_mutex = threading.Lock()
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
    # Create two threads as follows
    try:
        pir_thread=threading.Thread(name='pir_thread', target=PIR_cmd, args=(keyboard_Event,))
        pir_thread.start()
        THREADS.append(pir_thread)
    except:
        print "Error: unable to start thread"
    
    light_cmd(keyboard_Event)

def PIR_cmd(keyboard_Event):
    global red
    global green
    global blue
    global pinRelay
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

        if brightness_values[0] == 'D':
            GPIO.output(pinRelay, GPIO.LOW)
##            sql = """DELETE FROM lighting_ip WHERE ip = %s"""
##            try:
##                cursor.execute(sql, (local_ip))
##                db.commit()
##            except:
##                db.rollback()
            pid = os.getpid()
            os.kill(pid, signal.SIGKILL)
        elif float(brightness_values[0]) == 0 and float(brightness_values[1]) == 0 and float(brightness_values[2]) == 0:
            # * turn lights off
            print "entering sleep mode..."
            GPIO.output(pinRelay, GPIO.LOW)
            #red.stop()
            #green.stop()
            #blue.stop()
            #GPIO.cleanup()
            #GPIO.output(pinRelay, GPIO.LOW)
        else:
            #sepatate into red, green, blue values
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

def light_cmd(keyboard_Event):
    global red
    global green
    global blue
    global pinRelay
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
                print "turning lights off"
                GPIO.output(pinRelay, GPIO.LOW)
                # red.stop()
                # green.stop()
                # blue.stop()
                # GPIO.cleanup()
            else:
                # GPIO.output(pinRelay, GPIO.HIGH)
                # dutyCycle = (float(light_intensity) / 100) * 1024
                # wiringpi.pwmWrite(pinPWM, int(dutyCycle))
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

