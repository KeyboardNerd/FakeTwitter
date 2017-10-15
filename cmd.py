'''
boot up the server and attach a controller to the server
'''
import sys

import config
import storage
import service
import server
import api

from multiprocessing import Process
import client

def init_server(node, sites, data_file, debug_mode=False):
    database = storage.Storage(node, len(sites), data_file)
    tweet_service = service.TweetService(database, sites[node], sites)
    tweet_api = api.TweetAPI(tweet_service, server.async_send)
    if debug_mode:
        addr = sites[node].addr
    else:
        addr = "0.0.0.0" # bind to any any
    server.listen(addr, sites[node].port, tweet_api.route)

def parse_flag():
    if not sys.argv[1].isdigit():
        print "The site id \"" + sys.argv[1] + "\" is invalid. It should be an integer."
        exit(1)
    my_node = int(sys.argv[1])
    config_file = "config.json"
    data_file = "datafile%d.json"%(my_node,)
    my_site, sites = config.load(config_file, my_node)
    if my_site == None:
        print "The site id \"" + sys.argv[1] + "\" is invalid. It cannot be found in the config file."
        exit(1)
    print "I am User '%s' Addr '%s' Node %d"%(my_site.name, my_site.addr, my_site.node)
    print "I know these users:"
    for site in sites:
        print "User '%s' Addr '%s' Node %d"%(site.name, site.addr, site.node)
    return my_node, sites, data_file

if __name__ == '__main__':
    node, sites, data_file = parse_flag()
    Process(target=init_server, args=(node, sites, data_file)).start()
    client.init(node, sites)