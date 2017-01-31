

#     Author: Spatium Lucis
#Description: Receives light intensity value from control subsystem and updates light settings
#       Date: 11/7/2016
#Last Update: 11/7/2016

import socket
import wiringpi
import RPi.GPIO as GPIO
import time

port = 9090
ack_signal = 99
close_signal = -2
lightIntensity = -5

pinPWM = 18
pinRelay = 7

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pinRelay, GPIO.OUT)


wiringpi.wiringPiSetupGpio()
wiringpi.pinMode(pinPWM, 2)
wiringpi.pwmSetClock(5000)

sensor_ip = "192.168.1.4"
contol_ip = "192.168.1.6"
lighting_ip = "192.168.1.2"

port = 9090
    

def update_intensity(data):
    ###code to update the light
    if (int(data) == 0):
            GPIO.output(pinRelay, GPIO.LOW)
    else:
            GPIO.output(pinRelay, GPIO.HIGH)
            dutyCycle = (float(data)/100) * 1024
            wiringpi.pwmWrite(pinPWM, int(dutyCycle))
            

    time.sleep(1)
    global lightIntensity
    lightIntensity = data



sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((lighting_ip,port))

sock.listen(5)


while 1:
    clientsock, clientaddr = sock.accept()
    if(clientaddr[0] != sensor_ip):
            continue;
        
    clientfile  = clientsock.makefile("rw", 0)
    data = clientfile.readline().strip()
    print "Received: ", data, " from ", clientaddr

    if int(data) == close_signal:
        if(lightIntensity > 0):
                update_intensity(0)
        
        clientfile.close()
        clientsock.close()
        exit(1)
        
    #if data != lightIntensity:
    update_intensity(data)
    clientfile.close()
    clientsock.close()	

