
import socket

from config import *

if __name__ == '__main__':
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(SERVER_ADDRESS)
    print(BANNER)
    while True:
        message, address = udp_socket.recvfrom(SERVER_BUFFER_SIZE)
        print(message)