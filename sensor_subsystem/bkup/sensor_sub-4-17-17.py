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
import math

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

PREV_COLORS = [0, 0, 0]

WAKE_UP_TIME = 0

MASTER_CIRCADIAN_TABLE = []

MASTER_OFFSET_TABLE = []

MASTER_LUX_TABLE = []

USER_CIRCADIAN_TABLE = []

USER_OFFSET_TABLE = []

USER_LUX_TABLE = []

CURRENT_MINUTE = 0

SAVED_MINUTE = 0

primary_red_degraded = False
primary_red_comp= 0

primary_green_degraded = False
primary_green_comp = 0

primary_blue_degraded = False
primary_blue_comp = 0

CHANGE_THRES = False

CHANGE_WAKE = False
GPIO.setwarnings(False)
"""
Mutex locks are used to protect data that
can be read or written to from more than
one thread.
"""
sleep_mutex = threading.Lock()

change_par_mutex = threading.Lock()

keyboard_Event_mutex = threading.Lock()

color_threshold_mutex = threading.Lock()

user_ct_mutex = threading.Lock()

user_ot_mutex = threading.Lock()

wake_up_mutex = threading.Lock()

finalize_par_mutex = threading.Lock()

change_reset_Event_mutex = threading.Lock()

primary_deg_mutex = threading.Lock()

primary_comp_mutex = threading.Lock()

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
    cursor.execute(sql, ([local_ip]))
    temp = cursor.fetchall()


    if len(temp) == 0:
        """
        The sensor sub does NOT exist in the DB so insert it into
        the sensor_ip and sensor_status tables
        """
        sql = """INSERT INTO sensor_ip(ip, is_paired) VALUES(%s, 0)"""

        try:
            cursor.execute(sql, ([local_ip]))
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
        cursor.execute(sql, ([local_ip]))
        temp = cursor.fetchall()
        is_sensor_service = temp[0][11]
        is_red_deg = temp[0][5]
        is_green_deg = temp[0][6]
        is_blue_deg = temp[0][7]
        print "Deg values: %s %s %s %s" % (is_sensor_service, is_red_deg, is_green_deg, is_blue_deg)
        if is_sensor_service:
            sql = """UPDATE sensor_status SET service = 0 WHERE ip = %s"""
            try:
                cursor.execute(sql, ([local_ip]))
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
                    cursor.execute(sql, ([local_ip]))
                    db.commit()
                except:
                    db.rollback()
            except:
                db.rollback()
        if is_red_deg:
            sql = """UPDATE sensor_status SET red_degraded = 0 WHERE ip = %s"""
            try:
                cursor.execute(sql, ([local_ip]))
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
                    cursor.execute(sql, ([local_ip]))
                    db.commit()
                except:
                    db.rollback()
            except:
                db.rollback()
        if is_green_deg:
            sql = """UPDATE sensor_status SET green_degraded = 0 WHERE ip = %s"""
            try:
                cursor.execute(sql, ([local_ip]))
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
                    cursor.execute(sql, ([local_ip]))
                    db.commit()
                except:
                    db.rollback()
            except:
                db.rollback()
        if is_blue_deg:
            sql = """UPDATE sensor_status SET blue_degraded = 0 WHERE ip = %s"""
            try:
                cursor.execute(sql, ([local_ip]))
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
                    cursor.execute(sql, ([local_ip]))
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

        sql = """INSERT INTO sensor_status(ip, red, green, blue, lumens, red_degraded, green_degraded, blue_degraded, lumens_degraded, sleep_mode_status, distance, service) VALUEs(%s, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)"""
        try:
            cursor.execute(sql, ([local_ip]))
            db.commit()
        except:
            db.rollback()
        """
        Grab the lighting sub IP to be paired with.
        """
        sql = """SELECT * from lighting_ip where is_paired = 0"""
        cursor.execute(sql)
        temp = cursor.fetchall()
        lighting_ip = temp[0][0]
        print "lighting ip: ", lighting_ip

        """
        Update the DB with paired status
        """
        sql = """UPDATE sensor_ip SET is_paired = 1 WHERE ip = %s"""

        try:
            cursor.execute(sql, ([local_ip]))
            db.commit()
        except:
            db.rollback()

        sql = """UPDATE lighting_ip SET is_paired = 1 WHERE ip = %s"""

        try:
            cursor.execute(sql, ([lighting_ip]))
            db.commit()
        except:
            db.rollback()
        """
        Establish sensor-light pair
        """
        sql = """INSERT INTO sensor_light_pairs(sensor_ip, lighting_ip) VALUES(%s, %s)"""

        try:
            cursor.execute(sql, ([local_ip, lighting_ip]))
            db.commit()
        except:
            db.rollback()
        """
        Grab user's values
        """
        sql = """SELECT * FROM sensor_settings WHERE ip = %s"""
        cursor.execute(sql, ([local_ip]))
        temp = cursor.fetchall()
        print "Sensor Subsystem added with user values: ", temp[0]
        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = float(temp[0][2])/100
        print "COLOR_thres is:", COLOR_THRESHOLD
        LIGHT_THRESHOLD = float(temp[0][3])/100

    else:
        """
        The sensor sub DOES have a pair. Grab what lighting sub
        it was connected to by searching the sensor_light_pairs
        table in the DB.
        """
        print "Reconnecting to previous Lighting Subsystem..."
        sql = """SELECT * FROM sensor_light_pairs WHERE sensor_ip = %s"""
        cursor.execute(sql, ([local_ip]))
        temp = cursor.fetchall()

        lighting_ip = temp[0][1]

        """
        Grab previous sensor sub settings
        """
        sql = """SELECT * FROM sensor_settings WHERE ip = %s"""
        cursor.execute(sql, ([local_ip]))
        temp = cursor.fetchall()

        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = float(temp[0][2])/100
        LIGHT_THRESHOLD = float(temp[0][3])/100
        print "Sensor-Light pair re-established with values: ", temp[0]
        sql = """SELECT * FROM sensor_status WHERE ip = %s"""
        cursor.execute(sql, ([local_ip]))
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
    global MASTER_OFFSET_TABLE
    global MASTER_LUX_TABLE

    colors = []
    offsets = []

    t = 0
    while t < 1440:
        offsets.append(0)
        offsets.append(0)
        offsets.append(0)
        MASTER_LUX_TABLE.append(0)
        MASTER_OFFSET_TABLE.append(offsets)
        offsets = []

        t +=1

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
    init_red_offset()
    init_green_offset()
    init_blue_offset()
    init_master_lux_table()

def init_red_offset():
    global MASTER_OFFSET_TABLE
    t = 0
    while t < 1440:
        if t >= 313 and t <= 323:
            MASTER_OFFSET_TABLE[t][0] = 0
        elif t >= 323 and t <= 325:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 161.5
        elif t >= 325 and t <= 329:
            MASTER_OFFSET_TABLE[t][0] = 1
        elif t >= 329 and t <= 331:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 163.5
        elif t >= 331 and t <= 333:
            MASTER_OFFSET_TABLE[t][0] = 2
        elif t >= 333 and t <= 335:
            MASTER_OFFSET_TABLE[t][0] = t - 331
        elif t >= 335 and t <= 337:
            MASTER_OFFSET_TABLE[t][0] = 4
        elif t >= 337 and t <= 339:
            MASTER_OFFSET_TABLE[t][0] = t - 333
        elif t >= 339 and t <= 343:
            MASTER_OFFSET_TABLE[t][0] = 6
        elif t >= 343 and t <= 345:
            MASTER_OFFSET_TABLE[t][0] = t - 337
        elif t >= 345 and t <= 347:
            MASTER_OFFSET_TABLE[t][0] = 8
        elif t >= 347 and t <= 349:
            MASTER_OFFSET_TABLE[t][0] = t - 339
        elif t >= 349 and t <= 351:
            MASTER_OFFSET_TABLE[t][0] = 10
        elif t >= 351 and t <= 353:
            MASTER_OFFSET_TABLE[t][0] = t - 341
        elif t >= 353 and t <= 355:
            MASTER_OFFSET_TABLE[t][0] = 12
        elif t >= 355 and t <= 357:
            MASTER_OFFSET_TABLE[t][0] = t - 343
        elif t >= 357 and t <= 359:
            MASTER_OFFSET_TABLE[t][0] = 14
        elif t >= 359 and t <= 363:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 165.5
        elif t >= 363 and t <= 365:
            MASTER_OFFSET_TABLE[t][0] = t - 347
        elif t >= 365 and t <= 367:
            MASTER_OFFSET_TABLE[t][0] = 18
        elif t >= 367 and t <= 369:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 165.5
        elif t >= 369 and t <= 371:
            MASTER_OFFSET_TABLE[t][0] = t - 350
        elif t >= 371 and t <= 373:
            MASTER_OFFSET_TABLE[t][0] = 21
        elif t >= 373 and t <= 375:
            MASTER_OFFSET_TABLE[t][0] = t - 352
        elif t >= 375 and t <= 379:
            MASTER_OFFSET_TABLE[t][0] = 23
        elif t >= 379 and t <= 381:
            MASTER_OFFSET_TABLE[t][0] = t - 356
        elif t >= 381 and t <= 383:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 165.5
        elif t >= 383 and t <= 385:
            MASTER_OFFSET_TABLE[t][0] = t - 357
        elif t >= 385 and t <= 387:
            MASTER_OFFSET_TABLE[t][0] = 28
        elif t >= 387 and t <= 389:
            MASTER_OFFSET_TABLE[t][0] = t - 359
        elif t >= 389 and t <= 391:
            MASTER_OFFSET_TABLE[t][0] = 30
        elif t >= 391 and t <= 393:
            MASTER_OFFSET_TABLE[t][0] = t - 361
        elif t >= 393 and t <= 395:
            MASTER_OFFSET_TABLE[t][0] = 32
        elif t >= 395 and t <= 397:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 165.5
        elif t >= 397 and t <= 399:
            MASTER_OFFSET_TABLE[t][0] = t - 364
        elif t >= 399 and t <= 401:
            MASTER_OFFSET_TABLE[t][0] = 35
        elif t >= 401 and t <= 403:
            MASTER_OFFSET_TABLE[t][0] = t - 366
        elif t >= 403 and t <= 405:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 164.5
        elif t >= 405 and t <= 407:
            MASTER_OFFSET_TABLE[t][0] = 1.5 * t - 569.5
        elif t >= 407 and t <= 411:
            MASTER_OFFSET_TABLE[t][0] = 41
        elif t >= 411 and t <= 413:
            MASTER_OFFSET_TABLE[t][0] = t - 370
        elif t >= 413 and t <= 415:
            MASTER_OFFSET_TABLE[t][0] = 2 * t - 783
        elif t >= 415 and t <= 419:
            MASTER_OFFSET_TABLE[t][0] = 47
        elif t >= 419 and t <= 420:
            MASTER_OFFSET_TABLE[t][0] = t - 372
        elif t >= 420 and t <= 540:
            MASTER_OFFSET_TABLE[t][0] = 0.308*t - 81.8
        elif t >= 540 and t <= 600:
            MASTER_OFFSET_TABLE[t][0] = 0.35 * t - 104
        elif t >= 600 and t <= 660:
            MASTER_OFFSET_TABLE[t][0] = 0.4 * t - 134
        elif t >= 660 and t <= 720:
            MASTER_OFFSET_TABLE[t][0] = 0.283*t -57
        elif t >= 720 and t <= 840:
            MASTER_OFFSET_TABLE[t][0] = -0.05*t +183
        elif t >= 840 and t <= 900:
            MASTER_OFFSET_TABLE[t][0] = -0.0167*t+155
        elif t >= 900 and t <= 960:
            MASTER_OFFSET_TABLE[t][0] = 140
        elif t >= 960 and t <= 1020:
            MASTER_OFFSET_TABLE[t][0] = -0.033*t +172
        elif t >= 1020 and t <= 1080:
            MASTER_OFFSET_TABLE[t][0] = 138
        elif t >= 1080 and t <= 1140:
            MASTER_OFFSET_TABLE[t][0] = -0.1167*t +264
        elif t >= 1140 and t <= 1142:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2422
        elif t >= 1142 and t <= 1146:
            MASTER_OFFSET_TABLE[t][0] = -t * 1280
        elif t >= 1146 and t <= 1148:
            MASTER_OFFSET_TABLE[t][0] = 134
        elif t >= 1148 and t <= 1150:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 708
        elif t >= 1150 and t <= 1152:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2433
        elif t >= 1152 and t <= 1154:
            MASTER_OFFSET_TABLE[t][0] = 129
        elif t >= 1154 and t <= 1156:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2437
        elif t >= 1156 and t <= 1158:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 703
        elif t >= 1158 and t <= 1160:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2440
        elif t >= 1160 and t <= 1164:
            MASTER_OFFSET_TABLE[t][0] = 120
        elif t >= 1164 and t <= 1166:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3030
        elif t >= 1166 and t <= 1168:
            MASTER_OFFSET_TABLE[t][0] = 115
        elif t >= 1168 and t <= 1170:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2451
        elif t >= 1170 and t <= 1172:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 696
        elif t >= 1172 and t <= 1174:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2454
        elif t >= 1174 and t <= 1176:
            MASTER_OFFSET_TABLE[t][0] = 106
        elif t >= 1176 and t <= 1178:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 694
        elif t >= 1178 and t <= 1180:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2461
        elif t >= 1180 and t <= 1182:
            MASTER_OFFSET_TABLE[t][0] = 101
        elif t >= 1182 and t <= 1184:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2465
        elif t >= 1184 and t <= 1186:
            MASTER_OFFSET_TABLE[t][0] = 97
        elif t >= 1186 and t <= 1188:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 690
        elif t >= 1188 and t <= 1190:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1878
        elif t >= 1190 and t <= 1192:
            MASTER_OFFSET_TABLE[t][0] = 93
        elif t >= 1192 and t <= 1194:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3073
        elif t >= 1194 and t <= 1198:
            MASTER_OFFSET_TABLE[t][0] = 88
        elif t >= 1198 and t <= 1200:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2484
        elif t >= 1200 and t <= 1202:
            MASTER_OFFSET_TABLE[t][0] = 84
        elif t >= 1202 and t <= 1204:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3089
        elif t >= 1204 and t <= 1206:
            MASTER_OFFSET_TABLE[t][0] = 79
        elif t >= 1206 and t <= 1208:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2491
        elif t >= 1208 and t <= 1210:
            MASTER_OFFSET_TABLE[t][0] = 75
        elif t >= 1210 and t <= 1212:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 680
        elif t >= 1212 and t <= 1214:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1892
        elif t >= 1214 and t <= 1216:
            MASTER_OFFSET_TABLE[t][0] = 71
        elif t >= 1216 and t <= 1218:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2503
        elif t >= 1218 and t <= 1222:
            MASTER_OFFSET_TABLE[t][0] = 67
        elif t >= 1222 and t <= 1224:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3122
        elif t >= 1224 and t <= 1226:
            MASTER_OFFSET_TABLE[t][0] = 62
        elif t >= 1226 and t <= 1228:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1901
        elif t >= 1228 and t <= 1232:
            MASTER_OFFSET_TABLE[t][0] = 59
        elif t >= 1232 and t <= 1234:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3139
        elif t >= 1234 and t <= 1236:
            MASTER_OFFSET_TABLE[t][0] = 54
        elif t >= 1236 and t <= 1238:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1908
        elif t >= 1238 and t <= 1240:
            MASTER_OFFSET_TABLE[t][0] = 51
        elif t >= 1240 and t <= 1242:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 671
        elif t >= 1242 and t <= 1244:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1913
        elif t >= 1244 and t <= 1246:
            MASTER_OFFSET_TABLE[t][0] = 47
        elif t >= 1246 and t <= 1248:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1916
        elif t >= 1248 and t <= 1250:
            MASTER_OFFSET_TABLE[t][0] = 44
        elif t >= 1250 and t <= 1252:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1919
        elif t >= 1252 and t <= 1254:
            MASTER_OFFSET_TABLE[t][0] = 41
        elif t >= 1254 and t <= 1256:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1922
        elif t >= 1256 and t <= 1258:
            MASTER_OFFSET_TABLE[t][0] = 38
        elif t >= 1258 and t <= 1260:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 667
        elif t >= 1260 and t <= 1262:
            MASTER_OFFSET_TABLE[t][0] = -t * 1297
        elif t >= 1262 and t <= 1264:
            MASTER_OFFSET_TABLE[t][0] = 35
        elif t >= 1264 and t <= 1266:
            MASTER_OFFSET_TABLE[t][0] = -t + 1299
        elif t >= 1266 and t <= 1268:
            MASTER_OFFSET_TABLE[t][0] = 33
        elif t >= 1268 and t <= 1270:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 667
        elif t >= 1270 and t <= 1272:
            MASTER_OFFSET_TABLE[t][0] = -t + 1302
        elif t >= 1272 and t <= 1274:
            MASTER_OFFSET_TABLE[t][0] = 30
        elif t >= 1274 and t <= 1276:
            MASTER_OFFSET_TABLE[t][0] = -t + 1304
        elif t >= 1276 and t <= 1278:
            MASTER_OFFSET_TABLE[t][0] = 28
        elif t >= 1278 and t <= 1282:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 667
        elif t >= 1282 and t <= 1284:
            MASTER_OFFSET_TABLE[t][0] = 26
        elif t >= 1284 and t <= 1286:
            MASTER_OFFSET_TABLE[t][0] = -t + 1310
        elif t >= 1286 and t <= 1290:
            MASTER_OFFSET_TABLE[t][0] = 24
        elif t >= 1290 and t <= 1292:
            MASTER_OFFSET_TABLE[t][0] = -t + 1314
        elif t >= 1292 and t <= 1296:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 668
        elif t >= 1296 and t <= 1298:
            MASTER_OFFSET_TABLE[t][0] = 20
        elif t >= 1298 and t <= 1302:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 669
        elif t >= 1302 and t <= 1304:
            MASTER_OFFSET_TABLE[t][0] = 18
        elif t >= 1304 and t <= 1306:
            MASTER_OFFSET_TABLE[t][0] = -t + 1322
        elif t >= 1306 and t <= 1308:
            MASTER_OFFSET_TABLE[t][0] = 16
        elif t >= 1308 and t <= 1310:
            MASTER_OFFSET_TABLE[t][0] = -t + 1324
        elif t >= 1310 and t <= 1314:
            MASTER_OFFSET_TABLE[t][0] = 14
        elif t >= 1314 and t <= 1316:
            MASTER_OFFSET_TABLE[t][0] = -t + 1328
        elif t >= 1316 and t <= 1318:
            MASTER_OFFSET_TABLE[t][0] = 12
        elif t >= 1318 and t <= 1320:
            MASTER_OFFSET_TABLE[t][0] = -t + 1330
        elif t >= 1320 and t <= 1324:
            MASTER_OFFSET_TABLE[t][0] = 10
        elif t >= 1324 and t <= 1326:
            MASTER_OFFSET_TABLE[t][0] = -t + 1334
        elif t >= 1326 and t <= 1328:
            MASTER_OFFSET_TABLE[t][0] = 8
        elif t >= 1328 and t <= 1330:
            MASTER_OFFSET_TABLE[t][0] = -t + 1336
        elif t >= 1330 and t <= 1334:
            MASTER_OFFSET_TABLE[t][0] = 6
        elif t >= 1334 and t <= 1340:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 673
        elif t >= 1340 and t <= 1342:
            MASTER_OFFSET_TABLE[t][0] = 3
        elif t >= 1342 and t <= 1344:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 674
        elif t >= 1344 and t <= 1348:
            MASTER_OFFSET_TABLE[t][0] = 2
        elif t >= 1348 and t <= 1350:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 676
        else:
            MASTER_OFFSET_TABLE[t][0] = 0
        t += 1


def init_green_offset():
    global MASTER_OFFSET_TABLE
    t = 0
    print "INIT GREEN"
    while t < 1440:
        if t >= 313 and t <= 315:
            MASTER_OFFSET_TABLE[t][1] = 0
        elif t >= 315 and t <= 323:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 157.5
        elif t >= 323 and t <= 325:
            MASTER_OFFSET_TABLE[t][1] = 4
        elif t >= 325 and t <= 327:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 158
        elif t >= 327 and t <= 329:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 322
        elif t >= 329 and t <= 331:
            MASTER_OFFSET_TABLE[t][1] = 7
        elif t >= 331 and t <= 333:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 158
        elif t >= 333 and t <= 335:
            MASTER_OFFSET_TABLE[t][1] = t - 325
        elif t >= 335 and t <= 337:
            MASTER_OFFSET_TABLE[t][1] = 10
        elif t >= 337 and t <= 341:
            MASTER_OFFSET_TABLE[t][1] = t - 327
        elif t >= 341 and t <= 343:
            MASTER_OFFSET_TABLE[t][1] = 14
        elif t >= 343 and t <= 345:
            MASTER_OFFSET_TABLE[t][1] = t - 329
        elif t >= 345 and t <= 351:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 156.5
        elif t >= 351 and t <= 353:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 507.5
        elif t >= 353 and t <= 357:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 154.5
        elif t >= 357 and t <= 359:
            MASTER_OFFSET_TABLE[t][1] = t - 33
        elif t >= 359 and t <= 361:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 512.5
        elif t >= 361 and t <= 363:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 151.5
        elif t >= 363 and t <= 365:
            MASTER_OFFSET_TABLE[t][1] = t - 333
        elif t >= 365 and t <= 367:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 150.5
        elif t >= 367 and t <= 369:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 701
        elif t >= 369 and t <= 371:
            MASTER_OFFSET_TABLE[t][1] = 37
        elif t >= 371 and t <= 375:
            MASTER_OFFSET_TABLE[t][1] = t - 334
        elif t >= 375 and t <= 377:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 521.5
        elif t >= 377 and t <= 379:
            MASTER_OFFSET_TABLE[t][1] = t - 333
        elif t >= 379 and t <= 381:
            MASTER_OFFSET_TABLE[t][1] = 46
        elif t >= 381 and t <= 383:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 525.5
        elif t >= 383 and t <= 385:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 717
        elif t >= 385 and t <= 389:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 139.5
        elif t >= 389 and t <= 391:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 528.5
        elif t >= 391 and t <= 393:
            MASTER_OFFSET_TABLE[t][1] = t - 333
        elif t >= 393 and t <= 395:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 529.5
        elif t >= 395 and t <= 397:
            MASTER_OFFSET_TABLE[t][1] = t - 332
        elif t >= 397 and t <= 399:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 729
        elif t >= 399 and t <= 401:
            MASTER_OFFSET_TABLE[t][1] = 69
        elif t >= 401 and t <= 403:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 733
        elif t >= 403 and t <= 405:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 128.5
        elif t >= 405 and t <= 407:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 533.5
        elif t >= 407 and t <= 409:
            MASTER_OFFSET_TABLE[t][1] = t - 330
        elif t >= 409 and t <= 411:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 125.5
        elif t >= 411 and t <= 413:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 536.5
        elif t >= 413 and t <= 415:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 743
        elif t >= 415 and t <= 417:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 120.5
        elif t >= 417 and t <= 419:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 537.5
        elif t >= 419 and t <= 420:
            MASTER_OFFSET_TABLE[t][1] = t - 328
        elif t >= 420 and t <= 720:
            MASTER_OFFSET_TABLE[t][1] = 0.097 * t + 51.4
        elif t >= 720 and t <= 780:
            MASTER_OFFSET_TABLE[t][1] = -0.3 *t +336
        elif t >= 780 and t <= 840:
            MASTER_OFFSET_TABLE[t][1] = -0.25 *t +297
        elif t >= 840 and t <= 900:
            MASTER_OFFSET_TABLE[t][1] = -0.233 * t + 283
        elif t >= 900 and t <= 960:
            MASTER_OFFSET_TABLE[t][1] = -0.25*t +298
        elif t >= 960 and t <= 1080:
            MASTER_OFFSET_TABLE[t][1] = -0.2 * t + 250
        elif t >= 1080 and t <= 1140:
            MASTER_OFFSET_TABLE[t][1] = -0.133 * t + 178
        elif t >= 1140 and t <= 1146:
            MASTER_OFFSET_TABLE[t][1] = 28
        elif t >= 1146 and t <= 1148:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 601
        elif t >= 1148 and t <= 1150:
            MASTER_OFFSET_TABLE[t][1] = 27
        elif t >= 1150 and t <= 1152:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 602
        elif t >= 1152 and t <= 1154:
            MASTER_OFFSET_TABLE[t][1] = 26
        elif t >= 1154 and t <= 1156:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 603
        elif t >= 1156 and t <= 1164:
            MASTER_OFFSET_TABLE[t][1] = 25
        elif t >= 1164 and t <= 1166:
            MASTER_OFFSET_TABLE[t][1] = -t * +1189
        elif t >= 1166 and t <= 1172:
            MASTER_OFFSET_TABLE[t][1] = 23
        elif t >= 1172 and t <= 1174:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 609
        elif t >= 1174 and t <= 1178:
            MASTER_OFFSET_TABLE[t][1] = 22
        elif t >= 1178 and t <= 1182:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 611
        elif t >= 1182 and t <= 1194:
            MASTER_OFFSET_TABLE[t][1] = 20
        elif t >= 1194 and t <= 1198:
            MASTER_OFFSET_TABLE[t][1] = 18
        elif t >= 1198 and t <= 1200:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 617
        elif t >= 1200 and t <= 1202:
            MASTER_OFFSET_TABLE[t][1] = 17
        elif t >= 1202 and t <= 1204:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 618
        elif t >= 1204 and t <= 1210:
            MASTER_OFFSET_TABLE[t][1] = 16
        elif t >= 1210 and t <= 1212:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 621
        elif t >= 1212 and t <= 1216:
            MASTER_OFFSET_TABLE[t][1] = 15
        elif t >= 1216 and t <= 1218:
            MASTER_OFFSET_TABLE[t][1] = -t + 1231
        elif t >= 1218 and t <= 1226:
            MASTER_OFFSET_TABLE[t][1] = 13
        elif t >= 1226 and t <= 1230:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 626
        elif t >= 1230 and t <= 1238:
            MASTER_OFFSET_TABLE[t][1] = 11
        elif t >= 1238 and t <= 1240:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 630
        elif t >= 1240 and t <= 1242:
            MASTER_OFFSET_TABLE[t][1] = 10
        elif t >= 1242 and t <= 1244:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 631
        elif t >= 1244 and t <= 1250:
            MASTER_OFFSET_TABLE[t][1] = 9
        elif t >= 1250 and t <= 1252:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 634
        elif t >= 1252 and t <= 1254:
            MASTER_OFFSET_TABLE[t][1] = 8
        elif t >= 1254 and t <= 1256:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 635
        elif t >= 1256 and t <= 1264:
            MASTER_OFFSET_TABLE[t][1] = 7
        elif t >= 1264 and t <= 1266:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 639
        elif t >= 1266 and t <= 1268:
            MASTER_OFFSET_TABLE[t][1] = 6
        elif t >= 1268 and t <= 1270:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 640
        elif t >= 1270 and t <= 1280:
            MASTER_OFFSET_TABLE[t][1] = 5
        elif t >= 1280 and t <= 1282:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 645
        elif t >= 1282 and t <= 1290:
            MASTER_OFFSET_TABLE[t][1] = 4
        elif t >= 1290 and t <= 1292:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 649
        elif t >= 1292 and t <= 1298:
            MASTER_OFFSET_TABLE[t][1] = 3
        elif t >= 1298 and t <= 1300:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 652
        elif t >= 1300 and t <= 1308:
            MASTER_OFFSET_TABLE[t][1] = 2
        elif t >= 1308 and t <= 1310:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 656
        elif t >= 1310 and t <= 1328:
            MASTER_OFFSET_TABLE[t][1] = 1
        elif t >= 1328 and t <= 1330:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 665
        else:
            if t == 1343:
                print "Yes"
            MASTER_OFFSET_TABLE[t][1] = 0

        t += 1

def init_blue_offset():
    global MASTER_OFFSET_TABLE
    t = 0
    while t < 1440:
        if t >= 313 and t <= 319:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 165.5
        elif t >= 319 and t <= 321:
            MASTER_OFFSET_TABLE[t][2] = t - 316
        elif t >= 321 and t <= 323:
            MASTER_OFFSET_TABLE[t][2] = 5
        elif t >= 323 and t <= 325:
            MASTER_OFFSET_TABLE[t][2] = t - 318
        elif t >= 325 and t <= 327:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 155.5
        elif t >= 327 and t <= 329:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 482.5
        elif t >= 329 and t <= 333:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 153.5
        elif t >= 333 and t <= 335:
            MASTER_OFFSET_TABLE[t][2] = t - 320
        elif t >= 335 and t <= 337:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 152.5
        elif t >= 337 and t <= 339:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 489.5
        elif t >= 339 and t <= 341:
            MASTER_OFFSET_TABLE[t][2] = t - 320
        elif t >= 341 and t <= 345:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 149.5
        elif t >= 345 and t <= 347:
            MASTER_OFFSET_TABLE[t][2] = t - 322
        elif t >= 347 and t <= 349:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 495.5
        elif t >= 349 and t <= 351:
            MASTER_OFFSET_TABLE[t][2] = t - 321
        elif t >= 351 and t <= 353:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 847.5
        elif t >= 353 and t <= 355:
            MASTER_OFFSET_TABLE[t][2] = 35
        elif t >= 355 and t <= 357:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 497.5
        elif t >= 357 and t <= 365:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 676
        elif t >= 365 and t <= 367:
            MASTER_OFFSET_TABLE[t][2] = 54
        elif t >= 367 and t <= 369:
            MASTER_OFFSET_TABLE[t][2] = 4 * t - 1414
        elif t >= 369 and t <= 371:
            MASTER_OFFSET_TABLE[t][2] = t - 122.5
        elif t >= 371 and t <= 373:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 493.5
        elif t >= 373 and t <= 375:
            MASTER_OFFSET_TABLE[t][2] = 3 * t - 1053
        elif t >= 375 and t <= 377:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 865.5
        elif t >= 377 and t <= 379:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 111.5
        elif t >= 379 and t <= 383:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 688
        elif t >= 383 and t <= 385:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 871.5
        elif t >= 385 and t <= 387:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 679
        elif t >= 387 and t <= 389:
            MASTER_OFFSET_TABLE[t][2] = t - 292
        elif t >= 389 and t <= 391:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 681
        elif t >= 391 and t <= 397:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 876.5
        elif t >= 397 and t <= 399:
            MASTER_OFFSET_TABLE[t][2] = 3 * t - 1075
        elif t >= 399 and t <= 401:
            MASTER_OFFSET_TABLE[t][2] = 122
        elif t >= 401 and t <= 403:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 680
        elif t >= 403 and t <= 405:
            MASTER_OFFSET_TABLE[t][2] = 3 * t - 1083
        elif t >= 405 and t <= 407:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 475.5
        elif t >= 407 and t <= 409:
            MASTER_OFFSET_TABLE[t][2] = 3.5 * t - 1289.5
        elif t >= 409 and t <= 411:
            MASTER_OFFSET_TABLE[t][2] = 142
        elif t >= 411 and t <= 413:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 680
        elif t >= 413 and t <= 415:
            MASTER_OFFSET_TABLE[t][2] = 3.5 * t - 1299.5
        elif t >= 415 and t <= 417:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 884.5
        elif t >= 417 and t <= 419:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 467.5
        elif t >= 419 and t <= 420:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 677
        elif t >= 420 and t <= 720:
            MASTER_OFFSET_TABLE[t][2] = 0.103 * t + 117.6
        elif t >= 720 and t <= 780:
            MASTER_OFFSET_TABLE[t][2] = -0.467 * t + 526
        elif t >= 780 and t <= 840:
            MASTER_OFFSET_TABLE[t][2] = -0.4*t+474
        elif t >= 840 and t <= 900:
            MASTER_OFFSET_TABLE[t][2] = -0.4167 * t + 488
        elif t >= 900 and t <= 960:
            MASTER_OFFSET_TABLE[t][2] = -0.4*t+473
        elif t >= 960 and t <= 1020:
            MASTER_OFFSET_TABLE[t][2] = -0.367 * t + 441
        elif t >= 1020 and t <= 1080:
            MASTER_OFFSET_TABLE[t][2] = -0.3*t+373
        elif t >= 1080 and t <= 1140:
            MASTER_OFFSET_TABLE[t][2] = -0.2 * t + 265
        elif t >= 1140 and t <= 1142:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 612
        elif t >= 1142 and t <= 1144:
            MASTER_OFFSET_TABLE[t][2] = 41
        elif t >= 1144 and t <= 1146:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 613
        elif t >= 1146 and t <= 1150:
            MASTER_OFFSET_TABLE[t][2] = 40
        elif t >= 1150 and t <= 1152:
            MASTER_OFFSET_TABLE[t][2] = -t + 1190
        elif t >= 1152 and t <= 1154:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 614
        elif t >= 1154 and t <= 1158:
            MASTER_OFFSET_TABLE[t][2] = 37
        elif t >= 1158 and t <= 1160:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 616
        elif t >= 1160 and t <= 1164:
            MASTER_OFFSET_TABLE[t][2] = 36
        elif t >= 1164 and t <= 1166:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 618
        elif t >= 1166 and t <= 1168:
            MASTER_OFFSET_TABLE[t][2] = -t + 1201
        elif t >= 1168 and t <= 1172:
            MASTER_OFFSET_TABLE[t][2] = 33
        elif t >= 1172 and t <= 1174:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 619
        elif t >= 1174 and t <= 1178:
            MASTER_OFFSET_TABLE[t][2] = 32
        elif t >= 1178 and t <= 1180:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 621
        elif t >= 1180 and t <= 1182:
            MASTER_OFFSET_TABLE[t][2] = -t + 1211
        elif t >= 1182 and t <= 1188:
            MASTER_OFFSET_TABLE[t][2] = 29
        elif t >= 1188 and t <= 1192:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 623
        elif t >= 1192 and t <= 1194:
            MASTER_OFFSET_TABLE[t][2] = 27
        elif t >= 1194 and t <= 1196:
            MASTER_OFFSET_TABLE[t][2] = -t + 1221
        elif t >= 1196 and t <= 1202:
            MASTER_OFFSET_TABLE[t][2] = 25
        elif t >= 1202 and t <= 1204:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 626
        elif t >= 1204 and t <= 1206:
            MASTER_OFFSET_TABLE[t][2] = 24
        elif t >= 1206 and t <= 1208:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 627
        elif t >= 1208 and t <= 1210:
            MASTER_OFFSET_TABLE[t][2] = 23
        elif t >= 1210 and t <= 1212:
            MASTER_OFFSET_TABLE[t][2] = -t + 1233
        elif t >= 1212 and t <= 1216:
            MASTER_OFFSET_TABLE[t][2] = 21
        elif t >= 1216 and t <= 1218:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 629
        elif t >= 1218 and t <= 1222:
            MASTER_OFFSET_TABLE[t][2] = 20
        elif t >= 1222 and t <= 1228:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 631
        elif t >= 1228 and t <= 1230:
            MASTER_OFFSET_TABLE[t][2] = 30
        elif t >= 1230 and t <= 1232:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 632
        elif t >= 1232 and t <= 1236:
            MASTER_OFFSET_TABLE[t][2] = 16
        elif t >= 1236 and t <= 1240:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 634
        elif t >= 1240 and t <= 1242:
            MASTER_OFFSET_TABLE[t][2] = 14
        elif t >= 1242 and t <= 1244:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 635
        elif t >= 1244 and t <= 1246:
            MASTER_OFFSET_TABLE[t][2] = 13
        elif t >= 1246 and t <= 1248:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 636
        elif t >= 1248 and t <= 1254:
            MASTER_OFFSET_TABLE[t][2] = 12
        elif t >= 1254 and t <= 1256:
            MASTER_OFFSET_TABLE[t][2] = -t + 1266
        elif t >= 1256 and t <= 1262:
            MASTER_OFFSET_TABLE[t][2] = 10
        elif t >= 1262 and t <= 1264:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 641
        elif t >= 1264 and t <= 1268:
            MASTER_OFFSET_TABLE[t][2] = 9
        elif t >= 1268 and t <= 1272:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 643
        elif t >= 1272 and t <= 1280:
            MASTER_OFFSET_TABLE[t][2] = 7
        elif t >= 1280 and t <= 1282:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 647
        elif t >= 1282 and t <= 1284:
            MASTER_OFFSET_TABLE[t][2] = 6
        elif t >= 1284 and t <= 1286:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 648
        elif t >= 1286 and t <= 1294:
            MASTER_OFFSET_TABLE[t][2] = 5
        elif t >= 1294 and t <= 1296:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 652
        elif t >= 1296 and t <= 1298:
            MASTER_OFFSET_TABLE[t][2] = 4
        elif t >= 1298 and t <= 1300:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 653
        elif t >= 1300 and t <= 1308:
            MASTER_OFFSET_TABLE[t][2] = 3
        elif t >= 1308 and t <= 1310:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 657
        elif t >= 1310 and t <= 1320:
            MASTER_OFFSET_TABLE[t][2] = 2
        elif t >= 1320 and t <= 1322:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 662
        elif t >= 1322 and t <= 1338:
            MASTER_OFFSET_TABLE[t][2] = 1
        elif t >= 1338 and t <= 1340:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 670
        else:
            MASTER_OFFSET_TABLE[t][2] = 0

        t += 1

def init_master_lux_table():
    global MASTER_LUX_TABLE
    t = 0

    while t < 1440:
        if t >= 313 and t <= 319:
            MASTER_LUX_TABLE[t] = 0
        elif t >= 319 and t <= 321:
            MASTER_LUX_TABLE[t] = 0.5 * t - 159.5
        elif t >= 321 and t <= 325:
            MASTER_LUX_TABLE[t] = 1
        elif t >= 325 and t <= 327:
            MASTER_LUX_TABLE[t] = 0.5 * t - 161.5
        elif t >= 327 and t <= 335:
            MASTER_LUX_TABLE[t] = 2
        elif t >= 335 and t <= 337:
            MASTER_LUX_TABLE[t] = 0.5 * t - 165.5
        elif t >= 337 and t <= 343:
            MASTER_LUX_TABLE[t] = 3
        elif t >= 343 and t <= 345:
            MASTER_LUX_TABLE[t] = 0.5 * t - 168.5
        elif t >= 345 and t <= 349:
            MASTER_LUX_TABLE[t] = 4
        elif t >= 349 and t <= 351:
            MASTER_LUX_TABLE[t] = 0.5 * t - 170.5
        elif t >= 351 and t <= 353:
            MASTER_LUX_TABLE[t] = 5
        elif t >= 353 and t <= 355:
            MASTER_LUX_TABLE[t] = 0.5 * t - 171.5
        elif t >= 355 and t <= 359:
            MASTER_LUX_TABLE[t] = 6
        elif t >= 359 and t <= 361:
            MASTER_LUX_TABLE[t] = 0.5 * t - 173.5
        elif t >= 361 and t <= 363:
            MASTER_LUX_TABLE[t] = 7
        elif t >= 363 and t <= 365:
            MASTER_LUX_TABLE[t] = 0.5 * t - 174.5
        elif t >= 365 and t <= 369:
            MASTER_LUX_TABLE[t] = 8
        elif t >= 369 and t <= 373:
            MASTER_LUX_TABLE[t] = 0.5 * t - 176.5
        elif t >= 373 and t <= 377:
            MASTER_LUX_TABLE[t] = 10
        elif t >= 377 and t <= 379:
            MASTER_LUX_TABLE[t] = 0.5 * t - 178.5
        elif t >= 379 and t <= 381:
            MASTER_LUX_TABLE[t] = 11
        elif t >= 381 and t <= 385:
            MASTER_LUX_TABLE[t] = 0.5 * t - 179.5
        elif t >= 385 and t <= 389:
            MASTER_LUX_TABLE[t] = 13
        elif t >= 389 and t <= 393:
            MASTER_LUX_TABLE[t] = 0.5 * t - 181.5
        elif t >= 393 and t <= 397:
            MASTER_LUX_TABLE[t] = 15
        elif t >= 397 and t <= 401:
            MASTER_LUX_TABLE[t] = 0.5 * t - 183.5
        elif t >= 401 and t <= 403:
            MASTER_LUX_TABLE[t] = 17
        elif t >= 403 and t <= 405:
            MASTER_LUX_TABLE[t] = 0.5 * t - 184.5
        elif t >= 405 and t <= 407:
            MASTER_LUX_TABLE[t] = 18
        elif t >= 407 and t <= 409:
            MASTER_LUX_TABLE[t] = 0.5 * t - 185.5
        elif t >= 409 and t <= 411:
            MASTER_LUX_TABLE[t] = 19
        elif t >= 411 and t <= 415:
            MASTER_LUX_TABLE[t] = 0.5 * t - 186.5
        elif t >= 415 and t <= 420:
            MASTER_LUX_TABLE[t] = 21
        elif t >= 420 and t <= 720:
            MASTER_LUX_TABLE[t] = 0.023 * t + 11.2
        elif t >= 720 and t <= 1140:
            MASTER_LUX_TABLE[t] = -0.0452 * t + 60.57
        elif t >= 1140 and t <= 1142:
            MASTER_LUX_TABLE[t] = -0.5 * t + 579
        elif t >= 1142 and t <= 1152:
            MASTER_LUX_TABLE[t] = 8
        elif t >= 1152 and t <= 1154:
            MASTER_LUX_TABLE[t] = -0.5 * t + 584
        elif t >= 1154 and t <= 1164:
            MASTER_LUX_TABLE[t] = 7
        elif t >= 1164 and t <= 1166:
            MASTER_LUX_TABLE[t] = -0.5 * t + 589
        elif t >= 1166 and t <= 1180:
            MASTER_LUX_TABLE[t] = 6
        elif t >= 1180 and t <= 1182:
            MASTER_LUX_TABLE[t] = -0.5 * t + 596
        elif t >= 1182 and t <= 1196:
            MASTER_LUX_TABLE[t] = 5
        elif t >= 1196 and t <= 1198:
            MASTER_LUX_TABLE[t] = -0.5 * t + 603
        elif t >= 1198 and t <= 1214:
            MASTER_LUX_TABLE[t] = 4
        elif t >= 1214 and t <= 1216:
            MASTER_LUX_TABLE[t] = -0.5 * t + 611
        elif t >= 1216 and t <= 1230:
            MASTER_LUX_TABLE[t] = 3
        elif t >= 1230 and t <= 1232:
            MASTER_LUX_TABLE[t] = -0.5 * t + 618
        elif t >= 1232 and t <= 1258:
            MASTER_LUX_TABLE[t] = 2
        elif t >= 1258 and t <= 1260:
            MASTER_LUX_TABLE[t] = -0.5 * t + 631
        elif t >= 1260 and t <= 1292:
            MASTER_LUX_TABLE[t] = 1
        elif t >= 1292 and t <= 1294:
            MASTER_LUX_TABLE[t] = -0.5 * t + 647
        else:
            MASTER_LUX_TABLE[t] = 0
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
    global MASTER_OFFSET_TABLE
    global USER_OFFSET_TABLE
    global USER_LUX_TABLE
    # Clear current values from USER_CIRCADIAN_TABLE
    """
    When calculating the USER_CIRCADIAN_TABLE again,
    the past values must be cleared but must have the
    same length as the MASTER_CIRCADIAN_TABLE. So, set
    the USER_CIRCADIAN_TABLE to the MASTER_CIRCADIAN_TABLE.
    """
    user_ct_mutex.acquire()
    try:
        USER_CIRCADIAN_TABLE = MASTER_CIRCADIAN_TABLE[:]
        USER_OFFSET_TABLE = MASTER_OFFSET_TABLE[:]
        USER_LUX_TABLE = MASTER_LUX_TABLE[:]
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
                USER_OFFSET_TABLE[count + wake_diff] = MASTER_OFFSET_TABLE[count]
                USER_LUX_TABLE[count + wake_diff] = MASTER_LUX_TABLE[count]
                count += 1
        elif wake_diff > 0:
            """
            User wakes up later than 7 AM
            """
            while count < 1440:
                if (count+wake_diff) == 1189:
                    print "USER[%s] = MASTER[%s]"%((count+wake_diff), count)
                if (count + wake_diff) > 1439:
                    """
                    For later indexes in the list, the values must wrap around
                    to earlier indexes. Therefore, take the MOD.
                    """
                    USER_CIRCADIAN_TABLE[(count + wake_diff) % 1440] = MASTER_CIRCADIAN_TABLE[count]
                    USER_OFFSET_TABLE[(count + wake_diff) % 1440] = MASTER_OFFSET_TABLE[count]
                    USER_LUX_TABLE[(count + wake_diff) % 1440] = MASTER_LUX_TABLE[count]
                else:
                    USER_CIRCADIAN_TABLE[count + wake_diff] = MASTER_CIRCADIAN_TABLE[count]
                    USER_OFFSET_TABLE[count + wake_diff] = MASTER_OFFSET_TABLE[count]
                    USER_LUX_TABLE[count + wake_diff] = MASTER_LUX_TABLE[count]
                count += 1
        else:
            """
            User wakes up at 7 AM
            """
            USER_CIRCADIAN_TABLE = MASTER_CIRCADIAN_TABLE[:]
            USER_OFFSET_TABLE = MASTER_OFFSET_TABLE[:]
            USER_LUX_TABLE = MASTER_LUX_TABLE[:]
        """
        If the user changed the wake up time, then the change_par_Event is set.
        Set the the finalize_change_Event and wait 1 sec. This allows for thread
        synchronization.
        """
        change_par_mutex.acquire()
        try:
            change_par_status = change_par_Event.isSet()
        finally:
            change_par_mutex.release()
        if change_par_status:
            finalize_par_mutex.acquire()
            try:
                finalize_change_Event.set()
            finally:
                finalize_par_mutex.release()
            time.sleep(1)
    finally:
        user_ct_mutex.release()


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
    first_time_Event = threading.Event()
    change_reset_Event = threading.Event()
    wake_change_Event = threading.Event()
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
    # try:
    #     print "Starting PIR thread..."
    #     pir_thread = threading.Thread(name='pir_thread', target=PIR_sensor, args=(
    #         pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
    #         keyboard_Event,))
    #     pir_thread.start()
    #     THREADS.append(pir_thread)
    # except:
    #     print "Error: unable to start pir thread"
    try:
        print "Starting RGB thread..."
        rgb_thread = threading.Thread(name='rgb_thread', target=RGB_sensor, args=(
            pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
            keyboard_Event, first_time_Event,change_reset_Event,finalize_change_Event,))
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
            finalize_change_Event,first_time_Event,change_reset_Event,))
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

    """
    Get initial sleep mode state
    """
    trigger = 0
    trigger2 = 1
    sleep_mutex.acquire()
    try:
        sleep_mode = sleep_mode_Event.isSet()
    finally:
        sleep_mutex.release()
        
    if sleep_mode:
        print "setting trigger"
        trigger = 1
        trigger2 = 0
        
    while True and keyboard_Event.isSet():
        if timer == 60 or trigger:
            print "turning off lights"
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
            current_minute = time.localtime()[3] * 60 + time.localtime()[4]
            user_ct_mutex.acquire()
            try:
                user_ct = USER_CIRCADIAN_TABLE[:]
            finally:
                user_ct_mutex.release()
            pir_cmd = str(user_ct[current_minute][0]) + "|" + str(
                user_ct[current_minute][1]) + "|" + str(user_ct[current_minute][2]) + "|"
            sensor_to_lighting_cli_sock.send(pir_cmd)

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

                cursor.execute(sql, ([local_ip]))
                db.commit()
            except:
                db.rollback()

            sensor_to_lighting_cli_sock.close()
            trigger = 0
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
                    cursor.execute(sql, ([local_ip]))
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
                        cursor.execute(sql, ([local_ip]))
                        db.commit()
                    except:
                        db.rollback()
                except:
                    db.rollback()
                trigger2 = 1

            """
            Reset the timer upon motion.
            """
            timer = 0

        else:
            
            if timer <= 60 and trigger2:
                """
                Increase the motion timer
                """
                timer +=1
                print "sleep timer: ", timer
                time.sleep(1)


def RGB_sensor(pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
               keyboard_Event, first_time_Event,change_reset_Event,finalize_change_Event):
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

    global lighting_ip
    global COLOR_THRESHOLD
    global OLD_RED
    global OLD_GREEN
    global OLD_BLUE
    global USER_OFFSET_TABLE
    global USER_CIRCADIAN_TABLE
    global MASTER_LUX_TABLE
    global primary_red_comp
    global primary_red_degraded
    global primary_green_comp
    global primary_green_degraded
    global primary_blue_comp
    global primary_blue_degraded

    print "RGB thread created successfully."

    """
    Establish DB connection
    """
    print "Establishing Database connection in RGB thread...\n"
    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
    print "Database connection in RGB thread established.\n"
    cursor = db.cursor()

    """
    Set the rgb_DB_Event and wait for other DB connections to finish
    """
    rgb_DB_Event.set()
    #pir_DB_Event.wait()
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
    local_ip = get_ip()
    """
    Variables for degradation detection
    """
    #primary_red_deg = False
    secondary_red_degraded = False
    secondary_red_on = False

    #primary_green_deg = False
    secondary_green_degraded = False
    secondary_green_on = False

    #primary_blue_deg = False
    secondary_blue_degraded = False
    secondary_blue_on = False
    r_handled = False
    g_handled = False
    b_handled = False
    red_sec_val = 0
    red_prim_val = 0

    r_service = False
    g_service = False
    b_service = False

    red_deg_handled = False
    red_diff = 0
    green_diff = 0
    blue_diff = 0
    current_minute = time.localtime()[3] * 60 + time.localtime()[4]

    user_ct_mutex.acquire()
    try:
        prev_primary_red = USER_CIRCADIAN_TABLE[current_minute][0]
        prev_primary_green = USER_CIRCADIAN_TABLE[current_minute][1]
        prev_primary_blue = USER_CIRCADIAN_TABLE[current_minute][2]
    finally:
        user_ct_mutex.release()
    prev_secondary_red = 0
    prev_secondary_green = 0
    prev_secondary_blue = 0
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
            change_reset_Event_mutex.acquire()
            try:
                change_reset = change_reset_Event.isSet()
            finally:
                change_reset_Event_mutex.release()
            if change_par:
                """
                If the change_par_Event was set then
                wait for the changes to finalize
                """
                print "Here waiting to finalize2"
                finalize_change_Event.wait()
                time.sleep(1)
                print "Done with finalize2"
                finalize_par_mutex.acquire()
                try:
                    finalize_change_Event.clear()
                finally:
                    finalize_par_mutex.release()
            if sleep_mode == False and change_par == False and change_reset == False:
                if change_par:
                    """
                    If the change_par_Event was set then
                    wait for the changes to finalize
                    """
                    print "Here waiting to finalize3"
                    finalize_change_Event.wait()
                    time.sleep(1)
                    print "Done with finalize3"
                    finalize_par_mutex.acquire()
                    try:
                        finalize_change_Event.clear()
                    finally:
                        finalize_par_mutex.release()
                """
                Get current minute
                """
                current_minute = time.localtime()[3] * 60 + time.localtime()[4]
                print "current min:",current_minute
                comp_list = ["N", "N", "N", "N", "N", "N", "N", "N", "N", "N", "N", "N"]
                comp_cmd = ""
                """
                If the sleep_mode_Event and the change_par_Event
                are NOT set, then read from the RGB sensor
                """
                first_time_Event.wait()
                time.sleep(1)
                data = bus.read_i2c_block_data(0x29, 0)
                """
                The sensor readings must be converted to an RGB brightness.
                Initially the value is a 16-bit number so to get it an R, G,
                or B value, divide it by 256. Then to get the RGB brightness
                divide by 255 and multiply by 100.
                """
                red = float(data[3] << 8 | data[2])

                green = float(data[5] << 8 | data[4])

                blue = float(data[7] << 8 | data[6])

                #print "Raw R: %s, G: %s, B: %s" % (red, green, blue)
                """
                Get the current circadian table value for red
                """
                user_ct_mutex.acquire()
                try:
                    circadian_red = USER_CIRCADIAN_TABLE[current_minute][0]
                    circadian_green = USER_CIRCADIAN_TABLE[current_minute][1]
                    circadian_blue = USER_CIRCADIAN_TABLE[current_minute][2]
                    offset_red = USER_OFFSET_TABLE[current_minute][0]
                    offset_green = USER_OFFSET_TABLE[current_minute][1]
                    offset_blue = USER_OFFSET_TABLE[current_minute][2]
                finally:
                    user_ct_mutex.release()
                #print "offset_green:", offset_blue
                x = (float(circadian_red) / 100) * 147
                y = (float(circadian_green) / 100) * 121
                print "y: ",y
                z = (float(circadian_blue) / 100) * 189

                red2 = (float(red + (x - offset_red)) / 147 ) * 100
                green2 = (float(green + (y - offset_green)) / 121) * 100
                #print "green2:",green2
                blue2 = (float(blue + (z - offset_blue)) / 189) * 100

                primary_comp_mutex.acquire()
                try:
                    primary_red_comp = red2
                    primary_green_comp = green2
                    primary_blue_comp = blue2
                finally:
                    primary_comp_mutex.release()

                dist_in_meters = 8 * 0.3048
                try:
                    lux = ((red2 + green2 + blue2) / (circadian_red+circadian_green+circadian_blue)) * USER_LUX_TABLE[current_minute]
                    lumens = calc_Illuminance(lux, dist_in_meters, 120)
                except:
                    lux = 0
                    lumens = 0
                """
                Store Lumens into the database
                """
                print " RED should be: %s and is reading %s" % (circadian_red, red2)
                print " GREEN should be: %s and is reading %s" % (circadian_green, green2)
                print " BLUE should be: %s and is reading %s" % (circadian_blue, blue2)
                print "Lux: %s ; lumens: %s " % (lux, lumens)
                color_threshold_mutex.acquire()
                try:
                    color_threshold = COLOR_THRESHOLD
                finally:
                    color_threshold_mutex.release()
                if (red2 < (circadian_red - (circadian_red*color_threshold))) and r_service == False:
                    print "r_serv", r_service
                    primary_deg_mutex.acquire()
                    try:
                        primary_red_deg = primary_red_degraded
                    finally:
                        primary_deg_mutex.release()

                    if primary_red_deg:
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
                                    cursor.execute(sql, ([local_ip]))
                                    db.commit()
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
                                        cursor.execute(sql, ([local_ip]))
                                        db.commit()
                                    except:
                                        db.rollback()
                                except:
                                    db.rollback()
                                r_service = True
                            else:
                                """
                                Secondaries have degraded
                                """
                                print "Secondaries degraded"
                                secondary_red_comp = circadian_red - red2
                                primary_comp_mutex.acquire()
                                try:
                                    primary_red_comp = red2
                                    p_red_comp = circadian_red + (circadian_red - red2)
                                    comp_list[0] = str(prev_primary_red)
                                    comp_list[1] = str(p_red_comp)
                                    prev_primary_red = p_red_comp
                                finally:
                                    primary_comp_mutex.release()
                                comp_list[2] = str(prev_secondary_red)
                                comp_list[3] = str(2 * secondary_red_comp)
                                prev_secondary_red = 2 * secondary_red_comp

                                secondary_red_degraded = True
                        else:
                            """
                            Turn secondaries on
                            """
                            print "Turning secondaries on"

                            """
                            Send command to turn secondaries for red on
                            """
                            secondary_red_comp = circadian_red - red2
                            primary_comp_mutex.acquire()
                            try:
                                primary_red_comp = red2
                                p_red_comp = circadian_red + (circadian_red - red2)
                                comp_list[0] = str(prev_primary_red)
                                print "comp0",comp_list[0]
                                comp_list[1] = str(p_red_comp)
                                prev_primary_red = p_red_comp
                            finally:
                                primary_comp_mutex.release()
                            comp_list[2] = str(prev_secondary_red)
                            comp_list[3] = str(secondary_red_comp)
                            prev_secondary_red = secondary_red_comp

                            secondary_red_on = True
                            red_deg_handled = False
                    else:
                        """
                        Primary has now degraded
                        """
                        print "Primary Degraded"

                        sql = """UPDATE sensor_status SET red_degraded = 1 WHERE ip = %s"""
                        try:
                            cursor.execute(sql, ([local_ip]))
                            db.commit()
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
                                cursor.execute(sql, ([local_ip]))
                                db.commit()
                            except:
                                db.rollback()
                        except:
                            db.rollback()

                        primary_comp_mutex.acquire()
                        try:
                            primary_red_comp = red2
                            p_red_comp = circadian_red + (circadian_red - red2)
                            red_diff = circadian_red - red2
                            comp_list[0] = str(prev_primary_red)
                            comp_list[1] = str(p_red_comp)
                            prev_primary_red = p_red_comp
                        finally:
                            primary_comp_mutex.release()

                        primary_deg_mutex.acquire()
                        try:
                            primary_red_degraded = True
                        finally:
                            primary_deg_mutex.release()

                if red2 > (circadian_red + (circadian_red*color_threshold)):
                    if secondary_red_on:
                        """
                        Secondaries have degraded
                        """
                        print "Secondaries degraded"
                        secondary_red_comp = red_diff
                        primary_comp_mutex.acquire()
                        try:
                            primary_red_comp = circadian_red
                            p_red_comp = circadian_red + (red_diff)
                            comp_list[0] = str(prev_primary_red)
                            comp_list[1] = str(circadian_red)
                            prev_primary_red = circadian_red
                        finally:
                            primary_comp_mutex.release()
                        comp_list[2] = str(prev_secondary_red)
                        comp_list[3] = str(0)
                        prev_secondary_red = 0
                    else:
                        primary_comp_mutex.acquire()
                        try:
                            primary_red_comp = circadian_red
                            p_red_comp = circadian_red + (red_diff)
                            comp_list[0] = str(prev_primary_red)
                            comp_list[1] = str(circadian_red)
                            prev_primary_red = circadian_red
                        finally:
                            primary_comp_mutex.release()


                if (green2 < (circadian_green - (circadian_green*color_threshold))) and g_service == False:
                    print "g_serv", g_service
                    primary_deg_mutex.acquire()
                    try:
                        primary_green_deg = primary_green_degraded
                    finally:
                        primary_deg_mutex.release()
                    if primary_green_deg:
                        """
                        Primaries are degraded
                        """
                        if secondary_green_on:
                            if secondary_green_degraded:
                                """
                                Update DB to service lighting sub
                                """
                                sql = """UPDATE sensor_status SET service = 1 WHERE ip = %s"""
                                try:
                                    cursor.execute(sql, ([local_ip]))
                                    db.commit()
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
                                        cursor.execute(sql, ([local_ip]))
                                        db.commit()
                                    except:
                                        db.rollback()
                                except:
                                    db.rollback()
                                g_service = True
                            else:
                                """
                                Secondaries have degraded
                                """
                                print "Secondaries degraded"
                                secondary_green_comp = circadian_green - green2
                                primary_comp_mutex.acquire()
                                try:
                                    primary_green_comp = green2
                                    p_green_comp = circadian_green + (circadian_green - green2)
                                    comp_list[4] = str(prev_primary_green)
                                    comp_list[5] = str(p_green_comp)
                                    prev_primary_green = p_green_comp
                                finally:
                                    primary_comp_mutex.release()
                                comp_list[6] = str(prev_secondary_green)
                                comp_list[7] = str(2 * secondary_green_comp)
                                prev_secondary_green = 2 * secondary_green_comp

                                secondary_green_degraded = True
                        else:
                            """
                            Turn secondaries on
                            """
                            print "Turning secondaries on"

                            """
                            Send command to turn secondaries for red on
                            """
                            secondary_green_comp = circadian_green - green2

                            primary_comp_mutex.acquire()
                            try:
                                primary_green_comp = green2
                                p_green_comp = circadian_green + (circadian_green - green2)
                                comp_list[4] = str(prev_primary_green)
                                comp_list[5] = str(p_green_comp)
                                prev_primary_green = p_green_comp
                            finally:
                                primary_comp_mutex.release()
                            comp_list[6] = str(prev_secondary_green)
                            comp_list[7] = str(secondary_green_comp)
                            prev_secondary_green = secondary_green_comp


                            secondary_green_on = True
                    else:
                        """
                        Primary has now degraded
                        """
                        print "Primary Degraded"

                        sql = """UPDATE sensor_status SET green_degraded = 1 WHERE ip = %s"""
                        try:
                            cursor.execute(sql, ([local_ip]))
                            db.commit()
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
                                cursor.execute(sql, ([local_ip]))
                                db.commit()
                            except:
                                db.rollback()
                        except:
                            db.rollback()

                        primary_comp_mutex.acquire()
                        try:
                            green_diff = circadian_green - green2
                            primary_green_comp = green2
                            p_green_comp = circadian_green + (circadian_green - green2)
                            comp_list[4] = str(prev_primary_green)
                            comp_list[5] = str(p_green_comp)
                            prev_primary_green = p_green_comp
                        finally:
                            primary_comp_mutex.release()
                        
                        primary_deg_mutex.acquire()
                        try:
                            primary_green_degraded = True
                        finally:
                            primary_deg_mutex.release()
                if green2 > (circadian_green + (circadian_green * color_threshold)):
                    if secondary_green_on:
                        """
                        Secondaries have degraded
                        """
                        print "Secondaries degraded"
                        secondary_green_comp = red_diff
                        primary_comp_mutex.acquire()
                        try:
                            primary_green_comp = circadian_green
                            p_green_comp = circadian_green + (green_diff)
                            comp_list[4] = str(prev_primary_green)
                            comp_list[5] = str(circadian_green)
                            prev_primary_green = circadian_green
                        finally:
                            primary_comp_mutex.release()
                        comp_list[6] = str(prev_secondary_green)
                        comp_list[7] = str(0)
                        prev_secondary_green = 0
                    else:
                        primary_comp_mutex.acquire()
                        try:
                            primary_green_comp = circadian_green
                            p_green_comp = circadian_green + (green_diff)
                            comp_list[4] = str(prev_primary_green)
                            comp_list[5] = str(circadian_green)
                            prev_primary_green = circadian_green
                        finally:
                            primary_comp_mutex.release()

                if (blue2 < (circadian_blue - (circadian_blue*color_threshold))) and b_service == False:
                    print "b_serv",b_service
                    primary_deg_mutex.acquire()
                    try:
                        primary_blue_deg = primary_blue_degraded
                    finally:
                        primary_deg_mutex.release()
                    if primary_blue_deg:
                        """
                        Primaries are degraded
                        """
                        if secondary_blue_on:
                            if secondary_blue_degraded:
                                """
                                Update DB to service lighting sub
                                """
                                sql = """UPDATE sensor_status SET service = 1 WHERE ip = %s"""
                                try:
                                    cursor.execute(sql, ([local_ip]))
                                    db.commit()
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
                                        cursor.execute(sql, ([local_ip]))
                                        db.commit()
                                    except:
                                        db.rollback()
                                except:
                                    db.rollback()
                                b_service = True
                            else:
                                """
                                Secondaries have degraded
                                """
                                print "Secondaries degraded"
                                secondary_blue_comp = circadian_blue - blue2
                                primary_comp_mutex.acquire()
                                try:
                                    primary_blue_comp = blue2
                                    p_blue_comp = circadian_blue + (circadian_blue - blue2)
                                    comp_list[8] = str(prev_primary_blue)
                                    comp_list[9] = str(p_blue_comp)
                                    prev_primary_blue = p_blue_comp
                                finally:
                                    primary_comp_mutex.release()
                                comp_list[10] = str(prev_secondary_blue)
                                comp_list[11] = str(2 * secondary_blue_comp)
                                prev_secondary_blue = 2 * secondary_blue_comp

                                secondary_blue_degraded = True
                        else:
                            """
                            Turn secondaries on
                            """
                            print "Turning secondaries on"

                            """
                            Send command to turn secondaries for red on
                            """
                            secondary_blue_comp = circadian_blue - blue2
                            primary_comp_mutex.acquire()
                            try:
                                primary_blue_comp = blue2
                                p_blue_comp = circadian_blue + (circadian_blue - blue2)
                                comp_list[8] = str(prev_primary_blue)
                                comp_list[9] = str(p_blue_comp)
                                prev_primary_blue = p_blue_comp
                            finally:
                                primary_comp_mutex.release()
                            comp_list[10] = str(prev_secondary_blue)
                            comp_list[11] = str(secondary_blue_comp)
                            prev_secondary_blue = secondary_blue_comp


                            secondary_blue_on = True
                    else:
                        """
                        Primary has now degraded
                        """
                        print "Primary Degraded"

                        sql = """UPDATE sensor_status SET blue_degraded = 1 WHERE ip = %s"""
                        try:
                            cursor.execute(sql, ([local_ip]))
                            db.commit()
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
                                cursor.execute(sql, ([local_ip]))
                                db.commit()
                            except:
                                db.rollback()
                        except:
                            db.rollback()

                        primary_comp_mutex.acquire()
                        try:
                            primary_blue_comp = blue2
                            p_blue_comp = circadian_blue + (circadian_blue - blue2)
                            blue_diff = circadian_blue - blue2
                            comp_list[8] = str(prev_primary_blue)
                            comp_list[9] = str(p_blue_comp)
                            prev_primary_blue = p_blue_comp
                        finally:
                            primary_comp_mutex.release()

                        primary_deg_mutex.acquire()
                        try:
                            primary_blue_degraded = True
                        finally:
                            primary_deg_mutex.release()
                if blue2 > (circadian_blue + (circadian_blue * color_threshold)):
                    if secondary_blue_on:
                        """
                        Secondaries have degraded
                        """
                        print "Secondaries degraded"
                        secondary_blue_comp = red_diff
                        primary_comp_mutex.acquire()
                        try:
                            primary_blue_comp = circadian_blue
                            p_blue_comp = circadian_blue + (blue_diff)
                            comp_list[8] = str(prev_primary_blue)
                            comp_list[9] = str(circadian_blue)
                            prev_primary_blue = circadian_blue
                        finally:
                            primary_comp_mutex.release()
                        comp_list[10] = str(prev_secondary_blue)
                        comp_list[11] = str(0)
                        prev_secondary_blue = 0
                    else:
                        primary_comp_mutex.acquire()
                        try:
                            primary_blue_comp = circadian_blue
                            p_blue_comp = circadian_blue + (blue_diff)
                            comp_list[8] = str(prev_primary_blue)
                            comp_list[9] = str(circadian_blue)
                            prev_primary_blue = circadian_blue
                        finally:
                            primary_comp_mutex.release()
                for key in comp_list:
                    if key != "N":
                        comp_cmd += comp_list[0]
                        comp_cmd += "|"
                        comp_cmd += comp_list[1]
                        comp_cmd += "|"
                        comp_cmd += comp_list[2]
                        comp_cmd += "|"
                        comp_cmd += comp_list[3]
                        comp_cmd += "|"
                        comp_cmd += comp_list[4]
                        comp_cmd += "|"
                        comp_cmd += comp_list[5]
                        comp_cmd += "|"
                        comp_cmd += comp_list[6]
                        comp_cmd += "|"
                        comp_cmd += comp_list[7]
                        comp_cmd += "|"
                        comp_cmd += comp_list[8]
                        comp_cmd += "|"
                        comp_cmd += comp_list[9]
                        comp_cmd += "|"
                        comp_cmd += comp_list[10]
                        comp_cmd += "|"
                        comp_cmd += comp_list[11]
                        comp_cmd += "|"
                        print "comp_cmd:",comp_cmd
                        """
                        Create client socket connection to the lighting sub
                        """
                        comp_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        comp_cli_sock_host = lighting_ip.strip()
                        comp_cli_sock_port = 12356

                        """
                        Send the command string on the socket
                        """
                        comp_cli_sock.connect((comp_cli_sock_host, comp_cli_sock_port))
                        if change_par == False:
                            comp_cli_sock.send(comp_cmd)
                        comp_cli_sock.close()
                        time.sleep(1)
                        comp_cmd = ""
                        comp_list = []
                        break

                if red2 < (OLD_RED - (OLD_RED * 0.05)) or red > (OLD_RED + (OLD_RED * 0.05)):
                    """
                    If the red color reading is 5% less or greater than the previous
                    value, then update the database
                    """
                    sql = """UPDATE sensor_status SET red = %s WHERE ip = %s"""
                    try:
                        if red2 > 100:
                            red2 = circadian_red
                            sql = """UPDATE sensor_status SET red = %s WHERE ip = %s"""
                            cursor.execute(sql, ([red2, local_ip]))
                            db.commit()
                        else:
                            cursor.execute(sql, ([red2, local_ip]))
                            db.commit()
                        OLD_RED = red2
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
                            if red2 > 100:
                                red2 = circadian_red
                                sql = """UPDATE sensor_status SET red = %s WHERE ip = %s"""
                                cursor.execute(sql, ([red2, local_ip]))
                                db.commit()
                            else:
                                cursor.execute(sql, ([red2, local_ip]))
                                db.commit()
                            OLD_RED = red2
                        except:
                            db.rollback()
                    except:
                        db.rollback()

                if green2 < (OLD_GREEN - (OLD_GREEN * 0.05)) or green > (OLD_GREEN + (OLD_GREEN * 0.05)):
                    """
                    If the green color reading is 5% less or greater than the previous
                    value, then update the database
                    """
                    sql = """UPDATE sensor_status SET green = %s WHERE ip = %s"""
                    try:
                        if green2 > 100:
                            green2 = circadian_green
                            sql = """UPDATE sensor_status SET green = %s WHERE ip = %s"""
                            cursor.execute(sql, ([green2, local_ip]))
                            db.commit()
                        else:
                            cursor.execute(sql, ([green2, local_ip]))
                            db.commit()
                        OLD_GREEN = green2
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
                            if green2 > 100:
                                green2 = circadian_green
                                sql = """UPDATE sensor_status SET green = %s WHERE ip = %s"""
                                cursor.execute(sql, ([green2, local_ip]))
                                db.commit()
                            else:
                                cursor.execute(sql, ([green2, local_ip]))
                                db.commit()
                            OLD_GREEN = green2
                        except:
                            db.rollback()
                    except:
                        db.rollback()
                if blue2 < (OLD_BLUE - (OLD_BLUE * 0.05)) or blue > (OLD_BLUE + (OLD_BLUE * 0.05)):
                    """
                    If the blue color readings are 5% less or greater than previous reading, then
                    update the DB
                    """
                    sql = """UPDATE sensor_status SET blue = %s WHERE ip = %s"""
                    try:
                        if blue2 > 100:
                            blue2 = circadian_blue
                            sql = """UPDATE sensor_status SET blue = %s WHERE ip = %s"""
                            cursor.execute(sql, ([blue2, local_ip]))
                            db.commit()
                        else:
                            cursor.execute(sql, ([blue2, local_ip]))
                            db.commit()
                        OLD_BLUE = blue2
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
                            if blue2 > 100:
                                blue2 = circadian_blue
                                sql = """UPDATE sensor_status SET blue = %s WHERE ip = %s"""
                                cursor.execute(sql, ([blue2, local_ip]))
                                db.commit()
                            else:
                                cursor.execute(sql, ([blue2, local_ip]))
                                db.commit()
                            OLD_BLUE = blue2
                        except:
                            db.rollback()
                    except:
                        db.rollback()

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
    Connect to DB
    """
    print "Establishing Database connection in USR thread..."
    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
    print "Database connection established in USR thread."
    """
    Set the usr_DB_event and wait for other connections to finish
    """
    usr_DB_Event.set()
    #pir_DB_Event.wait()
    rgb_DB_Event.wait()
    cmd_DB_Event.wait()
    local_ip = get_ip()
    cursor = db.cursor()
    """
    Set the distance to be 8 in the DB
    """
    sql = """UPDATE sensor_status SET distance = 8 WHERE ip = %s"""
    try:
        cursor.execute(sql, ([local_ip]))
        db.commit()
    except (AttributeError, MySQLdb.OperationalError):
        print "Trying to reconnect to database in USR thread..."
        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
        print "Database connection re-established in USR thread."
        cursor = db.cursor()
        try:
            cursor.execute(sql, ([distInFt, local_ip]))
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
    # TRIG = 36
    # ECHO = 38
    TRIG = 7
    ECHO = 11
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

        if distInFt >= 7:
            """
            Print distance if >= 8. This will be removed.
            """
            #print "Distance:", distance, "cm"  # Print distance with 0.5 cm calibration; other website has "distance - 0.5","cm"
            #print "Distance:", distInFt, "ft"  # Print distance in ft
        else:
            """
            If distance is out of range then update DB
            """
            #print "Out Of Range",distInFt  # display out of range
            sql = """UPDATE sensor_status SET distance = -1 WHERE ip = %s"""
            try:
                cursor.execute(sql, ([local_ip]))
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
                    cursor.execute(sql, ([distInFt, local_ip]))
                    db.commit()
                except:
                    db.rollback()
            except:
                db.rollback()


def send_circadian_values(pir_DB_Event, rgb_DB_Event, usr_DB_Event, sleep_mode_Event, change_par_Event, cmd_DB_Event,
                          keyboard_Event, finalize_change_Event, first_time_Event, change_reset_Event):
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
    #global CURRENT_MINUTE
    global lighting_ip
    global primary_red_comp
    global primary_red_degraded
    global primary_green_comp
    global primary_green_degraded
    global primary_blue_comp
    global primary_blue_degraded
    global CHANGE_THRES
    global CHANGE_WAKE
    """
    Wait for DB connections to finish
    """
    usr_DB_Event.wait()
    #pir_DB_Event.wait()
    rgb_DB_Event.wait()
    cmd_DB_Event.wait()
    #local_ip = get_ip()
    count = 0
    first_time = 1

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
        if change_par:
            change_reset_Event_mutex.acquire()
            try:
                change_reset_Event.set()
            finally:
                change_reset_Event_mutex.release()
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
            primary_deg_mutex.acquire()
            try:
                primary_red_deg = primary_red_degraded
                primary_green_deg = primary_green_degraded
                primary_blue_deg = primary_blue_degraded
            finally:
                primary_deg_mutex.release()
            if primary_red_deg or primary_green_deg or primary_blue_deg:
                primary_comp_mutex.acquire()
                try:
                    red_comp = primary_red_comp
                    green_comp = primary_green_comp
                    blue_comp = primary_blue_comp
                finally:
                    primary_comp_mutex.release()
            circadian_cmd = ""
            user_ct_mutex.acquire()
            try:
                print "CHANGE_WAKE:",CHANGE_WAKE
                if primary_red_deg and not CHANGE_WAKE:
                    print "sending boosted red", red_comp, 2 * (USER_CIRCADIAN_TABLE[current_minute][0]) - red_comp
                    circadian_cmd = str(2 * (USER_CIRCADIAN_TABLE[current_minute][0]) - red_comp) + "|"
                else:
                    print "sending normal red"
                    circadian_cmd = str(USER_CIRCADIAN_TABLE[current_minute][0]) + "|"

                if primary_green_deg and not CHANGE_WAKE:
                    print "sending boosted green", green_comp,2 * (USER_CIRCADIAN_TABLE[current_minute][1])-green_comp
                    circadian_cmd += str(2 * (USER_CIRCADIAN_TABLE[current_minute][1])-green_comp) + "|"
                else:
                    print "sending normal green"
                    circadian_cmd += str(USER_CIRCADIAN_TABLE[current_minute][1]) + "|"

                if primary_blue_deg and not CHANGE_WAKE:
                    print "sending boosted blue", blue_comp,2 * (USER_CIRCADIAN_TABLE[current_minute][2])-blue_comp
                    circadian_cmd += str(2 * (USER_CIRCADIAN_TABLE[current_minute][2])-blue_comp) + "|"
                else:
                    print "sending normal blue"
                    circadian_cmd += str(USER_CIRCADIAN_TABLE[current_minute][2]) + "|"


                circadian_cmd += (str(PREV_COLORS[0]) + "|" + str(PREV_COLORS[1]) + "|" + str(PREV_COLORS[2]) + "|")

            finally:
                user_ct_mutex.release()

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
            user_ct_mutex.acquire()
            try:

                if primary_red_deg and not CHANGE_WAKE:
                    PREV_COLORS[0] = 2 * (USER_CIRCADIAN_TABLE[current_minute][0]) - red_comp
                else:
                    PREV_COLORS[0] = USER_CIRCADIAN_TABLE[current_minute][0]

                if primary_green_deg and not CHANGE_WAKE:
                    PREV_COLORS[1] = 2 * (USER_CIRCADIAN_TABLE[current_minute][1]) - green_comp
                else:
                    PREV_COLORS[1] = USER_CIRCADIAN_TABLE[current_minute][1]

                if primary_blue_deg and not CHANGE_WAKE:
                    PREV_COLORS[2] = 2 * (USER_CIRCADIAN_TABLE[current_minute][2]) - blue_comp
                else:
                    PREV_COLORS[2] = USER_CIRCADIAN_TABLE[current_minute][2]
                if CHANGE_WAKE:
                    CHANGE_WAKE = not CHANGE_WAKE

            finally:
                user_ct_mutex.release()
            circadian_cli_sock.close()
            if first_time:
                time.sleep(2)
                print "It's my first time..."
                first_time_Event.set()
                first_time = not first_time
            change_reset_Event_mutex.acquire()
            try:
                change_reset = change_reset_Event.isSet()
            finally:
                change_reset_Event_mutex.release()
            if change_reset:
                time.sleep(1)
                change_reset_Event.clear()
            """
            Count for 1 minute
            """
            while count < 60:

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
                        print "Here waiting to finalize"
                        finalize_change_Event.wait()
                        print "Done with finalize"
                        finalize_par_mutex.acquire()
                        try:
                            finalize_change_Event.clear()
                            finalize_change_Event.set()
                        finally:
                            finalize_par_mutex.release()
                    print "CHANGE_WAKE",CHANGE_WAKE
                    if CHANGE_WAKE or sleep_mode:
                        # if CHANGE_WAKE:
                        #     CHANGE_WAKE = False
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
    global USER_CIRCADIAN_TABLE
    global CHANGE_WAKE
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
    #pir_DB_Event.wait()
    rgb_DB_Event.wait()
    local_ip = get_ip()
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
                current_minute = time.localtime()[3] * 60 + time.localtime()[4]
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
                    delete_sock_port = 12355  # * Reserve a port for your service.
                    try:
                        delete_sock.connect((delete_sock_host, delete_sock_port))
                    except:
                        print "\nCould not connect to lighting subsystem\n"
                    user_ct_mutex.acquire()
                    try:
                        delete_cmd = str(USER_CIRCADIAN_TABLE[current_minute][0])+"|"+str(USER_CIRCADIAN_TABLE[current_minute][1])+"|"+str(USER_CIRCADIAN_TABLE[current_minute][2])+"|"
                    finally:
                        user_ct_mutex.release()
                    delete_sock.send(delete_cmd)
                    delete_sock.close()

                    sql = """DELETE FROM sensor_ip WHERE ip = %s"""
                    try:
                        cursor.execute(sql, ([local_ip]))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, ([local_ip]))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()

                    sql = """DELETE FROM sensor_settings WHERE ip = %s"""
                    try:
                        cursor.execute(sql, ([local_ip]))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, ([local_ip]))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()

                    sql = """DELETE FROM sensor_status WHERE ip = %s"""
                    try:
                        cursor.execute(sql, ([local_ip]))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, ([local_ip]))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()
                    sql = """DELETE FROM sensor_light_pairs WHERE sensor_ip = %s"""
                    try:
                        cursor.execute(sql, ([local_ip]))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing Database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, ([local_ip]))
                            db.commit()
                        except:
                            db.rollback()
                    except:
                        db.rollback()
                    sql = """DELETE FROM lighting_ip WHERE ip = %s"""
                    try:
                        cursor.execute(sql, ([lighting_ip]))
                        db.commit()
                    except (AttributeError, MySQLdb.OperationalError):
                        print "Re-establishing database connection in main thread..."
                        db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                             db="ilcs")
                        print "Database connection re-established in main thread."
                        cursor = db.cursor()
                        try:
                            cursor.execute(sql, ([lighting_ip]))
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
                    change_par_mutex.acquire()
                    try:
                        change_par_Event.set()
                    finally:
                        change_par_mutex.release()
                    time.sleep(2)
                    if cmd[0] != 'N':
                        CHANGE_WAKE = True
                        """
                        If the wake time field is NOT 'N' then recalculate
                        the USER_CIRCADIAN_TABLE
                        """
                        WAKE_UP_TIME = int(cmd[0])
                        user_ct_mutex.acquire()
                        try:
                            PREV_COLORS[0] = USER_CIRCADIAN_TABLE[current_minute][0]
                            PREV_COLORS[1] = USER_CIRCADIAN_TABLE[current_minute][1]
                            PREV_COLORS[2] = USER_CIRCADIAN_TABLE[current_minute][2]
                        finally:
                            user_ct_mutex.release()
                        calc_user_circadian_table(change_par_Event, finalize_change_Event)
                    if cmd[1] != 'N':
                        """
                        If the color threshold field is NOT 'N' then
                        set the new COLOR_THRESHOLD value
                        """
                        color_threshold_mutex.acquire()
                        try:
                            COLOR_THRESHOLD = float(cmd[1]) /100
                        finally:
                            color_threshold_mutex.release()

                        finalize_par_mutex.acquire()
                        try:
                            finalize_change_Event.set()
                        finally:
                            finalize_par_mutex.release()
                        time.sleep(1)
                    # if cmd[2] != 'N':
                    #     """
                    #     If the light threshold field is NOT 'N' then
                    #     set the new LIGHT_THRESHOLD value
                    #     """
                    #     LIGHT_THRESHOLD = float(cmd[2]) / 100
                    """
                    Clear the change_par_Event
                    """
                    change_par_mutex.acquire()
                    try:
                        change_par_Event.clear()
                    finally:
                        change_par_mutex.release()

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

def calc_Illuminance(lux, distance, angle):
    lum = lux * toArea(angle, distance)
    return lum

def toArea(angleInDeg, distance):
    return toSr(toRad(angleInDeg)) * distance * distance

def toSr(rad):
    return 2.0 * math.pi * (1.0 - math.cos(rad / 2.0))

def toRad(deg):
    return deg * (2.0 * math.pi / 360.0)
"""
This is where the Script starts. The boot_up()
function is always the first thing that will
be called when the sensor_sub.py script is
ran.
"""
boot_up()
