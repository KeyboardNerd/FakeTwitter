from collections import namedtuple
import json
import config as c
import message
import threading
import server

import reliablestorage as d

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
            results = _send_recv_to_all_acceptors(message.paxos(self.log_index, message.propose(n)))
            for i, v in enumerate(results):
                if not v:
                    continue
                d = json.loads(v)
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
