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

GPIO.setup(pinRelay, GPIO.OUT)

wiringpi.pinMode(17, 17) #Red on pin 17
wiringpi.softPwmCreate(17,0,100) #Red PWM with 100Hz
wiringpi.pinMode(27, 27) #Green
wiringpi.softPwmCreate(27,0,100)
wiringpi.pinMode(22, 22) #Blue
wiringpi.softPwmCreate(22,0,100)

GPIO.setup(pinRelayS, GPIO.OUT) #secondary relay

wiringpi.pinMode(6, 6) #RedS on pin 29
wiringpi.softPwmCreate(6,0,100) #Red PWM with 100Hz
wiringpi.pinMode(13, 13) #GreenS
wiringpi.softPwmCreate(13,0,100)
wiringpi.pinMode(26, 26) #BlueS
wiringpi.softPwmCreate(26,0,100)

MASTER_CIRCADIAN_TABLE = []

def init_circadian_table():
    """
    This function is used for creating the master
    circadian table. The table is a list that has
    1440 locations (1 for each minute of the day).
    Each location is also a list of R, G, B brightness
    values. The value depends on what time of day it is.
    Between different ranges of time, there are different
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
    global pinRelayS
    init_circadian_table()
    timer = 313
    temp = 0
    GPIO.output(pinRelay, GPIO.HIGH)
    time.sleep(1)
    try:
        while True:
            # if timer == 1380:
            #     timer = 313
            print "Current Minute: ", timer
            print "Current Red: ",int(MASTER_CIRCADIAN_TABLE[timer][0])
            print "Current Green: ",int(MASTER_CIRCADIAN_TABLE[timer][1])
            print "Current Blue: ",int(MASTER_CIRCADIAN_TABLE[timer][2])
            
            wiringpi.softPwmWrite(17, int(MASTER_CIRCADIAN_TABLE[720][0]))
            #wiringpi.softPwmWrite(27, int(MASTER_CIRCADIAN_TABLE[timer][1]))
            #wiringpi.softPwmWrite(22, int(MASTER_CIRCADIAN_TABLE[timer][2]))

            #wiringpi.softPwmWrite(6, 12)
            #wiringpi.softPwmWrite(13, 12)
            #wiringpi.softPwmWrite(26, 12)

            while temp < 59:
                time.sleep(1)
                temp +=1
            temp = 0
            #timer += 1
    except KeyboardInterrupt:
        GPIO.output(pinRelay, GPIO.LOW)

boot_up()
