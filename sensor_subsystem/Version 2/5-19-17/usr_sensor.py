import time
import os
import signal
import subprocess
import circadian
import MySQLdb
import socket
import datetime


"""
Global variables
"""
PIR_DB_CONNECTED = False
RGB_DB_CONNECTED = False
USR_DB_CONNECTED = False
SEND_CIRCADIAN_DB_CONNECTED = False
WAIT_FOR_CMD_DB_CONNECTED = False
SLEEP_MODE = False

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

while True:
    print "reading from USR..."
    time.sleep(3)