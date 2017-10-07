import json
import datetime
import storage
import threading
import requests

def _sort_by_time(eR):
    return eR.time

def now():
    return datetime.datetime.now().isoformat()

def serialize(timestamp, log):
    return json.dumps({"timestamp": timestamp, "log": log})

def deserialize(msg):
    v = json.loads(msg)
    return v['msg'], v['T'], v['eR']

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
        self.db.record(storage.Operation("tweet", json.dumps(params)))
        self.db.save()
        for target in self.all_sites:
            if target.node != self.my_site.node and not self.db.has((self.my_site.node, target.node)):
                new_log = []
                for eR in self.db.log:
                    if not self.db.hasRec(eR, target.node):
                        new_log.append(eR.to_dict())
                # async call
                sender(target.addr, serialize(self.db.timestamp, new_log))
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
        for eR in enumerate(tmp_log):
            if eR.op == 'tweet':
                new_log.append(eR)
            else:
                for site in self.all_sites:
                    if not self.db.hasRec(eR, site.node):
                        new_log.append(eR)
                        break
        self.db.log = new_log

    def _update_dict(self, ne):
        changes = {}
        for dR in ne:
            if not changes[dR.op.param]:
                changes[dR.op.param] = dR.op
            else:
                changes[dR.op.param].append(dR.op)
        for change in changes:
            # replay the events to determine if the change should be applied.
            sorted(changes[change], key=_sort_by_time)
            todo = 0 # 0 nothing, 1 add, -1 remove
            for i in changes[change]:
                if i.op == 'ins':
                    todo = min(todo + 1, 1)
                elif i.op == 'del':
                    todo = max(todo - 1, -1)
            if todo == -1:
                self.db.remove(change.param)
            elif todo == 1:
                self.db.put(change.param)

    def get_timeline(self):
        self.db.lock()
        timeline = []
        for eR in self.db.log:
            if eR.op.func == "tweet" and not self.db.has((self.my_site.node, eR.node)):
                timeline.append(eR)
        self.db.release()
        return {"timeline": [eR.op.to_dict() for eR in timeline]}

    def on_receive(self, from_node, timestamp, log):
        self.db.lock()
        # only process the ones that hasn't seen by me.
        ne = [] 
        for fR in log:
            if not self.db.hasRec(fR, self.my_site.node):
                ne.append(fR)
        self._update_dict(ne)
        self._update_log(ne)
        # update the timestamp matrix
        self._update_timestamp(timestamp, from_node)
        # save the state
        self.db.save()
        self.db.release()
        return True
