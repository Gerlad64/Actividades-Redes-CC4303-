import socket
import sys

from packet.packet import Packet


def main() -> None:
    """Envía cada línea de stdin como un paquete IP, todas con el mismo header, sin pausas entre envíos.
    Uso: python3 prueba_router.py ip_destino puerto_destino ttl ip_router_inicial puerto_router_inicial < archivo
    """
    dst_ip, dst_port, ttl, via_ip, via_port = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for line in sys.stdin:
        msg = line.rstrip("\n").encode()
        Packet(int.from_bytes(socket.inet_aton(dst_ip)), dst_port, msg, ttl).sendto(sock, via_ip, via_port)
    sock.close()


if __name__ == "__main__":
    main()
