"""
######################################################################################################
Project: Sensor Subsystem

Authors: Team Spatium Lucis

Version: v2.0

Target Device: Raspberry Pi 3

Files: circadian.py, pir_sensor.py, rgb_sensor.py, send_circadian_values.py, usr_sensor.py,
wait_for_cmd.py, start.py, stop.py, compensate.txt, config.txt, sensor_data.txt

Last edited: June 15, 2017

######################################################################################################

(I) start.py:
This is the init script for the sensor subsystem. Usage:

$ python start.py

*********DO NOT USE sudo python!!!

(II) circadian.py:
This file serves as a custom Python module that houses functions that are common to all the various sensor subsystem
files.

    (a) Module imports:
        (1) import subprocess
        (2) import socket
        (3) import MySQLdb
        (4) import time
        (5) import math
        (6) import datetime

    (b) Functions:
        (1) def init_circadian_table():
        This function creates base MASTER_CIRCADIAN_TABLE. Returns a list of lists containing RGB brightnesses
        percentages for each minute of the day for 7 AM wake up and 11 PM sleep. Example index (not relative to the
        actual table):
        MASTER_CIRCADIAN_TABLE[420] == [ 30, 40, 50 ]. Therefore, MASTER_CIRCADIAN_TABLE[420][0] == 30.

        (2) def init_offset_table():
        This function creates the base MASTER_OFFSET_TABLE. Returns a list of lists containing rgb sensor offset
        values for each minute of the day. These are needed because the rgb sensor cannot properly pick up the values
        of the lights so they are offset with these. This function calls init_red_offset(), init_green_offset(),
        and init_blue_offset() to generate the values for the MASTER_OFFSET_TABLE. This table is for 7 AM to 11 PM
        cycle. Example index (not relative to the actual table ):
        MASTER_OFFSET_TABLE[420] == [ 120, 130, 140 ]. Therefore, MASTER_OFFSET_TABLE[420][0] == 120.

        (3) def init_red_offset(MASTER_OFFSET_TABLE):
        This function generates the red offset values for the MASTER_OFFSET_TABLE.

        (4) def init_green_offset(MASTER_OFFSET_TABLE):
        This function generates the green offset values for the MASTER_OFFSET_TABLE.

        (5) def init_blue_offset(MASTER_OFFSET_TABLE):
        This function generates the blue offset values for the MASTER_OFFSET_TABLE.

        (6) def init_master_lux_table():
        This function creates the lux offset values for the MASTER_LUX_TABLE. Returns a list containing lux offset
        values. These offset values are needed for the rgb sensor to calculate lux values because it doesn't naturally
        do so. The values are for every minute of the day base on 7 AM/11 PM cycle. Example index (not relative to
        the actual table):
        MASTER_LUX_TABLE[420] == 50.

        (7) def calc_user_tables(WAKE_UP_TIME, MASTER_CIRCADIAN_TABLE, MASTER_OFFSET_TABLE, MASTER_LUX_TABLE):
        This function takes the user WAKE_UP_TIME, MASTER_CIRCADIAN_TABLE, MASTER_OFFSET_TABLE,
        and the MASTER_LUX_TABLE then shifts these tables based on the WAKE_UP_TIME. Returns a tuple with the newly
        shifted tables.

        (8) def calc_Illuminance(lux, distance, angle):
        This function takes a lux value, distance (in meters), and a viewing angle (in degrees). Returns the lumens
        value. Uses toArea(), toSr(), and toRad() in calculation. Source:

        (9) def get_pids():
        Returns a list with all of the process ids (pids) of the following scripts:
        pir_sensor.py, rgb_sensor.py, usr_sensor.py, wait_for_cmd.py, and send_circadian_values.py

        (10) def get_system_time():
        Returns the system time in mintues.

        (11) def get_ip():
        Returns the local IP address of the Raspberry Pi.

        (12) def create_log(cursor, db, message, user_name):
        This function takes a database cursor object, database object, a message string, and username string. Stores
        the message into the database using execute_dB_query().

        (13) def execute_dB_query(cursor, db, sql, sql_args):
        This function takes a database cursor object, database object, an sql string, and a tuple of lists that
        contain the sql query arguments and executes the query.

        (14) def get_circadian_cmd(USER_CIRCADIAN_TABLE, PREV_PRIMARY_COLORS, PREV_SECONDARY_COLORS, IS_PRIMARY_DEG,
                      IS_SEC_ON, IS_SEC_DEG):
        This function takes the USER_CIRCADIAN_TABLE, PREV_PRIMARY_COLORS, PREV_SECONDARY_COLORS, IS_PRIMARY_DEG,
        IS_SEC_ON, and IS_SEC_DEG lists as input. Returns a tuple containing the circadian string, list for new
        previous primary colors, and list for new previous secondary colors.

(III) pir_sensor.py:
This file is for the usage of the PIR motion sensor.

    (a) Module imports:
        (1) import time
        (2) import os
        (3) import signal
        (4) import subprocess
        (5) import circadian
        (6) import MySQLdb
        (7) import socket
        (8) import datetime
        (9) import RPi.GPIO as GPIO

    (b) Signal handling:
        These are the signal handler setups. When a kill -<number> is issued to the LINUX system, if it is one of the
        following numbers then it will be handled differently in the Python script. Theses are basically software
        interrupts.
        signal.signal(3, handle_change_cmd)
        signal.signal(4, catch_other_signals)
        signal.signal(5, catch_other_signals)
        signal.signal(6, handle_send_compensation)
        signal.signal(7, handle_send_circadian)
        signal.signal(8, handle_wait_for_cmd_dB_connect)
        signal.signal(10, catch_other_signals)
        signal.signal(11, handle_rgb_dB_connect)
        signal.signal(12, handle_usr_dB_connect)
        signal.signal(15, handle_send_circadian_dB_connect)

        You will notice that throughout the scripts that some signal handler functions don't do anything and that may
        seem redundant. This was done on purpose for (1) to catch the signal and (2) to keep the signal handling
        consistent among the scripts.

    (c) Functions:
        (1) def catch_other_signals(signum, stack):
        Does nothing but catch signals. Used with signal handling.

        (2) def handle_change_cmd(signum, stack):
        Catches kill -3. Simply performs time.sleep(3).

        (3) def handle_send_compensation(signum, stack):
        Catches kill -6. Simply performs time.sleep(3).

        (4) def handle_send_circadian(signum, stack):
        Catches kill -7. Simply performs time.sleep(3).

        (5) def handle_wait_for_cmd_dB_connect(signum, stack):
        Catches kill -8. Alerts the pir_sensor.py script that the wait_for_cmd.py script has connected to the database.

        (6) def handle_rgb_dB_connect(signum, stack):
        Catches kill -11. Alerts the pir_sensor.py script that the rgb_sensor.py script has connected to the database.

        (7) def handle_usr_dB_connect(signum, stack):
        Catches kill -12. Alerts the pir_sensor.py script that the usr_sensor.py script has connected to the database.

        (8) def handle_send_circadian_dB_connect(signum, stack):
        Catches kill -15. Alerts the pir_sensor.py script that the send_circadian_values.py script has connected to
        the database.

        (9) def handle_motion_detection(PIR_PIN):
        This function is the hardware interrupt handler for the PIR sensor.

(IV) rgb_sensor.py:
This file is for the usage of the RGB sensor.

    (a) Module imports;
        (1) import time
        (2) import os
        (3) import signal
        (4) import subprocess
        (5) import circadian
        (6) import MySQLdb
        (7) import socket
        (8) import datetime
        (9) import smbus

    (b) Signal handling: (See section in pir_sensor.py for more info on signal handling.)
        signal.signal(3, handle_change_cmd)
        signal.signal(4, handle_sleep_mode)
        signal.signal(5, handle_wake_up)
        signal.signal(6, catch_other_signals)
        signal.signal(7, handle_send_circadian)
        signal.signal(8, handle_wait_for_cmd_dB_connect)
        signal.signal(10, handle_pir_dB_connect)
        signal.signal(11, catch_other_signals)
        signal.signal(12, handle_usr_dB_connect)
        signal.signal(15, handle_send_circadian_dB_connect)

    (c) Functions:
        (1) def catch_other_signals(signum, stack):
        Does nothing but catch signals. Used with signal handling.

        (2) def handle_change_cmd(signum, stack):
        Catches kill -3. Handles when the user changes a parameter on the website.

        (3) def handle_sleep_mode(signum, stack):
        Catches kill -4. Updates database with sensor reading of 0 when system goes into sleep mode.

        (4) def handle_wake_up(signum, stack):
        Catches kill -5. Used in waking from sleep mode.

        (5) def handle_send_circadian(signum, stack):
        Catches kill -7. Simply does time.sleep(3).

        (6) def handle_wait_for_cmd_dB_connect(signum, stack):
        Catches kill -8. Tells rgb_sensor.py that wait_for_cmd.py connected to the database.

        (7) def handle_pir_dB_connect(signum, stack):
        Catches kill -10. Tells rgb_sensor.py that pir_sensor.py connected to the database.

        (8) def handle_usr_dB_connect(signum, stack):
        Catches kill -12. Tells rgb_sensor.py that usr_sensor.py connected to the database.

        (9) def handle_send_circadian_dB_connect(signum, stack):
        Catches kill -15. Tells rgb_sensor.py that sends_circadian_values.py connected to the database.

(V) send_circadian_values.py:
This file is responsible for sending circadian values to the lighting subsystem. This sends compensation values as well.

    (a) Module imports:
        (1) import time
        (2) import os
        (3) import signal
        (4) import subprocess
        (5) import circadian
        (6) import MySQLdb
        (7) import socket
        (8) import datetime

    (b) Signal handling: (See section in pir_sensor.py for more info on signal handling.)
        signal.signal(3, handle_change_cmd)
        signal.signal(4, handle_sleep_mode)
        signal.signal(5, handle_wake_up)
        signal.signal(6, handle_send_compensation)
        signal.signal(7, catch_other_signals)
        signal.signal(8, handle_wait_for_cmd_dB_connect)
        signal.signal(10, handle_pir_dB_connect)
        signal.signal(11, handle_rgb_dB_connect)
        signal.signal(12, handle_usr_dB_connect)
        signal.signal(15, catch_other_signals)

    (c) Functions:
        (1) def catch_other_signals(signum, stack):
        Catches signals. Does nothing else.

        (2) def handle_change_cmd(signum, stack):
        Catches kill -3. Used for when a user changes something from the website.

        (3) def handle_sleep_mode(signum, stack):
        Catches kill -4. Sends values to the lighting subsystem to put it to sleep.

        (4) def handle_wake_up(signum, stack):
        Catches kill -5. Makes the script send a value to wake the lights up.

        (5) def handle_send_compensation(signum, stack):
        Catches kill -6. Sends compensation values to the lighting subsystem.

        (6) def handle_wait_for_cmd_dB_connect(signum, stack):
        Catches kill -8. Alerts the send_circadian_values.py that wait_for_cmd.py connected to the DB.

        (7) def handle_pir_dB_connect(signum, stack):
        Catches kill -10. Alerts the send_circadian_values.py that pir_sensor.py connected to the DB.

        (8) def handle_rgb_dB_connect(signum, stack):
        Catches kill -11. Alerts the send_circadian_values.py that rgb_sensor.py connected to the DB.

        (9) def handle_usr_dB_connect(signum, stack):
        Catches kill -12. Alerts the send_circadian_values.py that usr_sensor.py connected to the DB.

(VI) usr_sensor.py:
This file is responsible for the usage of the ultra sonic range sensor.

    (a) Module imports:
        (1)  import time
        (2)  import os
        (3)  import signal
        (4)  import subprocess
        (5)  import circadian
        (6)  import MySQLdb
        (7)  import socket
        (8)  import datetime
        (9)  import math
        (10) import RPi.GPIO as GPIO

    (b) Signal handling: (See section in pir_sensor.py for more info on signal handling.)
        signal.signal(3, catch_other_signals)
        signal.signal(4, catch_other_signals)
        signal.signal(5, catch_other_signals)
        signal.signal(6, catch_other_signals)
        signal.signal(7, catch_other_signals)
        signal.signal(8, handle_wait_for_cmd_dB_connect)
        signal.signal(10, handle_pir_dB_connect)
        signal.signal(11, handle_rgb_dB_connect)
        signal.signal(12, catch_other_signals)
        signal.signal(15, handle_send_circadian_dB_connect)

    (c) Functions:
        (1) def catch_other_signals(signum, stack):
        Catches signals. Does nothing else.

        (2) def handle_wait_for_cmd_dB_connect(signum, stack):
        Catches kill -8. Tells usr_sensor.py that wait_for_cmd.py connected to the DB.

        (3) def handle_pir_dB_connect(signum, stack):
        Catches kill -10. Tells usr_sensor.py that pir_sensor.py connected to the DB.

        (4) def handle_rgb_dB_connect(signum, stack):
        Catches kill -11. Tells usr_sensor.py that rgb_sensor.py connected to the DB.

        (5) def handle_send_circadian_dB_connect(signum, stack):
        Catches kill -15. Tells usr_sensor.py that send_circadian_values.py connected to the DB.

(VII) wait_for_cmd.py:
This file is responsible for receiving commands from the website.

    (a) Module imports:
        (1) import time
        (2) import os
        (3) import signal
        (4) import subprocess
        (5) import circadian
        (6) import MySQLdb
        (7) import socket
        (8) import datetime

    (b) Signal handling: (See section in pir_sensor.py for more info on signal handling.)
        signal.signal(3, catch_other_signals)
        signal.signal(4, handle_sleep_mode)
        signal.signal(5, handle_wake_up)
        signal.signal(6, catch_other_signals)
        signal.signal(7, catch_other_signals)
        signal.signal(8, catch_other_signals)
        signal.signal(10, handle_pir_dB_connect)
        signal.signal(11, handle_rgb_dB_connect)
        signal.signal(12, handle_usr_dB_connect)
        signal.signal(15, handle_send_circadian_dB_connect)

    (c) Functions:
        (1) def catch_other_signals(signum, stack):
        Catches signals and does nothing else.

        (2) def handle_pir_dB_connect(signum, stack):
        Catches kill -10. Tells wait_for_cmd.py that pir_sensor.py connected to the DB.

        (3) def handle_rgb_dB_connect(signum, stack):
        Catches kill -11. Tells wait_for_cmd.py that rgb_sensor.py connected to the DB.

        (4) def handle_usr_dB_connect(signum, stack):
        Catches kill -12. Tells wait_for_cmd.py that usr_sensor.py connected to the DB.

        (5) def handle_send_circadian_dB_connect(signum, stack):
        Catches kill -15. Tells wait_for_cmd.py that send_circadian_values.py connected to the DB.

        (6) def handle_sleep_mode(signum, stack):
        Catches kill -4. Tells the script that the system entered sleep mode.

        (7) def handle_wake_up(signum, stack):
        Catches kill -5. Tells the script that the system exited sleep mode.

        (8) def boot_up():
        Initial database check to pair with the lighting subsystem and retrieve previous sensor subsystem settings if
        any.

(VIII) stop.py
This script is used for killing the sensor subsystem. Usage:

$ python stop.py

****DO NOT USE sudo python!!!

(IX) pause.py
This script is used for suspending the sensor and lighting subsystems. Usage:

$ python pause.py

****DO NOT USE sudo python!!!

(X) compensate.txt:
Holds the compensation data.

(XI) sensor_data.txt:
Holds the sensor readings. Uses in compensation.

(XII) config.txt:
Holds the values that were sent by the user. Needed because DB was misbehaving.
"""