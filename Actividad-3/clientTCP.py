#import socket
from config import *
from socketTCP import SocketTCP as socket

if __name__ == '__main__':
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect(SERVER_ADDRESS)
    client_sock.close()