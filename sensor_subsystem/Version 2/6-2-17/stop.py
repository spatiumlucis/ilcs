import subprocess
import os
import time
time.sleep(2)
os.system("fg")
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
print "System killed. Press the Enter key to continue..."