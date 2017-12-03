import json
from model import *
import config as c
import reliablestorage as data
import message

#from server import async_send
def async_send(addr, port, message):
    print addr, port, message

# async_send function is async

# for a new user, first recover all logs by async_sending dummy value to all sites, 
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

proposer_states = {}

def createState(log_index):
    proposer_states[log_index] = ProposerState(log_index, None, 0, None, set(), set())

def log(msg):
    # determine the current slot's value by using "synod" algorithm
    # this is a blocking call

    # try to log current message to last available index
    # create a new log preparation state
    log_index = data.new()
    createState(log_index)
    msg = message.propose(log_index, next_proposal_number(log_index))
    for site in c.all_sites:
        async_send(site.addr, site.port, msg)

def on_recv_accept(async_sender_site, msg):
    msg = json.loads(msg)
    proposal_number = msg['n']
    value = msg['v']
    log_index = msg['log_index']

    state = data.acquire(log_index)
    acceptor = state.acceptor
    if proposal_number >= acceptor.max_prepare:
        acceptor.acc_num = proposal_number
        acceptor.acc_val = value
        acceptor.max_prepare = proposal_number
        data.commit(log_index, state)
        reply_proposer(async_sender_site, message.ack(log_index, acceptor.acc_num, acceptor.acc_val))
    data.release(log_index)

def on_commit(sender_site, msg):
    msg = json.loads(msg)
    value = msg['v']
    log_index = msg['log_index']

    # set the final value
    state = data.acquire(log_index)
    state.value = value
    data.commit(log_index, state)
    data.release(log_index)

def reply_proposer(proposer_site, msg):
    async_send(proposer_site.addr, proposer_site.port, msg)
