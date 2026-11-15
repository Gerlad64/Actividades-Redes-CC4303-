import socket
import sys
import time

from packet.packet import Packet


def send(dst_ip: str, dst_port: int, msg: str, via_ip: str, via_port: int) -> None:
    """Envía un paquete IP con destino final (dst_ip, dst_port) a través del router (via_ip, via_port).
    Params:
        dst_ip: IP del router de destino final, se escribe en el header del paquete
        dst_port: puerto del router de destino final, se escribe en el header del paquete
        msg: mensaje a enviar, va después del header
        via_ip: IP del router al que se envía el paquete, no necesariamente es igual a dst_ip
        via_port: puerto del router al que se envía el paquete, no necesariamente es igual a dst_port
    """
    print(f"\n>>> enviando {dst_ip};{dst_port};{msg} a ({via_ip}, {via_port})", flush=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Packet(int.from_bytes(socket.inet_aton(dst_ip)), dst_port, msg.encode()).sendto(sock, via_ip, via_port)
    sock.close()
    time.sleep(0.3)


def main() -> None:
    """Uso: python3 -m packet.send ip_destino puerto_destino mensaje ip_envio puerto_envio"""
    send(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5]))


if __name__ == "__main__":
    main()
