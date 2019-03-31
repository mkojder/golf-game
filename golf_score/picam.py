import datetime
import time

import numpy
import picamera
import picamera.array

import events

VECTORS=10
THRESHOLD=88

# 45 rows

class DetectMotion(picamera.array.PiMotionAnalysis):

    def __init__(self, camera, event_queue):
        super().__init__(camera)
        self.event_queue = event_queue
        self.first = True

    def analyze(self, a):
        #a = a[15:18]
        a = numpy.sqrt(
            numpy.square(a['x'].astype(numpy.float)) +
            numpy.square(a['y'].astype(numpy.float))
        ).clip(0, 255).astype(numpy.uint8)
        # If there're more than 10 vectors with a magnitude greater
        # than 60, then say we've detected motion
        if (a > THRESHOLD).sum() > VECTORS:
            if self.first:
                self.first = False
            else:
                print('picam')
                self.event_queue.put(
                    (events.EventTypes.PICAM_MOTION, datetime.datetime.now()))
                self.first = True


def run_picamera_loop(event_queue, thread_kill):
    with picamera.PiCamera() as camera:
        with DetectMotion(camera, event_queue) as output:
            camera.resolution = (640, 480)
            event_queue.put((events.EventTypes.IGNORE_PERIOD, datetime.datetime.now()))
            camera.start_recording(
                '/dev/null', format='h264', motion_output=output)
            while not thread_kill.is_kill():
                camera.wait_recording()
                time.sleep(.2)
            camera.stop_recording()
