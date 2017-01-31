#Code derived from bradsrpi.blogspot.com


import smbus
import time
bus = smbus.SMBus(1)
#I2C address 0x29
#Register address must be OR'ed wit 0x80
bus.write_byte(0x29,0x80|0x12)
ver = bus.read_byte(0x29)
#version # should be 0x44

hardRed=11850
hardGreen=24108
hardBlue=22985
hardClear=60280
hardLux=17378

if ver == 0x44:
    print "Device found\n"
    bus.write_byte(0x29, 0x80|0x00) #0x00 = ENABLE register
    bus.write_byte(0x29, 0x01|0x02) #0x01 = Power on, 0x02 RGB sensors enabled
    bus.write_byte(0x29, 0x80|0x14) #Reading results start register 14, LSB then MSB
    while True:
        data = bus.read_i2c_block_data(0x29, 0)
        clear = clear = data[1] << 8 | data[0]
        red = data[3] << 8 | data [2]
        green = data[5] << 8 | data [4]
        blue = data[7] << 8 | data[6]
        lux = int((-0.32466*red) + (1.57837*green) + (-0.73191 * blue))
        crgbl = "C: %s, R: %s, G: %s, B: %s, Lux: %s" % (clear, red, green, blue, lux)
        print crgbl
        if red >= 10 and red < (hardRed*.95):
            redFlag = True
            print "Red Degradation"
        else:
            redFlag = False
        if green >= 10 and green < (hardGreen*.95):
            greenFlag = True
            print "Green Degradation"
        else:
            greenFlag = False
        if blue >= 10 and blue < (hardBlue*.95):
            blueFlag = True
            print "Blue Degradation"
        else:
            blueFlag = False
        if clear >= 10 and clear < (hardClear*.95):
            clearFlag = True
            print "Clear Degradation"
        else:
            clearFlag = False
        if lux >= 10 and lux < (hardLux*.95):
            luxFlag = True
            print "Intensity Degradation\n"
        if lux < 10:
            luxFlag = False
            print "Lights OFF\n"
        else:
            luxFlag = False
        time.sleep(2)
    else:
        print "Device not found\n"
