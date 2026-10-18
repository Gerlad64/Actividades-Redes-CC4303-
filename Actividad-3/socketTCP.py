from __future__ import annotations

import socket
from dataclasses import dataclass, field
from random import randint
from socket import SocketType

from exceptions.handshake_errs import *
from Segment import *


@dataclass
class SocketTCP:
    """ Dataclass SocketTCP
    Implementa una versión simplificada del protocolo TCP usando sockets UDP por debajo.
    Presenta la misma API que la de sockets TCP de Python, aunque no con la funcionalidad completa
    en algunos casos. Esto con el propósito de hacer compatibles aquellos scripts que usan sockets
    de Python.
    """
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
    _timeout: float | None = None
    _seq_id: int | None = None
    _remaining: int = 0
    _buffer: bytes = b''

    @property
    def bind_addr(self) -> tuple[str, int]:
        """Devuelve una vista de la dirección donde almacenada donde se escucharán peticiones"""
        return self._bind_addr

    @bind_addr.setter
    def bind_addr(self, addr: tuple[str, int]) -> None:
        """Establece una dirección a la que escuchar peticiones. Llama al método bind por detrás"""
        self.bind(addr)

    @property
    def ip(self) -> str:
        """Retorna la IP de bind"""
        return self.bind_addr[0]
        
    @property
    def port(self) -> int:
        """Devuelve el puerto de bind"""
        return self.bind_addr[1]

    def settimeout(self, t: float | None):
        """Establece un timeout para la comunicación STOP & WAIT. Si se establece None,
           la espera será bloqueante
        """
        self._timeout = t
        self._socket.settimeout(t)

    def gettimeout(self) -> float | None:
        return self._timeout

    @property
    def AF_INET(self):
        """Devuelve el mismo valor que socket.socket.AF_INET"""
        return socket.AF_INET

    @property
    def SOCK_STREAM(self):
        """Devuelve el mismo valor que socket.socket.AF_INET"""
        return socket.SOCK_STREAM
        
    # Métodos para mantener la misma API de socket.socket

    def connect(self, addr: tuple[str, int]) -> None:
        """Establece una conexión con el servidor en la dirección `addr`."""
        # Crear segmento
        seq_id = randint(0, 100)
        init_seg = Segment(seq_id, 0)
        init_seg.SYN = 1
        # Reservar dirección y actualizar bind_addr
        self._socket.bind(('127.0.0.1', 0))
        # Actualizar dirección de bind
        #self.bind_addr = self._socket.getsockname() # --> error: self.bind_addr ahora es property que llama a bind
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
        # Comunicación establecida
        # Se guarda addr
        self._conn_addr = addr_server
        # Se guarda el número de secuencia
        self._seq_id = seq_id
        # Completar el Handshake
        init_seg.SEQ = seq_id + 2
        # reset de flags
        init_seg.flags = 0
        init_seg.SYN = 0
        init_seg.ACK = 1
        self._seq_id = init_seg.SEQ
        self._socket.sendto(init_seg.to_bytes(), addr_server)
        
    
    def bind(self, addr: tuple[str, int]) -> None:
        """Establece la dirección de escucha peticiones en la dirección addr y actualiza la dirección de bind almacenada"""
        self._socket.bind(addr)
        self._bind_addr = self._socket.getsockname()

    def accept(self) -> tuple[SocketTCP, tuple[str, int]]:
        """Escucha peticiones"""
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
            new_sock._conn_addr = addr_client
            new_sock._seq_id = recv_seg.SEQ
            # Manda mensaje y retorna el socket usado como canal de
            # comunicación
            new_sock._socket.sendto(recv_seg.to_bytes(), addr_client)
            msg, _ = new_sock._socket.recvfrom(16)
            ack_seg = new_sock.parse_segment(msg)
            if ack_seg.flags == ACK:
                new_sock._seq_id = ack_seg.SEQ
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
        """Crea un socketTCP, los parámetros se mantienen para igualar a la API de sockets de python"""
        return cls()

    def listen(self, workers: int) -> None:
        pass

    def close(self) -> None:
        """Cierra la conexión"""
        print("Closing Connection")
        # TODO: mandar secuencia FIN
        self._socket.close()

    def send(self, message: bytes) -> None:
        """Manda un mensaje por el canal de comunicación establecido usando STOP & WAIT"""
        if not self._seq_id:
            raise Exception("No connection established")
        
        # Usa Stop & Wait para mandar el primer segmento indicando el
        # largo del mensaje, y luego, lo usa para mandar iterativamente
        # el mensaje en paquetes pequeños
        def _stop_and_wait(packet: bytes, expected_seq):
            while True:
                # Bucle hasta recibir segmentos adecuados
                self._socket.sendto(packet, self._conn_addr)
                try:
                    recv_msg, _ = self._socket.recvfrom(16)
                except TimeoutError: 
                    # Vuelve a mandar mensaje en caso de timeout
                    continue
                recv_seg = Segment.from_bytes(recv_msg)
                if recv_seg.SEQ == expected_seq and recv_seg.flags == ACK:
                    break # ACK recibido y secuencia correcta 
           
        seg = Segment(seq=self._seq_id)

        # Primer Segmento
        seg.DTA_LEN = len(message)
        expected_seq = seg.SEQ + seg.DTA_LEN
        _stop_and_wait(seg.to_bytes(), expected_seq)
         
        # Segmento recibido
        # Separa el mensaje en trozos de 16 bytes
        # y los manda mediante Stop & Wait
        for i in range(0, len(message), 16):
            m = message[i:i+16]
            seg.DTA_LEN = len(m)
            # armar paquete con segmento y mensaje
            msg = seg.to_bytes() + m
            expected_seq = seg.SEQ + seg.DTA_LEN
            _stop_and_wait(msg, expected_seq) 
            # actualizar secuencia para próximo paquete
            seg.SEQ = expected_seq
            
        self._seq_id = seg.SEQ
        
    def recv(self, buff_size: int) -> bytes:
        def _recv_seg() -> tuple[Segment, bytes]:
            while True:
                # Recibir y parsear segmento y datos
                recv_msg, _ = self._socket.recvfrom(5 + 16) # 5 == largo del segmento
                recv_seg = Segment.from_bytes(recv_msg)
                dta = recv_msg[5:]
                # Secuencia requerida para mandar ACK
                ack_seq = recv_seg.SEQ + recv_seg.DTA_LEN 
                # Mensaje nuevo: la secuencia recibida coincide con la guardada
                is_new = recv_seg.SEQ == self._seq_id
                # Mensaje duplicado: La secuencia de ACK coincide con la guardada
                is_dup = ack_seq == self._seq_id
                print(f"SEQ={recv_seg.SEQ} DTA_LEN={recv_seg.DTA_LEN} esperado={self._seq_id} dta={dta!r}")
                if not (is_new or is_dup): # Mensaje de externo
                    continue
                # Manda ACK (ya sea nuevo o duplicado)
                ack = Segment(seq=ack_seq, flags=ACK)
                self._socket.sendto(ack.to_bytes(), self._conn_addr)
                # Si el mensaje recibido es nuevo retorna el segmento y los datos
                # en la próxima llamada a _recv_seg se vuelve a mandar si no llegó la primera vez
                if is_new:
                    return recv_seg, dta
                
            
        # Primer segmento recibido contiene los datos a recibir
        if self._remaining == 0 and len(self._buffer) == 0:
            recv_seg, _ = _recv_seg()
            self._remaining = recv_seg.DTA_LEN
        target = min(self._remaining + len(self._buffer), buff_size)
        while len(self._buffer) < target:
            # recibe los datos
            recv_seg, dta = _recv_seg()
            assert(self._seq_id)
            assert(recv_seg.DTA_LEN == len(dta))
            # Actualiza el número de secuencia con 
            self._seq_id += len(dta)
            self._remaining -= len(dta)
            self._buffer += dta
        msg, self._buffer = self._buffer[:target], self._buffer[target:] 
        
        return msg
        
    @staticmethod
    def create_segment(seq: int, flags: int) -> Segment:
        """Crea un segmento"""
        return Segment(seq, flags)

    @staticmethod
    def parse_segment(seg: bytes, offset: int=0) -> Segment:
        """Parsea bytes recibidos a un segmento"""
        return Segment.from_bytes(seg, offset)