from __future__ import annotations

import socket
from dataclasses import dataclass, field
from random import randint

from Segment import Segment


@dataclass
class SocketTCP:
    bind_addr: tuple[str, int] = ('notvalid', 8080)
    conn_addr: tuple[str, int] = ('notvalid', 8070)
    _socket = field(default_factory=lambda: socket.socket(socket.AF_INET, socket.SOCK_DGRAM))

    @property
    def ip(self) -> str:
        return self.bind_addr[0]
        
    @property
    def port(self) -> int:
        return self.bind_addr[1]

    @property
    def AF_INET(self):
        return socket.AF_INET

    def SOCK_STREAM(self):
        return socket.SOCK_STREAM
        
    # Métodos para mantener la misma API de socket.socket

    def connect(self, addr: tuple[str, int]) -> None:
        # Crear segmento
        seq_id = randint(0, 100)
        init_seg = Segment(seq_id, 0)
        init_seg.SYN = 1
        # Reservar dirección
        self._socket.bind(('127.0.0.1', 0))
        # Actualizar dirección de bind
        self.bind_addr = self._socket.getsockname()
        # Mandarlo por la dirección bindeada
        self._socket.sendto(init_seg.to_bytes(), addr) # TODO timeout, mandar hasta recibir
        # Servidor crea nuevo socket, manda su addr y SYN+ACK
        # recibido por el socket
        while True:
            msg, addr_server = self._socket.recvfrom(16)
            recv_seg = SocketTCP.parse_segment(msg)
            if recv_seg.SYN == seq_id + 1 and recv_seg.ACK == 1:
                break
        
        # Se guarda addr
        self.conn_addr = addr_server
        # Completar el Handshake
        init_seg.SEQ += 2
        init_seg.SYN = 0
        init_seg.ACK = 1
        self._socket.sendto(init_seg.to_bytes(), addr_server)
        
    
    def bind(self, addr: tuple[str, int]) -> None:
        self._socket.bind(addr)
        self.bind_addr = self._socket.getsockname()

    def accept(self) -> tuple[SocketTCP, tuple[str, int]]:
        if self.bind_addr[0] == 'notvalid':
            raise Exception("Not bind address")
        # Espera recivir mensaje SYNchronize
        msg, addr_client = self._socket.recvfrom(16)
        recv_seg = SocketTCP.parse_segment(msg)
        # Sincronización recivida
        if recv_seg.SYN == 1:
            # Manda SYN + ACK 
            recv_seg.ACK = 1
            recv_seg.SEQ += 1
            # Crea nuevo socket (canal de comunicación)
            new_sock = SocketTCP()
            new_sock.bind((self.bind_addr[0], 0))
            new_sock.conn_addr = addr_client
            # Manda mensaje y retorna el socket usado como canal de
            # comunicación
            new_sock._socket.sendto(recv_seg.to_bytes(), addr_client)
            msg,_ = new_sock._socket.recvfrom(16)
            if new_sock.parse_segment(msg).ACK == 1:
                return (new_sock, new_sock.bind_addr)
                
        raise Exception("Accept error")

    @classmethod
    def socket(cls, foo, bar) -> SocketTCP:
        return cls()

    def listen(self, workers: int) -> None:
        pass

    def close(self) -> None:
        print("Closing Connection")
        
    @staticmethod
    def create_segment(seq: int, flags: int) -> Segment:
        return Segment(seq, flags)

    @staticmethod
    def parse_segment(seg: bytes, offset: int=0) -> Segment:
        return Segment.from_bytes(seg, offset)