import threading
import time
import os
import signal
from functools import partial

int_event_mutex = threading.Lock()

def begin_threading():

    int_event = threading.Event()
    signal.signal(signal.SIGUSR1, partial(handle_signal, int_event))

    try:
        #print "Starting PIR thread..."
        pir_thread = threading.Thread(name='pir_thread', target=PIR_sensor, args=(int_event,))
        pir_thread.start()
    except:
        print "Error: unable to start pir thread"

    main_func(int_event)

def PIR_sensor(int_event):
    count = 0
    while True:
        int_event_mutex.acquire()
        try:
            status = int_event.isSet()
        finally:
            int_event_mutex.release()
        if not status:
            print "Sitting in PIR_sensor thread"
        time.sleep(3)

def handle_signal(int_Event, signum, stack):
    print "Got signal", signum
    int_event_mutex.acquire()
    try:
        int_Event.set()
    finally:
        int_event_mutex.release()
    time.sleep(10)
    int_Event.clear()

def main_func(int_event):
    start_time = time.time()
    while True:
        current_time = time.time()
        if current_time - start_time >= 60:
            print "Diff", current_time-start_time
            pid = os.getpid()
            os.kill(pid, signal.SIGUSR1)
            start_time = time.time()

begin_threading()