import time
import os
import signal
import subprocess

"""
Global Variables
"""
SLEEP_MODE = False

"""
Signal Handlers
"""
def handle_change_cmd(signum, stack):
    print "Changing parameter..."
    time.sleep(3)

def handle_send_compensation(signum, stack):
    print "sending compensation value..."
    time.sleep(3)

def handle_send_circadian(signum, stack):
    print "sending circadian value..."
    time.sleep(3)

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
"""
signal.signal(signal.SIGQUIT, handle_change_cmd)
signal.signal(signal.SIGIOT, handle_send_compensation)
signal.signal(7, handle_send_circadian)

begin_timer = time.time()

while True:
    current_timer = time.time()
    time_diff = int(current_timer - begin_timer)
    if time_diff >= 60 and not SLEEP_MODE:
        SLEEP_MODE = True
        rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
        send_circadian_pid = int(subprocess.check_output(['pgrep', '-f', 'send_circadian_values.py']))
        print "Should go to sleep mode", rgb_sensor_pid
        os.kill(rgb_sensor_pid, signal.SIGILL)
        os.kill(send_circadian_pid, signal.SIGILL)
        begin_timer = time.time()
    elif time_diff >= 60 and SLEEP_MODE:
        SLEEP_MODE = False
        rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
        send_circadian_pid = int(subprocess.check_output(['pgrep', '-f', 'send_circadian_values.py']))
        print "Should exit sleep mode", rgb_sensor_pid
        os.kill(rgb_sensor_pid, signal.SIGTRAP)
        os.kill(send_circadian_pid, signal.SIGTRAP)
        begin_timer = time.time()