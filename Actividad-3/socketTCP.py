from __future__ import annotations

import socket
from dataclasses import dataclass, field
from random import randint
from socket import SocketType

from exceptions.handshake_errs import *
from Segment import *


@dataclass
class SocketTCP:
    _bind_addr: tuple[str, int] = field(
        default=('notvalid', 8080),
        init=False
    )
    _conn_addr: tuple[str, int] = field(
        default=('notvalid', 8070),
        init=False
    )
    _socket: SocketType = field(
        default_factory=lambda: socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
        repr=False,
        compare=False
    )

    @property
    def bind_addr(self) -> tuple[str, int]:
        return self._bind_addr

    @bind_addr.setter
    def bind_addr(self, addr: tuple[str, int]) -> None:
        self.bind(addr)

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
            if recv_seg.flags != SYN+ACK:
                raise SegmentFlagsErr(
                    expected=SYN+ACK, 
                    actual=recv_seg, 
                    step=f"while expecting server with addr {addr_server[0]}:{addr_server[1]} to respond SYN+ACK"
                )
            if recv_seg.SEQ != seq_id + 1:
                raise SequenceErr(
                    expected= seq_id + 1,
                    actual= recv_seg.SEQ,
                    step=f"after receiving SYN+ACK from server with addr {addr_server[0]}:{addr_server[1]}"
                )
            break
        
        # Se guarda addr
        self.conn_addr = addr_server
        # Completar el Handshake
        init_seg.SEQ = seq_id + 2
        # reset de flags
        init_seg.flags = 0
        init_seg.SYN = 0
        init_seg.ACK = 1
        self._socket.sendto(init_seg.to_bytes(), addr_server)
        
    
    def bind(self, addr: tuple[str, int]) -> None:
        self._socket.bind(addr)
        self._bind_addr = self._socket.getsockname()

    def accept(self) -> tuple[SocketTCP, tuple[str, int]]:
        if self.bind_addr[0] == 'notvalid':
            raise Exception("Not bind address")
        # Espera recivir mensaje SYNchronize
        msg, addr_client = self._socket.recvfrom(16)
        recv_seg = SocketTCP.parse_segment(msg)
        # Sincronización recivida
        if recv_seg.flags == SYN:
            # Manda SYN + ACK 
            recv_seg.flags = SYN + ACK
            recv_seg.SEQ += 1
            # Crea nuevo socket (canal de comunicación)
            new_sock = SocketTCP()
            new_sock.bind((self.bind_addr[0], 0))
            new_sock.conn_addr = addr_client
            # Manda mensaje y retorna el socket usado como canal de
            # comunicación
            new_sock._socket.sendto(recv_seg.to_bytes(), addr_client)
            msg, _ = new_sock._socket.recvfrom(16)
            ack_seg = new_sock.parse_segment(msg)
            if ack_seg.flags == ACK:
                return (new_sock, new_sock.bind_addr)
                
            raise SegmentFlagsErr(
                expected=ACK,
                actual=ack_seg,
                step="while completing the handshake's last step (ACK from client)"
            )
                
        raise SegmentFlagsErr(
            expected=SYN,
            actual=recv_seg.flags,
            step="while expecting SYN request from client"
        )

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