from flask import Flask, request
import json

app = Flask(__name__)

# http server usage:
# Put data using POST
# 

@app.route("/", methods=['GET', 'POST'])
def receive():
    return "Request method: " + request.method;1

def broadcast(msg, addrs):
    for addr in addrs:
        # multi threading, set correct timeout
        requests.post(addr+"/", msg)

def serialize(message, timestamp, previous_events):
    return json.dumps({"msg": message, "T": timestamp, "eR": previous_events})

def deserialize(msg):
    v = json.loads(msg)
    return v['msg'], v['T'], v['eR']

# start flask
app.run()