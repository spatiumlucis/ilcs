"""
File Name: sensor_sub.py

Version Number: v1.0

Target Device: Raspberry Pi 3

Dependencies:
-Control Subsystem database is online and connected to the same network
-lighting_sub.py

Authors:
-Zach Simpson
-Terry So
-Jeremy Trammell
-Chukwuebuka Nwankwo

Code Description:
This Python Script is to be used in the Intelligent Lighting Control System
project, by team Spatium Lucis. The code should NOT be executed before the
Lighting Subsystem Python script. This is because this script establishes
client socket connections with its Lighting Subsystem pair. Also ensure that
the Control Subsystem, both webserver and database are online and connected to
the proper network. This is because this code will attempt to connect to the
database in several locations.

The Sensor Subsystem is responsible for reading information about the Lighting
Subsystem and making sure that it is following the proper circadian rhythm values
set by the user. Several threads are established to allow each of the sensors to
read values independent of one another and write them to the database. Should there
be any detected degradation, the Sensor Subsystem will tell the Lighting Subsystem
to compensate.

Sources:
-PIR sensor code:
https://www.modmypi.com/blog/raspberry-pi-gpio-sensing-motion-detection

-RGB sensor code:
http://bradsrpi.blogspot.com/2013/05/tcs34725-rgb-color-sensor-raspberry-pi.html

-USR sensor code:
https://www.modmypi.com/blog/hc-sr04-ultrasonic-range-sensor-on-the-raspberry-pi

-Python socket code:
https://www.tutorialspoint.com/python/python_networking.html
http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/25850698#25850698

-Python MySQL code:
https://www.tutorialspoint.com/python/python_database_access.htm

-Python thread code:
https://www.tutorialspoint.com/python/python_multithreading.htm
"""

"""
Imports
"""
import time
import socket
import threading
import RPi.GPIO as GPIO
import MySQLdb
import smbus
import sys
import os
import signal

"""
Global Variables
"""
lighting_ip = ""

is_sensor_sub_paired = 0

SLEEP_MODE_STATUS = 0  # 0 == awake, 1 == sleep

COLOR_THRESHOLD = 0

LIGHT_THRESHOLD = 0

OLD_RED = 0

OLD_GREEN = 0

OLD_BLUE = 0

DISTANCE = 8

WAKE_UP_TIME = 0

MASTER_CIRCADIAN_TABLE = []

USER_CIRCADIAN_TABLE = []

CURRENT_MINUTE = 0

SAVED_MINUTE = 0

"""
Mutex locks are used to protect data that
can be read or written to from more than
one thread.
"""
sleep_mutex = threading.Lock()

change_par_mutex = threading.Lock()

keyboard_Event_mutex = threading.Lock()

local_ip = ""

THREADS = []

"""
Functions
"""


def get_ip():
    """
    This function is used to get the local IP address of the Raspberry Pi.

    :return: The local IP address.
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
    This is the main boot up sequence for the Sensor Subsystem.
    First, the function establishes a database connection and
    calculates the master circadian table by calling init_circadian_table().
    Then, the function will check the DB if this Raspberry Pi's IP address
    exists in the DB. If it does, then it will re-establish connection
    with the last known Lighting Subsystem it was paired with, as well as
    retrieve the circadian parameters. If the Sensor Subsystem is new then
    the code will wait until the Control Subsystem adds the room. After
    the circadian parameters are obtained from the DB, the room's circadian
    table is created by calling the calc_user_circadian_table() function.
    Lastly, control is passed to the begin_threading() function so that the
    sensors' threads can be created.

    :return: None
    """
    """
    Import global vars
    """
    global is_sensor_sub_paired
    global lighting_ip
    global COLOR_THRESHOLD
    global LIGHT_THRESHOLD
    global WAKE_UP_TIME
    global SLEEP_MODE_STATUS
    global local_ip
    print "Booting up..."
    """
    Establish DB connection
    """
    print "Establishing boot up database connection.....\n"
    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
    print "Boot up database connection established.\n"
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    print "Creating master circadian table..."
    init_circadian_table()
    print "Master circadian table created."
    local_ip = get_ip()

    """
    Check DB if the sensor sub exists
    """
    sql = """SELECT * FROM sensor_ip WHERE ip = %s"""
    cursor.execute(sql, (local_ip))
    temp = cursor.fetchall()
    if len(temp) == 0:
        """
        The sensor sub does NOT exist in the DB so insert it into
        the sensor_ip and sensor_status tables
        """
        sql = """INSERT INTO sensor_ip(ip, is_paired) VALUES(%s, 0)"""
        sql2 = """INSERT INTO sensor_status(ip, red, green, blue, lumens, red_degraded, green_degraded, blue_degraded, lumens_degraded, sleep_mode_status, distance, service) VALUEs(%s, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)"""
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

    else:
        """
        The sensor sub DOES exist in the DB. Grab its paired status
        """
        is_sensor_sub_paired = temp[0][1]

        """
        Check degrade status for red
        """
        sql = """SELECT * FROM sensor_status WHERE ip = %s"""
        cursor.execute(sql, (local_ip))
        temp = cursor.fetchall()
        is_sensor_service = temp[0][11]
        is_red_deg = temp[0][5]
        is_green_deg = temp[0][6]
        is_blue_deg = temp[0][7]

        if is_sensor_service:
            sql = """UPDATE sensor_status SET service = 0 WHERE ip = %s"""
            try:
                cursor.execute(sql, (local_ip))
                db.commit()
            except (AttributeError, MySQLdb.OperationalError):
                """
                If the DB connection was lost
                """
                print "Trying to reconnect to database in PIR thread..."
                db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                     db="ilcs")
                print "Database connection re-established in PIR thread."
                cursor = db.cursor()

                try:
                    """
                    Try to update DB again
                    """
                    cursor.execute(sql, (local_ip))
                    db.commit()
                except:
                    db.rollback()
            except:
                db.rollback()
        if is_red_deg:
            sql = """UPDATE sensor_status SET red_degraded = 0 WHERE ip = %s"""
            try:
                cursor.execute(sql, (local_ip))
                db.commit()
            except (AttributeError, MySQLdb.OperationalError):
                """
                If the DB connection was lost
                """
                print "Trying to reconnect to database in PIR thread..."
                db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                     db="ilcs")
                print "Database connection re-established in PIR thread."
                cursor = db.cursor()

                try:
                    """
                    Try to update DB again
                    """
                    cursor.execute(sql, (local_ip))
                    db.commit()
                except:
                    db.rollback()
            except:
                db.rollback()
        if is_green_deg:
            sql = """UPDATE sensor_status SET green_degraded = 0 WHERE ip = %s"""
            try:
                cursor.execute(sql, (local_ip))
                db.commit()
            except (AttributeError, MySQLdb.OperationalError):
                """
                If the DB connection was lost
                """
                print "Trying to reconnect to database in PIR thread..."
                db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                     db="ilcs")
                print "Database connection re-established in PIR thread."
                cursor = db.cursor()

                try:
                    """
                    Try to update DB again
                    """
                    cursor.execute(sql, (local_ip))
                    db.commit()
                except:
                    db.rollback()
            except:
                db.rollback()
        if is_blue_deg:
            sql = """UPDATE sensor_status SET blue_degraded = 0 WHERE ip = %s"""
            try:
                cursor.execute(sql, (local_ip))
                db.commit()
            except (AttributeError, MySQLdb.OperationalError):
                """
                If the DB connection was lost
                """
                print "Trying to reconnect to database in PIR thread..."
                db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                     db="ilcs")
                print "Database connection re-established in PIR thread."
                cursor = db.cursor()

                try:
                    """
                    Try to update DB again
                    """
                    cursor.execute(sql, (local_ip))
                    db.commit()
                except:
                    db.rollback()
            except:
                db.rollback()


    if is_sensor_sub_paired == 0:
        """
        If the sensor sub is NOT paired with any lighting sub, then
        establish server socket for control sub to connect to. This
        socket acts as a signal; as soon as the control sub connects,
        the sensor sub will continue with the adding process.
        """
        sensor_add_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sensor_add_svr_sock_host = ''
        sensor_add_svr_sock_port = 12348
        sensor_add_svr_sock.bind((sensor_add_svr_sock_host, sensor_add_svr_sock_port))

        sensor_add_svr_sock.listen(5)
        print "Waiting to be added by Control Subsystem..."

        sensor_add_svr_sock_connection, sensor_add_svr_sock_connection_addr = sensor_add_svr_sock.accept()
        print '\nGot connection from', sensor_add_svr_sock_connection_addr, "\n"
        sensor_add_svr_sock_connection.close()

        """
        Grab the lighting sub IP to be paired with. It ALWAYS will fetch
        the LAST IP in the lighing_ip table.
        """
        sql = """SELECT * from lighting_ip ORDER BY ip DESC LIMIT 1"""
        cursor.execute(sql)
        temp = cursor.fetchall()
        lighting_ip = temp[0][0]
        print "lighting ip: ", lighting_ip

        """
        Update the DB with paired status
        """
        sql = """UPDATE sensor_ip SET is_paired = 1 WHERE ip = %s"""

        try:
            cursor.execute(sql, (local_ip))
            db.commit()
        except:
            db.rollback()
        """
        Establish sensor-light pair
        """
        sql = """INSERT INTO sensor_light_pairs(sensor_ip, lighting_ip) VALUES(%s, %s)"""

        try:
            cursor.execute(sql, (local_ip, lighting_ip))
            db.commit()
        except:
            db.rollback()
        """
        Grab user's values
        """
        sql = """SELECT * FROM sensor_settings WHERE ip = %s"""
        cursor.execute(sql, (local_ip))
        temp = cursor.fetchall()
        print "Sensor Subsystem added with user values: ", temp[0]
        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = temp[0][2]
        LIGHT_THRESHOLD = temp[0][3]

    else:
        """
        The sensor sub DOES have a pair. Grab what lighting sub
        it was connected to by searching the sensor_light_pairs
        table in the DB.
        """
        print "Reconnecting to previous Lighting Subsystem..."
        sql = """SELECT * FROM sensor_light_pairs WHERE sensor_ip = %s"""
        cursor.execute(sql, (local_ip))
        temp = cursor.fetchall()

        lighting_ip = temp[0][1]

        """
        Grab previous sensor sub settings
        """
        sql = """SELECT * FROM sensor_settings WHERE ip = %s"""
        cursor.execute(sql, (local_ip))
        temp = cursor.fetchall()

        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = temp[0][2]
        LIGHT_THRESHOLD = temp[0][3]
        print "Sensor-Light pair re-established with values: ", temp[0]
        sql = """SELECT * FROM sensor_status WHERE ip = %s"""
        cursor.execute(sql, (local_ip))
        temp = cursor.fetchall()
        SLEEP_MODE_STATUS = temp[0][9]
    """
    These events are just temporary for calling calc_user_circadian_table().
    They are better explained in that function and the begin_threading()
    function.
    """
    finalize_change_Event = threading.Event()
    change_par_Event = threading.Event()

    """
    Calculate the user's circadian table for the sensor sub to use.
    """
    calc_user_circadian_table(change_par_Event, finalize_change_Event)
    print "Initializing threads..."
    begin_threading()


def init_circadian_table():
    """
    This function is used for creating the master
    circadian table. The table is a list that has
    1440 locations (1 for each minute of the day).
    Each location is also a list of R, G, B brightness
    values.The value depends on what time of day is is.
    Between different ranges of time there are different
    linear functions for the brightness values.
    NOTE: This table is calculated for a person that wakes
    up at 7AM (420 min) and goes to sleep at 11 PM (1380 min).

    :return: None
    """
    """
    Import global MASTER_CIRCADIAN_TABLE so that it can be edited
    """
    global MASTER_CIRCADIAN_TABLE
    colors = []

    t = 0

    while t < 1440:
        """
        The colors list is always filled in the order R, G, B.
        Afterwards it is appended to the MASTER_CIRCADIAN_TABLE
        """
        if t >= 300 and t <= 420:

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


def calc_user_circadian_table(change_par_Event, finalize_change_Event):
    """
    This function calculates the user's circadian table for the room
    that the Raspberry Pi will be in. Depending on when the user's
    wake up time is, the MASTER_CIRCADIAN_TABLE will be shifted. If the
    user's wake up time is earlier than 7 AM, then the USER_CIRCADIAN_TABLE
    will hold the MASTER_CIRCADIAN_TABLE shifted to the left. If the user
    wakes up later than 7 AM, then the USER_CIRCADIAN_TABLE will hold the
    MASTER_CIRCADIAN_TABLE shifted to the right. Lastly, if the user wakes up
    exactly at 7 AM, then the USER_CIRCADIAN_TABLE will exactly be the
    MASTER_CIRCADIAN_TABLE.

    :param change_par_Event: A threading event when user changed any
    circadian parameter.

    :param finalize_change_Event: A threading event for finalizing the
    change that the user made.

    :return: None.
    """
    """
    Import global vars to be edited
    """
    global WAKE_UP_TIME
    global MASTER_CIRCADIAN_TABLE
    global USER_CIRCADIAN_TABLE

    # Clear current values from USER_CIRCADIAN_TABLE
    """
    When calculating the USER_CIRCADIAN_TABLE again,
    the past values must be cleared but must have the
    same length as the MASTER_CIRCADIAN_TABLE. So, set
    the USER_CIRCADIAN_TABLE to the MASTER_CIRCADIAN_TABLE.
    """
    USER_CIRCADIAN_TABLE = MASTER_CIRCADIAN_TABLE[:]
    """
    Calculate if user wakes up earlier or later than 7 AM
    """
    wake_diff = WAKE_UP_TIME - 420
    count = 0
    if wake_diff < 0:
        """
        User wakes earlier than 7 AM
        """
        while count < 1440:
            USER_CIRCADIAN_TABLE[count + wake_diff] = MASTER_CIRCADIAN_TABLE[count]
            count += 1
    elif wake_diff > 0:
        """
        User wakes up later than 7 AM
        """
        while count < 1440:
            if (count + wake_diff) > 1439:
                """
                For later indexes in the list, the values must wrap around
                to earlier indexes. Therefore, take the MOD.
                """
                USER_CIRCADIAN_TABLE[(count + wake_diff) % 1440] = MASTER_CIRCADIAN_TABLE[count]
            else:
                USER_CIRCADIAN_TABLE[count + wake_diff] = MASTER_CIRCADIAN_TABLE[count]
            count += 1
    else:
        """
        User wakes up at 7 AM
        """
        USER_CIRCADIAN_TABLE = MASTER_CIRCADIAN_TABLE[:]
    """
    If the user changed the wake up time, then the change_par_Event is set.
    Set the the finalize_change_Event and wait 1 sec. This allows for thread
    synchronization.
    """
    if change_par_Event.isSet():
        finalize_change_Event.set()
        time.sleep(1)


def begin_threading():
    """
    This function creates the threads for the following:
    (1) The PIR Sensor
    (2) The RGB Color Sensor
    (3) The USR Sensor
    (4) Circadian commands
    (5) User commands

    All of the threads depend on some or all of some threading
    events. These events allow for synchronization between all of
    the threads. Theses events are:
    (1) Database Events:
        (a) pir_DB_Event
        (b) rgb_DB_Event
        (c) usr_DB_Event
        (d) cmd_DB_Event
        These events are used to make all of the threads wait for
        each of the threads to make their database connections. This
        connection time can vary so it is important to have all of the
        threads wait until all the other threads are ready.

    (2) Sleep Mode Event:
        (a) sleep_mode_Event
        This event is used to make all of the threads wait to write info
        to the database if the Sensor sub sent the Lighting Sub into sleep mode.

    (3) User/technician Events:
        (a) change_par_Event
        (b) finalize_change_Event
        These events are used to shortly pause the threads until the new
        parameters set by the user have been set.
        (c) keyboard_Event
        This event is used to make all of the threads end when the technician
        issues the Ctrl C command. Only works when the sleep_mode_Event is NOT
        set.

    :return: None.
    """
    """
    Import global vars.

    THREADS is a list that holds each of the threads
    and is used to make the main thread wait and join
    when the technician issues Ctrl C.
    """
    global SLEEP_MODE_STATUS
    global THREADS
    """
    Create threading events
    """
    pir_DB_Event = threading.Event()
    rgb_DB_Event = threading.Event()
    usr_DB_Event = threading.Event()
    sleep_mode_Event = threading.Event()
    change_par_Event = threading.Event()
    cmd_DB_Event = threading.Event()
    finalize_change_Event = threading.Event()
    keyboard_Event = threading.Event()
    """
    Set the keyboard_Event so that the Ctrl C
    command will be detected by the other threads
    """
    keyboard_Event.set()

    """
    Set the sleep_mode_Event if the SLEEP_MODE_STATUS
    was detected as 1 during boot up.
    """
    if SLEEP_MODE_STATUS == 1:
        sleep_mode_Event.set()
    """
    Try to create the threads and add them to the THREADS list.
    """
    try:
        print "Starting PIR thread..."
        pir_thread = threading.Thread(name='pir_thread', target=PIR_sensor, args=(
            pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
            keyboard_Event,))
        pir_thread.start()
        THREADS.append(pir_thread)
    except:
        print "Error: unable to start pir thread"
    try:
        print "Starting RGB thread..."
        rgb_thread = threading.Thread(name='rgb_thread', target=RGB_sensor, args=(
            pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
            keyboard_Event,))
        rgb_thread.start()
        THREADS.append(rgb_thread)
    except:
        print "Error: unable to start rgb thread"
    try:
        print "Starting USR thread..."
        usr_thread = threading.Thread(name='usr_thread', target=USR_sensor, args=(
            pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
            keyboard_Event,))
        usr_thread.start()
        THREADS.append(usr_thread)
    except:
        print "Error: unable to start usr thread"
    try:
        print "Starting circadian command thread..."
        circadian_thread = threading.Thread(name='circadian_thread', target=send_circadian_values, args=(
            pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event, keyboard_Event,
            finalize_change_Event,))
        circadian_thread.start()
        THREADS.append(circadian_thread)
    except:
        print "Error: unable to start circadian thread"

    """
    Main thread will wait for user commands
    """
    wait_for_cmd(pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
                 keyboard_Event, finalize_change_Event)


def PIR_sensor(pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
               keyboard_Event):
    """
    This function is the init_function for the PIR sensor thread.
    First the DB connection is established. Then, the PIR sensor
    is polled for motion. If there is not motion detected after
    1 min, then a socket connection is established with the Lighting
    Subsystem to put it into sleep mode. If motion is detected and
    the sleep_mode_Event is set, then the sensor sub will wake up the
    lighting sub via socket connection.

    :param pir_DB_Event: After the DB connection is established this event is set.

    :param rgb_DB_Event: The code will wait until the DB connection is finished in the
    RGB thread.

    :param usr_DB_Event: The code will wait until the DB connection is finished in the
    USR thread.

    :param sleep_mode_Event: If this event is set then the other threads will not write to
    the DB because the lighting sub is in sleep mode. This event is unset if motion is detected.

    :param change_par_Event: The PIR thread will pause if the user changed a circadian parameter
    and will resume after the new parameters are set.

    :param cmd_DB_Event: The PIR thread will wait until the DB connection is finished in the main thread.

    :param keyboard_Event: This event is used to make the thread end if the technician issues Ctrl C.

    :return: None.
    """
    """
    Import global vars
    """
    global SLEEP_MODE_STATUS
    global lighting_ip
    global USER_CIRCADIAN_TABLE
    global SAVED_MINUTE

    print "PIR thread created sucessfully."

    """
    Establish DB conenction
    """
    print "Establishing database connection in PIR thread..."
    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
    print "Database connection established in PIR thread."
    cursor = db.cursor()

    """
    Set the pir_DB_Event and wait for other DB connections to finish
    """
    pir_DB_Event.set()
    rgb_DB_Event.wait()
    usr_DB_Event.wait()
    cmd_DB_Event.wait()

    local_ip = get_ip()

    """
    Initialize the PIR sensor for the Raspberry Pi.
    Use physical pin numbering (GPIO.BOARD).
    The PIR pin is 12.
    Setup PIR as GPIO input
    """
    GPIO.setmode(GPIO.BOARD)
    pir = 12
    GPIO.setup(pir, GPIO.IN)
    print "Waiting for PIR sensor to settle..."
    time.sleep(2)
    print "PIR sensor has now settled."

    """
    Create timer variable and begin polling PIR sensor.
    """
    timer = 0
    while True and keyboard_Event.isSet():
        if timer == 60:
            """
            1 Min of no motion. Create client socket to lighting sub
            and issue sleep command.
            """
            sensor_to_lighting_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sensor_to_lighting_cli_sock_host = lighting_ip.strip()
            sensor_to_lighting_cli_sock_port = 12346
            try:
                sensor_to_lighting_cli_sock.connect(
                    (sensor_to_lighting_cli_sock_host, sensor_to_lighting_cli_sock_port))
            except:
                print "Could not connect to lighting subsystem"
            sensor_to_lighting_cli_sock.send("0|0|0|")

            print "Lighting Subsystem (IP: '%s') has entered sleep mode" % lighting_ip

            """
            Acquire mutex for sleep_mode_Event.
            Set the event.
            """
            sleep_mutex.acquire()
            try:
                sleep_mode_Event.set()
            finally:
                sleep_mutex.release()

            """
            Update DB that the Lighting Sub is in sleep mode.
            """
            sql = """UPDATE sensor_status SET sleep_mode_status = 1 WHERE ip = %s"""
            try:

                cursor.execute(sql, (local_ip))
                db.commit()
            except:
                db.rollback()

            sensor_to_lighting_cli_sock.close()
        """
        Poll PIR sensor for motion
        """
        if GPIO.input(pir):
            """
            Acquire sleep_mode_Event mutex to check status of event.
            """
            sleep_mutex.acquire()
            try:
                sleep_mode = sleep_mode_Event.isSet()
            finally:
                sleep_mutex.release()
            if sleep_mode:
                """
                If the sleep_mode_Event was set, then clear the event.
                """
                sleep_mutex.acquire()
                try:
                    sleep_mode_Event.clear()
                finally:
                    sleep_mutex.release()
                """
                Update the DB that the lighting sub is awake.
                """
                sql = """UPDATE sensor_status SET sleep_mode_status = 0 WHERE ip = %s"""
                try:
                    cursor.execute(sql, (local_ip))
                    db.commit()
                except (AttributeError, MySQLdb.OperationalError):
                    """
                    If the DB connection was lost
                    """
                    print "Trying to reconnect to database in PIR thread..."
                    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                         db="ilcs")
                    print "Database connection re-established in PIR thread."
                    cursor = db.cursor()

                    try:
                        """
                        Try to update DB again
                        """
                        cursor.execute(sql, (local_ip))
                        db.commit()
                    except:
                        db.rollback()
                except:
                    db.rollback()

            """
            Reset the timer upon motion.
            """
            timer = 0

        else:
            if timer <= 60:
                """
                Increase the motion timer
                """
                timer += 1
                print "sleep timer: ", timer
                time.sleep(1)


def RGB_sensor(pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
               keyboard_Event):
    """
    This function is the init function for the RGB thread. This function will first
    establish a DB connection and then wait for the other threads to establish their
    DB connections. Then, the thread will poll the RGB sensor and only write to the
    DB if there is a significant change in readings.

    :param pir_DB_Event: The code will wait until the DB connection is finished in the
    PIR thread.

    :param rgb_DB_Event: After the DB connection is established this event is set.

    :param usr_DB_Event: The code will wait until the DB connection is finished in the
    USR thread.

    :param sleep_mode_Event: If this event is set then the other threads will not write to
    the DB because the lighting sub is in sleep mode.

    :param change_par_Event: The RGB thread will pause if the user changed a circadian parameter
    and will resume after the new parameters are set.

    :param cmd_DB_Event: The RGB thread will wait until the DB connection is finished in the main thread.

    :param keyboard_Event: This event is used to make the thread end if the technician issues Ctrl C.

    :return: None.
    """

    """
    Import global vars.
    """
    global is_sensor_sub_paired
    global lighting_ip
    global COLOR_THRESHOLD
    global LIGHT_THRESHOLD
    global SLEEP_MODE_STATUS
    global WAKE_UP_TIME
    global local_ip
    global OLD_RED
    global OLD_GREEN
    global OLD_BLUE
    print "RGB thread created successfully."

    """
    Establish DB connection
    """
    print "Establishing Database connection.....\n"
    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
    print "Database connection established.\n"
    cursor = db.cursor()

    """
    Set the rgb_DB_Event and wait for other DB connections to finish
    """
    rgb_DB_Event.set()
    pir_DB_Event.wait()
    usr_DB_Event.wait()
    cmd_DB_Event.wait()

    """
    Initialize the RGB sensor
    The RGB sensor uses I2C Bus (smbus)
    Register address must be OR'ed wit 0x80
    """
    bus = smbus.SMBus(1)
    bus.write_byte(0x29, 0x80 | 0x12)
    ver = bus.read_byte(0x29)

    """
    Variables for degradation detection
    """
    primary_red_degraded = False
    secondary_red_degraded = False
    secondary_red_on = False

    if ver == 0x44:
        """
        Finish RGB setup
        0x00 = ENABLE register
        0x01 = Power on, 0x02 RGB sensors enabled
        Reading results start register 14, LSB then MSB
        """
        bus.write_byte(0x29, 0x80 | 0x00)
        bus.write_byte(0x29, 0x01 | 0x02)
        bus.write_byte(0x29, 0x80 | 0x14)

        while True and keyboard_Event.isSet():
            """
            Acquire the sleep_mode_Event mutex and
            acquire the change_par_Event mutex
            """
            sleep_mutex.acquire()
            try:
                sleep_mode = sleep_mode_Event.isSet()
            finally:
                sleep_mutex.release()
            change_par_mutex.acquire()
            try:
                change_par = change_par_Event.isSet()
            finally:
                change_par_mutex.release()
            if sleep_mode == False and change_par == False:
                """
                Get current minute
                """
                current_minute = time.localtime()[3] * 60 + time.localtime()[4]

                """
                If the sleep_mode_Event and the change_par_Event
                are NOT set, then read from the RGB sensor
                """
                data = bus.read_i2c_block_data(0x29, 0)
                """
                The sensor readings must be converted to an RGB brightness.
                Initially the value is a 16-bit number so to get it an R, G,
                or B value, divide it by 256. Then to get the RGB brightness
                divide by 255 and multiply by 100.
                """
                red = float(data[3] << 8 | data[2]) / 256
                red = float(float(red / 255)) * 100
                red = int(red)
                green = float(data[5] << 8 | data[4]) / 256
                green = float(float(green / 255)) * 100
                green = int(green)
                blue = float(data[7] << 8 | data[6]) / 256
                blue = float(float(blue / 255)) * 100
                blue = int(blue)
                lux = int((-0.32466 * red) + (1.57837 * green) + (-0.73191 * blue))
                print "R: %s, G: %s, B: %s, Lux: %s" % (red, green, blue, lux)
                if red < (OLD_RED - (OLD_RED * 0.05)) or red > (OLD_RED + (OLD_RED * 0.05)):
                    """
                    If the red color reading is 5% less or greater than the previous
                    value, then update the database
                    """
                    sql = """UPDATE sensor_status SET red = %s WHERE ip = %s"""
                    try:
                        cursor.execute(sql, (red, local_ip))
                        db.commit()
                        OLD_RED = red
                    except (AttributeError, MySQLdb.OperationalError):
                        """
                        If the DB connection was lost, then reconnect
                        """
                        print "Trying to reconnect to database in RGB thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in RGB thread."
                        cursor = db.cursor()

                        try:
                            cursor.execute(sql, (red, local_ip))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()

                    """
                    Get the current circadian table value for red
                    """
                    circadian_red = USER_CIRCADIAN_TABLE[current_minute][0]
                    if red < (circadian_red - (circadian_red*COLOR_THRESHOLD)):
                        if primary_red_degraded:
                            """
                            Primaries are degraded
                            """
                            if secondary_red_on:
                                if secondary_red_degraded:
                                    """
                                    Update DB to service lighting sub
                                    """
                                    sql = """UPDATE sensor_status SET service = 1 WHERE ip = %s"""
                                    try:
                                        cursor.execute(sql, (local_ip))
                                        db.commit()
                                        OLD_RED = red
                                    except (AttributeError, MySQLdb.OperationalError):
                                        """
                                        If the DB connection was lost, then reconnect
                                        """
                                        print "Trying to reconnect to database in RGB thread..."
                                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis",
                                                             passwd="spatiumlucis",
                                                             db="ilcs")
                                        print "Database connection re-established in RGB thread."
                                        cursor = db.cursor()

                                        try:
                                            cursor.execute(sql, (local_ip))
                                            db.commit()
                                        except:
                                            db.rollback()
                                    except:
                                        db.rollback()
                                else:
                                    """
                                    Secondaries have degraded
                                    """
                                    print "Secondaries degraded"
                                    # """
                                    # Send command to turn secondaries for red on
                                    # """
                                    # secondary_red_comp = circadian_red - red
                                    # primary_red_comp = circadian_red + (circadian_red - red)
                                    # comp_cmd = str(primary_red_comp) + "|" + str(2*secondary_red_comp)
                                    # """
                                    # Create client socket connection to the lighting sub
                                    # """
                                    # comp_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    # comp_cli_sock_host = lighting_ip.strip()
                                    # comp_cli_sock_port = 12347
                                    #
                                    # """
                                    # Send the command string on the socket
                                    # """
                                    # comp_cli_sock.connect((comp_cli_sock_host, comp_cli_sock_port))
                                    # comp_cli_sock.send(comp_cmd)
                                    # comp_cli_sock.close()
                                    # comp_cmd = ""
                                    secondary_red_degraded = True
                            else:
                                """
                                Turn secondaries on
                                """
                                print "Turning secondaries on"
                                # """
                                # Send command to turn secondaries for red on
                                # """
                                # secondary_red_comp = circadian_red - red
                                # primary_red_comp = circadian_red + (circadian_red - red)
                                # comp_cmd = str(primary_red_comp) + "|" + str(secondary_red_comp)
                                #
                                # """
                                # Create client socket connection to the lighting sub
                                # """
                                # comp_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                # comp_cli_sock_host = lighting_ip.strip()
                                # comp_cli_sock_port = 12347
                                #
                                # """
                                # Send the command string on the socket
                                # """
                                # comp_cli_sock.connect((comp_cli_sock_host, comp_cli_sock_port))
                                # comp_cli_sock.send(comp_cmd)
                                # comp_cli_sock.close()
                                # comp_cmd = ""
                                secondary_red_on = True
                        else:
                            """
                            Primary has now degraded
                            """
                            print "Primary Degraded"

                            sql = """UPDATE sensor_status SET red_degraded = 1 WHERE ip = %s"""
                            try:
                                cursor.execute(sql, (local_ip))
                                db.commit()
                                OLD_RED = red
                            except (AttributeError, MySQLdb.OperationalError):
                                """
                                If the DB connection was lost, then reconnect
                                """
                                print "Trying to reconnect to database in RGB thread..."
                                db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis",
                                                     passwd="spatiumlucis",
                                                     db="ilcs")
                                print "Database connection re-established in RGB thread."
                                cursor = db.cursor()

                                try:
                                    cursor.execute(sql, (local_ip))
                                    db.commit()
                                except:
                                    db.rollback()
                            except:
                                db.rollback()

                            # primary_red_comp = circadian_red + (circadian_red - red)
                            # comp_cmd = str(primary_red_comp) + "|"
                            #
                            # """
                            # Create client socket connection to the lighting sub
                            # """
                            # comp_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            # comp_cli_sock_host = lighting_ip.strip()
                            # comp_cli_sock_port = 12347
                            #
                            # """
                            # Send the command string on the socket
                            # """
                            # comp_cli_sock.connect((comp_cli_sock_host, comp_cli_sock_port))
                            # comp_cli_sock.send(comp_cmd)
                            # comp_cli_sock.close()
                            # comp_cmd = ""
                            primary_red_degraded = True
                if green < (OLD_GREEN - (OLD_GREEN * 0.05)) or green > (OLD_GREEN + (OLD_GREEN * 0.05)):
                    """
                    If the green color reading is 5% less or greater than the previous
                    value, then update the database
                    """
                    sql = """UPDATE sensor_status SET green = %s WHERE ip = %s"""
                    try:
                        cursor.execute(sql, (green, local_ip))
                        db.commit()
                        OLD_GREEN = green
                    except (AttributeError, MySQLdb.OperationalError):
                        """
                        If DB connection was lost, then reconnect
                        """
                        print "Trying to reconnect to database in RGB thread"
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in RGB thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, (green, local_ip))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()
                    """
                    Check if sensor reading is within threshold
                    """
                    #code
                if blue < (OLD_BLUE - (OLD_BLUE * 0.05)) or blue > (OLD_BLUE + (OLD_BLUE * 0.05)):
                    """
                    If the blue color readings are 5% less or greater than previous reading, then
                    update the DB
                    """
                    sql = """UPDATE sensor_status SET blue = %s WHERE ip = %s"""
                    try:
                        cursor.execute(sql, (blue, local_ip))
                        db.commit()
                        OLD_BLUE = blue
                    except (AttributeError, MySQLdb.OperationalError):
                        """
                        If DB connection was lost, then reconnect
                        """
                        print "Trying to reconnect to database in RGB thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in RGB thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, (blue, local_ip))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()
                    """
                    Check if sensor reading is within threshold
                    """
                    #code

                time.sleep(2)

    else:
        print "Error: RGB sensor not found."


def USR_sensor(pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
               keyboard_Event):
    """
    This function is the init function for the USR sensor.
    The purpose is to poll the USR sensor to check the distance between the sensor sub
    and lighting sub. If the distance falls below 8 Ft, then the DB will be updated so
    that an alert message can be created.

    :param pir_DB_Event: The code will wait until the DB connection is finished in the
    PIR thread.

    :param rgb_DB_Event: The code will wait until the DB connection is finished in the
    PIR thread.

    :param usr_DB_Event: This event is set after the DB connection has been established

    :param sleep_mode_Event: If this event is set then the other threads will not write to
    the DB because the lighting sub is in sleep mode.

    :param change_par_Event: The USR thread will pause if the user changed a circadian parameter
    and will resume after the new parameters are set.

    :param cmd_DB_Event: The USR thread will wait until the DB connection is finished in the main thread.

    :param keyboard_Event: This event is used to make the thread end if the technician issues Ctrl C.

    :return: None.
    """
    print "USR thread created successfully."
    """
    import global vars
    """
    global is_sensor_sub_paired
    global lighting_ip
    global COLOR_THRESHOLD
    global LIGHT_THRESHOLD
    global WAKE_UP_TIME
    """
    Connect to DB
    """
    print "Establishing Database connection in USR thread..."
    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
    print "Database connection established in USR thread."
    """
    Set the usr_DB_event and wait for other connections to finish
    """
    usr_DB_Event.set()
    pir_DB_Event.wait()
    rgb_DB_Event.wait()
    cmd_DB_Event.wait()

    cursor = db.cursor()
    """
    Set the distance to be 8 in the DB
    """
    sql = """UPDATE sensor_status SET distance = 8 WHERE ip = %s"""
    try:
        cursor.execute(sql, (local_ip))
        db.commit()
    except (AttributeError, MySQLdb.OperationalError):
        print "Trying to reconnect to database in USR thread..."
        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
        print "Database connection re-established in USR thread."
        cursor = db.cursor()
        try:
            cursor.execute(sql, (distInFt, local_ip))
            db.commit()
        except:
            db.rollback()
    except:
        db.rollback()
    """
    Initialize the USR sensor.
    Set Pin mode to physical pin mode (GPIO.BOARD)
    The TRIG pin is 36 and will be GPIO out
    The ECHO pin is 38 and will be GPIO in
    """
    GPIO.setmode(GPIO.BOARD)
    TRIG = 36
    ECHO = 38
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)

    while True and keyboard_Event.isSet():
        """
        Begin reading from the sensor
        """
        GPIO.output(TRIG, False)
        time.sleep(2)

        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        """
        Check if ECHO is LOW
        Save the last known time of LOW
        """
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
        """
        Check if ECHO is HIGH
        Save last know time of HIGH
        """
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        """
        Get pulse duration
        """
        pulse_duration = pulse_end - pulse_start

        """
        Get distance and convert to Feet from cm.
        """
        distance = pulse_duration * 17150
        distance = round(distance, 2)
        distInFt = distance / 30.48
        distInFt = round(distInFt, 2)

        if distInFt >= 8:
            """
            Print distance if >= 8. This will be removed.
            """
            print "Distance:", distance, "cm"  # Print distance with 0.5 cm calibration; other website has "distance - 0.5","cm"
            print "Distance:", distInFt, "ft"  # Print distance in ft
        else:
            """
            If distance is out of range then update DB
            """
            print "Out Of Range"  # display out of range
            sql = """UPDATE sensor_status SET distance = -1 WHERE ip = %s"""
            try:
                cursor.execute(sql, (local_ip))
                db.commit()
            except (AttributeError, MySQLdb.OperationalError):
                """
                If DB connection was lost, then reconnect
                """
                print "Trying to reconnect to database in USR thread..."
                db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                     db="ilcs")
                print "Database connection re-established in USR thread."
                cursor = db.cursor()
                try:
                    cursor.execute(sql, (distInFt, local_ip))
                    db.commit()
                except:
                    db.rollback()
            except:
                db.rollback()


def send_circadian_values(pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
                          keyboard_Event, finalize_change_Event):
    """
    This function sends a new RGB brightness command to the lighting sub via socket
    every minute. If the sleep_mode_Event is set then no command will be sent until
    the sleep_mode_Event is cleared. If the change_par_Event is set then a new command
    will immediately be sent to the lighting sub.

    :param pir_DB_Event: The function will wait until this event is set by the DB connection
    being established.

    :param rgb_DB_Event: The function will wait until this event is set by the DB connection
    being established.

    :param usr_DB_Event: The function will wait until this event is set by the DB connection
    being established.

    :param sleep_mode_Event: If this event is set then the other threads will not write to
    the DB because the lighting sub is in sleep mode. No brightness commands will not be sent.

    :param change_par_Event: The USR thread will pause if the user changed a circadian parameter
    and will resume after the new parameters are set.

    :param cmd_DB_Event: The function will wait until this event is set by the DB connection
    being established.

    :param keyboard_Event: This event is used to make the thread end if the technician issues Ctrl C.

    :param finalize_change_Event: This event is used for waiting until the new parameters
    have been finalized when the user changed a pararmeter.

    :return: None.
    """
    """
    Import global vars
    """
    global USER_CIRCADIAN_TABLE
    global SLEEP_MODE_STATUS
    #global CURRENT_MINUTE
    global lighting_ip

    """
    Wait for DB connections to finish
    """
    usr_DB_Event.wait()
    pir_DB_Event.wait()
    rgb_DB_Event.wait()
    cmd_DB_Event.wait()

    count = 0
    circadian_cmd = ""

    while True and keyboard_Event.isSet():
        """
        Acquire the sleep_mode_Event mutex and
        check its status
        """
        sleep_mutex.acquire()
        try:
            sleep_mode = sleep_mode_Event.isSet()
        finally:
            sleep_mutex.release()
        """
        Acquire the change_par_Event mutex and
        check its status
        """
        change_par_mutex.acquire()
        try:
            change_par = change_par_Event.isSet()
        finally:
            change_par_mutex.release()
        if sleep_mode == False and change_par == False:
            """
            If the sleep_mode_Event and the change_par_Event
            are NOT set, then send a brightness command
            """
            # time_mutex.acquire()
            # try:
            # print "noon: ", USER_CIRCADIAN_TABLE[720]
            """
            Get the current time from the Raspberry Pi.
            NOTE: If the device time is wrong, then
            the wrong values WILL be sent to the lights.
            Ensure that the Raspberry Pi has the correct time.
            """
            current_minute = time.localtime()[3] * 60 + time.localtime()[4]
            """
            Create the command string. Format:
                        R|G|B|
            """
            circadian_cmd += str(USER_CIRCADIAN_TABLE[current_minute][0])
            circadian_cmd += "|"
            circadian_cmd += str(USER_CIRCADIAN_TABLE[current_minute][1])
            circadian_cmd += "|"
            circadian_cmd += str(USER_CIRCADIAN_TABLE[current_minute][2])
            circadian_cmd += "|"

            """
            Create client socket connection to the lighting sub
            """
            circadian_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            circadian_cli_sock_host = lighting_ip.strip()
            circadian_cli_sock_port = 12347

            """
            Send the command string on the socket and close the socket
            """
            circadian_cli_sock.connect((circadian_cli_sock_host, circadian_cli_sock_port))
            circadian_cli_sock.send(circadian_cmd)
            circadian_cli_sock.close()

            """
            Clear the command string
            """
            circadian_cmd = ""

            """
            Count for 1 minute
            """
            while count < 60:
                keyboard_Event_mutex.acquire()
                try:
                    keyboard = keyboard_Event.isSet()
                finally:
                    keyboard_Event_mutex.release()
                if not keyboard:
                    break
                """
                Acquire the sleep_mode_Event mutex and check
                the status
                """
                sleep_mutex.acquire()
                try:
                    sleep_mode = sleep_mode_Event.isSet()
                finally:
                    sleep_mutex.release()
                """
                Acquire the sleep_mode_Event mutex and check
                the status
                """
                change_par_mutex.acquire()
                try:
                    change_par = change_par_Event.isSet()
                finally:
                    change_par_mutex.release()
                if sleep_mode or change_par:
                    """
                    If the sleep_mode_Event was set break out of
                    counting loop
                    """
                    print "vals changed"
                    if change_par:
                        """
                        If the change_par_Event was set then
                        wait for the changes to finalize
                        """
                        finalize_change_Event.wait()
                        finalize_change_Event.clear()
                    break
                print "count: ", count
                time.sleep(1)
                count += 1
            """
            Reset the counter after 1 min, or sleep mode or change par events
            """
            count = 0
        else:
            """
            To be removed later
            """
            print "checking again.."
            time.sleep(1)


def wait_for_cmd(pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
                 keyboard_Event, finalize_change_Event):
    """
    This function waits for commands from the user. The control subsystem will send a command
    to the server socket here on the sensor subsystem. The commands that will be recieved can
    be the following:
    (1) D|
    This command will delete the sensor subsystem and lighting subsystem information from
    all tables in the DB
    (2) <Wake time>|<Color Threshold>|<Light Threshold>|
    The command will contain values for the wake up time, color threshold, and light threshold.
    If there is not a value for any of these, then the letter 'N' will be in the place for that
    parameter.
    Example:
    380|N|70|
    This will set the new wake up time to 380 min, no nothing with the color threshold, and set the
    light threshold to 70%.

    :param pir_DB_Event: This event is used to make this thread wait until the PIR thread has
    established it DB connection

    :param rgb_DB_Event: This event is used to make this thread wait until the RGB thread has
    established it DB connection

    :param usr_DB_Event: This event is used to make this thread wait until the USR thread has
    established it DB connection

    :param sleep_mode_Event: Not used as of now.

    :param change_par_Event: Used to make all other threads to wait whenever the user sends
    a command from the control subsystem

    :param cmd_DB_Event: This event is set after this thread establishes DB connection

    :param keyboard_Event: This event is set when the technician issues a Ctrl C on the terminal

    :param finalize_change_Event: Used whenever the user changes a parameter. Allows other threads
    to continue.

    :return: None.
    """
    """
    Import global vars
    """
    global lighting_ip
    global COLOR_THRESHOLD
    global LIGHT_THRESHOLD
    global WAKE_UP_TIME
    global THREADS
    global local_ip

    """
    Establish DB connection
    """
    print "Establishing Database connection in main thread..."
    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
    print "Database connection established in main thread."
    cursor = db.cursor()

    """
    Wait for other DB connections to finish
    """
    cmd_DB_Event.set()
    usr_DB_Event.wait()
    pir_DB_Event.wait()
    rgb_DB_Event.wait()

    """
    Create server socket for control subsystem to connect to
    and send commands
    """
    wait_cmd_svr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    wait_cmd_svr_sock_host = ''
    wait_cmd_svr_sock_port = 12349
    wait_cmd_svr_sock.bind((wait_cmd_svr_sock_host, wait_cmd_svr_sock_port))

    wait_cmd_svr_sock.listen(5)
    try:
        while True:
            # print "current values", WAKE_UP_TIME, " ", COLOR_THRESHOLD, " ", LIGHT_THRESHOLD
            wait_cmd_svr_sock_connection, wait_cmd_svr_sock_connection_addr = wait_cmd_svr_sock.accept()  # * Establish connection w
            print '\nGot connection from', wait_cmd_svr_sock_connection_addr, "\n"

            """
            Receive the command on the socket
            """
            cmd = (wait_cmd_svr_sock_connection.recv(1024)).strip()
            if len(cmd) == 0:
                wait_cmd_svr_sock_connection.close()
                continue
            else:
                """
                Split the string on '|'
                """
                cmd = cmd.split('|')
                print "cmd got: ", cmd
                if cmd[0] == 'D':
                    """
                    If the the delete command was issued, then delete
                    all data from the tables in the DB.
                    Also, tell the lighting sub to turn off via socket
                    connection.
                    """
                    delete_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # * Create a socket object
                    delete_sock_host = lighting_ip  # * Get lighting IP
                    delete_sock_port = 12346  # * Reserve a port for your service.
                    try:
                        delete_sock.connect((delete_sock_host, delete_sock_port))
                    except:
                        print "\nCould not connect to lighting subsystem\n"
                    delete_sock.send("D|")
                    delete_sock.close()

                    sql = """DELETE FROM sensor_ip WHERE ip = %s"""
                    try:
                        cursor.execute(sql, (local_ip))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, (local_ip))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()

                    sql = """DELETE FROM sensor_settings WHERE ip = %s"""
                    try:
                        cursor.execute(sql, (local_ip))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, (local_ip))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()

                    sql = """DELETE FROM sensor_status WHERE ip = %s"""
                    try:
                        cursor.execute(sql, (local_ip))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, (local_ip))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()
                    sql = """DELETE FROM sensor_light_pairs WHERE sensor_ip = %s"""
                    try:
                        cursor.execute(sql, (local_ip))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing Database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, (local_ip))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()
                    sql = """DELETE FROM lighting_ip WHERE ip = %s"""
                    try:
                        cursor.execute(sql, (lighting_ip))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, (lighting_ip))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()
                    """
                    Issue kill command to the script
                    """
                    pid = os.getpid()
                    os.kill(pid, signal.SIGKILL)
                else:
                    """
                    If the control subsystem sent a command string then
                    set the change_par_Event so that other threads pause.
                    """
                    change_par_Event.set()
                    time.sleep(2)
                    if cmd[0] != 'N':
                        """
                        If the wake time field is NOT 'N' then recalculate
                        the USER_CIRCADIAN_TABLE
                        """
                        WAKE_UP_TIME = int(cmd[0])
                        calc_user_circadian_table(change_par_Event, finalize_change_Event)
                    if cmd[1] != 'N':
                        """
                        If the color threshold field is NOT 'N' then
                        set the new COLOR_THRESHOLD value
                        """
                        COLOR_THRESHOLD = int(cmd[1])
                    if cmd[2] != 'N':
                        """
                        If the light threshold field is NOT 'N' then
                        set the new LIGHT_THRESHOLD value
                        """
                        LIGHT_THRESHOLD = int(cmd[2])
                    """
                    Clear the change_par_Event
                    """
                    change_par_Event.clear()

            wait_cmd_svr_sock_connection.close()
    except KeyboardInterrupt:
        """
        If the technician issues the Ctrl C command on the terminal,
        try to end the script. Only works if the sleep_mode_Event is
        NOT set
        """
        keyboard_Event.clear()
        """
        Wait for threads to end
        """
        for thread in THREADS:
            thread.join()
        """
        End the script
        """
        sys.exit()


"""
This is where the Script starts. The boot_up()
function is always the first thing that will
be called when the sensor_sub.py script is
ran.
"""
boot_up()
