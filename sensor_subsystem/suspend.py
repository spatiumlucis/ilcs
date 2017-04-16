from subprocess import check_output
import os
import signal

def get_pid(name):
    return check_output(["pidof",name])

pid = get_pid("python")
temp = pid.split(" ")
print "pid: ", temp[1]
os.kill(int(temp[1]), signal.SIGTERM)