import json
import os
import copy

class Storage(object):
    def __init__(self, file_name):
        self.timestamp = []
        self.dictionary = []
        self.tweet_log = []
        self.block_log = []
        self.file_name = file_name
        self.backup_file_name = file_name + ".backup"
        self._load()

    def save(self):
        with open(self.backup_file_name, "w+") as f:
            json.dump(self.export_dict(), f)
        if os.path.exists(self.file_name):
            os.remove(self.file_name)
        os.rename(self.backup_file_name, self.file_name)

    def load_dict(self, s):
        # load a dictionary
        self.timestamp = s['timestamp']
        self.tweet_log = s['tweet_log']
        self.block_log = s['block_log']
        self.dictionary = s['dict']

    def export_dict(self):
        return {"timestamp": self.timestamp, "tweet_log": self.tweet_log, "block_log": self.block_log, "dict": self.dictionary}

    def _load(self):
        if os.path.exists(self.file_name) and not os.path.exists(self.backup_file_name):
            # normal condition
            with open(self.file_name, "r") as f:
                self.load_dict(json.load(f))
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

    def dict_put(self, key, value):
        # lock
        self.dictionary.append((key, value))
        self.save()
        # release
    
    def dict_exists(self, key, value):
        return (key, value) in self.dictionary

    def tweet_log_put(self, message):
        # lock tweet log
        self.tweet_log.append(message)
        self.save()
        # release log
    
    def tweet_log_get(self):
        # return a copied log in case that other processes will modify the log
        return copy.deepcopy(self.tweet_log)
    
    def block_log_put(self, message):
        # lock
        self.block_log.append(message)
        self.save()
        # release
    
S = Storage("data_file")
if __name__ == '__main__':
    S.tweet_log_put("this is a good message")
    S.dict_put("a", "b")