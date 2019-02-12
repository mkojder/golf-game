import time
import numpy
import picamera
import picamera.array

class DetectMotionCalibrate(picamera.array.PiMotionAnalysis):
    
    def __init__(self, camera):
        super().__init__(camera)
        self.first = True

    def analyze(self, a):
        a = a[17:18]
        a = numpy.sqrt(
            numpy.square(a['x'].astype(numpy.float)) +
            numpy.square(a['y'].astype(numpy.float))
        ).clip(0, 255).astype(numpy.uint8)
        # If there're more than 10 vectors with a magnitude greater
        # than 60, then say we've detected motion
        if (a > 88).sum() > 10:
            if self.first:
                self.first = False
            else:
                print('Motion detected picamera!')
                self.first = True


with picamera.PiCamera() as camera:
    with DetectMotionCalibrate(camera) as output:
        camera.resolution = (1280, 720)
        #camera.start_preview()
        camera.start_recording(
            '/dev/null', format='h264', motion_output=output)
        time.sleep(60)
        #camera.stop_preview()
        camera.stop_recording()
