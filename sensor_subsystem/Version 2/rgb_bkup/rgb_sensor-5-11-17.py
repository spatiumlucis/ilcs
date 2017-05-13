import time
import os
import signal
import subprocess

"""
Global variables
"""
SLEEP_MODE = False
COLOR_THRESHOLD = 0

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
    time.sleep(0.5)

def handle_wake_up(signum, stack):
    global SLEEP_MODE
    SLEEP_MODE = False
    print "Exiting sleep mode..."
    time.sleep(0.5)

"""
Non-Signal Handler Functions
"""
##

"""
Signal declarations (software interrupts)
SIGQUIT: kill -3 is for when user changes parameter
SIGILL: kill -4 is for when the system entered sleep mode
SIGTRAP: kill -5 is for when the system exits sleep mode
"""
signal.signal(signal.SIGQUIT, handle_change_cmd)
signal.signal(signal.SIGILL, handle_sleep_mode)
signal.signal(signal.SIGTRAP, handle_wake_up)

while True:
    if SLEEP_MODE:
        print "I'm sleeping..."
    else:
        print "I'm reading from the RGB..."
    time.sleep(3)
