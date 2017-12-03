# block/unblock: {"op": "b", "u": <id>, "o": <id>}
# tweet: {"op": "t", "u": "<id>", "m": "<msg>", 't': "<UTC timestamp>"}
def block(my_site, other_site):
	return json.dumps({'op': 'b', 'u': my_site.id, 'o': other_site.id})

def unblock(my_site, other_site):
	return json.dumps({'op': 'u', 'u': my_site.id, 'o': other_site.id})

def tweet(my_site, msg, timestamp):
	return json.dumps({'op': 't', 'u': my_site.id, 'm': msg, 't': timestamp})

def promise(log_index, accNum, accVal):
	return json.dumps({"log_index": log_index, "accNum": accNum, "accVal": accVal})
