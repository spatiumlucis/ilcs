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
##

"""
Non-Signal Handler Functions
"""
##

begin_timer = time.time()

while True:
    current_timer = time.time()
    time_diff = int(current_timer - begin_timer)
    if time_diff >= 60 and not SLEEP_MODE:
        SLEEP_MODE = True
        rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
        print "Should go to sleep mode", rgb_sensor_pid
        os.kill(rgb_sensor_pid, signal.SIGILL)
        begin_timer = time.time()
        time.sleep(3)
    elif time_diff >= 60 and SLEEP_MODE:
        SLEEP_MODE = False
        rgb_sensor_pid = int(subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py']))
        print "Should exit sleep mode", rgb_sensor_pid
        os.kill(rgb_sensor_pid, signal.SIGTRAP)
        begin_timer = time.time()