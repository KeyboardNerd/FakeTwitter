'''
boot up the server and attach a controller to the server
'''
import sys

import config

from multiprocessing import Process
import client
import config as c
import server
import tweeter
import reliablestorage as data
import paxos

def init_server(sid, sport):
    try:
        data.init("%d"%(sid,))
        server.listen("0.0.0.0", sport, tweeter.router)
    except KeyboardInterrupt:
        print '\n=====server terminated by user=====\n'

def parse_flag():
    if not sys.argv[1].isdigit():
        print "The site id \"" + sys.argv[1] + "\" is invalid. It should be an integer."
        exit(1)

    my_node = int(sys.argv[1])
    c.load_sites("config.json")
    c.my_site = c.get_site_by_id(my_node)

    if not c.my_site:
        print "The site id \"" + sys.argv[1] + "\" is invalid. It cannot be found in the config file."
        exit(1)

    print "I am User '%s' Addr '%s' Node %d"%(c.my_site.name, c.my_site.addr, c.my_site.id)
    print "I know these users:"
    for site in c.all_sites:
        print "User '%s' Addr '%s' Node %d"%(site.name, site.addr, site.id)

if __name__ == '__main__':
    parse_flag()
    Process(target=init_server, args=(c.my_site.id,c.my_site.port)).start()
    try:
        client.init(c.my_site.id, c.all_sites)
    except KeyboardInterrupt:
        print '\n=====client terminated by user=====\n'
