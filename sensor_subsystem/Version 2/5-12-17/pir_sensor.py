import time
import os
import signal
import subprocess
import circadian
import MySQLdb

"""
Global Variables
"""

"""
Establish DB connection
"""
print "Establishing Database connection in main thread..."
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
print "Database connection established in main thread."
cursor = db.cursor()

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

"""
Non-Signal Handler Functions
"""
def execute_db_query(cursor, db, sql):
    if sql[0] != 'S' or sql[0] != 's':
        """
        Query is something other than select query
        """
        try:
            cursor.execute(sql)
            db.commit()
        except (AttributeError, MySQLdb.OperationalError):
            print "Re-establishing database connection in main thread..."
            db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                 db="ilcs")
            print "Database connection re-established in main thread."
            cursor = db.cursor()
            try:
                cursor.execute(sql)
                db.commit()
            except:
                db.rollback()
        except:
            db.rollback()
    else:
        """
        query is select query
        """
        cursor.execute(sql, ([local_ip]))
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
"""
signal.signal(signal.SIGQUIT, handle_change_cmd)
signal.signal(signal.SIGIOT, handle_send_compensation)
signal.signal(7, handle_send_circadian)

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