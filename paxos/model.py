from collections import namedtuple
import json
import config as c
import message
import threading
import server

import reliablestorage as data

def _send_recv_to_all_acceptors(msg):
    thread_pool = []
    result = [None]*len(c.all_sites)
    for i, site in enumerate(c.all_sites):
        if site != c.my_site:
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
        return None
    
    def on_recv_accept(self, msg):
        msg = json.loads(msg)
        n = msg['n']
        v = msg['v']
        print self.max_prepare
        print msg
        if n >= self.max_prepare:
            self.accNum = n
            self.accVal = v
            self.max_prepare = n
            return message.ack(self.accNum, self.accVal)
        return None

class Proposer(object):
    def __init__(self, log_index, value):
        self.proposal_counter = 0
        self.log_index = log_index
        self.value = value
        self.max_accNum_accVal = None
        self.max_accNum = 0

        self.choose_own = True
        self.promise_set = set()
        self.ack_set = set()

    def run(self):
        # proposer for log at log_index
        # only if majority of the acceptors promised, it will stop listenning
        # and continue to send accept
        n = None

        while len(self.promise_set) < 2:
            print "propose-promise step"
            self.promise_set = set()
            n = self.next_proposal_number()
            results = _send_recv_to_all_acceptors(message.paxos(self.log_index, "propose", message.propose(n)))
            for i, v in enumerate(results):
                if not v:
                    continue
                d = json.loads(v)
                if d['status'] != 200:
                    continue
                d = json.loads(d['body'])
                if d['t'] != 'promise' or d['log_index'] != self.log_index:
                    continue
                d = json.loads(d['msg'])

                accNum = d['accNum']
                accVal = d['accVal']

                if accNum > self.max_accNum:
                    self.max_accNum_accVal = accVal
                    self.max_accNum = accNum

                if accVal:
                    self.choose_own = False
                self.promise_set.add(i)

        # choose value
        v = self.value
        if not self.choose_own:
            v = self.max_accNum_accVal
        print "proposal number %d reached majority on log index %d with value %s"%(n, self.log_index, v)
        # _send_recv_to_all_acceptors(message.paxos(self.log_index, message.accept(n, v)))

    def next_proposal_number(self):
        # lamport timestamp
        number = ((self.proposal_counter + 1) << 16) | c.my_site.id
        self.proposal_counter += 1
        return number

class LogState(object):
    def __init__(self, final_value = None, acceptor=Acceptor()):
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
