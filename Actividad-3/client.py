import socket
import sys

from config import *

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = sys.stdin.read()

    for i in range(0, len(msg), 16):
        m = msg[i:i+16]
        sock.sendto(m.encode(), SERVER_ADDRESS)
    sock.sendto(b"EOF", SERVER_ADDRESS)