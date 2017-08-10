from subprocess import check_output
import os
import signal
import time
import socket
import threading
import RPi.GPIO as GPIO
import MySQLdb #Required for MySQL stuff
import wiringpi
import sys
import os
import signal

def get_pid(name):
    return check_output(["pidof",name])

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

wiringpi.pinMode(29, 29) #RedS on pin 29
wiringpi.softPwmCreate(17,0,100) #Red PWM with 100Hz
wiringpi.pinMode(31, 31) #GreenS
wiringpi.softPwmCreate(27,0,100)
wiringpi.pinMode(33, 33) #BlueS
wiringpi.softPwmCreate(22,0,100)

wiringpi.softPwmWrite(17, 0)
wiringpi.softPwmWrite(27, 0)
wiringpi.softPwmWrite(22, 0)
wiringpi.softPwmWrite(29, 0)
wiringpi.softPwmWrite(31, 0)
wiringpi.softPwmWrite(33, 0)
time.sleep(1)
GPIO.output(pinRelay, GPIO.LOW)
GPIO.output(pinRelayS, GPIO.LOW)
pid = get_pid("python")
temp = pid.split(" ")
print "pid: ", temp[1]
os.kill(int(temp[1]), signal.SIGTERM)