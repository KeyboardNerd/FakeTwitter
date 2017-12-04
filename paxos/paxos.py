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
    for i in data._LOG:
        state = data.acquire(i)
        if not state.final_value:
            # use a dummy value to retrieve this
            log_index = i
            p = Proposer(log_index, None)
            p.run()
    
    # try to retrive other values
    while True:
        log_index = data.next_slot()
        p = Proposer(log_index, None)
        b = p.run()
        if not b: # if the run fails or it hits the end, it'll stop running.
            return

        