import subprocess
import os
import signal
import MySQLdb
import socket


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

local_ip = get_ip()

"""
Establish DB connection
"""
print "Establishing boot up database connection.....\n"
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
print "Boot up database connection established.\n"
# prepare a cursor object using cursor() method
cursor = db.cursor()
sql = """UPDATE sensor_status SET being_serviced = 1 WHERE ip = %s"""
try:
    cursor.execute(sql, ([local_ip]))
    db.commit()
except (AttributeError, MySQLdb.OperationalError):
    """
    If the DB connection was lost
    """
    print "Trying to reconnect to database in PIR thread..."
    db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                         db="ilcs")
    print "Database connection re-established in PIR thread."
    cursor = db.cursor()

    try:
        """
        Try to update DB again
        """
        cursor.execute(sql, ([local_ip]))
        db.commit()
    except:
        db.rollback()
except:
    db.rollback()

try:
    pir_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'pir_sensor.py']))
    os.kill(pir_sensor_pid, 9)
except:
    print "PIR dead already"
try:
    rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
    os.kill(rgb_sensor_pid, 9)
except:
    print "rgb dead already"
try:
    usr_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'usr_sensor.py']))
    os.kill(usr_sensor_pid, 9)
except:
    print "usr dead already"
try:
    send_circadian_pid = int(subprocess.check_output(['pgrep', '-f', 'send_circadian_values.py']))
    os.kill(send_circadian_pid, 9)
except:
    print "send dead already"
try:
    wait_pid = int(subprocess.check_output(['pgrep', '-f', 'wait_for_cmd.py']))
    os.kill(wait_pid, 9)
except:
    print "wait dead already"

os.system("clear")
print "System paused. Press the Enter key to continue..."