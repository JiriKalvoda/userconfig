#!/bin/env python3

from threading import Thread
import subprocess
from time import sleep
from datetime import datetime

exit_thread = False

suspend_times = []

def threaded_function():
    while True:
        if exit_thread:
            return
        print(f"{datetime.now()} Press ESC")
        p = subprocess.run(["xdotool", "key", "Escape"])
        t = datetime.now()
        suspend_times.append(t)
        print(f"{t}: doing suspend!")
        p = subprocess.run(["systemctl", "suspend", "-i"])
        for i in range(15):
            if exit_thread:
                return
            sleep(1)


thread = Thread(target=threaded_function)
thread.start()


p = subprocess.run(["xtrlock"])
exit_thread = True
msg = ["Unlocked", f"Suspender: suspend done {len(suspend_times)} times"]
print("\n".join(msg))
p = subprocess.run(["osdc", *msg])
