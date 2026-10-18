#import socket
from time import sleep
from config import *
from socketTCP import SocketTCP as socket

if __name__ == '__main__':
    """ TESTS de socketTCP por el lado del cliente"""
    #client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #client_sock.connect(SERVER_ADDRESS)
    #client_sock.close()

    # CLIENT
    client_socketTCP = socket.socket(1,2)
    client_socketTCP.connect(SERVER_ADDRESS)
    print(client_socketTCP._conn_addr)
    # test 1
    message = "Mensje de len=16".encode()
    client_socketTCP.send(message)
    # test 2
    message = "Mensaje de largo 19".encode()
    client_socketTCP.send(message)
    # test 3
    print(client_socketTCP._conn_addr)
    message = "Mensaje de largo 19".encode()
    client_socketTCP.send(message)
    sleep(0.5)
    print(client_socketTCP._conn_addr)
    client_socketTCP.close()