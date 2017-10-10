import requests
import config
import sys
# global timeout = 3000

def run():
    _, all_sites = config.load("config.json")
    my_site = None
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        for site in all_sites:
            if site.node == int(sys.argv[1]):
                my_site = site
    while not my_site:
        name = raw_input("Twitter username: ")
        for site in all_sites:
            if site.name == name:
                my_site = site
        if not my_site:
            print "Make sure you entered a correct site name instead of a site id. Try again."

    print "Welcome user " + my_site.name + "!\nNode: " + str(my_site.node) + "\nAddress: " + my_site.addr
    print "Try 'tweet <message>', 'block/unblock <username>', 'view', 'suicide', 'quit':"
    while True:
        command = raw_input(my_site.name + "> ")
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
            print "Tweet list: "
            # fetch tweets
            r = requests.get(my_site.addr+"/timeline")
            for tweet in r.json()['timeline']:
                print "@%s %s\n%s"%(tweet['user'], tweet['time'].split(".")[0].replace("T", " "), str(tweet['message']))
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