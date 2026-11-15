from __future__ import annotations

import ctypes
import socket


class Packet(ctypes.BigEndianStructure):
    """ Packet
    Clase Packet del modulo ip.
    Maneja paquetes IP con dirección  y puerto
    """
    
    _fields_ = [
        ("IP", ctypes.c_uint32),
        ("PORT", ctypes.c_uint16),
    ]
    _pack_ = 1

    
    def __init__(self, ip: int, port: int, msg: bytes = b'') -> None:
        super().__init__(ip, port)
        self.msg: bytes = msg
    
    
    @classmethod
    def from_bytes(cls, IP_packet: bytes, offset: int = 0):
        """Crea un paquete a partir de bytes."""
        ip_start   = offset
        ip_end     = offset+4
        port_start = offset+4
        port_end   = offset+6
        return Packet(
            int.from_bytes(IP_packet[ip_start: ip_end]), 
            int.from_bytes(IP_packet[port_start: port_end]), 
            IP_packet[port_end:]
        )

    def to_bytes(self):
        return bytes(memoryview(self)) + self.msg

    def sendto(self, sock: socket.socket, ip: str, port: int) -> None:
        """Manda el paquete con dirección ip, puerto y mensaje almacenado en el objeto a otro router.
        Params:
            sock: socket no orientado a conexión por donde enviar el paquete
            ip: IP de envío, no necesariamente es igual a self.IP
            port: puerto de envío, no necesariamente es igual a self.PORT
        """
        sock.sendto(self.to_bytes(), (ip, port))
