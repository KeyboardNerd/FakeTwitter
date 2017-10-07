from flask import Flask, request, jsonify
import json
import service
import storage
import config
import threading
import requests

app = Flask(__name__)
# http server usage:
# Put data using POST
# 

def post_request_sender(addr, message):
    t = threading.Thread(target=requests.post, args=(addr+"/recv", None, message))
    t.start()

@app.route("/recv", methods=['POST'])
def recv():
    d = request.get_json()
    twitter.on_receive(d['node'], d['timestamp'], d['log'])
    return 

@app.route("/post", methods=['POST'])
def post():
    twitter.tweet(request.data, post_request_sender)

@app.route("/block", methods=['GET'])
def block():
    blocked = request.args.get('user')
    twitter.block(blocked)

@app.route("/unblock", methods=['GET'])
def unblock():
    unblocked = request.args.get('user')
    twitter.unblock(unblocked)

@app.route("/timeline", methods=['GET'])
def timeline():
    return jsonify(twitter.get_timeline())

if __name__ == '__main__':
    my_site, sites = config.load("config.json")
    database = storage.Storage(my_site.node, len(sites), "datafile")
    twitter = service.TweetService(database, my_site, sites)
    app.run(host=my_site.addr.split(":")[0], port=my_site.addr.split(":")[1])