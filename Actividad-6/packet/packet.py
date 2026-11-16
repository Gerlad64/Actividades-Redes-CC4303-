from __future__ import annotations

import ctypes
import socket


class Packet(ctypes.BigEndianStructure):
    """ Packet
    Clase Packet del modulo ip.
    Maneja paquetes IP (o fragmentos) con dirección, puerto, TTL y los campos de fragmentación.
    `msg` tiene largo variable, por eso no está en `_fields_`.
    """
    IP: int
    PORT: int
    TTL: int
    ID: int
    OFFSET: int
    SIZE: int
    FLAG: int
    msg: bytes

    _fields_ = [
        ("IP", ctypes.c_uint32),
        ("PORT", ctypes.c_uint16),
        ("TTL", ctypes.c_uint8),
        ("ID", ctypes.c_uint16),
        ("OFFSET", ctypes.c_uint32),
        ("SIZE", ctypes.c_uint32),
        ("FLAG", ctypes.c_uint8),
    ]
    _pack_ = 1


    @property
    def ADDR(self) -> tuple[str, int]:
        return (socket.inet_ntoa(self.IP.to_bytes(4, byteorder='big')), self.PORT)

    def __init__(self, ip: int, port: int, msg: bytes = b'', ttl: int = 64,
                 packet_id: int = 0, offset: int = 0, flag: int = 0) -> None:
        """Crea un paquete. `SIZE` no se recibe: siempre es el largo de `msg`."""
        super().__init__(ip, port, ttl, packet_id, offset, len(msg), flag)
        self.msg = msg


    @classmethod
    def from_bytes(cls, IP_packet: bytes, offset: int = 0) -> Packet:
        """Crea un paquete a partir de bytes. Cumple el rol de `parse_packet`."""
        packet = cls.from_buffer_copy(IP_packet, offset)
        msg_start = offset + HEADER_SIZE
        packet.msg = IP_packet[msg_start: msg_start + packet.SIZE]
        return packet

    def to_bytes(self) -> bytes:
        """Entrega el paquete en bytes (header + mensaje). Cumple el rol de `create_packet`."""
        return bytes(memoryview(self)) + self.msg

    def __str__(self) -> str:
        """Paquete en formato legible: IP;Puerto;TTL;ID;Offset;Tamaño;FLAG;mensaje"""
        ip, port = self.ADDR
        msg = self.msg.decode(errors="replace")  # un fragmento puede cortar un carácter de más de 1 byte
        return f"{ip};{port};{self.TTL};{self.ID};{self.OFFSET};{self.SIZE};{self.FLAG};{msg}"

    def sendto(self, sock: socket.socket, ip: str, port: int) -> None:
        """Manda el paquete con dirección ip, puerto y mensaje almacenado en el objeto a otro router.
        Params:
            sock: socket no orientado a conexión por donde enviar el paquete
            ip: IP de envío, no necesariamente es igual a self.IP
            port: puerto de envío, no necesariamente es igual a self.PORT
        """
        sock.sendto(self.to_bytes(), (ip, port))


HEADER_SIZE: int = ctypes.sizeof(Packet)
"""Tamaño del header en bytes (18): es fijo, por lo que no depende del mensaje"""
