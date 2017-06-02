import time
import os
import signal
import subprocess
import circadian
import MySQLdb

"""
Global variables
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

"""
Signal Handlers
"""

def handle_send_compensation(signum, stack):
    print "sending compensation value..."
    time.sleep(3)

def handle_send_circadian(signum, stack):
    print "sending circadian value..."
    time.sleep(3)

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
    # global is_sensor_sub_paired
    # global lighting_ip
    global COLOR_THRESHOLD
    # global LIGHT_THRESHOLD
    global WAKE_UP_TIME
    # global SLEEP_MODE_STATUS
    global db
    global cursor

    print "Booting up..."

    local_ip = get_ip()

    """
    Check DB if the sensor sub exists
    """
    sql = "SELECT * FROM sensor_ip WHERE ip = " + local_ip
    temp = execute_db_query(cursor, db, sql)

    if len(temp) == 0:
        """
        The sensor sub does NOT exist in the DB so insert it into
        the sensor_ip and sensor_status tables
        """
        sql = "INSERT INTO sensor_ip(ip, is_paired) VALUES(" + local_ip + ", 0)"

        execute_db_query(cursor, db, sql)
    else:
        """
        The sensor sub DOES exist in the DB. Grab its paired status
        """
        is_sensor_sub_paired = temp[0][1]

        """
        Check degrade status for red
        """
        sql = "SELECT * FROM sensor_status WHERE ip = " + local_ip
        temp = execute_db_query(cursor, db, sql)

        is_sensor_service = temp[0][11]
        is_being_serviced = temp[0][12]
        is_red_deg = temp[0][5]
        is_green_deg = temp[0][6]
        is_blue_deg = temp[0][7]
        is_lumen_deg = temp[0][8]
        sql = "UPDATE sensor_status SET distance = 8 WHERE ip = " + local_ip
        execute_db_query(cursor, db, sql)

        if is_sensor_service:
            sql = "UPDATE sensor_status SET service = 0 WHERE ip = " + local_ip
            execute_db_query(cursor, db, sql)
        if is_being_serviced:
            sql = "UPDATE sensor_status SET being_serviced = 0 WHERE ip = " + local_ip
            execute_db_query(cursor, db, sql)
        if is_red_deg:
            sql = "UPDATE sensor_status SET red_degraded = 0 WHERE ip = " + local_ip
            execute_db_query(cursor, db, sql)
        if is_green_deg:
            sql = "UPDATE sensor_status SET green_degraded = 0 WHERE ip = " + local_ip
            execute_db_query(cursor, db, sql)
        if is_blue_deg:
            sql = "UPDATE sensor_status SET blue_degraded = 0 WHERE ip = " + local_ip
            execute_db_query(cursor, db, sql)
        if is_lumen_deg:
            sql = "UPDATE sensor_status SET lumens_degraded = 0 WHERE ip = " + local_ip
            execute_db_query(cursor, db, sql)

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

        sql = "INSERT INTO sensor_status(ip, red, green, blue, lumens, red_degraded, green_degraded, blue_degraded, lumens_degraded, sleep_mode_status, distance, service, being_serviced) VALUEs(" + local_ip + ", 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0)"
        execute_db_query(cursor,db, sql)

        """
        Grab the lighting sub IP to be paired with.
        """
        sql = "SELECT * from lighting_ip where is_paired = 0"
        temp = execute_db_query(cursor, db, sql)
        lighting_ip = temp[0][0]

        """
        Update the DB with paired status
        """
        sql = "UPDATE sensor_ip SET is_paired = 1 WHERE ip = " + local_ip
        execute_db_query(cursor, db, sql)

        sql = "UPDATE lighting_ip SET is_paired = 1 WHERE ip = " + lighting_ip
        execute_db_query(cursor, db, sql)

        """
        Establish sensor-light pair
        """
        sql = "INSERT INTO sensor_light_pairs(sensor_ip, lighting_ip) VALUES(" + local_ip + "," + lighting_ip + ")"
        execute_db_query(cursor, db, sql)

        """
        Grab user's values
        """
        sql = "SELECT * FROM sensor_settings WHERE ip = " + local_ip
        temp = execute_db_query(cursor, db, sql)

        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = float(temp[0][2])/100

    else:
        """
        The sensor sub DOES have a pair. Grab what lighting sub
        it was connected to by searching the sensor_light_pairs
        table in the DB.
        """
        print "Reconnecting to previous Lighting Subsystem..."
        sql = "SELECT * FROM sensor_light_pairs WHERE sensor_ip = " + local_ip
        temp = execute_db_query(cursor, db, sql)

        lighting_ip = temp[0][1]

        """
        Grab previous sensor sub settings
        """
        sql = "SELECT * FROM sensor_settings WHERE ip = " + local_ip
        temp = execute_db_query(cursor, db, sql)

        WAKE_UP_TIME = temp[0][1]
        COLOR_THRESHOLD = float(temp[0][2])/100

        print "Sensor-Light pair re-established with values: ", temp[0]
        # sql = "SELECT * FROM sensor_status WHERE ip = " + local_ip
        # temp = execute_db_query(cursor, db, sql)
        # SLEEP_MODE_STATUS = temp[0][9]

    """
    Calculate the user's circadian table for the sensor sub to use.
    """
    calc_user_circadian_table(change_par_Event, finalize_change_Event)

    #sql = """INSERT INTO system_logs(time, message, user) VALUES(%s, %s, %s)"""

    current_time = datetime.datetime.now()
    current_time = current_time.strftime("%Y-%m-%d %H:%M")

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
SIGEMT: kill -7 is for sending circadian values
"""
signal.signal(signal.SIGIOT, handle_send_compensation)
signal.signal(7, handle_send_circadian)
local_ip = get_ip()


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
            # print "current values", WAKE_UP_TIME, " ", COLOR_THRESHOLD, " ", LIGHT_THRESHOLD
            wait_cmd_svr_sock_connection, wait_cmd_svr_sock_connection_addr = wait_cmd_svr_sock.accept()  # * Establish connection w
            print '\nGot connection from', wait_cmd_svr_sock_connection_addr, "\n"

            """
            Receive the command on the socket
            """
            cmd = (wait_cmd_svr_sock_connection.recv(1024)).strip()

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
                delete_cmd = ["0", "0", "0"]

                delete_sock.send(delete_cmd)
                delete_sock.close()

                sql = "DELETE FROM sensor_ip WHERE ip = " + local_ip
                execute_db_query(cursor, db, sql)

                sql = "DELETE FROM sensor_settings WHERE ip = " + local_ip
                execute_db_query(cursor, db, sql)

                sql = "DELETE FROM sensor_status WHERE ip = " + local_ip
                execute_db_query(cursor, db, sql)

                sql = "DELETE FROM sensor_light_pairs WHERE sensor_ip = " + local_ip
                execute_db_query(cursor, db, sql)

                sql = "DELETE FROM lighting_ip WHERE ip = " + lighting_ip
                execute_db_query(cursor, db, sql)

                """
                Issue kill command to the scripts
                """
                rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
                pir_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'pir_sensor.py']))
                send_circadian_pid = int(subprocess.check_output(['pgrep', '-f', 'send_circadian_values.py']))
                os.kill(rgb_sensor_pid, signal.SIGINT)
                os.kill(pir_sensor_pid, signal.SIGINT)
                os.kill(send_circadian_pid, signal.SIGINT)
                pid = os.getpid()
                os.kill(pid, signal.SIGINT)
            else:
                """
                If the control subsystem sent a command string then
                set the change_par_Event so that other threads pause.
                """

                if cmd[0] != 'N':
                    """
                    If the wake time field is NOT 'N' then recalculate
                    the USER_CIRCADIAN_TABLE
                    """
                    WAKE_UP_TIME = int(cmd[0])

                if cmd[1] != 'N':
                    """
                    If the color threshold field is NOT 'N' then
                    set the new COLOR_THRESHOLD value
                    """
                    COLOR_THRESHOLD = float(cmd[1]) / 100

                rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
                pir_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'pir_sensor.py']))
                send_circadian_pid = int(subprocess.check_output(['pgrep', '-f', 'send_circadian_values.py']))
                os.kill(rgb_sensor_pid, signal.SIGQUIT)
                os.kill(pir_sensor_pid, signal.SIGQUIT)
                os.kill(send_circadian_pid, signal.SIGQUIT)

            wait_cmd_svr_sock_connection.close()
    except KeyboardInterrupt:

        sys.exit()