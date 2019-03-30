import datetime
import enum
import os
import queue
import subprocess
import threading
import time

from skimage import measure
import cv2
import numpy

import events


THRESHOLD0 = .72
THRESHOLD1 = .9


def capture_from_usb(event_queue, kill_queue, cam_num):
    THRESHOLD=THRESHOLD0 if cam_num == 0 else THRESHOLD1
    process = subprocess.Popen(
        ['ffmpeg -loglevel panic -f v4l2 -r 15 -video_size 320x180 -i /dev/video{} -f mjpeg -'.format(cam_num)], stdout=subprocess.PIPE, shell=True, bufsize=10**8)
    bytes_str = b''
    last_img = None
    last_two = []
    total = 0
    stopped = False
    stop_time = None
    while True:
        try:
            kill_queue.get(False)
            break
        except queue.Empty:
            pass
        bytes_str += process.stdout.read(1024)
        if stopped and datetime.datetime.now() - stop_time > datetime.timedelta(seconds=2):
            stopped = False
        a = bytes_str.find(b'\xff\xd8')
        b = bytes_str.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes_str[a:b+2]
            bytes_str = bytes_str[b+2:]
            img = cv2.imdecode(numpy.fromstring(jpg, dtype=numpy.uint8), cv2.IMREAD_GRAYSCALE)
            img = img[95:145] if cam_num == 0 else img[70:190]
            if last_img is not None:
                score, _ = measure.compare_ssim(
                    img, last_img, full=True)
                if len(last_two) == 2:
                    total -= last_two.pop(0)
                last_two.append(score)
                total += score
                if not stopped and len(last_two) == 3 and total / 2 < THRESHOLD:
                    print(total/2)
                    print(last_two)
                    print('motion detected usb {} !'.format(cam_num))
                    event_queue.put(
                        (events.EventTypes.USB_MOTION0 if cam_num == 0 else events.EventTypes.USB_MOTION1, datetime.datetime.now()))
                    os.kill(process.pid, subprocess.signal.SIGSTOP)
                    stopped = True
                    stop_time = datetime.datetime.now()
            last_img = img
