import json
import datetime
import storage

def _sort_by_time(eR):
    return eR.time

def now():
    return datetime.datetime.now().isoformat()

class Site(object):
    def __init__(self, node, name, addr):
        self.node = node
        self.name = name
        self.addr = addr

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
            print "that's no guy I know"
            return 
        self.db.lock()
        self.db.put((self.my_site.node, bad_node))
        self.db.save()
        self.db.release()

    def unblock(self, bad_guy):
        bad_node = self._find_node(bad_guy)
        if bad_node is None:
            print "that's no guy I know"
            return 
        self.db.lock()
        self.db.remove((self.my_site.node, bad_node))
        self.db.save()
        self.db.release()

    def tweet(self, message):
        params = (self.my_site.name, message, now())
        self.db.lock()
        self.db.record(storage.Operation("tweet", json.dumps(params)))
        self.db.save()
        for target in self.all_sites:
            if target.node != self.my_site.node and not self.db.has((self.my_site.node, target.node)):
                new_log = []
                for eR in self.db.log:
                    if not self.db.hasRec(eR, target.node):
                        new_log.append(eR)
                # async
            elif target.node != self.my_site.node:
                print "%s he is a bad guy, I'm not gonna send shit to him"%(target.name, )
        self.db.release()

    def _update_timestamp(self, timestamp, from_site):
        for k in self.all_sites:
            self.db.timestamp[self.my_site.node][k.node] = max(self.db.timestamp[self.my_site.node][k.node], timestamp[from_site][k.node])
        for k in self.all_sites:
            for l in self.all_sites:
                self.db.timestamp[k.node][l.node] = max(self.db.timestamp[k.node][l.node], timestamp[k.node][l.node])
    
    def _update_log(self, timestamp, ne, from_site):
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
                        break;
        self.db.log = new_log

    def _update_dict(self, timestamp, ne, from_site):
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
    
    def on_receive(self, from_site, timestamp, log):
        self.db.lock()
        # only process the ones that hasn't seen by me.
        ne = [] 
        for fR in log:
            if not self.db.hasRec(fR, self.my_site.node):
                ne.append(fR)

        self._update_dict(timestamp, ne, from_site)
        self._update_log(timestamp, ne, from_site)
        # update the timestamp matrix
        self._update_timestamp(timestamp, from_site)
        # save the state
        self.db.save()
        self.db.release()