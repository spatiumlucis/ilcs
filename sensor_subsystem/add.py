import socket
import MySQLdb
print "Establishing Database connection.....\n"
db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis", db="ilcs")
print "Database connection established.\n"
cursor = db.cursor()
sql = """INSERT INTO sensor_settings VALUES('192.168.1.4', 0, 0, 0, 'test')"""
try:
    cursor.execute(sql)
    db.commit()
except:
    db.rollback()
sensor_to_lighting_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # * Create a socket object
sensor_to_lighting_cli_sock_host = ''  # * Get lighting IP
sensor_to_lighting_cli_sock_port = 12348  # * Reserve a port for your service.
try:
    sensor_to_lighting_cli_sock.connect((sensor_to_lighting_cli_sock_host, sensor_to_lighting_cli_sock_port))
except:
    print "\nCould not connect to lighting subsystem\n"
sensor_to_lighting_cli_sock.close()
