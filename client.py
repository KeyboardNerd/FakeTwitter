import requests
import config
import sys
import socket
# global timeout = 3000

all_sites, my_site = None, None
address, port = None, 0

def run():
    print "Welcome user " + my_site.name + "!\nNode: " + str(my_site.node) + ", address: " + my_site.addr
    print "Global Twitter users:", 
    for site in all_sites:
        print "\"" + site.name + "\"",
    print ""
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
            print "unblock <username> - unblock a user by site id"
            print "suicide - shut down the server"
            print "view - view the timeline"
            print "quit - exit this program"

def request(address, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address, port))
    sock.send(message)
    sock.send('\00')
    data = ""
    while True:
        segment = sock.recv(1024)
        if not segment:
            break
        data += segment
    print data

if __name__ == '__main__':
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
    address = my_site.addr.split(":")[0]
    port = int(my_site.addr.split(":")[1])
    request(address, port, "request test message 123123123")
    run()