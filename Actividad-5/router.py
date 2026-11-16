
import socket
import sys

from config import *
from packet.packet import Packet
from router_table import RouterTable


def network(router_ip: str, router_port: int, router_routes: str) -> None:
    """Levanta un router en (router_ip, router_port) que hace forwarding según la tabla `router_routes`."""
    router_addr = (router_ip, router_port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    table = RouterTable(ROUTES_PATH / router_routes)

    sock.bind((router_ip, router_port))
    while True:
        try:
            msg, _ = sock.recvfrom(32)
            packet = Packet.from_bytes(msg)
            packet_str = f"{packet.ADDR[0]};{packet.ADDR[1]};{packet.TTL};{packet.msg.decode()}"
            if packet.TTL == 0:
                print(f"Se recibió paquete {packet_str} con TTL 0")
            elif packet.ADDR == router_addr:
                m = packet.msg.decode()
                print("paquete recibido:" + m)
            elif (next_hop := table.check(packet.ADDR)) is not None:
                packet.TTL -= 1
                packet.sendto(sock, *next_hop)
                print(f"redirigiendo paquete {packet_str} con destino final {packet.ADDR} desde {router_addr} hacia {next_hop}")
            else:
                print(f"No hay rutas hacia {packet.ADDR} para paquete {packet_str}")

        except KeyboardInterrupt:
            break

    sock.close()


if __name__ == '__main__':
    print(BANNER)
    network(sys.argv[1], int(sys.argv[2]), sys.argv[3])
