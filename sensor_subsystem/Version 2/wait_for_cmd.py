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
MASTER_CIRCADIAN_TABLE = circadian.init_circadian_table()
MASTER_OFFSET_TABLE = circadian.init_offset_table()
MASTER_LUX_TABLE = circadian.init_master_lux_table()

lighting_ip = ""

"""
Signal Handlers
"""
def catch_other_signals(signum, stack):
    pass

def handle_pir_dB_connect(signum, stack):
    global PIR_DB_CONNECTED
    PIR_DB_CONNECTED = True

def handle_rgb_dB_connect(signum, stack):
    global RGB_DB_CONNECTED
    RGB_DB_CONNECTED = True

def handle_usr_dB_connect(signum, stack):
    global USR_DB_CONNECTED
    USR_DB_CONNECTED = True

def handle_send_circadian_dB_connect(signum, stack):
    global SEND_CIRCADIAN_DB_CONNECTED
    SEND_CIRCADIAN_DB_CONNECTED = True

def handle_sleep_mode(signum, stack):
    global SLEEP_MODE
    SLEEP_MODE = True

def handle_wake_up(signum, stack):
    global SLEEP_MODE
    SLEEP_MODE = False

"""
Non-Signal Handler Functions
"""
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
    #global is_sensor_sub_paired
    # global lighting_ip
    global COLOR_THRESHOLD
    # global LIGHT_THRESHOLD
    global WAKE_UP_TIME
    # global SLEEP_MODE_STATUS
    global db
    global cursor
    global lighting_ip

    local_ip = circadian.get_ip()
    is_sensor_sub_paired = 0

    """
    Check DB if the sensor sub exists
    """
    sql = """SELECT * FROM sensor_ip WHERE ip = %s"""
    temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

    if len(temp) == 0:
        """
        The sensor sub does NOT exist in the DB so insert it into
        the sensor_ip and sensor_status tables
        """
        sql = """INSERT INTO sensor_ip(ip, is_paired) VALUES(%s, 0)"""

        circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
    else:
        """
        The sensor sub DOES exist in the DB. Grab its paired status
        """
        is_sensor_sub_paired = temp[0][1]

        """
        Check degrade status for red
        """
        sql = """SELECT * FROM sensor_status WHERE ip = %s"""
        temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

        is_sensor_service = temp[0][11]
        is_being_serviced = temp[0][12]
        is_red_deg = temp[0][5]
        is_green_deg = temp[0][6]
        is_blue_deg = temp[0][7]
        is_lumen_deg = temp[0][8]
        sql = """UPDATE sensor_status SET distance = 8 WHERE ip = %s"""
        circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

        if is_sensor_service:
            sql = """UPDATE sensor_status SET service = 0 WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
        if is_being_serviced:
            sql = """UPDATE sensor_status SET being_serviced = 0 WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
        if is_red_deg:
            sql = """UPDATE sensor_status SET red_degraded = 0 WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
        if is_green_deg:
            sql = """UPDATE sensor_status SET green_degraded = 0 WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
        if is_blue_deg:
            sql = """UPDATE sensor_status SET blue_degraded = 0 WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([local_ip]))
        if is_lumen_deg:
            sql = """UPDATE sensor_status SET lumens_degraded = 0 WHERE ip = %s"""
            circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

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

        sql = """INSERT INTO sensor_status(ip, red, green, blue, lumens, red_degraded, green_degraded, blue_degraded, lumens_degraded, sleep_mode_status, distance, service, being_serviced) VALUEs(%s, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0)"""
        circadian.execute_dB_query(cursor,db, sql, ([local_ip]))

        """
        Grab the lighting sub IP to be paired with.
        """
        sql = """SELECT * from lighting_ip where is_paired = 0"""
        temp = circadian.execute_dB_query(cursor, db, sql, ())
        lighting_ip = temp[0][0]

        """
        Update the DB with paired status
        """
        sql = """UPDATE sensor_ip SET is_paired = 1 WHERE ip = %s"""
        circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

        sql = """UPDATE lighting_ip SET is_paired = 1 WHERE ip = %s"""
        circadian.execute_dB_query(cursor, db, sql, ([lighting_ip]))

        """
        Establish sensor-light pair
        """
        sql = """INSERT INTO sensor_light_pairs(sensor_ip, lighting_ip) VALUES(%s ,%s)"""
        circadian.execute_dB_query(cursor, db, sql, ([local_ip, lighting_ip]))

        """
        Grab user's values
        """
        sql = """SELECT * FROM sensor_settings WHERE ip = %s"""
        temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = float(temp[0][2])/100

    else:
        """
        The sensor sub DOES have a pair. Grab what lighting sub
        it was connected to by searching the sensor_light_pairs
        table in the DB.
        """
        print "Reconnecting to previous Lighting Subsystem..."
        sql = """SELECT * FROM sensor_light_pairs WHERE sensor_ip = %s"""
        temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

        lighting_ip = temp[0][1]

        """
        Grab previous sensor sub settings
        """
        sql = """SELECT * FROM sensor_settings WHERE ip = %s"""
        temp = circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = float(temp[0][2])/100

        print "Sensor-Light pair re-established with values: ", temp[0]


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
signal.signal(4, handle_sleep_mode)
signal.signal(5, handle_wake_up)
signal.signal(6, catch_other_signals)
signal.signal(7, catch_other_signals)
signal.signal(8, catch_other_signals)
signal.signal(10, handle_pir_dB_connect)
signal.signal(11, handle_rgb_dB_connect)
signal.signal(12, handle_usr_dB_connect)
signal.signal(15, handle_send_circadian_dB_connect)
local_ip = circadian.get_ip()

"""
Establish DB connection
"""
print "\nBooting up..."
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
cursor = db.cursor()

"""
BOOT UP
"""
boot_up()
print "Boot up successful"
message = "Sensor Subsystem (" + local_ip + ") has booted successfully."
circadian.create_log(cursor, db, message, "None")
"""
Calc. user tables
"""
user_tuple = circadian.calc_user_tables(WAKE_UP_TIME, MASTER_CIRCADIAN_TABLE, MASTER_OFFSET_TABLE, MASTER_LUX_TABLE)
USER_CIRCADIAN_TABLE = user_tuple[0]
USER_OFFSET_TABLE = user_tuple[1]
USER_LUX_TABLE = user_tuple[2]
"""
Execute the other scripts here
"""
os.system("python pir_sensor.py &")
os.system("python rgb_sensor.py &")
os.system("python usr_sensor.py &")
os.system("python send_circadian_values.py &")
time.sleep(1)

"""
Alert other Python scripts that the wait cmd has connected
"""
pid_list = circadian.get_pids()
for pid in pid_list:
    os.kill(pid, 8)

"""
Wait for other sensor scripts to connect to the DB
"""
print "Establishing database connections..."
while not SEND_CIRCADIAN_DB_CONNECTED or not PIR_DB_CONNECTED or not USR_DB_CONNECTED or not RGB_DB_CONNECTED:
    time.sleep(1)

while True:
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
            try:
                wait_cmd_svr_sock_connection, wait_cmd_svr_sock_connection_addr = wait_cmd_svr_sock.accept()
            except:
                continue
            print '\nGot connection from', wait_cmd_svr_sock_connection_addr, "\n"

            """
            Receive the command on the socket
            """
            cmd = (wait_cmd_svr_sock_connection.recv(1024)).strip()
            cmd_str = cmd
            #current_minute = time.localtime()[3] * 60 + time.localtime()[4]
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

                """
                Get user ct values for delete cmd here.
                """
                sys_time = circadian.get_system_time()
                if not SLEEP_MODE:
                    delete_cmd = str(USER_CIRCADIAN_TABLE[sys_time][0])+"|"\
                                 +str(USER_CIRCADIAN_TABLE[sys_time][1])+"|"+str(USER_CIRCADIAN_TABLE[sys_time][2])+"|"
                else:
                    delete_cmd = "0|0|0|"

                delete_sock.send(delete_cmd)
                delete_sock.close()

                sql = """DELETE FROM sensor_ip WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

                sql = """DELETE FROM sensor_settings WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

                sql = """DELETE FROM sensor_status WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

                sql = """DELETE FROM sensor_light_pairs WHERE sensor_ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([local_ip]))

                sql = """DELETE FROM lighting_ip WHERE ip = %s"""
                circadian.execute_dB_query(cursor, db, sql, ([lighting_ip]))

                """
                Issue kill command to the scripts
                """
                os.system("python stop.py &")

            else:
                """
                If the control subsystem sent a command
                """

                if cmd[0] != 'N':
                    """
                    If the wake time field is NOT 'N' then recalculate
                    the USER_CIRCADIAN_TABLE
                    """
                    WAKE_UP_TIME = int(cmd[0])
                    """
                    Set ALL the things
                    """
                    user_tuple = circadian.calc_user_tables(WAKE_UP_TIME, MASTER_CIRCADIAN_TABLE, MASTER_OFFSET_TABLE,
                                                            MASTER_LUX_TABLE)
                    USER_CIRCADIAN_TABLE = user_tuple[0]
                    USER_OFFSET_TABLE = user_tuple[1]
                    USER_LUX_TABLE = user_tuple[2]

                if cmd[1] != 'N':
                    """
                    If the color threshold field is NOT 'N' then
                    set the new COLOR_THRESHOLD value
                    """
                    COLOR_THRESHOLD = float(cmd[1]) / 100
                """
                Write to config file
                """
                file = open("config.txt", "w")
                file.write(cmd_str)
                file.close()
                pid_list = circadian.get_pids()
                for pid in pid_list:
                    os.kill(pid, 3)

            wait_cmd_svr_sock_connection.close()
    except KeyboardInterrupt:
        sys.exit()