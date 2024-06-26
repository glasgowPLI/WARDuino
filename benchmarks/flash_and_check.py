"""
Write a file to the serial device and count the number of seconds
between the emmission of "START" and "DONE".
"""

import serial
import serial.tools.list_ports
import time
import sys
import math


def await_output(s: serial.Serial, target: str, failure=None):
    target = target.encode('utf-8')
    if failure:
        failure = failure.encode('utf-8')
    curpos: int = 0
    while True:
        x = s.read()
        print(x.decode('utf-8', 'replace'), end="", file=sys.stderr)
        x = x[0]
        if x == b'\r'[0]:
            continue
        if curpos < len(target) and x == target[curpos]:
            curpos += 1
            if curpos == len(target):
                curpos = 0
                return True
        elif failure and x == failure[curpos]:
            curpos += 1
            if curpos == len(failure):
                curpos = 0
                return False
        else:
            curpos = 0


if __name__ == "__main__":
    port = None
    ports = [port.device for port in serial.tools.list_ports.comports()]
    if not ports:
        print("Device not found!")
        exit(1)
    elif len(ports) > 1:
        print("More than one serial port found!")
        for i in range(len(ports)):
            print(f"{i}: {ports[i]}")
        port = ports[int(input(f"Select port [0-{len(ports) - 1}]:"))]
    else:
        port = ports[0]
    print(f"using {port}", file=sys.stderr)


    with serial.Serial(port, 115200) as serial:
        if len(sys.argv) == 2:
            print("Await start", file=sys.stderr)
            await_output(serial, "START\n")
            startTime = time.monotonic()
            print("START found, waiting for DONE", file=sys.stderr)
            success = await_output(serial, "DONE\n", failure="Guru Meditation Error")
            if success:
                endTime = time.monotonic()
                print(f"{sys.argv[1]}: iterations=1 runtime: {math.floor((endTime - startTime) * 1000000)}us")
            else:
                print("\nnan")

