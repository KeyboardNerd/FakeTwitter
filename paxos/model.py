from collections import namedtuple
import json
import config as c
import message
import threading

import reliablestorage as d

# from server import async_send
def async_send(addr, port, msg):
    print addr, port, msg

# for every entry in the log, there are one acceptor state and one proposer state
# proposer's state is ephemeral and acceptor state is non-volatile.

class Acceptor(object):
    def __init__(self, max_prepare=0, accNum=None, accVal=None):
        self.max_prepare = max_prepare
        self.accNum = accNum
        self.accVal = accVal

    def on_recv_propose(self, sender_site, msg):
        msg = json.loads(msg)
        n = msg['n']
        log_index = msg['log_index']

        if n > self.max_prepare:
            self.max_prepare = n
            return message.promise(log_index, self.accNum, self.accVal)
    
    def on_recv_accept(self, sender_site, msg):
        msg = json.loads(msg)
        n = msg['n']
        v = msg['v']
        if n >= self.max_prepare:
            self.accNum = n
            self.accVal = v
            self.max_prepare = n
            # ack after saving accNum and accVal
            return message.accept(self.accNum, self.accVal)
        return None

class Paxos(object):
    def __init__(self):
        proposers = {}
    
    def log(message):
        log_index = d.next_slot()
        threading.Thread(target=_log, args(log_index, message)).start()

    def _log(log_index, message):
        proposer[log_index] = Proposer(message)
    
    def on_recv_promise(self, sender_site, msg):
        msg = json.loads(msg)
        log_index = msg['log_index']
        value = msg['value']
        msg = proposer[log_index].on_recv_promise(sender_site, value)
        # TODO: if there's no majority after a timeout, start over.
        if msg:
            # if there's a majority, send the message to all sites
            async_send_to_all_acceptors(message.paxos(log_index, msg))

    def on_recv_propose(self, sender_site, msg):
        msg = json.loads(msg)
        log_index = msg['log_index']
        value = msg['value']
        
        logentry_state = d.acquire(log_index)
        logentry_state.acceptor.on_recv_propose(sender_site, msg)
        d.commit(log_index, logentry_state)
        d.release()
    
    def async_send_to_all_acceptors(self, msg):
        for site in c.all_sites:
            if site != c.my_site:
                async_send(site.addr, site.port, msg)

class Proposer(object):
    def __init__(self, value):
        self.proposal_counter = 0

        self.value = value
        self.max_accNum_accVal = None
        self.max_accNum = 0

        self.choose_own = True
        self.promise_set = set()
        self.ack_set = set()

        self.stage = 0
        # 0 = proposed, 1 = accepted, 2 = committed

    def next_proposal_number(self):
        # lamport timestamp
        number = ((self.proposal_counter + 1) << 16) | c.my_site.id
        self.proposal_counter += 1
        return number
    
    def propose(self):
        n = self.next_proposal_number()
        self.stage = 0
        return message.propose(n)

    def on_recv_promise(self, sender_site, msg):
        if self.stage > 0:
            return None

        msg = json.loads(msg)
        accNum = msg['accNum']
        accVal = msg['accVal']

        # update value with largest accNum number
        if accVal and accNum > self.max_accNum:
            self.max_accNum_accVal = accVal
            self.max_accNum = accNum

        # whether to choose own value or not
        if accVal:
            self.choose_own = False

        # update promise set
        self.promise_set.add(sender_site.id)

        # if proposer receives response from majority
        if len(self.promise_set) >= len(c.all_sites)/2:
            # choose value v
            v = self.value
            if not state.choose_own:
                v = self.max_accNum_accVal
            self.stage = 1
            return message.accept(state.log_index, state.proposal_number, state.value)
        return None

    def on_recv_ack(self, msg):
        json.loads(msg)

class LogState(object):
    def __init__(self, final_value = None, acceptor=AcceptorState()):
        self.final_value = final_value
        self.acceptor = acceptor
    def to_json(self):
        return json.dumps(
            {"value": self.final_value, 
             "acceptor_state": 
             {"max_prepare": self.acceptor.max_prepare, 
            "accNum": self.acceptor.accNum, 
            "accVal": self.acceptor.accVal}
            })
    def decode_log_state(msg):
        d = json.loads(msg)
        a = d['acceptor_state']
        acceptor = AcceptorState(a['max_prepare'], a['accNum'], a['accVal'])
        log = LogState(d['value'], acceptor)
        return log
