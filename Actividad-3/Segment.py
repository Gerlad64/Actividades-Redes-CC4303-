from __future__ import annotations

import ctypes
from enum import IntEnum


class SegmentFlags(IntEnum):
    ACK = 4
    SYN = 2
    FIN = 1

ACK = SegmentFlags.ACK
SYN = SegmentFlags.SYN
FIN = SegmentFlags.FIN

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
    DTA_LEN: int
    
    _fields_ = [
        ("SEQ", ctypes.c_uint32),
        ("DTA_LEN", ctypes.c_uint8, 5),
        ("ACK", ctypes.c_uint8, 1),
        ("SYN", ctypes.c_uint8, 1),
        ("FIN", ctypes.c_uint8, 1),
    ]
    _pack_ = 1

    def __init__(self, seq: int, flags: int = 0, len: int = 0) -> None:
        if flags < 0 or flags > 7:
            raise ValueError(
                f"Unexpected flag: A valid flag range from 0 to 7 inclusive,"
                f"but got {flags}"
            )
        if len > 31 or len < 0:
            raise ValueError(
                f"Unexpected data length: A Segment can only store positive numbers up to 31,"
                f"but got {len}"
            )
            
        super().__init__(
            SEQ= seq,
            DTA_LEN=len,
            ACK=flags & ACK != 0,
            SYN=flags & SYN != 0,
            FIN=flags & FIN != 0
        )

    @property
    def flags(self) -> int:
        return (self.ACK << 2) + (self.SYN << 1) + self.FIN

    @flags.setter
    def flags(self, value: int) -> None:
        self.ACK = value & ACK != 0
        self.SYN = value & SYN != 0
        self.FIN = value & FIN != 0
    
    def to_bytes(self):
        return bytes(self)

    @classmethod
    def from_bytes(cls, seg: bytes, offset: int = 0) -> Segment:
        """Dado un mensaje en bytes, retorna la estructura con los campos
           almacenados. Requiere una secuencia de almenos 5 bytes, donde 
           los primeros 4 almacenan el número de secuencia y el resto 
           las flags ACK, SYN, FIN en ese orden.
        """
        if len(seg) - offset < 5:
            raise ValueError(
                f"Byte sequence too short: expected at least 5 bytes after offset {offset},"
                f"but got {len(seg) - offset}"
            )
        seq     = int.from_bytes(seg[offset:offset+4])
        flags   = int.from_bytes(seg[offset + 4:offset + 5]) & 7
        dta_len = int.from_bytes(seg[offset + 4:offset + 5]) >> 3
        return cls(seq, flags, dta_len)

    def flag_to_str(self):
        """Devuelve un string que indica cuales flags del segmento guradado están activas"""
        active_flags = [f for f in ["ACK", "SYN", "FIN"] if getattr(self, f) > 0]
        
        return "NO-FLAGS" if self.flags == 0 else "+".join(active_flags)

    @staticmethod
    def intflag_to_str(flags: int):
        """Toma una flag en formato int y devuelve un string que indica cuales flags se encuentran activas"""
        active_flags = [f.name for f in SegmentFlags if (flags & f.value) > 0] 

        return "NO-FLAGS" if flags & 7 == 0 else "+".join(active_flags)