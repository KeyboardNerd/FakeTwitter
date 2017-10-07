from service import TweetService, Site
from storage import Storage
import json
import sys

my_site = None
sites = []
# read config file
with open("config.json") as f:
    d =  json.load(f)
    for site in d["sites"]:
        new_site = Site(site['node'], site['name'], site['addr'])
        sites.append(new_site)
        if site["node"] == d["my_node"]:
            my_site = new_site

# connect to database
db = Storage(my_site.node, len(sites), "datafile")
# initialize service
twitter = TweetService(db, my_site, sites)
twitter.block("Ha MaPi")
twitter.unblock("Ha MaPi")
twitter.tweet("Wo yao chifan")
