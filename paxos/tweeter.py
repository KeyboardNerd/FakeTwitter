import message as m
import config as c
import model
import json
import datetime
import paxos
import os

def now():
    return datetime.datetime.utcnow().isoformat()

def recover():
    # recover the data store
    pass

def tweet(msg):
    # tweet a message
    log_msg = m.tweet(c.my_site, msg, now())
    return paxos.log(log_msg)

def block(user_name):
    # block a user
    site = c.get_site_by_name(user_name)
    log_msg = m.block(c.my_site, site)
    return paxos.log(log_msg)

def unblock(user_name):
    # unblock a user
    site = c.get_site_by_name(user_name)
    log_msg = m.unblock(c.my_site, site)
    return paxos.log(log_msg)

def view():
    # view the timeline
    log = paxos.get()
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
    # sort, will work as long as format is unchanged
    filtered_tweet = sorted(filtered_tweet, key=lambda eR: eR[2])
    # done
    return 200, filtered_tweet

def suicide():
    os.system('kill $PPID')

# paxos message
def recv(body):
    return model.acceptor_recv(body)

def router(message):
    d = json.loads(message)
    head = d['head']
    dict_body = d['body']
    stat = 400
    r_body = "unknown command"
    if head == 'tweet':
        stat, r_body = tweet(dict_body)
    elif head == 'block':
        stat, r_body =  block(dict_body)
    elif head == 'unblock':
        stat, r_body =  unblock(dict_body)
    elif head == 'view':
        stat, r_body =  view()
    elif head == 'suicide':
        suicide()
    elif head == 'recv': # paxos
        stat, r_body = recv(dict_body)
    return json.dumps({"stat": stat, "body": r_body})
