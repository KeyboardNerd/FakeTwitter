from collections import namedtuple
from threading import Lock
import model as m

import os 
import json

LogEntryFile = namedtuple("LogEntryFile", ["filename", "backupname", "lock"])

folder = None
_LOG = {}

# each log contains: the stateful acceptor information and 

# each log entry occupies a single file in order to simplify IO lock implementation.
# each file is named with the index of the log.

def init(folder_name):
    global folder
    folder = folder_name
    # initialize the storage by loading the file and creating a copy of it.
    # it will then use the paxos algorithm to catch up to the latest update of the log.
    # open a set of file descriptors for IO.
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    all_files = os.listdir(folder_name)
    # create file descriptor for each of the files.
    for filename in all_files:
        if filename[:2] == '_.':
            index = int(filename[2:])
            _LOG[index] = LogEntryFile(folder_name + "/" + filename, folder_name + "/" + filename+".bk", Lock())

def get_log():
    r = []
    for i in _LOG:
        r.append(json.loads(_load(_LOG[i].filename, _LOG[i].backupname))["value"])
    r.sort()
    return r

def acquire(log_index):
    ''' get the log state of a log index to prevent the acquire function to be called twice.
    '''
    entry = _LOG.get(log_index, None)
    if not entry:
        # initialize the log entry
        _LOG[log_index] = LogEntryFile('%s/_.%d'%(folder, log_index), '%s/_.%d.bk'%(folder, log_index), Lock())
        _LOG[log_index].lock.acquire()
        state = m.LogState()
        # commit the log entry
        commit(log_index, state)
        return state

    # access the log entry
    entry.lock.acquire()
    with open(entry.filename, 'r') as f:
        d = json.load(f)
        return m.LogState(d['value'], m.Acceptor(d['acceptor_state']['max_prepare'], d['acceptor_state']['accNum'], d['acceptor_state']['accVal']))

def commit(log_index, state):
    ''' save the log state changes to log_index

    this function can only be called if the log acceptor state has already been acquired.'''
    entry = _LOG.get(log_index, None)
    if entry:
        _save(entry.filename, entry.backupname, state.to_json())

def release(log_index):
    ''' release locking the state and allow another acquire.
    '''
    entry = _LOG.get(log_index, None)
    if entry:
        entry.lock.release()

def next_slot():
    if not _LOG:
        _LOG[0] = None
    else:
        _LOG[max(_LOG)+1] = None
    return max(_LOG)

def _save(filename, backupname, value):
    with open(backupname, "w+") as f:
        f.write(value)
    if os.path.exists(filename):
        os.remove(filename)
    os.rename(backupname, filename)

def _load(file_name, backup_file_name):
    if os.path.exists(file_name) and not os.path.exists(backup_file_name):
        # normal condition
        with open(file_name, "r") as f:
            return ''.join(f.readlines())
    elif not os.path.exists(file_name) and os.path.exists(backup_file_name):
        # failed on os.rename
        os.rename(backup_file_name, file_name)
    else:
        # failed on os.remove
        os.remove(file_name)
        os.rename(backup_file_name, file_name)
