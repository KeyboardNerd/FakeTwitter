'''
API: 

the language is
tweet: {"head": "tweet", "body": "<message>"} -> {"stat": 200, "body": ""}
block: {"head": "block", "body": "<username>"} -> {"stat": 200, "body": ""}
unblock: {"head": "unblock", "body":"<username>"} -> {"stat": 200, "body": ""}
view: {"head": "view", "body": ""} -> {"stat": 200, "body": [["<username>", "<message>", "<time>"]]}
recv: {"head": "recv", "body": {"log": [{"node": <sid>, "time": <counter_timestamp>, "op": {"func": "<action_name>", "params": ["param",...]}}]}, "node": <sid>, "timestamp": <counter_timestamp>} -> {"stat": 200, "body": ""}
'''

import os
import json
import sys
import abc

import service
import storage
import config

class TweetAPI(object):
    def __init__(self, tweet_service, request_sender):
        self.service = tweet_service
        self.request_sender = request_sender
    
    def _tweet_request_sender(self, address, port, message):
        message = json.dumps({"head": "recv", "body": message})
        return self.request_sender(address, port, message)
    # every function accepts a dictionary ( json body ) and returns a number as
    # status and a string as result.
    def recv(self, body):
        log = []
        body = json.loads(body)
        for fR in body['log']:
            log.append(storage.EventRecord(fR['node'], fR['time'], storage.Operation(fR['op']['func'], fR['op']['params'])))
        self.service.on_receive(body['node'], body['timestamp'], log)
        return 200, ""

    def tweet(self, content):
        self.service.tweet(content, self._tweet_request_sender)
        return 200, ""

    def block(self, user_name):
        if not self.service.block(user_name):
            return 400, "user not found"
        return 200, ""

    def unblock(self, user_name):
        if not self.service.unblock(user_name):
            return 400, "user not found"
        return 200, ""

    def view(self):
        tl = self.service.get_timeline()['timeline']
        res = []
        for op in tl:
            res.append(op['params'])
        return 200, json.dumps(res)

    def suicide(self):
        os.system('kill $PPID')

    def route(self, message):
        d = json.loads(message)
        head = d['head']
        dict_body = d['body']
        stat = 400
        r_body = "unknown command"
        if head == 'tweet':
            stat, r_body = self.tweet(dict_body)
        elif head == 'block':
            stat, r_body =  self.block(dict_body)
        elif head == 'unblock':
            stat, r_body =  self.unblock(dict_body)
        elif head == 'view':
            stat, r_body =  self.view()
        elif head == 'suicide':
            stat, r_body =  self.suicide()
        elif head == 'recv':
            stat, r_body = self.recv(dict_body)
        return json.dumps({"stat": stat, "body": r_body})
