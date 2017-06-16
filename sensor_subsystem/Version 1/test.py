import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
pir = 12
GPIO.setup(pir, GPIO.IN)
print "Waiting for PIR sensor to settle..."
time.sleep(2)
sleep_time = 0
wake_time = 0
timer = 0
sleep = False
false_positive = False
false_count = 0

try:
    while True:
        if timer == 60:
            sleep = True
            timer += 1
            sleep_time = int(time.time())
            print "sleep",sleep_time, sleep
        if GPIO.input(pir):
            print "Motion Detected"
            time.sleep(1)
            timer = 0
            # wake_time = int(time.time())
            # # time.sleep(1)
            # # false_list = []
            # # n = 45
            # # while n < 60:
            # #     if not ((wake_time - sleep_time) % n):
            # #         false_list.append(1)
            # #     else:
            # #         false_list.append(0)
            # #     n += 1
            # if (wake_time - sleep_time) >= 45 and (wake_time-sleep_time) <= 59:
            #     print "false positive", sleep
            # else:
            #     # sleep = False
            #     # false_positive = False
            #     # false_count = 0
            #     timer = 0
            #     # wake_time = int(time.time())
            #     # print "Detected motion",wake_time, sleep
            #     print "Diff", wake_time - sleep_time
            #time.sleep(2)

        else:
            if timer < 60:
                timer += 1
                time.sleep(1)
                print "no motion", timer
except KeyboardInterrupt:
    GPIO.cleanup()
    print "Done"