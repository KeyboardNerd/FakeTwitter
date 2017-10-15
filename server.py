'''
server handles incoming connections and send responds.

the language is <message>\00
'''

import socket
import threading
import json
import api

def listen(hostname, port, router):
    '''
    start listening to a port on hostname:port
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((hostname, port))
    print "server| Server started at " + hostname + ":" + str(port)
    sock.listen(1)
    while True:
        connection, clientaddress = sock.accept()
        print "server| connection from " + str(clientaddress)
        handle = threading.Thread(
            target = connectionhandler, 
            args = (connection, router)
        )
        handle.start()

def connectionhandler(conn, router):
    data = []
    valid = False
    while True:
        segment = conn.recv(1024)
        if not segment or segment[-1] == '\00':
            if segment:
                valid = True
                data.append(segment[:-1])
            break
        data.append(segment)
    if valid:
        response = router("".join(data))
        conn.send(make_message(response))
    conn.close()

def async_send(address, port, message):
    threading.Thread(target=try_send, args=(address, port, message)).start()

def try_send(address, port, message):
    '''
    send sends a message to designated address:port with the message + \00
    '''
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        conn.connect((address, port))
        conn.send(make_message(message))
    except Exception as e:
        print 'server| %s, trying send to %s:%d'%(str(e), address, port)
    finally:
        # remove zombie sockets
        conn.close()

def make_message(message):
    return message + '\00'
def blocking_req(address, port, message):
    print "client| sending %s to %s:%d"%(message, address, port)
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((address, port))
    conn.send(make_message(message))
    data = []
    valid = False
    while True:
        segment = conn.recv(1024)
        if not segment or segment[-1] == '\00':
            if segment:
                valid = True
                data.append(segment[:-1])
            break
        data.append(segment)
    if valid:
        return ''.join(data)
    return json.dumps({"stat": 500}) # server drop connection unexpectly
