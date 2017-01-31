import wiringpi
import RPi.GPIO as GPIO
import time


lightIntensity = -5
pinPWM = 18
pinRelay = 7


wiringpi.wiringPiSetupGpio()
wiringpi.pinMode(pinPWM, 2)
wiringpi.pwmSetClock(5000)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pinRelay, GPIO.OUT)
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


while 1:
    data = input("Enter intensity: ")
    if data < 0:
        break
    else:
        update_intensity(data)
