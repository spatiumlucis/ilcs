# PIR code from: modmypi.com/blog/raspberry-pi-gpio-sensing-motion-detection
# Socket code: tutorialspoint.com/python/python_networking.html
import thread
import time
import socket
from threading import Lock
import RPi.GPIO as GPIO  # Import GPIO library
import MySQLdb  # Required for MySQL stuff

# Open database connection
print "Establishing Database connection.....\n"
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
print "Database connection established.\n"
# prepare a cursor object using cursor() method
cursor = db.cursor()

lighting_ip = ""

is_sensor_sub_paired = 0

SLEEP_MODE_STATUS = 0  # 0 == awake, 1 == sleep

COLOR_THRESHOLD = 0

LIGHT_THRESHOLD = 0

WAKE_UP_TIME = 0

MASTER_CIRCADIAN_TABLE = []

USER_CIRCADIAN_TABLE = []

CURRENT_MINUTE = 0

sleep_mutex = Lock()

time_mutex = Lock()

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
    print "Booting up...."
    global cursor
    global is_sensor_sub_paired
    global lighting_ip
    global COLOR_THRESHOLD
    global LIGHT_THRESHOLD
    global WAKE_UP_TIME

    init_circadian_table()

    local_ip = get_ip()
    sql = """SELECT * FROM sensor_ip WHERE ip = %s"""
    cursor.execute(sql, (local_ip))
    temp = cursor.fetchall()
    if len(temp) == 0:
        print "empty tuple"
        # insert into DB
        sql = """INSERT INTO sensor_ip(ip, is_paired) VALUES(%s, 0)"""
        sql2 = """INSERT INTO sensor_status(ip, red, green, blue, lumens, red_degraded, green_degraded, blue_degraded, lumens_degraded, sleep_mode_status, distance) VALUEs(%s, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)"""
        try:
            cursor.execute(sql, (local_ip))
            db.commit()
        except:
            db.rollback()
        try:
            cursor.execute(sql2, (local_ip))
            db.commit()
        except:
            db.rollback()
            # is_sensor_sub_paired = temp[0][1]

    else:
        is_sensor_sub_paired = temp[0][1]

    if is_sensor_sub_paired == 0:  # not paired yet
        # establish server socket and wait to be told to continue

        sensor_add_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
        sensor_add_svr_sock_host = ''  # * Get local machine name
        sensor_add_svr_sock_port = 12349  # PIR port.
        sensor_add_svr_sock.bind((sensor_add_svr_sock_host, sensor_add_svr_sock_port))  # * Bind to the port

        sensor_add_svr_sock.listen(5)  # * Now wait for client connection.
        print "listening on add sensor sub socket...."

        sensor_add_svr_sock_connection, sensor_add_svr_sock_connection_addr = sensor_add_svr_sock.accept()  # * Establish connection
        print '\nGot connection from', sensor_add_svr_sock_connection_addr, "\n"
        sensor_add_svr_sock_connection.close()
        # grab ip for lighting subsystem pair
        sql = """SELECT * from lighting_ip ORDER BY ip DESC LIMIT 1"""
        cursor.execute(sql)
        temp = cursor.fetchall()
        lighting_ip = temp[0][0]
        print "lighting ip: ", lighting_ip

        # update DB that this sensor sub has been paired
        sql = """UPDATE sensor_ip SET is_paired = 1 WHERE ip = %s"""

        try:
            cursor.execute(sql, (local_ip))
            db.commit()
        except:
            db.rollback()
        # establish pair with lighting sub
        sql = """INSERT INTO sensor_light_pairs(sensor_ip, lighting_ip) VALUES(%s, %s)"""

        try:
            cursor.execute(sql, (local_ip, lighting_ip))
            db.commit()
        except:
            db.rollback()
        # set the values from the user
        sql = """SELECT * FROM sensor_settings WHERE ip = %s"""
        cursor.execute(sql, (local_ip))
        temp = cursor.fetchall()
        print "temp: ", temp
        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = temp[0][2]
        LIGHT_THRESHOLD = temp[0][3]

    else:
        # sensor sub has a pair
        # grab the pair
        sql = """SELECT * FROM sensor_light_pairs WHERE sensor_ip = %s"""
        cursor.execute(sql, (local_ip))
        temp = cursor.fetchall()
        print "temp: ", temp
        lighting_ip = temp[0][1]
        # retrieve old settings
        sql = """SELECT * FROM sensor_settings WHERE ip = %s"""
        cursor.execute(sql, (local_ip))
        temp = cursor.fetchall()

        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = temp[0][2]
        LIGHT_THRESHOLD = temp[0][3]

        # print "old settings: ", WAKE_UP_TIME, " ", COLOR_THRESHOLD, " ", LIGHT_THRESHOLD," ",lighting_ip,"\n"
    calc_user_circadian_table()
    begin_threading()

def init_circadian_table:
    global MASTER_CIRCADIAN_TABLE
    colors = []

    t = 0

    while t < 1440:
        print "t", t
        if t >= 300 and t <= 420:
            # red_values.append((135/120)*t - 337.5)
            colors.append((((135.0 / 120) * t - 337.5) / 255) * 100)

            colors.append((((206.0 / 120) * t - 515) / 255) * 100)

            colors.append((((250.0 / 120) * t - 625) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []

        elif t >= 420 and t <= 720:
            colors.append((((120.0 / 300) * t - 33) / 255) * 100)

            colors.append((((49.0 / 300) * t + 137.4) / 255) * 100)

            colors.append((((5.0 / 300) * t + 243) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []
        elif t >= 720 and t <= 1140:
            colors.append((((-2.0 / 420) * t + 258.429) / 255) * 100)

            colors.append((((-161.0 / 420) * t + 531) / 255) * 100)

            colors.append((((-172.0 / 420) * t + 549.857) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []
        elif t >= 1140 and t <= 1380:
            colors.append((((-253.0 / 240) * t + 1454.75) / 255) * 100)

            colors.append((((-94.0 / 240) * t + 540.5) / 255) * 100)

            colors.append((((-83.0 / 240) * t + 477.25) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []
        else:
            colors.append(0)

            colors.append(0)

            colors.append(0)

            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []

        t += 1

def calc_user_circadian_table:
    global WAKE_UP_TIME
    global MASTER_CIRCADIAN_TABLE
    global USER_CIRCADIAN_TABLE

    #Clear current values from USER_CIRCADIAN_TABLE
    USER_CIRCADIAN_TABLE = []

    wake_diff = WAKE_UP_TIME - 420 #wake - 7 AM
    count = 0
    if wake_diff < 0:
        #user wakes earlier
        while count < 1440:
            USER_CIRCADIAN_TABLE[count + wake_diff] = MASTER_CIRCADIAN_TABLE[count]
    elif wake_diff > 0:
        #user wakes later
        if (count + wake_diff) > 1439:
            USER_CIRCADIAN_TABLE[(count + wake_diff) % 1440] = MASTER_CIRCADIAN_TABLE[count]
        else:
            USER_CIRCADIAN_TABLE[count+wake_diff] = MASTER_CIRCADIAN_TABLE[count]
    else:
        USER_CIRCADIAN_TABLE = MASTER_CIRCADIAN_TABLE

def begin_threading():
    # Create two threads as follows
    try:
        thread.start_new_thread(PIR_sensor, ())
        thread.start_new_thread(RGB_sensor, ())
        thread.start_new_thread(USR_sensor, ())
        thread.start_new_thread(send_circadian_values, ())

    except:
        print "Error: unable to start thread"
    wait_for_cmd()

def PIR_sensor():
    print "Entered read_PIR!\n"
    # global CURRENT_LIGHT_INTENSITY
    global SLEEP_MODE_STATUS
    global cursor
    global lighting_ip
    global USER_CIRCADIAN_TABLE
    global CURRENT_MINUTE


    local_ip = get_ip()
    # * set up client connection to Lighting Subsystem
    sensor_to_lighting_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # * Create a socket object
    sensor_to_lighting_cli_sock_host = lighting_ip  # * Get lighting IP
    sensor_to_lighting_cli_sock_port = 12346  # * Reserve a port for your service.

    # * Set up PIR
    GPIO.setmode(GPIO.BOARD)  # Set GPIO pin numbering
    pir = 40  # Associate pin 40 to pir
    GPIO.setup(pir, GPIO.IN)  # Set pin as GPIO in
    print "\nWaiting for sensor to settle\n"
    time.sleep(2)  # Waiting 2 seconds for the sensor to initiate
    print "\nDetecting motion\n"
    # * Begin reading from PIR

    timer = 0  # * create timer
    while True:
        if timer == 60:
            try:
                sensor_to_lighting_cli_sock.connect(
                    (sensor_to_lighting_cli_sock_host, sensor_to_lighting_cli_sock_port))
            except:
                print "\nCould not connect to lighting subsystem\n"
            sensor_to_lighting_cli_sock.send("0|0|0|")

            print "\nEntering sleep mode\n"
            # * set into sleep mode
            sleep_mutex.acquire()
            try:
                SLEEP_MODE_STATUS = 1
                # Prepare SQL query to UPDATE required records
                sql = """UPDATE sensor_status SET sleep_mode_status = 1 WHERE ip = %s"""
                try:
                    # Execute the SQL command
                    cursor.execute(sql, (local_ip))
                    # Commit your changes in the database
                    db.commit()
                except:
                    # Rollback in case there is any error
                    db.rollback()
            finally:
                sleep_mutex.release()

            sensor_to_lighting_cli_sock.close()

        if GPIO.input(pir) and SLEEP_MODE_STATUS == 1:  # Check whether pir is HIGH
            print "\nMotion Detected!\n"
            # * turn lights back on with the current values
            try:
                sensor_to_lighting_cli_sock.connect(
                    (sensor_to_lighting_cli_sock_host, sensor_to_lighting_cli_sock_port))
            except:
                print "\nCould not connect to lighting subsystem\n"

            ########code to check Circadian table#######################
            circadian_cmd = ""
            time_hour_in_min = (time.localtime()[3]) * 60
            time_min_in_min = (time.localtime()[4])

            total_time = time_hour_in_min + time_min_in_min

            circadian_cmd += str(USER_CIRCADIAN_TABLE[total_time][0])
            circadian_cmd += "|"
            circadian_cmd += str(USER_CIRCADIAN_TABLE[total_time][1])
            circadian_cmd += "|"
            circadian_cmd += str(USER_CIRCADIAN_TABLE[total_time][2])
            circadian_cmd += "|"

            sensor_to_lighting_cli_sock.send(circadian_cmd)

            timer = 0
            time.sleep(2)  # D1- Delay to avoid multiple detection

            # * change SLEEP_MODE_STATUS to AWAKE
            sleep_mutex.acquire()
            try:
                SLEEP_MODE_STATUS = 0
                sql = """UPDATE sensor_status SET sleep_mode_status = 0 WHERE ip = %s"""
                try:
                    # Execute the SQL command
                    cursor.execute(sql, (local_ip))
                    # Commit your changes in the database
                    db.commit()
                except:
                    # Rollback in case there is any error
                    db.rollback()
            finally:
                sleep_mutex.release()

            time_mutex.acquire()
            try:
                CURRENT_MINUTE = total_time
            finally:
                time_mutex.release()

            sensor_to_lighting_cli_sock.close()

        else:
            timer += 1
            print "\n", timer, " SLEEP: ", SLEEP_MODE_STATUS
            time.sleep(1)


def RGB_sensor():
    print "Entered read_RGB!\n"
    global cursor
    global is_sensor_sub_paired
    global lighting_ip
    global COLOR_THRESHOLD
    global LIGHT_THRESHOLD
    global WAKE_UP_TIME


def USR_sensor():
    print "Entered read_USR!\n"
    global cursor
    global is_sensor_sub_paired
    global lighting_ip
    global COLOR_THRESHOLD
    global LIGHT_THRESHOLD
    global WAKE_UP_TIME

def send_circadian_values:
    global USER_CIRCADIAN_TABLE
    global SLEEP_MODE_STATUS
    global CURRENT_MINUTE
    #create client socket connection
    circadian_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # * Create a socket object
    circadian_cli_sock_host = lighting_ip  # * Get lighting IP
    circadian_cli_sock_port = 12347  # * Reserve a port for your service.

    count = 0
    circadian_cmd = ""
    while True:

        if SLEEP_MODE_STATUS == 0:
            time_hour_in_min = (time.localtime()[3]) * 60
            time_min_in_min = (time.localtime()[4])

            time_mutex.acquire()
            try:
                CURRENT_MINUTE = time_hour_in_min + time_min_in_min

            finally:
                time_mutex.release()

            circadian_cmd += str(USER_CIRCADIAN_TABLE[CURRENT_MINUTE][0])
            circadian_cmd += "|"
            circadian_cmd += str(USER_CIRCADIAN_TABLE[CURRENT_MINUTE][1])
            circadian_cmd += "|"
            circadian_cmd += str(USER_CIRCADIAN_TABLE[CURRENT_MINUTE][2])
            circadian_cmd += "|"
            # send on socket
            circadian_cli_sock.connect((circadian_cli_sock_host, circadian_cli_sock_port))
            circadian_cli_sock.send(circadian_cmd)
            # close socket
            circadian_cli_sock.close()

            # wait for a minute
            while count < 60:
                time.sleep(1)
                count += 1

            count = 0
            circadian_cmd = ""



def wait_for_cmd():
    print "Entered wait cmd!\n"
    global cursor
    global is_sensor_sub_paired
    global lighting_ip
    global COLOR_THRESHOLD
    global LIGHT_THRESHOLD
    global WAKE_UP_TIME
    # create server socket for user to connect to for changing values

    wait_cmd_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # * Create a socket object
    wait_cmd_svr_sock_host = ''  # * Get local machine name
    wait_cmd_svr_sock_port = 12349  # sensor sub port
    wait_cmd_svr_sock.bind((wait_cmd_svr_sock_host, wait_cmd_svr_sock_port))  # * Bind to the port

    wait_cmd_svr_sock.listen(5)  # * Now wait for client connection.
    print "listening for cmds from user...."

    while True:
        wait_cmd_svr_sock_connection, wait_cmd_svr_sock_connection_addr = wait_cmd_svr_sock.accept()  # * Establish connection w
        print '\nGot connection from', wait_cmd_svr_sock_connection_addr, "\n"

        cmd = (wait_cmd_svr_sock_connection.recv(1024)).strip()  # * read light intensity from control
        if len(cmd) == 0:
            wait_cmd_svr_sock_connection.close()
            continue

        print "cmd got: ", cmd

        wait_cmd_svr_sock_connection.close()


boot_up()