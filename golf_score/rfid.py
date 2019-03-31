import time

import MFRC522
import RPi.GPIO as GPIO

import events

def uid_to_str(uid):
    return ''.join([str(x) for x in uid])

def rfid_loop(event_queue, kill_queue):
    # Create an object of the class MFRC522
    MIFAREReader = MFRC522.MFRC522()
    # This loop checks for chips. If one is near it will get the UID
    try:    
        while True:
            try:
                kill_queue.get(False)
                break
            except queue.Empty:
                pass
            # Scan for cards
            (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
            
            # Get the UID of the card
            (status,uid) = MIFAREReader.MFRC522_Anticoll()

            # If we have the UID, continue
            if status == MIFAREReader.MI_OK:
                uid_str = uid_to_str(uid)
                # Print UID
                print("UID: " + uid_str)
                event_queue.put((events.EventTypes.RFID_SCAN, uid_str))
        
            time.sleep(1)
    
    except KeyboardInterrupt:
        GPIO.cleanup()
