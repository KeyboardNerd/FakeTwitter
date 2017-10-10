import json
import os
from threading import Lock

def hasRec(timestamp, event_record, target):
    return timestamp[target][event_record.node] >= event_record.time

class Site(object):
    def __init__(self, node, name, addr):
        self.node = node
        self.name = name
        self.addr = addr

class EventRecord(object):
    def __init__(self, node, time, op):
        self.node = node
        self.time = time
        self.op = op

    def to_dict(self):
        return {"node": self.node, "time": self.time, "op": self.op.to_dict()}

class Operation(object):
    def __init__(self, func, params):
        # param -> tuple of premitives
        self.func = func
        self.param = params
    
    def to_dict(self):
        return {"func": self.func, "params": self.param[:]}

class Storage(object):
    # all functions should be thread safe
    def __init__(self, my_node, num_node, file_name):
        self.my_node = my_node

        self.mutex = Lock()
        self.timestamp = [[0]*num_node for _ in xrange(num_node)]
        self.dict = set()
        self.log = []
        self.file_name = file_name
        self.backup_file_name = file_name + ".backup"
        self._load()

    def hasRec(self, eR, k):
        return self.timestamp[k][eR.node] >= eR.time

    def record(self, operation):
        self.timestamp[self.my_node][self.my_node] += 1
        event_record = EventRecord(node=self.my_node,
            time = self.timestamp[self.my_node][self.my_node],
            op=operation)
        self.log.append(event_record)

    def put(self, value):
        self.record(Operation("ins", value))
        self.dict.add(value)

    def remove(self, value):
        self.record(Operation("del", value))
        if value in self.dict:
            self.dict.remove(value)

    def has(self, value):
        return value in self.dict

    def save(self):
        with open(self.backup_file_name, "w+") as f:
            json.dump(self._export_dict(), f)
        if os.path.exists(self.file_name):
            os.remove(self.file_name)
        os.rename(self.backup_file_name, self.file_name)

    def lock(self):
        self.mutex.acquire()
    
    def release(self):
        self.mutex.release()

    def _load_dict(self, s):
        # load a dictionary
        self.timestamp = s['timestamp']
        log = s['log']
        self.log = []
        for eR in log:
            self.log.append(EventRecord(eR["node"], eR["time"], Operation(eR["op"]["func"], eR["op"]["params"])))
        self.dict = set([tuple(x) for x in s['dict']])

    def _export_dict(self):
        log = []
        for eR in self.log:
            log.append(eR.to_dict())
        return {"timestamp": self.timestamp, "log": log, "dict": list(self.dict)}

    def _load(self):
        if os.path.exists(self.file_name) and not os.path.exists(self.backup_file_name):
            # normal condition
            with open(self.file_name, "r") as f:
                self._load_dict(json.load(f))
        elif not os.path.exists(self.file_name) and not os.path.exists(self.backup_file_name):
            # initialization condition
            self.save()
        elif not os.path.exists(self.file_name) and os.path.exists(self.backup_file_name):
            # failed on os.rename
            os.rename(self.backup_file_name, self.file_name)
        else:
            # failed on os.remove
            os.remove(self.file_name)
            os.rename(self.backup_file_name, self.file_name)
