import json
from storage import Site

def load(file_name):
    my_site = None
    sites = []
    # read config file
    with open(file_name) as f:
        d =  json.load(f)
        for site in d["sites"]:
            new_site = Site(site['node'], site['name'], site['addr'])
            sites.append(new_site)
            if site["node"] == d["my_node"]:
                my_site = new_site
    return my_site, sites