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
TOO_BRIGHT_HANDLED = [False, False, False]
local_ip = circadian.get_ip()
SERVICE = [False, False, False]
PRIMARY_DEGRADED =[False, False, False]
SECONDARY_ON =[False, False, False]
SECONDARY_DEGRADED = [False, False, False]
OLD_RED = 0
OLD_GREEN = 0
OLD_BLUE = 0

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
    global db
    global cursor
    global local_ip
    SLEEP_MODE = True
    """
    Update database for sleep mode
    """
    sql = """UPDATE sensor_status SET red = 0 WHERE ip = %s"""
    circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
    sql = """UPDATE sensor_status SET green = 0 WHERE ip = %s"""
    circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
    sql = """UPDATE sensor_status SET blue = 0 WHERE ip = %s"""
    circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
    sql = """UPDATE sensor_status SET lumens = 0 WHERE ip = %s"""
    circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

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
Alert other Python scripts that the RGB has connected
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
        TOO_BRIGHT_HANDLED = [True, True, True]
        print "IT IS TOO BRIGHT IN THE BEGINNING!", TOO_BRIGHT_HANDLED

while True:
    if not SLEEP_MODE:
        """
        comp_cmd format:
        PR|SR$0/1|PG|SG$0/1|PB|SB$0/1
        the $0/1 will indicate if the secondary had degraded
        These are the ending values. Beginning values are taken care of in send_circadian_values.py
        """
        comp_list = ["N","N","N","N","N","N"]
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
        Get Lux and Lumens
        """
        dist_in_meters = 8 * 0.3048
        if red2 > USER_CIRCADIAN_TABLE[sys_time][0]:
            red_temp = USER_CIRCADIAN_TABLE[sys_time][0]
        else:
            red_temp = red2
        if green2 > USER_CIRCADIAN_TABLE[sys_time][1]:
            green_temp = USER_CIRCADIAN_TABLE[sys_time][1]
        else:
            green_temp = green2
        if blue2 > USER_CIRCADIAN_TABLE[sys_time][2]:
            blue_temp = USER_CIRCADIAN_TABLE[sys_time][2]
        else:
            blue_temp = blue2
        try:
            lux_num = red_temp + green_temp + blue_temp
            lux_den = USER_CIRCADIAN_TABLE[sys_time][0] + USER_CIRCADIAN_TABLE[sys_time][1] + \
                      USER_CIRCADIAN_TABLE[sys_time][2]

            lux = (lux_num / lux_den) * USER_LUX_TABLE[sys_time]
            lumens = int(circadian.calc_Illuminance(lux, dist_in_meters, 120))
        except:
            lux = 0
            lumens = 0

        if (red2 < (USER_CIRCADIAN_TABLE[sys_time][0] - USER_CIRCADIAN_TABLE[sys_time][0]*COLOR_THRESHOLD)) and not \
                SERVICE[0]:
            if PRIMARY_DEGRADED[0]:
                if SECONDARY_ON[0]:
                    if SECONDARY_DEGRADED[0]:
                        """
                        Set service to true
                        """
                        SERVICE[0] = True

                        """
                        update the database
                        """
                        sql = """UPDATE sensor_status SET service = 1 WHERE ip = %s"""
                        circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

                    else:
                        """
                        Secondaries have degraded
                        """
                        SECONDARY_DEGRADED[0] = True

                        message = "Sensor Subsystem (" + local_ip + ") secondary red LEDs have degraded."
                        circadian.create_log(cursor, db, message, "None")

                        """
                        Add primary and secondary to comp_cmd
                        """
                        comp_list[0] = str(USER_CIRCADIAN_TABLE[sys_time][0] + (USER_CIRCADIAN_TABLE[sys_time][0] -
                                                                               red2))
                        comp_list[1] = str(2 * (USER_CIRCADIAN_TABLE[sys_time][0] - red2))+"$1"
                else:
                    """
                    Turn secondary red on
                    """
                    SECONDARY_ON[0] = True

                    message = "Sensor Subsystem (" + local_ip + ") secondary red LEDs have turned on."
                    circadian.create_log(cursor, db, message, "None")

                    """
                    Add primary and secondary to comp_cmd
                    """
                    comp_list[0] = str(USER_CIRCADIAN_TABLE[sys_time][0] + (USER_CIRCADIAN_TABLE[sys_time][0] - red2))
                    comp_list[1] = str(USER_CIRCADIAN_TABLE[sys_time][0] - red2)+"$0"
            else:
                """
                Primary red has degraded
                """
                PRIMARY_DEGRADED[0] = True
                TOO_BRIGHT_HANDLED[0] = False

                message = "Sensor Subsystem (" + local_ip + ") primary red LEDs have degraded."
                circadian.create_log(cursor, db, message, "None")

                """
                Add to comp_cmd
                """
                comp_list[0] = str(USER_CIRCADIAN_TABLE[sys_time][0] + (USER_CIRCADIAN_TABLE[sys_time][0] - red2))

                """
                update the database
                """
                sql = """UPDATE sensor_status SET red_degraded = 1 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
                sql = """UPDATE sensor_status SET lumens_degraded = 1 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
        elif (red2 > USER_CIRCADIAN_TABLE[sys_time][0]) and not TOO_BRIGHT_HANDLED[0]:
            """
            sensor reading is too bright. Either from compensation or light pollution
            then reduce back to normal and reset the service and compensation stuff
            """
            TOO_BRIGHT_HANDLED[0] = True
            PRIMARY_DEGRADED[0] = False
            SECONDARY_ON[0] = False
            SECONDARY_DEGRADED[0] = False
            SERVICE[0] = False

            comp_list[0] = str(USER_CIRCADIAN_TABLE[sys_time][0])
            comp_list[1] =  "0$0"
            """
            Update the database
            """
            sql = """UPDATE sensor_status SET red_degraded = 0 WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
            sql = """SELECT * FROM sensor_status WHERE ip = %s"""
            temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
            if not int(temp[0][5]) and not int(temp[0][6]) and not int(temp[0][7]):
                sql = """UPDATE sensor_status SET lumens_degraded = 0 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
                sql = """UPDATE sensor_status SET service = 0 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

        """
        Green and blue check goes here
        """
        if (green2 < (USER_CIRCADIAN_TABLE[sys_time][1] - USER_CIRCADIAN_TABLE[sys_time][1] * COLOR_THRESHOLD)) and \
                not SERVICE[1]:
            if PRIMARY_DEGRADED[1]:
                if SECONDARY_ON[1]:
                    if SECONDARY_DEGRADED[1]:
                        """
                        Set service to true
                        """
                        SERVICE[1] = True

                        """
                        update the database
                        """
                        sql = """UPDATE sensor_status SET service = 1 WHERE ip = %s"""
                        circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

                    else:
                        """
                        Secondaries have degraded
                        """
                        SECONDARY_DEGRADED[1] = True

                        message = "Sensor Subsystem (" + local_ip + ") secondary green LEDs have degraded."
                        circadian.create_log(cursor, db, message, "None")

                        """
                        Add primary and secondary to comp_cmd
                        """
                        comp_list[2] = str(USER_CIRCADIAN_TABLE[sys_time][1] + (USER_CIRCADIAN_TABLE[sys_time][1] -
                                                                                green2))
                        comp_list[3] = str(2 * (USER_CIRCADIAN_TABLE[sys_time][1] - green2)) + "$1"
                else:
                    """
                    Turn secondary green on
                    """
                    SECONDARY_ON[1] = True

                    message = "Sensor Subsystem (" + local_ip + ") secondary green LEDs have turned on."
                    circadian.create_log(cursor, db, message, "None")

                    """
                    Add primary and secondary to comp_cmd
                    """
                    comp_list[2] = str(USER_CIRCADIAN_TABLE[sys_time][1] + (USER_CIRCADIAN_TABLE[sys_time][1] - green2))
                    comp_list[3] = str(USER_CIRCADIAN_TABLE[sys_time][1] - green2) + "$0"
            else:
                """
                Primary green has degraded
                """
                PRIMARY_DEGRADED[1] = True
                TOO_BRIGHT_HANDLED[1] = False

                message = "Sensor Subsystem (" + local_ip + ") primary green LEDs have degraded."
                circadian.create_log(cursor, db, message, "None")

                """
                Add to comp_cmd
                """
                comp_list[2] = str(USER_CIRCADIAN_TABLE[sys_time][1] + (USER_CIRCADIAN_TABLE[sys_time][1] - green2))

                """
                update the database
                """
                sql = """UPDATE sensor_status SET green_degraded = 1 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
                sql = """UPDATE sensor_status SET lumens_degraded = 1 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
        elif (green2 > USER_CIRCADIAN_TABLE[sys_time][1]) and not TOO_BRIGHT_HANDLED[1]:
            """
            sensor reading is too bright. Either from compensation or light pollution
            then reduce back to normal and reset the service and compensation stuff
            """
            TOO_BRIGHT_HANDLED[1] = True
            PRIMARY_DEGRADED[1] = False
            SECONDARY_ON[1] = False
            SECONDARY_DEGRADED[1] = False
            SERVICE[1] = False

            comp_list[2] = str(USER_CIRCADIAN_TABLE[sys_time][1])
            comp_list[3] = "0$0"
            """
            Update the database
            """
            sql = """UPDATE sensor_status SET green_degraded = 0 WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
            sql = """SELECT * FROM sensor_status WHERE ip = %s"""
            temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
            if not int(temp[0][5]) and not int(temp[0][6]) and not int(temp[0][7]):
                sql = """UPDATE sensor_status SET lumens_degraded = 0 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
                sql = """UPDATE sensor_status SET service = 0 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

        if (blue2 < (USER_CIRCADIAN_TABLE[sys_time][2] - USER_CIRCADIAN_TABLE[sys_time][2] * COLOR_THRESHOLD)) and not \
                SERVICE[2]:
            if PRIMARY_DEGRADED[2]:
                if SECONDARY_ON[2]:
                    if SECONDARY_DEGRADED[2]:
                        """
                        Set service to true
                        """
                        SERVICE[2] = True

                        """
                        update the database
                        """
                        sql = """UPDATE sensor_status SET service = 1 WHERE ip = %s"""
                        circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

                    else:
                        """
                        Secondaries have degraded
                        """
                        SECONDARY_DEGRADED[2] = True

                        message = "Sensor Subsystem (" + local_ip + ") secondary blue LEDs have degraded."
                        circadian.create_log(cursor, db, message, "None")

                        """
                        Add primary and secondary to comp_cmd
                        """
                        comp_list[4] = str(USER_CIRCADIAN_TABLE[sys_time][2] + (USER_CIRCADIAN_TABLE[sys_time][2] -
                                                                                blue2))
                        comp_list[5] = str(2 * (USER_CIRCADIAN_TABLE[sys_time][2] - blue2)) + "$1"
                else:
                    """
                    Turn secondary blue on
                    """
                    SECONDARY_ON[2] = True

                    message = "Sensor Subsystem (" + local_ip + ") secondary blue LEDs have turned on."
                    circadian.create_log(cursor, db, message, "None")

                    """
                    Add primary and secondary to comp_cmd
                    """
                    comp_list[4] = str(USER_CIRCADIAN_TABLE[sys_time][2] + (USER_CIRCADIAN_TABLE[sys_time][2] - blue2))
                    comp_list[5] = str(USER_CIRCADIAN_TABLE[sys_time][2] - blue2) + "$0"
            else:
                """
                Primary blue has degraded
                """
                PRIMARY_DEGRADED[2] = True
                TOO_BRIGHT_HANDLED[2] = False

                message = "Sensor Subsystem (" + local_ip + ") primary blue LEDs have degraded."
                circadian.create_log(cursor, db, message, "None")

                """
                Add to comp_cmd
                """
                comp_list[4] = str(USER_CIRCADIAN_TABLE[sys_time][2] + (USER_CIRCADIAN_TABLE[sys_time][2] - blue2))

                """
                update the database
                """
                sql = """UPDATE sensor_status SET blue_degraded = 1 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
                sql = """UPDATE sensor_status SET lumens_degraded = 1 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
        elif (blue2 > USER_CIRCADIAN_TABLE[sys_time][2]) and not TOO_BRIGHT_HANDLED[2]:
            """
            sensor reading is too bright. Either from compensation or light pollution
            then reduce back to normal and reset the service and compensation stuff
            """
            TOO_BRIGHT_HANDLED[2] = True
            PRIMARY_DEGRADED[2] = False
            SECONDARY_ON[2] = False
            SECONDARY_DEGRADED[2] = False
            SERVICE[2] = False

            comp_list[4] = str(USER_CIRCADIAN_TABLE[sys_time][2])
            comp_list[5] = "0$0"
            """
            Update the database
            """
            sql = """UPDATE sensor_status SET blue_degraded = 0 WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
            sql = """SELECT * FROM sensor_status WHERE ip = %s"""
            temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
            if not int(temp[0][5]) and not int(temp[0][6]) and not int(temp[0][7]):
                sql = """UPDATE sensor_status SET lumens_degraded = 0 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
                sql = """UPDATE sensor_status SET service = 0 WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
        """
        Check if a comp value needs to be sent
        """
        for key in comp_list:
            if key != "N":
                comp_cmd = comp_list[0]+"|"+comp_list[1]+"|"+comp_list[2]+"|"+comp_list[3]+"|"+comp_list[4]\
                           +"|"+comp_list[5]+"|"
                """
                Write comp_cmd to compensate file and send signal to the send_circadian_values.py process
                """
                file = open("compensate.txt", "w")
                file.write(comp_cmd)
                file.close()
                pid_list = circadian.get_pids()
                for pid in pid_list:
                    os.kill(pid, 6)
                break
        """
        update database with sensor readings
        """
        if red2 > (OLD_RED + OLD_RED * 0.05) or red2 < (OLD_RED - OLD_RED * 0.05):
            if red2 > USER_CIRCADIAN_TABLE[sys_time][0]:
                OLD_RED = USER_CIRCADIAN_TABLE[sys_time][0]
                sql = """UPDATE sensor_status SET red = %s WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([USER_CIRCADIAN_TABLE[sys_time][0], local_ip]))
            else:
                OLD_RED = red2
                sql = """UPDATE sensor_status SET red = %s WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([red2, local_ip]))
            """
            Write comp_cmd to compensate file and send signal to the send_circadian_values.py process
            """
            sensor_cmd = str(OLD_RED) + "|" + str(OLD_GREEN) + "|" + str(OLD_BLUE) + "|"
            file = open("sensor_data.txt", "w")
            file.write(sensor_cmd)
            file.close()

            """
            Store lumens into DB
            """
            sql = """UPDATE sensor_status SET lumens = %s WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([lumens, local_ip]))

        if green2 > (OLD_GREEN + OLD_GREEN * 0.05) or green2 < (OLD_GREEN - OLD_GREEN * 0.05):
            if green2 > USER_CIRCADIAN_TABLE[sys_time][1]:
                OLD_GREEN = USER_CIRCADIAN_TABLE[sys_time][1]
                sql = """UPDATE sensor_status SET green = %s WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([USER_CIRCADIAN_TABLE[sys_time][1], local_ip]))
            else:
                OLD_GREEN = green2
                sql = """UPDATE sensor_status SET green = %s WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([green2, local_ip]))
            """
            Write comp_cmd to compensate file and send signal to the send_circadian_values.py process
            """
            sensor_cmd = str(OLD_RED) + "|" + str(OLD_GREEN) + "|" + str(OLD_BLUE) + "|"
            file = open("sensor_data.txt", "w")
            file.write(sensor_cmd)
            file.close()

            """
            Store lumens into DB
            """
            sql = """UPDATE sensor_status SET lumens = %s WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([lumens, local_ip]))

        if blue2 > (OLD_BLUE + OLD_BLUE * 0.05) or blue2 < (OLD_BLUE - OLD_BLUE * 0.05):
            if blue2 > USER_CIRCADIAN_TABLE[sys_time][2]:
                OLD_BLUE = USER_CIRCADIAN_TABLE[sys_time][2]
                sql = """UPDATE sensor_status SET blue = %s WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([USER_CIRCADIAN_TABLE[sys_time][2], local_ip]))
            else:
                OLD_BLUE = blue2
                sql = """UPDATE sensor_status SET blue = %s WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([blue2, local_ip]))
            """
            Write comp_cmd to compensate file and send signal to the send_circadian_values.py process
            """
            sensor_cmd = str(OLD_RED) + "|" + str(OLD_GREEN) + "|" + str(OLD_BLUE) + "|"
            file = open("sensor_data.txt", "w")
            file.write(sensor_cmd)
            file.close()

            """
            Store lumens into DB
            """
            sql = """UPDATE sensor_status SET lumens = %s WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([lumens, local_ip]))

    time.sleep(3)
