import time
import os
import signal
import subprocess
import circadian
import MySQLdb
import socket
import datetime

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

"""
Signal Handlers
"""
def handle_change_cmd(signum, stack):
    global db
    global cursor
    global WAKE_UP_TIME
    global COLOR_THRESHOLD
    print "Changing parameter..."
    time.sleep(3)

def handle_send_compensation(signum, stack):
    print "sending compensation value..."
    time.sleep(3)

def handle_send_circadian(signum, stack):
    print "sending circadian value..."
    time.sleep(3)

def handle_wait_for_cmd_dB_connect(signum, stack):
    global WAIT_FOR_CMD_DB_CONNECTED
    print "Wait for DB connection established"
    WAIT_FOR_CMD_DB_CONNECTED = True

def handle_rgb_dB_connect(signum, stack):
    global RGB_DB_CONNECTED
    print "RGB DB connection established"
    RGB_DB_CONNECTED = True

def handle_usr_dB_connect(signum, stack):
    global USR_DB_CONNECTED
    print "RGB DB connection established"
    USR_DB_CONNECTED = True

def handle_send_circadian_dB_connect(signum, stack):
    global SEND_CIRCADIAN_DB_CONNECTED
    print "Send circadian DB connection established"
    SEND_CIRCADIAN_DB_CONNECTED = True

"""
Non-Signal Handler Functions
"""
def execute_db_query(cursor, db, sql, sql_args):
    if sql[0] != 'S' and sql[0] != 's':
        print "im here"
        """
        Query is something other than select query
        """
        try:
            if len(sql_args) == 0:
                cursor.execute(sql)
            else:
                cursor.execute(sql, sql_args)
            db.commit()
        except (AttributeError, MySQLdb.OperationalError):
            print "Re-establishing database connection in main thread..."
            db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                 db="ilcs")
            print "Database connection re-established in main thread."
            cursor = db.cursor()
            try:
                if len(sql_args) == 0:
                    cursor.execute(sql)
                else:
                    cursor.execute(sql, sql_args)
                db.commit()
            except:
                db.rollback()
        except:
            db.rollback()
    else:
        """
        query is select query
        """
        if len(sql_args) == 0:
            cursor.execute(sql)
        else:
            cursor.execute(sql, sql_args)
        result = cursor.fetchall()
        return result

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
signal.signal(signal.SIGQUIT, handle_change_cmd)
signal.signal(signal.SIGIOT, handle_send_compensation)
signal.signal(7, handle_send_circadian)
signal.signal(8, handle_wait_for_cmd_dB_connect)
signal.signal(11, handle_rgb_dB_connect)
signal.signal(12, handle_usr_dB_connect)
signal.signal(15, handle_send_circadian_dB_connect)

"""
Establish DB connection
"""
print "Establishing Database connection in main thread..."
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
print "Database connection established in main thread."
cursor = db.cursor()
"""
Alert other Python scripts that the PIR has connected
"""
rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
usr_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'usr_sensor.py']))
wait_for_cmd_pid = int(subprocess.check_output(['pgrep', '-f', 'wait_for_cmd.py']))
send_circadian_pid = int(subprocess.check_output(['pgrep', '-f', 'send_circadian_values.py']))
os.kill(rgb_sensor_pid, 10)
os.kill(usr_sensor_pid, 10)
os.kill(wait_for_cmd_pid, 10)
os.kill(send_circadian_pid, 10)

"""
Wait for other sensor scripts to connect to the DB
"""
while not WAIT_FOR_CMD_DB_CONNECTED or not RGB_DB_CONNECTED or not USR_DB_CONNECTED or not SEND_CIRCADIAN_DB_CONNECTED:
    pass

"""
Begin reading from the motion sensor
"""
begin_timer = time.time()
while True:
    current_timer = time.time()
    time_diff = int(current_timer - begin_timer)
    if time_diff >= 60 and not SLEEP_MODE:
        SLEEP_MODE = True
        rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
        send_circadian_pid = int(subprocess.check_output(['pgrep', '-f', 'send_circadian_values.py']))
        print "Should go to sleep mode", rgb_sensor_pid
        os.kill(rgb_sensor_pid, signal.SIGILL)
        os.kill(send_circadian_pid, signal.SIGILL)
        begin_timer = time.time()
    elif time_diff >= 60 and SLEEP_MODE:
        SLEEP_MODE = False
        rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
        send_circadian_pid = int(subprocess.check_output(['pgrep', '-f', 'send_circadian_values.py']))
        print "Should exit sleep mode", rgb_sensor_pid
        os.kill(rgb_sensor_pid, signal.SIGTRAP)
        os.kill(send_circadian_pid, signal.SIGTRAP)
        begin_timer = time.time()