import storage
import server
# global timeout = 3000

if __name__ == '__main__':
    print "Starting server at ..."
    # start listening server
    print "Welcome user ..."
    # accept input
    while True:
        print "======================================================="
        print "Please make a selection (tweet/block/unblock/view/quit)"
        command = raw_input("> ")
        if command.startswith("tweet "):
            message = command[6:]
            print "Sending Tweet: \"" + message + "\""
            # send message
        elif command.startswith("block "):
            toblock = command[6:]
            print "Blocking user: \"" + toblock + "\""
            # block user
        elif command.startswith("unblock "):
            tounblock = command[8:]
            print "Unblocking user: \"" + tounblock + "\""
            # unblock user
        elif command == "view":
            print "Here are all the tweets: "
            # show tweets
        elif command == "quit":
            print "Bye!"
            os.exit(0)
        else:
            print "Invalid command! Usage:"
            print "> tweet <message> - tweet a message"
            print "> block <sid> - block a user by site id"
            print "> unblock <sid> - tweet a message"
            print "> quit - close this program"

def broadcastTweet(message):
    # dictionary is global
    # storage.dict.for all
    # new thread
    # send message
    pass
