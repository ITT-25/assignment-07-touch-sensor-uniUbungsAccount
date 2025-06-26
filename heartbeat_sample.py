import socket
import time
import json

IP = '127.0.0.1'
PORT = 5700

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

counter = 0

# sends every second an increasing heartbeat number
while True:
    message_dict = {}
    message_dict['heartbeat'] = counter

    message = json.dumps(message_dict)
    print(message)

    sock.sendto(message.encode(), (IP, PORT))

    counter += 1
    time.sleep(1)