'''
server handles incoming connections and send responds.

the language is <message>\00
'''

import socket
import threading
import json

DEBUG = True
def debug_print(msg):
    if DEBUG:
        print msg
        
def listen(hostname, port, router):
    '''
    start listening to a port on hostname:port
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((hostname, port))
    debug_print("server| Server started at " + hostname + ":" + str(port))
    sock.listen(1)
    while True:
        connection, clientaddress = sock.accept()
        debug_print("server| connection from " + str(clientaddress))
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

# Async of try_send
def async_send(address, port, message):
    threading.Thread(target=try_send, args=(address, port, message)).start()

def make_message(message):
    return message + '\00'

# For propose (promise), accept (ack)
# Response is returned as json data
def blocking_req(address, port, message):
    debug_print("client| blocking sending %s to %s:%d"%(message, address, port))
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.settimeout(5)
    try:
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
            ret = ''.join(data)
            debug_print("client| success with", str(ret))
            return ret
    except Exception as e:
        debug_print("client| failed with " + str(e))
    finally:
        conn.close()
    return None

# For commit
# Response is not monitored
def try_send(address, port, message):
    debug_print("client| non-blocking sending %s to %s:%d"%(message, address, port))
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.settimeout(5)
    try:
        conn.connect((address, port))
        conn.send(make_message(message))
    except Exception as e:
        debug_print("client| failed with " + str(e))
    finally:
        conn.close()
