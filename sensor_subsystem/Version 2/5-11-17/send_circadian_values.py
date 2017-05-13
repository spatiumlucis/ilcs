import time
import os
import signal
import subprocess
import circadian

"""
Global variables
"""
SLEEP_MODE = False
COLOR_THRESHOLD = 0
MASTER_CIRCADIAN_TABLE = circadian.init_circadian_table()

"""
Signal Handlers
"""
def handle_change_cmd(signum, stack):
    print "Changing parameter..."
    time.sleep(3)

def handle_sleep_mode(signum, stack):
    global SLEEP_MODE
    SLEEP_MODE = True
    print "Entering sleep mode..."
    while SLEEP_MODE:
        print "sleeping..."
        time.sleep(3)

def handle_wake_up(signum, stack):
    global SLEEP_MODE
    SLEEP_MODE = False
    print "Exiting sleep mode..."

def handle_send_compensation(signum, stack):
    print "sending compensation value..."
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
SIGEMT: kill -7 is for sending circadian values
"""
signal.signal(signal.SIGQUIT, handle_change_cmd)
signal.signal(signal.SIGILL, handle_sleep_mode)
signal.signal(signal.SIGTRAP, handle_wake_up)
signal.signal(signal.SIGIOT, handle_send_compensation)

begin_timer = time.time()

while True:
    current_timer = time.time()
    time_diff = int(current_timer - begin_timer)
    if time_diff >= 60:
        rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
        pir_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'pir_sensor.py']))
        print "Sending circadian", rgb_sensor_pid, pir_sensor_pid
        os.kill(rgb_sensor_pid, 7)
        os.kill(pir_sensor_pid, 7)
        begin_timer = time.time()
