import json
import config as c
import reliablestorage as data

from server import send
from collections import namedtuple

# send function is async

# for a new user, first recover all logs by sending dummy value to all sites, 
# and only if all sites agrees on the dummy value, it knows that that log location is the most uptodate location.

# for any tweet, block, unblock event, select this log location (i) and replicate it to all other sites.
# if not success, output failed and retry.
# if success, output success and put it into the correct log location.
# on receive of adding a new log, the site should keep track of the latest log location + 1
# if log location jumps, it should create holes in the log in order to receive the log later.
# 

# for all the tweets, are they going to always be in correct order?
# tweets should be displayed in UTC time order.
# for all the blocks and unblock operations, since it must be true that for any one site, the order is causal order.
# the blocking and unblocking should be true.

# proposer state trakcs the proposal number, 
# number of acc, 
# value with largest accNum
# 

proposer_states = {}

def createState(log_index):
    proposer_states[log_index] = ProposerState(None, 0, 0, 0)

def selectState(log_index):
    proposer_states.get(log_index, None)

def next_proposal_number(log_index):
    # lamport timestamp
    return ((selectState(log_index).last_proposal_number + 1) << 16) | my_site.id

def log(msg, send):
    # determine the current slot's value by using "synod" algorithm
    # this is a blocking call

    # try to log current message to last available index
    # create a new log preparation state
    log_index = len(data.next_index())
    createState(log_index)
    propose(next_proposal_number(log_index))

def get_log():
    return data.get()

def send_propose(number):
    msg = json.dumps({"n": number})
    for site in all_sites:
        send(site.addr, site.port, msg)

def on_recv_propose(sender_site, msg):
    msg = json.loads(msg)
    n = msg['n']
    log_index = msg['log_index']
    data.lock(log_index)
    if n > data.get_max_prepare(log_index):
        data.set_max_prepare(log_index, n)
        send_promise(log_index)
    data.unlock(log_index)

def send_promise(log_index, reply_site):
    state = data.get(log_index)
    msg = message.promise(log_index, state.accNum, state.accVal)
    send(reply_site.addr, reply_site.port, msg)

def on_recv_promise(sender_site, log_index, msg, send):
    msg = json.loads(msg)
    accNum = msg['accNum']
    accVal = msg['accVal']
    state = selectState(log_index)
    state.

def send_accept():
