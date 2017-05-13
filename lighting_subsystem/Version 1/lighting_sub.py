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


GPIO.setwarnings(False)
pinRelay = 4
pinRelayS = 5

wiringpi.wiringPiSetupGpio()
GPIO.setmode(GPIO.BCM) #choose BCM or BOARD numbering schemes

GPIO.setup(pinRelay, GPIO.OUT)

wiringpi.pinMode(17, 17) #Red on pin 17
wiringpi.softPwmCreate(17,0,100) #Red PWM with 100Hz
wiringpi.pinMode(27, 27) #Green
wiringpi.softPwmCreate(27,0,100)
wiringpi.pinMode(22, 22) #Blue
wiringpi.softPwmCreate(22,0,100)

GPIO.setup(pinRelayS, GPIO.OUT) #secondary relay


wiringpi.pinMode(6, 6) #RedS on pin 29
wiringpi.softPwmCreate(6,0,100) #Red PWM with 100Hz
wiringpi.pinMode(13, 13) #GreenS
wiringpi.softPwmCreate(13,0,100)
wiringpi.pinMode(26, 26) #BlueS
wiringpi.softPwmCreate(26,0,100)

pause_time = 0.02

PREV_SEC_RED = 0
PREV_SEC_GREEN = 0
PREV_SEC_BLUE = 0
SECONDARY_RELAY_HIGH = False
PRIMARY_RELAY_HIGH = False
THREADS = []

keyboard_Event_mutex = threading.Lock()
delete_Event_mutex = threading.Lock()

light_mutex = threading.Lock()
secondary_mutex = threading.Lock()

comp_Event_mutex = threading.Lock()

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
    #print "entered"
    # Open database connection
    print "connecting to database..."
    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
    # prepare a cursor object using cursor() method
    cursor = db.cursor()

    # get local ip
    local_ip = get_ip()
    sql = """SELECT * FROM lighting_ip WHERE ip = %s"""
    cursor.execute(sql, ([local_ip]))
    temp = cursor.fetchall()
    if len(temp) == 0:
        #print "empty tuple"
        #insert into DB
        sql = """INSERT INTO lighting_ip(ip, is_paired) VALUES(%s, 0)"""
        try:
            cursor.execute(sql, ([local_ip]))
            db.commit()
        except:
            db.rollback()
        begin_threading()
    else:
        db.close()
        begin_threading()

def begin_threading():
    global THREADS
    keyboard_Event = threading.Event()
    keyboard_Event.set()
    comp_Event = threading.Event()
    comp_Event.set()
    delete_Event = threading.Event()
    delete_Event.set()
    # Create two threads as follows
    try:
        pir_thread=threading.Thread(name='pir_thread', target=PIR_cmd, args=(keyboard_Event,comp_Event,delete_Event,))
        pir_thread.start()
        THREADS.append(pir_thread)
    except:
        print "Error: unable to start sleep mode thread"
    try:
        delete_thread=threading.Thread(name='delete_thread', target=delete_cmd, args=(delete_Event,))
        delete_thread.start()
        THREADS.append(delete_thread)
    except:
        print "Error: unable to start delete thread"
    try:
        comp_thread=threading.Thread(name='comp_thread', target=comp_cmd, args=(comp_Event,delete_Event,))
        comp_thread.start()
        THREADS.append(comp_thread)
    except:
        print "Error: unable to start delete thread"
    
    light_cmd(keyboard_Event,comp_Event, delete_Event)

def delete_cmd(delete_Event):
    global pinRelay
    global pinRelayS
    global PREV_SEC_RED
    global PREV_SEC_GREEN
    global PREV_SEC_BLUE

    lighting_del_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
    lighting_del_svr_sock_host = ''  # * Get local machine name
    lighting_del_svr_sock_port = 12355  # delete port.
    lighting_del_svr_sock.bind((lighting_del_svr_sock_host, lighting_del_svr_sock_port))  # * Bind to the port

    lighting_del_svr_sock.listen(5)  # * Now wait for client connection.
    print "listening on delete thread..."
    lighting_del_svr_sock_connection, lighting_del_svr_sock_connection_addr = lighting_del_svr_sock.accept()  # * Establish connection w
    print '\nGot connection from', lighting_del_svr_sock_connection_addr, "\n"
    delete_Event_mutex.acquire()
    try:
        delete_Event.clear()
    finally:
        delete_Event_mutex.release()
    cmd = (lighting_del_svr_sock_connection.recv(1024)).strip()
    cmd = cmd.split('|')
    end_red = int(float(cmd[0]))
    end_green = int(float(cmd[1]))
    end_blue = int(float(cmd[2]))

    #print "Values at delete: %s %s %s"%(end_red, end_green, end_blue)
    secondary_mutex.acquire()
    try:
        end_red_s = PREV_SEC_RED
        end_green_s = PREV_SEC_GREEN
        end_blue_s = PREV_SEC_BLUE
    finally:
        secondary_mutex.release()
    light_mutex.acquire()
    #print "gotcha"
    try:
        #print "about to delete"
        while end_red > 0 or end_green > 0 or end_blue > 0 or end_red_s > 0 or end_green_s > 0 or end_blue_s > 0:
            if end_red > 0:
                #"red"
                end_red -= 1
                wiringpi.softPwmWrite(17, int(float(end_red)/2))
            if end_green > 0:
                #"green"
                end_green -= 1
                wiringpi.softPwmWrite(27, int(float(end_green) / 2))
            if end_blue > 0:
                #"blue"
                end_blue -= 1
                wiringpi.softPwmWrite(22, int(float(end_blue) / 2))
            if end_red_s > 0:
                #"red"
                end_red_s -= 1
                wiringpi.softPwmWrite(6, int(float(end_red_s)/2))
            if end_green_s > 0:
                #"green"
                end_green_s -= 1
                wiringpi.softPwmWrite(13, int(float(end_green_s) / 2))
            if end_blue_s > 0:
                #"blue"
                end_blue_s -= 1
                wiringpi.softPwmWrite(26, int(float(end_blue_s) / 2))
            time.sleep(0.005)
        GPIO.output(pinRelay, GPIO.LOW)
        GPIO.output(pinRelayS, GPIO.LOW)
    finally:
        #print "releasing mutex"
        light_mutex.release()

    pid = os.getpid()
    os.kill(pid, signal.SIGKILL)

def comp_cmd(comp_Event, delete_Event):
    global pinRelayS
    global pinRelay
    global PREV_SEC_RED
    global PREV_SEC_GREEN
    global PREV_SEC_BLUE
    global SECONDARY_RELAY_HIGH
    global PRIMARY_RELAY_HIGH

    lighting_comp_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
    lighting_comp_svr_sock_host = ''  # * Get local machine name
    lighting_comp_svr_sock_port = 12356  # comp port.
    lighting_comp_svr_sock.bind((lighting_comp_svr_sock_host, lighting_comp_svr_sock_port))  # * Bind to the port
    lighting_comp_svr_sock.listen(5)
    print "Listening on comp_cmd thread..."
    while True:
        lighting_comp_svr_sock_connection, lighting_comp_svr_sock_connection_addr = lighting_comp_svr_sock.accept()  # * Establish connection w
        print '\nGot connection from', lighting_comp_svr_sock_connection_addr, "\n"

        light_intensity = lighting_comp_svr_sock_connection.recv(1024)
        cmd = light_intensity.split('|')
        print "GOT on comp_cmd thread: ", cmd
        comp_Event_mutex.acquire()
        try:
            comp_Event.clear()
        finally:
            comp_Event_mutex.release()
        delete_Event_mutex.acquire()
        try:
            delete_status = delete_Event.isSet()
        finally:
            delete_Event_mutex.release()
        if not delete_status:
            delete_Event.wait()

        """
        Primary Lights first
        """
        secondary_mutex.acquire()
        try:
            if not SECONDARY_RELAY_HIGH:
                GPIO.output(pinRelayS, GPIO.HIGH)
                SECONDARY_RELAY_HIGH = True
            if not PRIMARY_RELAY_HIGH:
                GPIO.output(pinRelay, GPIO.HIGH)
                PRIMARY_RELAY_HIGH = True
        finally:
            secondary_mutex.release()


        if cmd[0] != "":
            if cmd[1] != "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red,int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()

            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()


            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()

            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))


                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))


                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()

            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()


                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()


            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))

                prev_greenS = int(float(cmd[6]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))


                h_p_r_thread.start()


                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()


            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))

                prev_blueS = int(float(cmd[10]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))


                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()


                h_p_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()



            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))

                h_p_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()


            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))


                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_s_b_thread.start()



            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()


            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))


                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()

            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))


                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()


                h_p_g_thread.start()
                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))



                h_p_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()


            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))



                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()

                h_p_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))


                h_p_r_thread.start()


                h_p_g_thread.start()

            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))


                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()
                h_s_r_thread.start()


                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))


                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))



                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))



                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))


                h_p_r_thread.start()
                h_s_r_thread.start()


                h_p_b_thread.start()

            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))


                h_p_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))


                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))


                h_p_r_thread.start()


                h_p_b_thread.start()

            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))


                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))


                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()
                h_s_r_thread.start()


                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))


                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_r_thread.start()
                h_s_r_thread.start()
                h_s_g_thread.start()


            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))



                h_p_r_thread.start()
                h_s_r_thread.start()

            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))


                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()

                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))



                h_p_r_thread.start()

                h_s_g_thread.start()

            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] != "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_r_thread.start()

                h_s_b_thread.start()
            elif cmd[1] != "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] == "N":
                prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[1])),))


                h_p_r_thread.start()

            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))


                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))



                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))


                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))


                h_s_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))


                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))



                h_s_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()

            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))



                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))

                h_p_g_thread.start()


                h_p_b_thread.start()

            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_s_r_thread.start()

                h_p_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))

                h_s_r_thread.start()

                h_p_g_thread.start()

            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))


                h_p_g_thread.start()
                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))



                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_g_thread.start()
                h_s_g_thread.start()

            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] != "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[5])),))

                h_p_g_thread.start()

            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))


                h_s_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))


                h_s_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))


                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_s_r_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))


                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))


                h_s_r_thread.start()

                h_p_b_thread.start()

            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))



                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))

                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))



                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] != "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[9])),))

                h_p_b_thread.start()

            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_s_r_thread.start()

                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] != "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_s_r_thread.start()

                h_s_g_thread.start()

            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))


                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_s_r_thread.start()

                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] != "N" and cmd[7] == "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[3])),))

                h_s_r_thread.start()


            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))


                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))


                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))


                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] != "N" and cmd[11] == "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                prev_greenS = int(float(cmd[6]))
                #prev_blueS = int(float(cmd[10]))


                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[7])),))

                h_s_g_thread.start()

            elif cmd[1] == "N" and cmd[5] == "N" and cmd[9] == "N" and cmd[3] == "N" and cmd[7] == "N" and cmd[11] != "N":
                #prev_red = int(float(cmd[0]))
                #prev_green = int(float(cmd[4]))
                #prev_blue = int(float(cmd[8]))
                #prev_redS = int(float(cmd[2]))
                #prev_greenS = int(float(cmd[6]))
                prev_blueS = int(float(cmd[10]))


                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[11])),))

                h_s_b_thread.start()

        comp_Event_mutex.acquire()
        try:
            comp_Event.set()
        finally:
            comp_Event_mutex.release()
        lighting_comp_svr_sock_connection.close()

def handle_primary_red(start, end):
    if start < end:
        light_mutex.acquire()
        try:
            while start < end:
                if start < end:
                    start += 1
                    wiringpi.softPwmWrite(17, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    elif start > end:
        light_mutex.acquire()
        try:
            while start > end:
                if start > end:
                    start -= 1
                    wiringpi.softPwmWrite(17, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    else:
        light_mutex.acquire()
        try:
            wiringpi.softPwmWrite(17, int(float(start) / 2))
        finally:
            light_mutex.release()

def handle_secondary_red(start, end):
    global PREV_SEC_RED
    if start < end:
        light_mutex.acquire()
        try:
            while start < end:
                if start < end:
                    start += 1
                    wiringpi.softPwmWrite(6, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    elif start > end:
        light_mutex.acquire()
        try:
            while start > end:
                if start > end:
                    start -= 1
                    wiringpi.softPwmWrite(6, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    else:
        light_mutex.acquire()
        try:
            wiringpi.softPwmWrite(6, int(float(start) / 2))
        finally:
            light_mutex.release()
    secondary_mutex.acquire()
    try:
        PREV_SEC_RED = int(end)
    finally:
        secondary_mutex.release()

def handle_primary_green(start, end):
    if start < end:
        light_mutex.acquire()
        try:
            while start < end:
                if start < end:
                    start += 1
                    wiringpi.softPwmWrite(27, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    elif start > end:
        light_mutex.acquire()
        try:
            while start > end:
                if start > end:
                    start -= 1
                    wiringpi.softPwmWrite(27, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    else:
        light_mutex.acquire()
        try:
            wiringpi.softPwmWrite(27, int(float(start) / 2))
        finally:
            light_mutex.release()

def handle_secondary_green(start, end):
    global PREV_SEC_GREEN
    if start < end:
        light_mutex.acquire()
        try:
            while start < end:
                if start < end:
                    start += 1
                    wiringpi.softPwmWrite(13, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    elif start > end:
        light_mutex.acquire()
        try:
            while start > end:
                if start > end:
                    start -= 1
                    wiringpi.softPwmWrite(13, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    else:
        light_mutex.acquire()
        try:
            wiringpi.softPwmWrite(13, int(float(start) / 2))
        finally:
            light_mutex.release()
    secondary_mutex.acquire()
    try:
        PREV_SEC_GREEN = int(end)
    finally:
        secondary_mutex.release()

def handle_primary_blue(start, end):
    if start < end:
        light_mutex.acquire()
        try:
            while start < end:
                if start < end:
                    start += 1
                    wiringpi.softPwmWrite(22, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    elif start > end:
        light_mutex.acquire()
        try:
            while start > end:
                if start > end:
                    start -= 1
                    wiringpi.softPwmWrite(22, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    else:
        light_mutex.acquire()
        try:
            wiringpi.softPwmWrite(22, int(float(start) / 2))
        finally:
            light_mutex.release()

def handle_secondary_blue(start, end):
    global PREV_SEC_BLUE
    if start < end:
        light_mutex.acquire()
        try:
            while start < end:
                if start < end:
                    start += 1
                    wiringpi.softPwmWrite(26, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    elif start > end:
        light_mutex.acquire()
        try:
            while start > end:
                if start > end:
                    start -= 1
                    wiringpi.softPwmWrite(26, int(float(start) / 2))
                time.sleep(0.005)
        finally:
            light_mutex.release()
    else:
        light_mutex.acquire()
        try:
            wiringpi.softPwmWrite(26, int(float(start) / 2))
        finally:
            light_mutex.release()
    secondary_mutex.acquire()
    try:
        PREV_SEC_BLUE = int(end)
    finally:
        secondary_mutex.release()

def PIR_cmd(keyboard_Event, comp_Event, delete_Event):
    #global red
    #global green
    #global blue
    global pinRelay
    global pinRelayS
    global local_ip
    global cursor
    global db
    global PREV_SEC_RED
    global PREV_SEC_GREEN
    global PREV_SEC_BLUE
    # *establish server socket for Control subsystem to connect to for LI send
    lighting_pir_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
    lighting_pir_svr_sock_host = ''  # * Get local machine name
    lighting_pir_svr_sock_port = 12346  # PIR port.
    lighting_pir_svr_sock.bind((lighting_pir_svr_sock_host, lighting_pir_svr_sock_port))  # * Bind to the port

    lighting_pir_svr_sock.listen(5)  # * Now wait for client connection.
    print "listening on pir thread...."
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
        if not delete_Event.isSet():
            delete_Event.wait()
        lighting_pir_svr_sock_connection, lighting_pir_svr_sock_connection_addr = lighting_pir_svr_sock.accept()  # * Establish connection w
        print '\nGot connection from', lighting_pir_svr_sock_connection_addr, "\n"

        cmd = lighting_pir_svr_sock_connection.recv(1024)
        cmd = cmd.split('|')
        print "GOT on pir_cmd thread: ", cmd
        #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        end_red = int(float(cmd[0]))
        end_green = int(float(cmd[1]))
        end_blue = int(float(cmd[2]))

        #print "Values at delete: %s %s %s" % (end_red, end_green, end_blue)
        secondary_mutex.acquire()
        try:
            end_red_s = PREV_SEC_RED
            end_green_s = PREV_SEC_GREEN
            end_blue_s = PREV_SEC_BLUE
        finally:
            secondary_mutex.release()
        light_mutex.acquire()
        #print "gotcha"
        try:
            #print "about to sleep"
            while end_red > 0 or end_green > 0 or end_blue > 0 or end_red_s > 0 or end_green_s > 0 or end_blue_s > 0:
                if end_red > 0:
                    #"red"
                    end_red -= 1
                    wiringpi.softPwmWrite(17, int(float(end_red) / 2))
                if end_green > 0:
                    #"green"
                    end_green -= 1
                    wiringpi.softPwmWrite(27, int(float(end_green) / 2))
                if end_blue > 0:
                    #"blue"
                    end_blue -= 1
                    wiringpi.softPwmWrite(22, int(float(end_blue) / 2))
                if end_red_s > 0:
                    #"red"
                    end_red_s -= 1
                    wiringpi.softPwmWrite(6, int(float(end_red_s) / 2))
                if end_green_s > 0:
                    #"green"
                    end_green_s -= 1
                    wiringpi.softPwmWrite(13, int(float(end_green_s) / 2))
                if end_blue_s > 0:
                    #"blue"
                    end_blue_s -= 1
                    wiringpi.softPwmWrite(26, int(float(end_blue_s) / 2))
                time.sleep(0.005)
            #GPIO.output(pinRelay, GPIO.LOW)
            #GPIO.output(pinRelayS, GPIO.LOW)
        finally:
            #print "releasing mutex"
            light_mutex.release()
        # end_red = int(float(cmd[2]))
        # end_green = int(float(cmd[1]))
        # end_blue = int(float(cmd[2]))
        # print "Values at delete: %s %s %s" % (end_red, end_green, end_blue)
        # light_mutex.acquire()
        # try:
        #     while end_red > 0 or end_green > 0 or end_blue > 0:
        #         if end_red > 0:
        #             end_red -= 1
        #             #red.ChangeDutyCycle(end_red / 2)
        #             wiringpi.softPwmWrite(17, int(float(end_red)/ 2))
        #         if end_green > 0:
        #             end_green -= 1
        #             #green.ChangeDutyCycle(end_green / 2)
        #             wiringpi.softPwmWrite(27, int(float(end_green) / 2))
        #         if end_blue > 0:
        #             end_blue -= 1
        #             #blue.ChangeDutyCycle(end_blue / 2)
        #             wiringpi.softPwmWrite(22, int(float(end_blue) / 2))
        #         time.sleep(0.005)
        #     GPIO.output(pinRelay, GPIO.LOW)
        # finally:
        #     light_mutex.release()
        lighting_pir_svr_sock_connection.close()

def light_cmd(keyboard_Event, comp_Event, delete_Event):
    #global red
    #global green
    #global blue
    #global redS
    #global greenS
    #global blueS
    global pinRelay
    global pinRelayS
    global THREADS
    global SECONDARY_RELAY_HIGH
    global PRIMARY_RELAY_HIGH

    # *establish server socket for Control subsystem to connect to for LI send
    lighting_lightCmd_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
    lighting_lightCmd_svr_sock_host = ''  # * Get local machine name
    lighting_lightCmd_svr_sock_port = 12347  # PIR port.
    lighting_lightCmd_svr_sock.bind((lighting_lightCmd_svr_sock_host, lighting_lightCmd_svr_sock_port))  # * Bind to the port

    lighting_lightCmd_svr_sock.listen(5)  # * Now wait for client connection.
    print "listening on light_cmd thread..."
    # print s.recv(1024)
    # s.close                     #* Close the socket when done

    while True:
        lighting_lightCmd_svr_sock_connection, lighting_lightCmd_svr_sock_connection_addr = lighting_lightCmd_svr_sock.accept()  # * Establish connection w
        print '\nGot connection from', lighting_lightCmd_svr_sock_connection_addr, "\n"

        light_intensity = lighting_lightCmd_svr_sock_connection.recv(1024)
        cmd = light_intensity.split('|')
        print "GOT on light_cmd thread: ", cmd

        if not delete_Event.isSet():
            delete_Event.wait()

        comp_Event_mutex.acquire()
        try:
            comp_status = comp_Event.isSet()
        finally:
            comp_Event_mutex.release()
        if not comp_status:
            comp_Event.wait()
        secondary_mutex.acquire()
        try:
            if not SECONDARY_RELAY_HIGH:
                GPIO.output(pinRelayS, GPIO.HIGH)
                SECONDARY_RELAY_HIGH = True
            if not PRIMARY_RELAY_HIGH:
                GPIO.output(pinRelay, GPIO.HIGH)
                PRIMARY_RELAY_HIGH = True
        finally:
            secondary_mutex.release()
        if cmd[0] != "":
            if cmd[0] != "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()

            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()


            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()

            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()

            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()


            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))

                prev_greenS = int(float(cmd[9]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()


            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))

                prev_blueS = int(float(cmd[11]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()



            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()


            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_s_b_thread.start()



            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()


            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_g_thread.start()

            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()


            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()

                h_p_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_r_thread.start()

                h_p_g_thread.start()

            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_p_b_thread.start()

            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_r_thread.start()

                h_p_b_thread.start()

            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_r_thread.start()
                h_s_r_thread.start()
                h_s_g_thread.start()


            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))
                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_r_thread.start()
                h_s_r_thread.start()

            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()

                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_r_thread.start()

                h_s_g_thread.start()

            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] != "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_r_thread.start()

                h_s_b_thread.start()
            elif cmd[0] != "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] == "N":
                prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_p_r_thread = threading.Thread(name='h_p_r', target=handle_primary_red,
                                                args=(prev_red, int(float(cmd[0])),))

                h_p_r_thread.start()

            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_s_r_thread.start()

                h_p_g_thread.start()

                h_p_b_thread.start()

            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_g_thread.start()

                h_p_b_thread.start()

            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_r_thread.start()

                h_p_g_thread.start()
                h_s_g_thread.start()

            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_r_thread.start()

                h_p_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_s_r_thread.start()

                h_p_g_thread.start()

            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_g_thread.start()
                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))



                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))
                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_g_thread.start()
                h_s_g_thread.start()

            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] != "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_p_g_thread = threading.Thread(name='h_p_g', target=handle_primary_green,
                                                args=(prev_green, int(float(cmd[2])),))

                h_p_g_thread.start()

            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_s_r_thread.start()

                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_r_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_s_r_thread.start()

                h_p_b_thread.start()

            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_g_thread.start()

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_s_g_thread.start()

                h_p_b_thread.start()

            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))
                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_p_b_thread.start()
                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] != "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_p_b_thread = threading.Thread(name='h_p_b', target=handle_primary_blue,
                                                args=(prev_blue, int(float(cmd[4])),))

                h_p_b_thread.start()

            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_r_thread.start()

                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] != "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_r_thread.start()

                h_s_g_thread.start()

            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_r_thread.start()

                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] != "N" and cmd[3] == "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_s_r_thread = threading.Thread(name='h_s_r', target=handle_secondary_red,
                                                args=(prev_redS, int(float(cmd[1])),))

                h_s_r_thread.start()


            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_g_thread.start()

                h_s_b_thread.start()
            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] != "N" and cmd[5] == "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[10]))
                # prev_redS = int(float(cmd[7]))
                prev_greenS = int(float(cmd[9]))
                # prev_blueS = int(float(cmd[11]))


                h_s_g_thread = threading.Thread(name='h_s_g', target=handle_secondary_green,
                                                args=(prev_greenS, int(float(cmd[3])),))

                h_s_g_thread.start()

            elif cmd[0] == "N" and cmd[2] == "N" and cmd[4] == "N" and cmd[1] == "N" and cmd[3] == "N" and cmd[5] != "N":
                # prev_red = int(float(cmd[6]))
                # prev_green = int(float(cmd[8]))
                # prev_blue = int(float(cmd[8]))
                # prev_redS = int(float(cmd[7]))
                # prev_greenS = int(float(cmd[9]))
                prev_blueS = int(float(cmd[11]))

                h_s_b_thread = threading.Thread(name='h_s_b', target=handle_secondary_blue,
                                                args=(prev_blueS, int(float(cmd[5])),))

                h_s_b_thread.start()


        wiringpi.delay(10)
        lighting_lightCmd_svr_sock_connection.close()



boot_up()

