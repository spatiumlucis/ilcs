import wiringpi
import RPi.GPIO as GPIO
from time import sleep

pinRelay = 4

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

GPIO.output(pinRelay, GPIO.HIGH)

pause_time = 0.02


try:
    while True:

        red.ChangeDutyCycle(50)
        green.ChangeDutyCycle(50)
        blue.ChangeDutyCycle(50)
        #for i in range(0,101):
        #    red.ChangeDutyCycle(i)
        #    green.ChangeDutyCycle(100-i)
        #    blue.ChangeDutyCycle(i)
        #    sleep(pause_time)
        #for i in range(100,-1,-1):
        #    red.ChangeDutyCycle(i)
        #    green.ChangeDutyCycle(100-i)
        #    blue.ChangeDutyCycle(i)
        #    sleep(pause_time)

except KeyboardInterrupt:
    GPIO.output(pinRelay, GPIO.HIGH)
    red.stop()
    green.stop()
    blue.stop()
    GPIO.cleanup()
