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