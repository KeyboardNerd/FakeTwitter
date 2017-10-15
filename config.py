'''
config contains the loading function to load the configuration file to sites.

NOTICE that the node numbers are inferred from the index of a site in the sites
list.
'''
import json
from storage import Site

def load(file_name, my_node):
    '''
    load loads the configuration file from disk.
    '''
    sites = []
    with open(file_name) as config_file:
        config = json.load(config_file)
        for node, site in enumerate(config["sites"]):
            new_site = Site(node, site['name'], site['addr'], site['port'])
            sites.append(new_site)
    return sites[my_node], sites
