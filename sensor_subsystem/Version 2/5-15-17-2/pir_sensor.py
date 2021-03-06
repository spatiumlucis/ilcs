import time
import os
import signal
import subprocess
import circadian
import MySQLdb
import socket
import datetime
import RPi.GPIO as GPIO

"""
Global Variables
"""
PIR_DB_CONNECTED = False
RGB_DB_CONNECTED = False
USR_DB_CONNECTED = False
SEND_CIRCADIAN_DB_CONNECTED = False
WAIT_FOR_CMD_DB_CONNECTED = False
SLEEP_MODE = False
WAKE_UP_TIME = 0
COLOR_THRESHOLD = 0
MASTER_CIRCADIAN_TABLE = circadian.init_circadian_table()
USER_CIRCADIAN_TABLE = []
USER_OFFSET_TABLE = []
USER_LUX_TABLE = []
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
PIR_PIN = 12
GPIO.setup(PIR_PIN, GPIO.IN)

"""
Signal Handlers
"""
def catch_other_signals(signum, stack):
    pass

def handle_change_cmd(signum, stack):
    global db
    global cursor
    global WAKE_UP_TIME
    global COLOR_THRESHOLD
    time.sleep(3)

def handle_send_compensation(signum, stack):
    time.sleep(3)

def handle_send_circadian(signum, stack):
    time.sleep(3)

def handle_wait_for_cmd_dB_connect(signum, stack):
    global WAIT_FOR_CMD_DB_CONNECTED
    WAIT_FOR_CMD_DB_CONNECTED = True

def handle_rgb_dB_connect(signum, stack):
    global RGB_DB_CONNECTED
    RGB_DB_CONNECTED = True

def handle_usr_dB_connect(signum, stack):
    global USR_DB_CONNECTED
    USR_DB_CONNECTED = True

def handle_send_circadian_dB_connect(signum, stack):
    global SEND_CIRCADIAN_DB_CONNECTED
    SEND_CIRCADIAN_DB_CONNECTED = True

def handle_motion_detection(PIR_PIN):
    global begin_timer
    global SLEEP_MODE
    print "MOTION DETECTED!!"
    if SLEEP_MODE:
        SLEEP_MODE = False
        pid_list = circadian.get_pids()
        for pid in pid_list:
            os.kill(pid, 5)
    begin_timer = time.time()

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
GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=handle_motion_detection)

"""
Establish DB connection
"""
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
cursor = db.cursor()

"""
Alert other Python scripts that the PIR has connected
"""
pid_list = circadian.get_pids()
for pid in pid_list:
    os.kill(pid, 10)

"""
Wait for other sensor scripts to connect to the DB
"""
while not WAIT_FOR_CMD_DB_CONNECTED or not RGB_DB_CONNECTED or not USR_DB_CONNECTED or not SEND_CIRCADIAN_DB_CONNECTED:
    time.sleep(1)

"""
Begin reading from the motion sensor
"""
begin_timer = time.time()
while True:
    current_timer = time.time()
    time_diff = int(current_timer - begin_timer)
    if time_diff >= 60 and not SLEEP_MODE:
        SLEEP_MODE = True
        pid_list = circadian.get_pids()
        for pid in pid_list:
            os.kill(pid, 4)
        begin_timer = time.time()