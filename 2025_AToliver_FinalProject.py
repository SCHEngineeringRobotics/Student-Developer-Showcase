import qwiic_rfid
import time
import csv
from datetime import datetime
import os

my_rfid = qwiic_rfid.QwiicRFID()

if my_rfid.begin():
    print("RFID reader is ready")

else:
    print("RFID reader is not ready")
    exit() #stop code if not connected

csv_file="rfid_log.csv"
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "TagID", "Status", "Points"])

tag_status = {}

while True:
    if my_rfid.available():
        tag_initial = my_rfid.get_tag()
        my_rfid.clear_tags()
        tag_hex = ''.join(f'{b:02X}' for b in tag_initial)  # Convert to hex
        print(f"Tag ID (hex): {tag_hex}")
        now=datetime.now()

        if tag_hex not in tag_status or tag_status[tag_hex] == False:
            tag_status[tag_hex] = True
            status = "Checked Out"
        else:
            tag_status[tag_hex] = False
            status = "Returned"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"{timestamp} - Tag ID: {tag_hex} - Status: {status}")

        # add to CSV
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, tag_hex, status])

        # Wait to avoid double-logging
        time.sleep(1.5)
    time.sleep(0.75)