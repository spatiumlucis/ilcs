import time
import socket
import threading
import RPi.GPIO as GPIO
import MySQLdb #Required for MySQL stuff
import wiringpi
import sys
import os
import signal


GPIO.setwarnings(False)
pinRelay = 4
pinRelayS = 5

wiringpi.wiringPiSetupGpio()
GPIO.setmode(GPIO.BCM) #choose BCM or BOARD numbering schemes
GPIO.setup(17, GPIO.OUT) #set GIPO 17 as red led
GPIO.setup(27, GPIO.OUT) #set GIPO 27 as green led
GPIO.setup(22, GPIO.OUT) #set GIPO 22 as blue led
GPIO.setup(pinRelay, GPIO.OUT)

red = GPIO.PWM(17, 100) #create object red for PWM on port 17 at 100Hz
green = GPIO.PWM(27, 100) #create object red for PWM on port 27 at 100Hz
blue = GPIO.PWM(22, 100) #create object red for PWM on port 22 at 100Hz

red.start(0)
green.start(0)
blue.start(0)

GPIO.setup(29, GPIO.OUT) #set GIPO 17 as red led
GPIO.setup(31, GPIO.OUT) #set GIPO 27 as green led
GPIO.setup(33, GPIO.OUT) #set GIPO 22 as blue led
GPIO.setup(pinRelayS, GPIO.OUT) #secondary relay

redS = GPIO.PWM(29, 100) #create object red for PWM on port 17 at 100Hz
greenS = GPIO.PWM(31, 100) #create object red for PWM on port 27 at 100Hz
blueS = GPIO.PWM(33, 100) #create object red for PWM on port 22 at 100Hz

redS.start(0)
greenS.start(0)
blueS.start(0)

MASTER_CIRCADIAN_TABLE = []

def init_circadian_table():
    """
    This function is used for creating the master
    circadian table. The table is a list that has
    1440 locations (1 for each minute of the day).
    Each location is also a list of R, G, B brightness
    values.The value depends on what time of day is is.
    Between different ranges of time there are different
    linear functions for the brightness values.
    NOTE: This table is calculated for a person that wakes
    up at 7AM (420 min) and goes to sleep at 11 PM (1380 min).

    :return: None
    """
    """
    Import global MASTER_CIRCADIAN_TABLE so that it can be edited
    """
    global MASTER_CIRCADIAN_TABLE

    colors = []

    t = 0

    while t < 1440:
        """
        The colors list is always filled in the order R, G, B.
        Afterwards it is appended to the MASTER_CIRCADIAN_TABLE
        """
        if t >= 300 and t <= 420:

            colors.append((((135.0 / 120) * t - 337.5) / 255) * 100)

            colors.append((((206.0 / 120) * t - 515) / 255) * 100)

            colors.append((((250.0 / 120) * t - 625) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []

        elif t >= 420 and t <= 720:
            colors.append((((120.0 / 300) * t - 33) / 255) * 100)

            colors.append((((49.0 / 300) * t + 137.4) / 255) * 100)

            colors.append((((5.0 / 300) * t + 243) / 255) * 100)


            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []
        elif t >= 720 and t <= 1140:
            colors.append((((-2.0 / 420) * t + 258.429) / 255) * 100)

            colors.append((((-161.0 / 420) * t + 531) / 255) * 100)

            colors.append((((-172.0 / 420) * t + 549.857) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []
        elif t >= 1140 and t <= 1380:
            colors.append((((-253.0 / 240) * t + 1454.75) / 255) * 100)

            colors.append((((-94.0 / 240) * t + 540.5) / 255) * 100)

            colors.append((((-83.0 / 240) * t + 477.25) / 255) * 100)


            MASTER_CIRCADIAN_TABLE.append(colors)

            colors = []

        else:
            colors.append(0)

            colors.append(0)

            colors.append(0)


            MASTER_CIRCADIAN_TABLE.append(colors)

            colors = []


        t += 1

def boot_up():
    global MASTER_CIRCADIAN_TABLE
    global red
    global green
    global blue
    global pinRelay
    init_circadian_table()
    timer = 300
    GPIO.output(pinRelay, GPIO.HIGH)
    try:
        while True:
            if timer > 1380:
                timer = 300

            red.ChangeDutyCycle(MASTER_CIRCADIAN_TABLE[timer][0] / 2)
            green.ChangeDutyCycle(MASTER_CIRCADIAN_TABLE[timer][1] / 2)
            blue.ChangeDutyCycle(MASTER_CIRCADIAN_TABLE[timer][2] / 2)
            time.sleep(0.005)

            timer += 1
    except KeyboardInterrupt:
        GPIO.output(pinRelay, GPIO.LOW)

boot_up()