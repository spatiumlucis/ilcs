from subprocess import check_output
import os
import signal
import MySQLdb
import socket
def get_pid(name):
    return check_output(["pidof",name])
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

pid = get_pid("python")
temp = pid.split(" ")
print "pid: ", temp[1]
os.kill(int(temp[1]), signal.SIGTERM)