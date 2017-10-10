import threading
import os
import json
import sys

from urlparse import urlparse
from flask import Flask, request, jsonify, abort
from requests.exceptions import ConnectionError
import service
import storage
import config
import requests

app = Flask(__name__)
# http server usage:
# Put data using POST

def try_post(addr, message):
    try:
        requests.post(addr, None, message)
    except ConnectionError as e:
        print "ConnectionError: the endpoint %s is not online"%(addr,)

def post_request_sender(addr, message):
    print "broadcasted information:" + json.dumps(message) + " to " + addr
    t = threading.Thread(target=try_post, args=(addr+"/recv", message))
    t.start()

@app.route("/recv", methods=['POST'])
def recv():
    d = request.get_json()
    log = []
    for fR in d['log']:
        log.append(storage.EventRecord(fR['node'], fR['time'], storage.Operation(fR['op']['func'], fR['op']['params'])))
    twitter.on_receive(d['node'], d['timestamp'], log)
    return jsonify(status="ok")

@app.route("/post", methods=['POST'])
def post():
    twitter.tweet(request.get_json()["message"], post_request_sender)
    return jsonify(status="ok")

@app.route("/block", methods=['GET'])
def block():
    blocked = request.args.get('user')
    if not twitter.block(blocked):
        abort(400)
    return jsonify(status="ok")

@app.route("/unblock", methods=['GET'])
def unblock():
    unblocked = request.args.get('user')
    if not twitter.unblock(unblocked):
        abort(400)
    return jsonify(status="ok")

@app.route("/timeline", methods=['GET'])
def timeline():
    tl = twitter.get_timeline()['timeline']
    res = []
    for op in tl:
        msg = op['params']
        res.append({"user": msg[0], "message": msg[1], "time": msg[2]})
    return jsonify({"timeline": res})

@app.route("/suicide", methods=['GET'])
def suicide():
    # ohhhh yeah, just suicide quick! right thru the throat
    os.system('kill $PPID')

if __name__ == '__main__':
    if not sys.argv[1].isdigit():
        print "The site id \"" + sys.argv[1] + "\" is invalid. It should be an integer."
        exit(1)
    my_node = int(sys.argv[1])
    config_file = sys.argv[2]
    data_file = sys.argv[3]
    my_site, sites = config.load(config_file, my_node)
    if my_site == None:
        print "The site id \"" + sys.argv[1] + "\" is invalid. It cannot be found in the config file."
        exit(1)
    print "I am User '%s' Addr '%s' Node %d"%(my_site.name, my_site.addr, my_site.node)
    print "I know these users:"
    for site in sites:
        print "User '%s' Addr '%s' Node %d"%(site.name, site.addr, site.node)

    database = storage.Storage(my_site.node, len(sites), data_file)
    twitter = service.TweetService(database, my_site, sites)
    r = urlparse(my_site.addr)
    app.run(host=r.hostname, port=r.port)