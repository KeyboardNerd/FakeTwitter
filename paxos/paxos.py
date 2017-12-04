from model import *
import reliablestorage as data
import message

def log(msg):
    # determine the current slot's value by using "synod" algorithm
    # this is a blocking call

    # try to log current message to last available index
    # create a new log preparation state
    log_index = data.next_slot()
    p = Proposer(log_index, msg)
    b = p.run()
    if b:
        return 200, ""
    else:
        return 500, ""

def get():
    return data.get_log()

def recover():
    # if there's no such log or the log is empty, then we'll need to recover the value.
    i = 0
    print "start recovering"
    while True:
        print i
        if i in data._LOG and data._LOG[i].iscommit:
            i += 1
            continue
        # use paxos to recover this value, if the final state is None, 
        # we know that the value is the last one and stop recovering.
        print "starting proposer for ", i
        p = Proposer(i, None)
        b = p.run()
        if not b or not data.acquire(i).final_value:
            break
        i += 1
    return 200, ""
