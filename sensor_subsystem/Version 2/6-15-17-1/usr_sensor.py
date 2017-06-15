import time
import os
import signal
import subprocess
import circadian
import MySQLdb
import socket
import datetime
import math
import RPi.GPIO as GPIO

"""
Global variables
"""
PIR_DB_CONNECTED = False
RGB_DB_CONNECTED = False
USR_DB_CONNECTED = False
SEND_CIRCADIAN_DB_CONNECTED = False
WAIT_FOR_CMD_DB_CONNECTED = False
SLEEP_MODE = False
DISTANCE_DEG = False
local_ip = circadian.get_ip()
GPIO.setwarnings(False)

"""
Signal Handlers
"""
def catch_other_signals(signum, stack):
    pass

def handle_wait_for_cmd_dB_connect(signum, stack):
    global WAIT_FOR_CMD_DB_CONNECTED
    WAIT_FOR_CMD_DB_CONNECTED = True

def handle_pir_dB_connect(signum, stack):
    global PIR_DB_CONNECTED
    PIR_DB_CONNECTED = True

def handle_rgb_dB_connect(signum, stack):
    global RGB_DB_CONNECTED
    RGB_DB_CONNECTED = True

def handle_send_circadian_dB_connect(signum, stack):
    global SEND_CIRCADIAN_DB_CONNECTED
    SEND_CIRCADIAN_DB_CONNECTED = True

"""
Non-Signal Handler Functions
"""
##

"""
Signal declarations (software interrupts)
SIGQUIT: kill -3 is for when user changes parameter
SIGILL: kill -4 is for when the system entered sleep mode
SIGTRAP: kill -5 is for when the system exits sleep mode
SIGIOT: kill -6 is for when the rgb_sensor.py sends compensation values
SIGEMT: kill -7 is for when the send_circadian_values.py sends brightness values every minute
kill -8 is wait_for_cmd dB connection
kill -10 is pir_sensor dB connection
kill -11 is rgb_sensor dB connection
kill -12 is usr_sensor dB connection
kill -15 is send_circadian dB connection
"""

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

"""
Establish DB connection
"""
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
cursor = db.cursor()
print "USR DB connection established"

"""
Set the 8 feet in DB
"""
sql = """UPDATE sensor_status SET distance = 8 WHERE ip = %s"""
circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

"""
Alert other Python scripts that the PIR has connected
"""
pid_list = circadian.get_pids()
for pid in pid_list:
    os.kill(pid, 12)

"""
Wait for other sensor scripts to connect to the DB
"""
while not WAIT_FOR_CMD_DB_CONNECTED or not RGB_DB_CONNECTED or not PIR_DB_CONNECTED or not SEND_CIRCADIAN_DB_CONNECTED:
    time.sleep(1)

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
num_of_less = 0
temp = 0

while True:
    print "reading from USR..."
    if temp == 5:
        temp = 0
        num_of_less = 0
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

    if distInFt < 7:
        num_of_less += 1
    elif distInFt >= 8:
        num_of_less = 0
    if num_of_less >= 5 and not DISTANCE_DEG:
        DISTANCE_DEG = True
        """
        Set the 8 feet degraded in DB
        """
        sql = """UPDATE sensor_status SET distance = -1 WHERE ip = %s"""
        circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

        message = "Sensor Subsystem (" + local_ip + ") has fallen below 8 Feet."
        circadian.create_log(cursor, db, message, "None")
    temp += 1
    time.sleep(3)