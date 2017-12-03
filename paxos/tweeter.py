import message as m
import config as c
import paxos
from server import send

def now():
    return datetime.datetime.utcnow().isoformat()

def tweet(msg):
	# tweet a message
	log_msg = m.tweet(c.my_site, msg, now())
	return paxos.log(log_msg, send)

def block(user_name):
	# block a user
	site = c.get_site_by_name(user_name)
	log_msg = m.block(c.my_site, site)
	return paxos.log(log_msg, send)

def unblock(user_name):
	# unblock a user
	site = c.get_site_by_name(user_name)
	log_msg = m.unblock(c.my_site, site)
	return paxos.log(log_msg, send)

def view():
	# view the timeline
	log = paxos.get_log()
	block_set = set()
	tweets = []
	for l in log:
		d = json.loads(l)
		# replay the log
		if d['op'] == 'b':
			block_set.add((d['u'], d['o']))
		elif d['op'] == 'u':
			block_set.remove((d['u'], d['o']))
		elif d['op'] == 't':
			tweets.append((d['u'], d['m'], d['t']))
	filtered_tweet = []
	for t in tweets:
		if (t[0], c.my_site.id) not in block_set:
			filtered_tweet.append(t)
	return filtered_tweet
