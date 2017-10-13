import json
import sys
import datetime
import storage
import threading
import requests

def _sort_by_time(eR):
    return eR.time

def now():
    return datetime.datetime.now().isoformat()

def to_dict(node, timestamp, log):
    return {"node": node, "timestamp": timestamp, "log": log}

class TweetService(object):
    def __init__(self, db, my_site, all_sites):
        self.my_site = my_site
        self.all_sites = all_sites
        self.db = db

    def _find_node(self, name):
        for site in self.all_sites:
            if site.name == name:
                return site.node

    def block(self, bad_guy):
        bad_node = self._find_node(bad_guy)
        if bad_node is None:
            return False
        self.db.lock()
        self.db.put((self.my_site.node, bad_node))
        self.db.save()
        self.db.release()
        return True

    def unblock(self, bad_guy):
        bad_node = self._find_node(bad_guy)
        if bad_node is None:
            return False
        self.db.lock()
        self.db.remove((self.my_site.node, bad_node))
        self.db.save()
        self.db.release()
        return True

    def tweet(self, message, sender):
        params = (self.my_site.name, message, now())
        self.db.lock()
        self.db.record(storage.Operation("tweet", params))
        self.db.save()
        for target in self.all_sites:
            if target.node != self.my_site.node and not self.db.has((self.my_site.node, target.node)):
                new_log = []
                for eR in self.db.log:
                    if not self.db.hasRec(eR, target.node):
                        new_log.append(eR.to_dict())
                # async call
                sender(target.addr, to_dict(self.my_site.node, self.db.timestamp, new_log))
        self.db.release()

    def _update_timestamp(self, timestamp, from_node):
        for k in self.all_sites:
            self.db.timestamp[self.my_site.node][k.node] = max(self.db.timestamp[self.my_site.node][k.node], timestamp[from_node][k.node])
        for k in self.all_sites:
            for l in self.all_sites:
                self.db.timestamp[k.node][l.node] = max(self.db.timestamp[k.node][l.node], timestamp[k.node][l.node])
    
    def _update_log(self, ne):
        # add the logs not in db and remove the block logs that every one knows
        # about.
        new_log = []
        tmp_log = self.db.log + ne
        for eR in tmp_log:
            if eR.op.func == 'tweet':
                new_log.append(eR)
            else:
                for site in self.all_sites:
                    if not self.db.hasRec(eR, site.node):
                        new_log.append(eR)
                        break
        self.db.log = new_log

    def _update_dict(self, ne):
        operations = {} # contains target -> [operations]
        for dR in ne:
            if dR.op.func != 'tweet':
                key = json.dumps(dR.op.param)
                if key not in operations:
                    operations[key] = [dR]
                else:
                    operations[key].append(dR)

        for target in operations:
            # replay the events to determine if the change should be applied.
            sorted(operations[target], key=_sort_by_time)
            todo = 0 # 0 nothing, 1 add, -1 remove
            for i in operations[target]:
                if i.op.func == 'ins':
                    todo = min(todo + 1, 1)
                elif i.op.func == 'del':
                    todo = max(todo - 1, -1)
            if todo == -1:
                self.db.remove(tuple(json.loads(target)))
            elif todo == 1:
                self.db.put(tuple(json.loads(target)))

    def get_timeline(self):
        self.db.lock()
        timeline = []
        for eR in self.db.log:
            if eR.op.func == "tweet" and not self.db.has((self.my_site.node, eR.node)): 
                # insertion sort to put message in timeline, descending order
                for i in range(len(timeline) + 1):
                    if i == len(timeline) or eR.op.param[2] > timeline[i].op.param[2]:
                        timeline.insert(i, eR)
                        break
        return {"timeline": [eR.op.to_dict() for eR in timeline]}

    def on_receive(self, from_node, timestamp, log):
        self.db.lock()
        # only process the ones that hasn't seen by me.
        new_events = [] 
        for fR in log:
            if not self.db.hasRec(fR, self.my_site.node):
                new_events.append(fR)
        self._update_dict(new_events)
        self._update_log(new_events)
        # update the timestamp matrix
        self._update_timestamp(timestamp, from_node)
        # save the state
        self.db.save()
        self.db.release()
        return True
