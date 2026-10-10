#import socket
from config import *
from socketTCP import SocketTCP as socket

if __name__ == '__main__':
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(SERVER_ADDRESS)
    sock.listen(1)

    conn_sock, addr = sock.accept()
    print(addr)
    sock.close()