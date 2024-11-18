from socket import *
import sys
import time
from threading import Thread
import ast
import os


if len(sys.argv) != 2:
    print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT ======\n")
    exit(0)
serverPort = int(sys.argv[1])
serverAddress = ('127.0.0.1', serverPort)

# define a socket for the client side, it would be used to communicate with the server
# the sending port is automatically picked from one of the free ports so no need to bind
clientSocket = socket(AF_INET, SOCK_DGRAM)
# define a listejning socket for the client to client connection 
clientTCPListeningSocket = socket(AF_INET, SOCK_STREAM)
# I made the TCP listening port automatically assigned to free port using 0
clientTCPListeningSocket.bind(('127.0.0.1', 0))
listeningSocketAddress = clientTCPListeningSocket.getsockname()
clientTCPListeningSocket.listen(10)

def newTCPconnections(clientTCPListeningSocket):
    while 1:
        connectionSocket, addr = clientTCPListeningSocket.accept()
        #print(f"New connection from {addr}")
        sentence = connectionSocket.recv(1024)
        message = sentence.decode('utf-8')
        parts = message.split("/", 1)
        message = parts[0] 
        userName = parts[1].strip()
        if message[:4] == "get:":
            file_path = os.path.join(os.getcwd(), userName, message[4:])
            with open(file_path, 'rb') as f:
                #print("Sending file...")
                while True:
                    file_data = f.read(1024)
                    if not file_data:
                        connectionSocket.close()
                        break
                    connectionSocket.send(file_data)


def heartbeat():
    while True:
        message = "heartbeat"
        clientSocket.sendto(message.encode('utf-8'), serverAddress)
        time.sleep(2)

def requestFile(message):
    parts = message.split("/", 3) 
    # Extract clientAddress
    clientAddressPart = parts[0]
    # extract filename
    file = parts[1].strip()
    # extract user with file username
    userName = parts[2].strip()
    #extract current user who wants file
    curr = parts[3].strip()
    # Further split to get the actual address value
    clientAddress = ast.literal_eval(clientAddressPart.split(":")[1])
    clientTCPSocket = socket(AF_INET, SOCK_STREAM)
    clientTCPSocket.connect(clientAddress)
    message = "get:" + file + "/" + userName
    clientTCPSocket.send(message.encode())
    # Open a file to write the received data to
    file_path = os.path.join(os.getcwd(), curr, file)
    with open(file_path, 'wb') as f:  
        while True:
            #print("entered this loop")
            data = clientTCPSocket.recv(1024)
            if not data:  
                #print("we finally exiting")
                break
            #print("writing this shit up: "+ data.decode())
            f.write(data)

    print(file + " downloaded successfully")

def primary():
    print("Welcome to BitTrickle!")
    print("Available commands are: get, lap, lpf, pub, sch, unp, xit")
    while 1:
        message = input("> ")
        if message == "xit":
            print("Goodbye!")
            break
        clientSocket.sendto(message.encode('utf-8'), serverAddress)
        data = clientSocket.recv(1024)
        receivedMessage = data.decode()
        if receivedMessage[:26] == "clientTCPListeningAddress:":
            requestFile(receivedMessage)
        else:
            print(receivedMessage)
    
# log in credentials loop
unverified = 1

while unverified:
    userName = input("Enter username: ")
    userPassword = input("Enter password: ")
    userLogin = "Login:" + userName + " " + userPassword + " " + str(listeningSocketAddress)
    # print(userLogin)
    clientSocket.sendto(userLogin.encode('utf-8'), serverAddress)
    data = clientSocket.recv(1024)
    loginConfirmation = data.decode()
    if loginConfirmation == '1': 
        unverified = 0
        if not os.path.exists(userName):
            # print("created folder")
            os.makedirs(userName)
    else:
        print("Authentication failed. Please try again.")

# put heartbeat onto a seperate thread
heartbeat_thread = Thread(target=heartbeat)
heartbeat_thread.daemon = True 
heartbeat_thread.start()

# Put newTCPconnections onto a separate thread
tcp_listener_thread = Thread(target=newTCPconnections, args=(clientTCPListeningSocket,))
tcp_listener_thread.daemon = True
tcp_listener_thread.start()

# start primary program
primary()

clientSocket.close()
clientTCPListeningSocket.close()
