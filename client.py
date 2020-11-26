from socket import *

serverName = 'localhost'

serverPort = 12000

clientSocket = socket(AF_INET, SOCK_DGRAM)

with open('configA.txt') as f:
    read_data = f.read()
f.close()

print(read_data)

# message = input("Input lowercase sentence: ")
# messageEncoded = message.encode()
# print(messageEncoded)
# print(messageEncoded.decode())
# clientSocket.sendto(messageEncoded, (serverName, serverPort))

clientSocket.sendto(read_data.encode(), (serverName, serverPort))

modifiedMessage, serverAddress = clientSocket.recvfrom(2048)

print(modifiedMessage.decode())

clientSocket.close()
