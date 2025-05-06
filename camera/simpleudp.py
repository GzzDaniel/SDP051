from socket import *

clientSocket = socket(AF_INET, SOCK_DGRAM)

message = input('input: ')

clientSocket.sendto(message.encode(), ('100.77.69.88', 3000))


modifiedMessage, addr = clientSocket.recvfrom(2048)
print(modifiedMessage.decode())

clientSocket.close()
