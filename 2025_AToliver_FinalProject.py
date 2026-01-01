import qwiic_rfid
import time
import csv
from datetime import datetime, timedelta
import os
import json
import tkinter as tk
from tkinter import ttk

my_rfid = qwiic_rfid.QwiicRFID()

if my_rfid.begin():
    print("RFID reader is ready")

else:
    print("RFID reader is not ready")
    exit() #stop code if not connected

csv_file="rfid_log.csv"
json_file="tag_status.json"

if os.path.exists(json_file):
    with open(json_file, 'r') as f:
        tag_status = json.load(f)
    #convert last_scan strings back to datetime
    for tag in tag_status:
        tag_status[tag]["last_scan"]=datetime.fromisoformat(tag_status[tag]["last_scan"])
else:
    tag_status = {}

#create csv
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "tag_hex", "status", "points" ])

while True:
    if my_rfid.available():
        tag_initial = my_rfid.get_tag()
        my_rfid.clear_tags()
        tag_hex = ''.join(f'{b:02X}' for b in tag_initial)  # Convert to hex
        now = datetime.now()
        print(f"Tag ID (hex): {tag_hex}")

        if tag_hex not in tag_status:
            tag_status[tag_hex] = {"status": True, "last_scan":now, "points":0}
            status = "Checked Out"
        else:
            previous= tag_status[tag_hex]
            if previous["status"]:
                difference = now - previous["last_scan"]
                if difference <= timedelta(hours=1):
                    tag_status[tag_hex]["points"]+=1
                    print(f"Point awarded to {tag_hex}! Total:{tag_status[tag_hex]['points']}")
                status="Returned"
                tag_status[tag_hex]["status"]=False

            else:
                status="Checked Out"
                tag_status[tag_hex]["status"]=True

            tag_status[tag_hex]["last_scan"] = now
        timestamp=now.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} - Tag ID: {tag_hex} - Status: {status}")

        # add to CSV
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, tag_hex, status, tag_status[tag_hex]["points"]])

        #save JSON over mutliple days
        to_save = tag_status.copy()
        for tag in to_save:
            to_save[tag]["last_scan"] = to_save[tag]["last_scan"].isoformat()
        with open(json_file, 'w') as f:
            json.dump(to_save, f)

        # Wait to avoid double-logging
        time.sleep(1.5)
    time.sleep(0.75)