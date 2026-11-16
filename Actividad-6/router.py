
import socket
import sys

from config import *
from packet.fragmentation import fragment_IP_packet, reassemble_IP_packet
from packet.packet import Packet
from router_table import RouterTable


def network(router_ip: str, router_port: int, router_routes: str) -> None:
    """Levanta un router en (router_ip, router_port) que hace forwarding según la tabla `router_routes`.
    Fragmenta lo que reenvía según el MTU del enlace y reensambla los fragmentos destinados a él.
    """
    router_addr = (router_ip, router_port)
    # fragmentos recibidos con destino a este router: ID del paquete -> fragmentos acumulados (en bytes)
    received: dict[int, list[bytes]] = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    table = RouterTable(ROUTES_PATH / router_routes)

    sock.bind((router_ip, router_port))
    while True:
        try:
            msg, _ = sock.recvfrom(SOCK_BUFFER_SIZE)
            packet = Packet.from_bytes(msg)
            packet_str = str(packet)
            if packet.TTL == 0:
                print(f"Se recibió paquete {packet_str} con TTL 0")
            elif packet.ADDR == router_addr:
                received.setdefault(packet.ID, []).append(msg)
                IP_packet = reassemble_IP_packet(received[packet.ID])
                if IP_packet is not None:
                    del received[packet.ID]
                    print("paquete recibido:" + Packet.from_bytes(IP_packet).msg.decode())
            elif (route := table.check(packet.ADDR)) is not None:
                next_hop, mtu = route
                packet.TTL -= 1
                fragments = fragment_IP_packet(packet.to_bytes(), mtu)
                for fragment in fragments:
                    sock.sendto(fragment, next_hop)
                print(f"redirigiendo paquete {packet_str} con destino final {packet.ADDR} desde {router_addr} hacia {next_hop}"
                      f" en {len(fragments)} fragmento(s) (MTU {mtu})")
            else:
                print(f"No hay rutas hacia {packet.ADDR} para paquete {packet_str}")

        except KeyboardInterrupt:
            break

    sock.close()


if __name__ == '__main__':
    print(BANNER)
    network(sys.argv[1], int(sys.argv[2]), sys.argv[3])
