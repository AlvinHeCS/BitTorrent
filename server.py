#coding: utf-8
from socket import *
from threading import Thread
import sys, time

if len(sys.argv) != 2:
    print("\n===== Error usage ======\n")
    exit(0)
serverPort = int(sys.argv[1])
serverAddress = ('127.0.0.1', serverPort)

# UDP server socket for all UDP request from clients
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(serverAddress)
print('The server is ready to receive')

# dictionary mapping online clients to heartbeat 
# need clientAddress for when another peer wants to dowload a file from that peer
# example {clientAddress} : ({username}, {heartbeat}, {TCPlisteningport})
onlineClients = {}

# dictionary mapping username to files
# example {username} : {[listOfFiles]}
userFiles = {}

# returns true if user is online and false if user is not online
def alreadyOnline(username, onlineClients):
    usernames = []
    for value in onlineClients.values():
        user, heartbeat, tcpConnection = value
        usernames.append(user)
    
    for user in usernames:
        if user == username:
            return True
    return False

# checks if a login is valid
def process_login(userPassConnection, clientAddress, onlineClients):
    print(userPassConnection)
    username, password, TCPlisteningPort1, TCPlisteningPort2  = userPassConnection.split()
    userPass = username + " " + password
    with open('server/credentials.txt', 'r') as file:
        for line in file:
            if line.strip() == userPass and not alreadyOnline(username, onlineClients):
                print(line.strip())
                print(userPass)
                # passed login validity
                print("this login has correct creditentials")
                message = '1'
                serverSocket.sendto(message.encode(), clientAddress)
                return 1

        else:
            message = '0'
            serverSocket.sendto(message.encode(), clientAddress)
            return 0

# removes clients that havnt sent a heartbeat in the last 3 seconds
def monitorOnlineUsers():
    while True:
        current_time = time.time()
        inactiveClients = []
        for client, information in onlineClients.items():
            username, lastHeartbeat, tcpListeningPort = information
            if current_time - lastHeartbeat > 3:
                inactiveClients.append(client)

        for client in inactiveClients:
            print("deleted this client" + str(client))
            del onlineClients[client]
        print(onlineClients)
        time.sleep(1) 

#commands
def login(message, clientAddress, onlineClients, userFiles):
    print("New login request")
    print(message[6:])
    if process_login(message[6:], clientAddress, onlineClients):
    # add user to onlineClients
        message = message[6:].strip()
        user, password, TCPlisteningPort1, TCPlisteningPort2 = message.split()
        TCPlisteningPort = TCPlisteningPort1 + " " + TCPlisteningPort2
        onlineClients[clientAddress] = (user, time.time(), TCPlisteningPort)
        print("===========")
        print(onlineClients[clientAddress])
        # create a userfile of this
        if onlineClients[clientAddress][0] not in userFiles:
            userFiles[onlineClients[clientAddress][0]] = []
    return onlineClients, userFiles

def lap(onlineClients, clientAddress, serverSocket):
    print("active peers request")
    if len(onlineClients) == 1:
        message = "No active peers"
        serverSocket.sendto(message.encode(), clientAddress)
        return
    currUser = onlineClients[clientAddress][0]
    peers = ""
    amountOfPeers = 0
    for value in onlineClients.values():
        user = value[0]
        if user != currUser:
            amountOfPeers += 1
            peers = peers + user + "\n" 
    peers = peers.rstrip()
    if amountOfPeers == 1:
        message = "active peer:\n" 
    else:
        message = "active peers:\n"
    message = str(amountOfPeers) + " " + message + peers
    serverSocket.sendto(message.encode(), clientAddress)  

def heartbeat(onlineClients, clientAddress):
    username = onlineClients[clientAddress][0]
    tcplisteningconnection = onlineClients[clientAddress][2]
    onlineClients[clientAddress] = username, time.time(), tcplisteningconnection
    return onlineClients

def pub(userFiles, file, user, serverSocket, clientAddress):
    if file not in userFiles[user]:
        message = "File published successfully"
        serverSocket.sendto(message.encode(), clientAddress)
        return userFiles[user].append(file)
    else:
        message = "File published successfully"
        serverSocket.sendto(message.encode(), clientAddress)
        return userFiles
    
def lpf(userFiles, user, clientAddress, serverSocket):
    message = "file published:\n"
    if len(userFiles[user]) == 0:
        message = "No files published"
        serverSocket.sendto(message.encode(), clientAddress)
        return
    for file in userFiles[user]:
        message = message + file.strip() + "\n"
    message = str(len(userFiles[user])) + " " + message.rstrip()
    serverSocket.sendto(message.encode(), clientAddress)

def unp(userFiles, clientAddress, serverSocket, user, file):
    if file in userFiles[user]:
        userFiles[user].remove(file)
        message = "File unpublished successfully"
        serverSocket.sendto(message.encode(), clientAddress)
    else:
        message = "File unpublication failed"
        serverSocket.sendto(message.encode(), clientAddress)   
    return userFiles

def sch(substring, userFiles, clientAddress, serverSocket, currUser):
    matchingFiles = []
    message = ""
    for user, files in userFiles.items():      
        for file in files:
            if substring.strip() in file and alreadyOnline(user, onlineClients) and file not in userFiles[currUser]:
                matchingFiles.append(file)
    if len(matchingFiles) == 0:
        message = "No files found"
        serverSocket.sendto(message.encode(), clientAddress) 
    else:
        message = str(len(matchingFiles)) + " " + "file found:\n"
        for file in matchingFiles:
            message = message + file.strip() + "\n"
        message = message.rstrip()
        serverSocket.sendto(message.encode(), clientAddress)

# sends either the ip address of an active client with the designated file or unsuccessful
def get(targetFile, userFiles, serverSocket, clientAddress, onlineClients):
    for key, value in onlineClients.items():
        for file in userFiles[value[0]]:
            if file == targetFile:
                # print("file found")
                message = "clientTCPListeningAddress:" + value[2] + "/" + targetFile + "/" + value[0] + "/" + onlineClients[clientAddress][0]
                # print(key)
                serverSocket.sendto(message.encode(), clientAddress)
                return 
    message = "File not found"
    serverSocket.sendto(message.encode(), clientAddress)
    
# put monitor OnlineUsers in a seperate thread
monitor_thread = Thread(target=monitorOnlineUsers)
monitor_thread.daemon = True  # Allows the thread to close when the main program exits
monitor_thread.start()


while 1:
    # receive data from the client, now we know who we are talking with
    message, clientAddress = serverSocket.recvfrom(2048)
    message = message.decode()
    if message[:6] == 'Login:':
        onlineClients, userFiles = login(message, clientAddress, onlineClients, userFiles)
    # update heartbeat for clients 
    elif message == 'heartbeat':
        onlineClients = heartbeat(onlineClients, clientAddress)
    elif message == 'lap':
        lap(onlineClients, clientAddress, serverSocket)
    elif message[:3] == 'pub':
        pub(userFiles, message[3:], onlineClients[clientAddress][0], serverSocket, clientAddress)
        print(userFiles)
    elif message == 'lpf':
        lpf(userFiles, onlineClients[clientAddress][0], clientAddress, serverSocket)
    elif message[:3] == 'unp':
        unp(userFiles, clientAddress, serverSocket, onlineClients[clientAddress][0], message[3:])
    elif message[:3] == 'sch':
        sch(message[3:], userFiles, clientAddress, serverSocket, onlineClients[clientAddress][0])
    elif message[:3] == 'get':
        get(message[3:], userFiles, serverSocket, clientAddress, onlineClients)
    else:
        print("Cannot understand this message: " + message)

        


