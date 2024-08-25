import cv2
import requests
from flask import Flask, render_template, jsonify, request
from ultralytics import YOLO
from threading import Thread
from time import time 
import time as tm
import numpy as np
import csv
import pytz
from datetime import datetime

app = Flask(__name__)

# model_path = r'X:\Skripsi\trained datasets\train11\weights\best.pt'
# model = YOLO(model_path)

# cap = cv2.VideoCapture(0)

# status = second to green
intersection_status = {
    '1' : {"status" : 0, "count" : 0},
    '2' : {"status" : 0, "count" : 0},
    '3' : {"status" : 0, "count" : 0},
    '4' : {"status" : 0, "count" : 0}
};

batch_start = 0
batch_fifo = {}
total_timer = 0

@app.route('/monitor', methods=["GET"])
def monitor():
    return render_template('monitor.html')

@app.route('/simulator', methods=["GET"])
def simulator():
    return render_template('simulator.html')

@app.route('/simulator', methods=["POST"])
def simulatorUpdate():
    data = request.json
    return {
        "status" : updateStatus(data),
        "history" : retrieve_batch_fifo_from_csv()
    }

@app.route('/status', methods=['GET'])
def getAllStatus():
    return getStatus()

@app.route('/status', methods=["POST"])
def updateStatusHttp():
    updateStatus(request.json)
    return {}

@app.route('/count', methods=["GET"])
def getCount():
    return intersection_status

@app.route('/batch', methods=["GET"])
def getBatchStatus():
    global batch_fifo
    global batch_start

    batch = batch_fifo.copy()
    response = {}
    data = []
    for key, b in batch.items():
        data.append({
            "intersection_id": key,
            "green_time": b
        })

    if len(data) > 0:
        response["batch"] = data
        response["time_elapsed"] = int(time()) - batch_start
        # response["history"] = retrieve_batch_fifo_from_csv()

    return response

@app.route('/batch/history', methods=["GET"])
def getBatchHistory():
    return retrieve_batch_fifo_from_csv()

def getStatus():
    global batch_start
    global batch_fifo
    global total_timer

    statusResponse = {}
    counter = 0
    for key, d in batch_fifo.items():
        status = d - (int(time()) - batch_start - counter)
        statusResponse[key] = status if status > 0 and status < d else 0
        counter += d
    if len(statusResponse) > 0:
        statusResponse["time_elapsed"] = int(time()) - batch_start
    return statusResponse

def updateStatus(data = None, history = True):
    global intersection_status
    global batch_start
    global batch_fifo
    global total_timer

    if data is None:
        data = {}
        for key, d in intersection_status.items():
            data[key] = d['count']

    # update count
    for key, d in data.items():
        # intersection_status.update({key: {"status": intersection_status[key].get("status"), "count" : d}})
        intersection_status.update({key: {"status": intersection_status[key]["status"], "count" : d}})

    if batch_start == 0:
        # sort
        keys = list(data.keys())
        values = list(data.values())
        sorted_value_index = np.argsort(values)[::-1]
        sorted_dict = {keys[i]: values[i] for i in sorted_value_index}

        total_timer = 0
        for key, d in sorted_dict.items():
            timer = 34 if d >= 1 else 0
            timer = timer + 5 if d > 5 else timer
            total_timer += timer
            batch_fifo[key] = timer
            intersection_status[key].update({key: {"status": timer, "count" : d}})

        batch_start = int(time())

        if(total_timer < 1):
            batch_start = 0
            batch_fifo = {}
        else:
            # Get current datetime in Asia/Jakarta timezone
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            current_time = datetime.now(jakarta_tz).strftime('%Y-%m-%d %H:%M:%S')

            if history:
                # Append batch_fifo to a CSV file
                with open('batch_fifo_history.csv', 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    csvdata = []
                    sorted_keys = sorted(batch_fifo.keys())
                    for key in sorted_keys:
                        timer = batch_fifo[key]
                        csvdata.append(timer)
                    for key in sorted_keys:
                        csvdata.append(data[key]) # vehicle count

                    csvdata.append(current_time)

                    # Read existing data from CSV
                    existing_data = []
                    try:
                        with open('batch_fifo_history.csv', 'r') as csvfile:
                            reader = csv.reader(csvfile)
                            existing_data = list(reader)
                    except FileNotFoundError:
                        pass

                    # Write new and existing data back to CSV
                    with open('batch_fifo_history.csv', 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        # Write new data first
                        writer.writerows([csvdata])
                        # Append existing data
                        writer.writerows(existing_data)
            
    if(total_timer < (int(time()) - batch_start)):
        batch_start = 0
        batch_fifo = {}

    return getStatus()

def updateInterval():
    start_time = time()

    current_status = updateStatus(history=False)
    print(current_status)

    # Calculate elapsed time
    elapsed_time = time() - start_time
    # Sleep to ensuretime is exactly 1 seconds
    if elapsed_time < 1.0:
        tm.sleep(1.0 - elapsed_time)


def retrieve_batch_fifo_from_csv(filename='batch_fifo_history.csv'):
    history = []
    try:
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                history.append(row)
    except FileNotFoundError:
        print(f"File {filename} not found.")
    
    return history

if __name__ == '__main__':
    update_thread = Thread(target=updateInterval, args=())

    update_thread.start()
    
    # detection_thread = Thread(target=detect_vehicles)
    # detection_thread.start()
    app.run(host='0.0.0.0', port=5000)