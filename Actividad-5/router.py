
import socket
import sys

from config import *

if __name__ == '__main__':
    router_ip = sys.argv[1]
    router_port = int(sys.argv[2])
    router_routes = sys.argv[3]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.bind((router_ip, router_port))
    print(BANNER)
    print(router_ip, router_port, router_routes, sep="\t")
    
    sock.close()