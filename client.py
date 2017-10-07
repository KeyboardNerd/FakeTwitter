import requests
import config
import sys
# global timeout = 3000

def run():
    _, all_sites = config.load("config.json")
    my_site = None
    while not my_site:
        name = raw_input("who are you?\r\n> ")
        for site in all_sites:
            if site.name == name:
                my_site = site

    print "welcome user " + my_site.name + " node " + str(my_site.node) + " addr " + my_site.addr
    print "you can tell me to 'tweet <message>' or 'block <username>' or 'unblock <username>' or 'view' timeline or 'suicide' or 'quit':"
    while True:
        command = raw_input("> ")
        if command.startswith("tweet "):
            message = command[6:]
            print "Sending Tweet: \"" + message + "\""
            print requests.post(my_site.addr+"/post", json={"message": message})
        elif command.startswith("block "):
            toblock = command[6:]
            print "Blocking user: \"" + toblock + "\""
            print requests.get(my_site.addr+"/block", params={"user": toblock})
        elif command.startswith("unblock "):
            tounblock = command[8:]
            print "Unblocking user: \"" + tounblock + "\""
            print requests.get(my_site.addr+"/unblock", params={"user": tounblock})
        elif command == "view":
            print "Here are all the tweets: "
            # show tweets
            r = requests.get(my_site.addr+"/timeline")
            for tweet in r.json()['timeline']:
                print "user: %s says '%s' on '%s'"%(tweet['user'], tweet['message'], tweet['time'])
        elif command == "quit":
            sys.exit(0)
        elif command == 'suicide':
            requests.get(my_site.addr+"/suicide")
        else:
            print "Invalid command! Usage:"
            print "tweet <message> - tweet a message"
            print "block <username> - block a user by site id"
            print "unblock <username> - tweet a message"
            print "suicide - to shut down the server"
            print "view - to view the timeline"
            print "quit - close this program"

if __name__ == '__main__':
    run()