import json
import os

data_name = "data.1"
backup_name = "data.2"
# {"log": {
#           "tweet": [{"message": "", "ptime": "", "sid": ""}], 
#           "blocking": [{"type": "block", "sid": "", "blocked_sid": "(another sid)"}]},
# "dictionary": [("(sid)", "(blocked_sid)"), ()],
# "T": [[numbers]]
# }
# 

S = None

    with open(data_name, "r") as f:
        S = json.load(f)

def save():
    with open(backup_name, "w+") as f:
        json.dump(S, f)
    os.remove(data_name)
    os.rename(backup_name, data_name)