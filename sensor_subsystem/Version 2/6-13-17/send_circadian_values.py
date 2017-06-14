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
WAKE_UP_TIME = 0
COLOR_THRESHOLD = 0
local_ip = circadian.get_ip()
MASTER_CIRCADIAN_TABLE = circadian.init_circadian_table()
MASTER_OFFSET_TABLE = circadian.init_offset_table()
MASTER_LUX_TABLE = circadian.init_master_lux_table()
PREV_PRIMARY_COLORS = [0, 0, 0]
PREV_SECONDARY_COLORS = [0, 0, 0]
IS_PRIMARY_DEG = [False, False, False]
IS_SEC_ON = [False, False, False]
IS_SEC_DEG = [False, False, False]

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
    global MASTER_CIRCADIAN_TABLE
    global USER_CIRCADIAN_TABLE
    global USER_OFFSET_TABLE
    global USER_LUX_TABLE
    global MASTER_LUX_TABLE
    global MASTER_OFFSET_TABLE
    global begin_timer
    global local_ip
    print "User changed something..."
    time.sleep(3)
    file = open("config.txt", "r")
    cmd_str = file.read()
    file.close()
    cmd = cmd_str.split('|')
    if cmd[0] != "N":
        temp_wake_time = int(cmd[0])

        if temp_wake_time != WAKE_UP_TIME:
            """
            User changed wake up time
            """
            WAKE_UP_TIME = temp_wake_time
            user_tuple = circadian.calc_user_tables(WAKE_UP_TIME, MASTER_CIRCADIAN_TABLE, MASTER_OFFSET_TABLE, MASTER_LUX_TABLE)
            USER_CIRCADIAN_TABLE = user_tuple[0]
            USER_OFFSET_TABLE = user_tuple[1]
            USER_LUX_TABLE = user_tuple[2]
            begin_timer = -60



def handle_sleep_mode(signum, stack):
    global SLEEP_MODE
    global PREV_PRIMARY_COLORS
    global USER_CIRCADIAN_TABLE
    global lighting_ip
    global db
    global cursor
    global local_ip
    global begin_timer
    SLEEP_MODE = True
    print "Entering sleep mode..."
    """
    Get user ct values for sleep cmd here.
    """
    sys_time = circadian.get_system_time()
    sleep_cmd = str(USER_CIRCADIAN_TABLE[sys_time][0]) + "|" + str(USER_CIRCADIAN_TABLE[sys_time][1]) + "|" + str(
        USER_CIRCADIAN_TABLE[sys_time][2]) + "|"
    """
    Connect to lighting subsystem and send sleep mode cmd
    """
    pir_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pir_cli_sock_host = lighting_ip.strip()
    pir_cli_sock_port = 12346
    pir_cli_sock.connect((pir_cli_sock_host, pir_cli_sock_port))
    pir_cli_sock.send(sleep_cmd)
    pir_cli_sock.close()
    PREV_PRIMARY_COLORS[0] = 0
    PREV_PRIMARY_COLORS[1] = 0
    PREV_PRIMARY_COLORS[2] = 0
    """
    Update the DB with sleep mode status as 1
    """
    sql = """UPDATE sensor_status SET sleep_mode_status = 1 WHERE ip = %s"""
    circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
    begin_timer = time.time()



def handle_wake_up(signum, stack):
    global SLEEP_MODE
    global db
    global cursor
    global local_ip
    global begin_timer
    SLEEP_MODE = False
    """
    Update the DB with sleep mode status as 0
    """
    sql = """UPDATE sensor_status SET sleep_mode_status = 0 WHERE ip = %s"""
    circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
    begin_timer = -60

def handle_send_compensation(signum, stack):
    file = open("compensate.txt", "r")
    cmd_str = file.read()
    file.close()
    cmd = cmd_str.split('|')
    print "RGB sent compensation value", cmd
    time.sleep(3)

def handle_wait_for_cmd_dB_connect(signum, stack):
    global WAIT_FOR_CMD_DB_CONNECTED
    WAIT_FOR_CMD_DB_CONNECTED = True

def handle_pir_dB_connect(signum, stack):
    global PIR_DB_CONNECTED
    PIR_DB_CONNECTED = True

def handle_rgb_dB_connect(signum, stack):
    global RGB_DB_CONNECTED
    RGB_DB_CONNECTED = True

def handle_usr_dB_connect(signum, stack):
    global USR_DB_CONNECTED
    USR_DB_CONNECTED = True

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
signal.signal(4, handle_sleep_mode)
signal.signal(5, handle_wake_up)
signal.signal(6, handle_send_compensation)
signal.signal(7, catch_other_signals)
signal.signal(8, handle_wait_for_cmd_dB_connect)
signal.signal(10, handle_pir_dB_connect)
signal.signal(11, handle_rgb_dB_connect)
signal.signal(12, handle_usr_dB_connect)
signal.signal(15, catch_other_signals)

"""
Establish DB connection
"""
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
cursor = db.cursor()
print "Send circadian DB connection established"

"""
Get lighting sub IP
"""
sql = """SELECT * FROM sensor_light_pairs WHERE sensor_ip = %s"""
temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
lighting_ip = temp[0][1]

"""
Get User initial parameters and calc user tables
"""
sql = """SELECT * FROM sensor_settings WHERE ip = %s"""
temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
WAKE_UP_TIME = int(temp[0][1])
user_tuple = circadian.calc_user_tables(WAKE_UP_TIME, MASTER_CIRCADIAN_TABLE, MASTER_OFFSET_TABLE, MASTER_LUX_TABLE)
USER_CIRCADIAN_TABLE = user_tuple[0]
USER_OFFSET_TABLE = user_tuple[1]
USER_LUX_TABLE = user_tuple[2]

"""
Alert other Python scripts that the PIR has connected
"""
pid_list = circadian.get_pids()
for pid in pid_list:
    os.kill(pid, 15)

"""
Wait for other sensor scripts to connect to the DB
"""
while not WAIT_FOR_CMD_DB_CONNECTED or not PIR_DB_CONNECTED or not USR_DB_CONNECTED or not RGB_DB_CONNECTED:
    time.sleep(1)
"""
Connect to lighting subsystem and send circadian value
"""

circadian_cmd_tuple = circadian.get_circadian_cmd(USER_CIRCADIAN_TABLE, PREV_PRIMARY_COLORS, PREV_SECONDARY_COLORS, IS_PRIMARY_DEG, IS_SEC_ON, IS_SEC_DEG)
circadian_cmd = circadian_cmd_tuple[0]

pid_list = circadian.get_pids()
for pid in pid_list:
    os.kill(pid, 7)
"""
Connect to lighting subsystem and send circadian value
"""
circadian_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
circadian_cli_sock_host = lighting_ip.strip()
circadian_cli_sock_port = 12347
circadian_cli_sock.connect((circadian_cli_sock_host, circadian_cli_sock_port))
circadian_cli_sock.send(circadian_cmd)
circadian_cli_sock.close()
PREV_PRIMARY_COLORS[0] = circadian_cmd_tuple[1][0]
PREV_PRIMARY_COLORS[1] = circadian_cmd_tuple[1][1]
PREV_PRIMARY_COLORS[2] = circadian_cmd_tuple[1][2]
begin_timer = time.time()

while True:
    if not SLEEP_MODE:
        current_timer = time.time()
        time_diff = int(current_timer - begin_timer)
        if time_diff >= 60:
            circadian_cmd_tuple = circadian.get_circadian_cmd(USER_CIRCADIAN_TABLE, PREV_PRIMARY_COLORS, PREV_SECONDARY_COLORS, IS_PRIMARY_DEG, IS_SEC_ON, IS_SEC_DEG)
            circadian_cmd = circadian_cmd_tuple[0]

            pid_list = circadian.get_pids()
            for pid in pid_list:
                os.kill(pid, 7)
            """
            Connect to lighting subsystem and send circadian value
            """
            circadian_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            circadian_cli_sock_host = lighting_ip.strip()
            circadian_cli_sock_port = 12347
            circadian_cli_sock.connect((circadian_cli_sock_host, circadian_cli_sock_port))
            circadian_cli_sock.send(circadian_cmd)
            circadian_cli_sock.close()
            PREV_PRIMARY_COLORS[0] = circadian_cmd_tuple[1][0]
            PREV_PRIMARY_COLORS[1] = circadian_cmd_tuple[1][1]
            PREV_PRIMARY_COLORS[2] = circadian_cmd_tuple[1][2]

            begin_timer = time.time()
