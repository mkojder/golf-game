from skimage import measure
import cv2
import numpy
import subprocess


THRESHOLD = .8
last_image = None
count = 1
process = subprocess.Popen(
    ['ffmpeg -loglevel panic  -f v4l2 -r 30 -i /dev/video1 -f mjpeg -'], stdout=subprocess.PIPE, shell=True, bufsize=10**8)
bytes_str = b''
last_three = []
total = 0
while True:
    bytes_str += process.stdout.read(1024)
    a = bytes_str.find(b'\xff\xd8')
    b = bytes_str.find(b'\xff\xd9')
    if a != -1 and b != -1:
        jpg = bytes_str[a:b+2]
        bytes_str = bytes_str[b+2:]
        img = cv2.imdecode(numpy.fromstring(jpg, dtype=numpy.uint8), cv2.IMREAD_GRAYSCALE)
        img = img[95:145]
        #cv2.imshow('cropped', img)
        #cv2.waitKey(0)
        if last_image is not None:
            score, _ = measure.compare_ssim(
                img, last_image, full=True)
            if len(last_three) == 3:
                total -= last_three.pop(0)
            last_three.append(score)
            total += score
            if len(last_three) == 3 and total / 3 < THRESHOLD:
                print('motion')

        last_image = img
