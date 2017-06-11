import time
import os
import signal
import subprocess
import circadian
import MySQLdb
import socket
import datetime
import smbus

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
MASTER_CIRCADIAN_TABLE = circadian.init_circadian_table()
MASTER_OFFSET_TABLE = circadian.init_offset_table()
MASTER_LUX_TABLE = circadian.init_master_lux_table()
TOO_BRIGHT = False
local_ip = circadian.get_ip()

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
            user_tuple = circadian.calc_user_tables(WAKE_UP_TIME, MASTER_CIRCADIAN_TABLE, MASTER_OFFSET_TABLE,
                                                    MASTER_LUX_TABLE)
            USER_CIRCADIAN_TABLE = user_tuple[0]
            USER_OFFSET_TABLE = user_tuple[1]
            USER_LUX_TABLE = user_tuple[2]
    if cmd[1] != "N":
        temp_color_thres = float(cmd[1]) / 100
        if temp_color_thres != COLOR_THRESHOLD:
            COLOR_THRESHOLD = temp_color_thres

def handle_sleep_mode(signum, stack):
    global SLEEP_MODE
    SLEEP_MODE = True

def handle_wake_up(signum, stack):
    global SLEEP_MODE
    SLEEP_MODE = False

def handle_send_circadian(signum, stack):
    print "New circadian value sent..."
    time.sleep(3)

def handle_wait_for_cmd_dB_connect(signum, stack):
    global WAIT_FOR_CMD_DB_CONNECTED
    WAIT_FOR_CMD_DB_CONNECTED = True

def handle_pir_dB_connect(signum, stack):
    global PIR_DB_CONNECTED
    PIR_DB_CONNECTED = True

def handle_usr_dB_connect(signum, stack):
    global USR_DB_CONNECTED
    USR_DB_CONNECTED = True

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

"""
Establish DB connection
"""
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
cursor = db.cursor()
print "RGB DB connection established"

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
COLOR_THRESHOLD = float(temp[0][2])/100
user_tuple = circadian.calc_user_tables(WAKE_UP_TIME, MASTER_CIRCADIAN_TABLE, MASTER_OFFSET_TABLE, MASTER_LUX_TABLE)
USER_CIRCADIAN_TABLE = user_tuple[0]
USER_OFFSET_TABLE = user_tuple[1]
USER_LUX_TABLE = user_tuple[2]

"""
Alert other Python scripts that the PIR has connected
"""
pid_list = circadian.get_pids()
for pid in pid_list:
    os.kill(pid, 11)

"""
Wait for other sensor scripts to connect to the DB
"""
while not WAIT_FOR_CMD_DB_CONNECTED or not PIR_DB_CONNECTED or not USR_DB_CONNECTED or not SEND_CIRCADIAN_DB_CONNECTED:
    time.sleep(1)
"""
Initialize the RGB sensor
The RGB sensor uses I2C Bus (smbus)
Register address must be OR'ed wit 0x80
"""
bus = smbus.SMBus(1)
bus.write_byte(0x29, 0x80 | 0x12)
ver = bus.read_byte(0x29)

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
    data = bus.read_i2c_block_data(0x29, 0)

    red = float(data[3] << 8 | data[2])
    green = float(data[5] << 8 | data[4])
    blue = float(data[7] << 8 | data[6])
    sys_time = circadian.get_system_time()
    x = (float(USER_CIRCADIAN_TABLE[sys_time][0]) / 100) * 147
    y = (float(USER_CIRCADIAN_TABLE[sys_time][1]) / 100) * 121
    z = (float(USER_CIRCADIAN_TABLE[sys_time][2]) / 100) * 189
    # print "offset red",offset_red
    red2 = (float(red + (x - USER_OFFSET_TABLE[sys_time][0])) / 147) * 100
    green2 = (float(green + (y - USER_OFFSET_TABLE[sys_time][1])) / 121) * 100
    blue2 = (float(blue + (z - USER_OFFSET_TABLE[sys_time][2])) / 189) * 100
    """
    test if its too bright i.e. there is outside light pollution
    """
    if red2 > USER_CIRCADIAN_TABLE[sys_time][0] and green2 > USER_CIRCADIAN_TABLE[sys_time][1] and blue2 > \
            USER_CIRCADIAN_TABLE[sys_time][2]:
        TOO_BRIGHT = True
        print "IT IS TOO BRIGHT IN THE BEGINNING!", TOO_BRIGHT

while True:
    if not SLEEP_MODE:

        data = bus.read_i2c_block_data(0x29, 0)

        red = float(data[3] << 8 | data[2])
        green = float(data[5] << 8 | data[4])
        blue = float(data[7] << 8 | data[6])
        sys_time = circadian.get_system_time()
        x = (float(USER_CIRCADIAN_TABLE[sys_time][0]) / 100) * 147
        y = (float(USER_CIRCADIAN_TABLE[sys_time][1]) / 100) * 121
        z = (float(USER_CIRCADIAN_TABLE[sys_time][2]) / 100) * 189
        # print "offset red",offset_red
        red2 = (float(red + (x - USER_OFFSET_TABLE[sys_time][0])) / 147) * 100
        green2 = (float(green + (y - USER_OFFSET_TABLE[sys_time][1])) / 121) * 100
        blue2 = (float(blue + (z - USER_OFFSET_TABLE[sys_time][2])) / 189) * 100

        print "I'm reading from the RGB %s %s %s..."%(red2, green2, blue2)
        """
        Compensation check will be done here
        """
    time.sleep(3)
