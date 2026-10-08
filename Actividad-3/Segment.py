from __future__ import annotations

import ctypes


class Segment(ctypes.BigEndianStructure):
    """ Segment
    Clase Segment para parsear segmentos de mensajes de
    comunicación TCP.
    """
    
    SEQ: int
    """Entero que almacena el número de secuencia"""
    ACK: int
    """bit que almacena la flag ACK"""
    SYN: int
    """bit que almacena la flag SYN"""
    FIN: int
    """bit que almacena la flag FIN"""
    
    _fields_ = [
        ("SEQ", ctypes.c_uint32),
        ("ACK", ctypes.c_uint8, 1),
        ("SYN", ctypes.c_uint8, 1),
        ("FIN", ctypes.c_uint8, 1),
        #("padd", ctypes.c_uint8, 5)
    ]
    _pack_ = 1

    def __init__(self, seq: int, flags: int) -> None:
        if flags < 0 or flags > 7:
            raise Exception("Flag Inválida")
            
        super().__init__(
            SEQ= seq,
            ACK=flags,
            SYN=flags,
            FIN=flags
           # padd=0
        )

    def to_bytes(self):
        return bytes(self)

    @classmethod
    def from_bytes(cls, seg: bytes, offset: int = 0) -> Segment:
        """Dado un mensaje en bytes, retorna la estructura con los campos
           almacenados. Requiere una secuencia de almenos 5 bytes, donde 
           los primeros 4 almacenan el número de secuencia y el resto 
           las flags ACK, SYN, FIN en ese orden.
        """
        if len(seg[offset:]):
            raise Exception("Byte sequence too short")
        seq   = int.from_bytes(seg[offset: offset+5])
        flags = int.from_bytes(seg[offset+5:])
        return cls(seq, flags)