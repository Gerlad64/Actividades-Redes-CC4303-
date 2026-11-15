
import socket
import sys

if __name__ == '__main__':
    router_ip = sys.argv[0]
    router_port = int(sys.argv[1])
    router_routes = sys.argv[2]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.bind((router_ip, router_port))