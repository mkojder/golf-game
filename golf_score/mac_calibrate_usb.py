from skimage import measure
import cv2
import numpy
import subprocess

last_image = None
count = 1
process = subprocess.Popen(
    ['ffmpeg  -f avfoundation -r 30 -i "0" -f mjpeg -'], stdout=subprocess.PIPE, shell=True, bufsize=10**8)
bytes_str = b''
while True:
    bytes_str += process.stdout.read(1024)
    a = bytes_str.find(b'\xff\xd8')
    b = bytes_str.find(b'\xff\xd9')
    if a != -1 and b != -1:
        jpg = bytes_str[a:b+2]
        bytes_str = bytes_str[b+2:]
        img = cv2.imdecode(numpy.fromstring(jpg, dtype=numpy.uint8), cv2.IMREAD_GRAYSCALE)
        img = img[95:145, 100:220]
        cv2.imshow('cropped', img)
        cv2.waitKey(0)
        if last_image is not None:
            (score, diff) = measure.compare_ssim(
                img, last_image, full=True)
            print(score)
        last_image = img
