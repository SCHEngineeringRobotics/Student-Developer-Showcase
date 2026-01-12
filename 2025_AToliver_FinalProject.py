import qwiic_rfid
import csv
from datetime import datetime, timedelta
import os
import json
import tkinter as tk
import time


#setup tkinter
window=tk.Tk()
window.title("Forkomatic")
window.geometry("500x350")
title_label = tk.Label(window, text="Please Scan Your ID", font=("Arial", 20, "bold"))
title_label.pack(pady=10)

tag_label = tk.Label(window, text="Tag ID: --", font=("Arial", 12))
tag_label.pack()

status_label = tk.Label(window, text="Status: --", font=("Arial", 12))
status_label.pack()

last_scan_label = tk.Label(window, text="Last Scan: --", font=("Arial", 12))
last_scan_label.pack()

points_label = tk.Label(window, text="Points: 0", font=("Arial", 12))
points_label.pack()

scans_label = tk.Label(window, text="Total Scans: 0", font=("Arial", 12))
scans_label.pack()

#rfid setup
my_rfid = qwiic_rfid.QwiicRFID()

if my_rfid.begin():
    print("RFID reader is ready") #RFID is ready

else:
    print("RFID reader is not ready") #RFID is not ready
    exit() #stop code if not connected

#file setup
csv_file="rfid_log.csv"
json_file="tag_status.json"

#open existing JSON file to edit
if os.path.exists(json_file):
    with open(json_file, 'r') as f:
        tag_status = json.load(f)

    for tag in tag_status:
        tag_status[tag]["last_scan"]=datetime.fromisoformat(tag_status[tag]["last_scan"]) #convert last_scan strings back to datetime
else:
    tag_status = {}

#create csv
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "tag_hex", "status", "points", "total_scans"])
#sound function
def beep(duration=0.1):
    my_rfid.set_buzzer(True)
    window.after(int(duration*1000), lambda:my_rfid.set_buzzer(False))

#RFID Function
def scan_rfid():
    if my_rfid.available():
        tag_initial = my_rfid.get_tag()
        my_rfid.clear_tags()
        beep(0.15)

        tag_hex = ''.join(f'{b:02X}' for b in tag_initial)
        now = datetime.now()# check time

        if tag_hex not in tag_status:
            tag_status[tag_hex] = {"status": True, "last_scan":now, "points":0, "scans":0}
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
        tag_status[tag_hex]["scans"]+=1

        timestamp=now.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} - Tag ID: {tag_hex} - Status: {status}")

        # add to CSV
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp,
                             tag_hex,
                             status,
                             tag_status[tag_hex]["points"],
                             tag_status[tag_hex]["scans"]
                             ])

        # save JSON over multiple days
        to_save = tag_status.copy()
        for tag in to_save:
            to_save[tag]["last_scan"] = to_save[tag]["last_scan"].isoformat()
        with open(json_file, 'w') as f:
            json.dump(to_save, f)

        #Update window
        title_label.config(text="Scan Complete!")
        tag_label.config(text=f"Tag ID: {tag_hex}")
        status_label.config(text=f"Status: {status}")
        last_scan_label.config(text=f"Last Scan: {timestamp}")
        points_label.config(text=f"Points: {tag_status[tag_hex]['points']}")
        scans_label.config(text=f"Total Scans: {tag_status[tag_hex]['scans']}")

    #check again after 120 seconds
    window.after(120,scan_rfid)

#start program
scan_rfid()
window.mainloop()
