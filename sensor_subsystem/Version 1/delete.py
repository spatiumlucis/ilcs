import socket


sensor_to_lighting_cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # * Create a socket object
sensor_to_lighting_cli_sock_host = ''  # * Get lighting IP
sensor_to_lighting_cli_sock_port = 12349  # * Reserve a port for your service.
try:
    sensor_to_lighting_cli_sock.connect((sensor_to_lighting_cli_sock_host, sensor_to_lighting_cli_sock_port))
except:
    print "\nCould not connect to lighting subsystem\n"
sensor_to_lighting_cli_sock.send("D|")
sensor_to_lighting_cli_sock.close()
