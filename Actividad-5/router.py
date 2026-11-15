
import socket
import sys

from config import *
from ip import Packet
from router_table import RouterTable

if __name__ == '__main__':
    router_ip = sys.argv[1]
    router_port = int(sys.argv[2])
    router_addr = (router_ip, router_port)
    router_routes = sys.argv[3]
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    table = RouterTable(ROUTES_PATH / router_routes)
    
    sock.bind((router_ip, router_port))
    print(BANNER)
    while True:
        try:
            msg, _ = sock.recvfrom(16)
            packet = Packet.from_bytes(msg)
            if packet.ADDR == router_addr:
                m = packet.msg.decode()
                print("paquete recibido:" + m[:5] + ("..." if len(m) > 5 else ""))
            elif (next_hop := table.check(packet.ADDR)) is not None:
                packet.sendto(sock, *next_hop)
                print("...")
            else:
                print("No hay rutas hacia...")
            
        except KeyboardInterrupt:
            break
    
    sock.close()