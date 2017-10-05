from flask import Flask
import json

app = Flask(__name__)

@app.route("/")
def receive():
    # update my log, dict
    pass

def broadcast(msg, addrs):
    for addr in addrs:
        # multi threading, set correct timeout
        requests.post(addr+"/", msg)

def serialize(message, timestamp, previous_events):
    return json.dumps({"msg": message, "T": timestamp, "eR": previous_events})

def deserialize(msg):
    v = json.loads(msg)
    return v['msg'], v['T'], v['eR']