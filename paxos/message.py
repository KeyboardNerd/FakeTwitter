import json
from collections import namedtuple

# block/unblock: {"op": "b", "u": <sender id>, "o": <blocked-site id>}
# tweet: {"op": "t", "u": "<sender id>", "m": "<tweet msg>", 't': "<UTC timestamp>"}
def block(my_site, other_site):
	return json.dumps({'op': 'b', 'u': my_site.id, 'o': other_site.id})

def unblock(my_site, other_site):
	return json.dumps({'op': 'u', 'u': my_site.id, 'o': other_site.id})

def tweet(my_site, msg, timestamp):
	return json.dumps({'op': 't', 'u': my_site.id, 'm': msg, 't': timestamp})

def propose(proposal_number):
    return json.dumps({"n": proposal_number})

def promise(accNum, accVal):
	return json.dumps({"accNum": accNum, "accVal": accVal})

def accept(proposal_number, value):
    return json.dumps({"n": proposal_number, "v": value})

def ack(accNum, accVal):
    return json.dumps({"accNum": accNum, "accVal": accVal})

def commit(value):
    return json.dumps({"v": value})

def paxos(log_index, t, msg):
	return json.dumps({"log_index": log_index, "type": t, "msg": msg})