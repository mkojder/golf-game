from tkinter import Tk, BOTH
import multiprocessing
import os
import queue
import sqlite3
import threading

import events
import game_state
import picam
import ui
import usb_camera

def main():
    input_queue = multiprocessing.Queue()
    event_queue = multiprocessing.Queue()
    root = Tk()
    root.geometry("450x300")
    game_ui = ui.UI(root, event_queue)
    game_ui.pack(fill=BOTH, expand=True)
    # Start the thread that will look for input from the picamera
    picam_kill = events.ThreadKill()
    run_cam_thread = threading.Thread(
        target=picam.run_picamera_loop, args=(event_queue, picam_kill))
    run_cam_thread.start()
    usb_queue_kill = multiprocessing.Queue()
    usb_loop0 = multiprocessing.Process(
        target=usb_camera.capture_from_usb, args=(event_queue, usb_queue_kill, 0))
    usb_loop0.start()
    usb_loop1 = multiprocessing.Process(
        target=usb_camera.capture_from_usb, args=(event_queue, usb_queue_kill, 1))
    usb_loop1.start()
    event_queue_thread = threading.Thread(
        target=events.event_loop, args=(event_queue, game_ui))
    event_queue_thread.start()
    root.mainloop()
    input_queue.put(None)
    event_queue.put(None)
    picam_kill.kill()
    usb_queue_kill.put(True)
    usb_queue_kill.put(True)
    run_cam_thread.join()
    event_queue_thread.join()
    usb_loop0.join()
    usb_loop1.join()

if __name__ == '__main__':
    main()
