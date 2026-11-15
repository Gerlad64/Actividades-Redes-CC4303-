import socket
import sys
import time

from packet.packet import Packet


def send(ip: str, dst_port: int, msg: str, via_port: int) -> None:
    """Envía `msg` con destino final (ip, dst_port) a través del router (ip, via_port)."""
    print(f"\n>>> enviando {ip};{dst_port};{msg} a ({ip}, {via_port})", flush=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Packet(int.from_bytes(socket.inet_aton(ip)), dst_port, msg.encode()).sendto(sock, ip, via_port)
    sock.close()
    time.sleep(0.3)


def main() -> None:
    """Uso: python3 -m packet.send ip puerto_destino mensaje puerto_envio"""
    send(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))


if __name__ == "__main__":
    main()
