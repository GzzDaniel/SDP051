from socket import *

def send_command(command):
    pi_ip = "100.102.212.96"
    pi_port = 4000

    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((pi_ip, pi_port))
    clientSocket.send(command.encode())
    response = clientSocket.recv(1024).decode()
    print(f"Response from Pi: {response}")
    clientSocket.close()

if __name__ == "__main__":
    send_command("forward")