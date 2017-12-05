from collections import namedtuple
import json
import config as c
import message
import threading
import server
import time

import reliablestorage as data

def _send_recv_to_all_acceptors(msg):
    thread_pool = []
    result = [None]*len(c.all_sites)
    for i, site in enumerate(c.all_sites):
        thread = threading.Thread(target=async_blocking_req, args=(site.addr, site.port, msg, result, i))
        thread_pool.append(thread)
        thread.start()

    for thread in thread_pool:
        thread.join()
    return result

def async_blocking_req(addr, port, msg, result, i):
    result[i] = server.blocking_req(addr, port, msg)

def acceptor_recv(msg):
    d = json.loads(msg)
    msgt = d['type']
    log_index = d['log_index']
    print 'acceptor(%d): recv %s'%(log_index, msgt)
    # retrieve corresponding acceptor from reliable storage
    if msgt == 'propose':
        log_entry = data.acquire(log_index)
        print log_index, log_entry.acceptor.max_prepare
        result = log_entry.acceptor.on_recv_propose(d['msg'])
        data.commit(log_index, log_entry)
        data.release(log_index)
        if not result:
            return 400, ""
        return 200, message.paxos(log_index, "promise", result)
    elif msgt == 'accept':
        log_entry = data.acquire(log_index)
        result = log_entry.acceptor.on_recv_accept(d['msg'])
        data.commit(log_index, log_entry)
        data.release(log_index)
        if not result:
            return 400, ""
        return 200, message.paxos(log_index, "ack", result)
    elif msgt == 'commit':
        log_entry = data.acquire(log_index)
        print msg
        msg = json.loads(d['msg'])
        log_entry.final_value = msg['v']
        data.commit(log_index, log_entry)
        data.release(log_index)
        return 200, ""
    return 404, ""

class Acceptor(object):
    def __init__(self, max_prepare=0, accNum=None, accVal=None):
        self.max_prepare = max_prepare
        self.accNum = accNum
        self.accVal = accVal

    def on_recv_propose(self, msg):
        msg = json.loads(msg)
        n = msg['n']
        print 'recv propose #%d'%(n,)
        if n > self.max_prepare:
            self.max_prepare = n
            return message.promise(self.accNum, self.accVal)
        print 'fail propose #%d < %d'%(n, self.max_prepare)
        return None
    
    def on_recv_accept(self, msg):
        msg = json.loads(msg)
        n = msg['n']
        v = msg['v']
        print "acceptor(#%d) receives accept %s"%(n, v)
        if n >= self.max_prepare:
            self.accNum = n
            self.accVal = v
            self.max_prepare = n
            return message.ack(self.accNum, self.accVal)
        print "acceptor(#%d) refuses (%d)"%(n, self.accNum)
        return None

class Proposer(object):
    def __init__(self, log_index, value):
        self.proposal_counter = 0
        self.log_index = log_index
        self.value = value
        self.max_accNum_accVal = None
        self.max_accNum = 0

        self.choose_own = True
        self.promise_set = []
        self.ack_set = []

    def run(self):
        # proposer for log at log_index
        # only if majority of the acceptors promised, it will stop listenning
        # and continue to send accept
        n = None

        retry_counter = 0
        while len(self.promise_set) < 3 and retry_counter < c.retry_counter:
            retry_counter += 1
            print "propose-promise step"
            self.promise_set = []
            n = self.next_proposal_number()
            msg = message.paxos(self.log_index, "propose", message.propose(n))
            results = _send_recv_to_all_acceptors(json.dumps({"head": "recv", "body": msg}))
            for i, v in enumerate(results):
                if not v:
                    continue
                d = json.loads(v)
                if d['stat'] != 200:
                    continue
                d = json.loads(d['body'])
                if d['type'] != 'promise' or d['log_index'] != self.log_index:
                    continue
                d = json.loads(d['msg'])

                accNum = d['accNum']
                accVal = d['accVal']

                if accNum > self.max_accNum:
                    self.max_accNum_accVal = accVal
                    self.max_accNum = accNum

                if accVal:
                    self.choose_own = False
                self.promise_set.append(i)
            
            if len(self.promise_set) < 3:
                print "failed to reach majority, retrying..."
                time.sleep(1)

        if len(self.promise_set) < 3:
            print "failed to reach majority"
            return False

        # choose value
        final_value = self.value
        if not self.choose_own:
            final_value = self.max_accNum_accVal
        
        print "proposal number %d reached majority on log index %d with value %s"%(n, self.log_index, final_value)

        # special case: 
        # we know that this is the end of the log.
        if not final_value:
            return False

        msg = message.paxos(self.log_index, "accept", message.accept(n, final_value))

        results = _send_recv_to_all_acceptors(json.dumps({"head": "recv", "body": msg}))
        print results
        for i, v in enumerate(results):
            print "proposer(%d): recv: %s"%(self.log_index, v)
            if not v:
                continue
            d = json.loads(v)
            if d['stat'] != 200:
                continue
            d = json.loads(d['body'])
            if d['type'] != 'ack' or d['log_index'] != self.log_index:
                continue
            d = json.loads(d['msg'])

            accNum = d['accNum']
            accVal = d['accVal']
            self.ack_set.append(i)

        if len(self.ack_set) >= 3:
            msg = message.paxos(self.log_index, "commit", message.commit(final_value))
            _send_recv_to_all_acceptors(json.dumps({"head": "recv", "body": msg}))
        else:
            print "Failed to create log entry", self.ack_set
            return False
        return True

    def next_proposal_number(self):
        # lamport timestamp
        number = ((self.proposal_counter + 1) << 16) | c.my_site.id
        self.proposal_counter += 1
        return number

class LogState(object):
    def __init__(self, final_value = None, acceptor=Acceptor(0, None, None)):
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

    def decode_log_state(self, msg):
        d = json.loads(msg)
        a = d['acceptor_state']
        acceptor = Acceptor(a['max_prepare'], a['accNum'], a['accVal'])
        log = LogState(d['value'], acceptor)
        return log
