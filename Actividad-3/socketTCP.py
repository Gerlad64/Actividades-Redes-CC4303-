from __future__ import annotations

import socket
import time
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
    _timeout: float | None = 1.0
    _seq_id: int | None = None
    _remaining: int = 0
    _buffer: bytes = b''

    def __post_init__(self) -> None:
        self._socket.settimeout(self._timeout)

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
        self._bind_addr = self._socket.getsockname()
        
        # Enviar SYN y esperar SYN+ACK con retransmisión por timeout
        addr_server = None
        while True:
            self._socket.sendto(init_seg.to_bytes(), addr)
            try:
                msg, addr_server = self._socket.recvfrom(16)
            except TimeoutError:
                print("DEBUG: Client connect timeout. Retrying SYN...")
                continue
            # segmento recibido!
            recv_seg = SocketTCP.parse_segment(msg)
            
            # flags inesperadas: se descarta
            if recv_seg.flags != SYN + ACK:
                continue
            # secuencia inesperada: se descarta
            if recv_seg.SEQ != seq_id + 1:
                continue
            break
        
        self._conn_addr = addr_server
        self._seq_id = seq_id
        
        # Completar el 3-way handshake enviando ACK final
        init_seg.SEQ = seq_id + 2
        init_seg.flags = ACK
        self._seq_id = init_seg.SEQ
        self._socket.sendto(init_seg.to_bytes(), addr_server)
        print("DEBUG: Client handshake complete.")
    
    def bind(self, addr: tuple[str, int]) -> None:
        """Establece la dirección de escucha peticiones en la dirección addr y actualiza la dirección de bind almacenada"""
        self._socket.bind(addr)
        self._bind_addr = self._socket.getsockname()

    def accept(self) -> tuple[SocketTCP, tuple[str, int]]:
        """Escucha peticiones de sincronización. 
        Cuando recibe una, crea un nuevo socket para establecer el canal de comunicación.

        Returns:
            El nuevo socket y la dirección del cliente.
        """
        if self.bind_addr[0] == 'notvalid':
            raise Exception("Not bind address")
        
        # Espera mensaje SYN
        while True:
            try:
                msg, addr_client = self._socket.recvfrom(16)
            except TimeoutError:
                continue
            # segmento recibido!
            recv_seg = SocketTCP.parse_segment(msg)
            # SYNchronización recibida!
            if recv_seg.flags == SYN:
                # configurar SYN + ACK y aumentar número de secuencia
                recv_seg.flags = SYN + ACK
                recv_seg.SEQ += 1
                # Crear nuevo socket y configurarlo (canal de comunicación)
                new_sock = SocketTCP()
                # Asigna misma IP de escucha en un puerto diferente
                new_sock.bind((self.bind_addr[0], 0))
                new_sock._conn_addr = addr_client
                new_sock._seq_id = recv_seg.SEQ
                new_sock.settimeout(self._timeout)
                
                # Enviar SYN+ACK y esperar ACK final del handshake
                while True:
                    new_sock._socket.sendto(recv_seg.to_bytes(), addr_client)
                    try:
                        msg_ack, _ = new_sock._socket.recvfrom(16)
                    except TimeoutError:
                        print("DEBUG: Server accept timeout waiting for final ACK. Retrying SYN+ACK...")
                        continue
                    
                    ack_seg = new_sock.parse_segment(msg_ack)
                    # ACK recibido!
                    if ack_seg.flags == ACK:
                        new_sock._seq_id = ack_seg.SEQ
                        print("DEBUG: Server handshake complete.")
                        return (new_sock, new_sock._conn_addr)
                    # SYN recibido por pérdida previa: volver a mandar SYN+ACK
                    elif ack_seg.flags == SYN:
                        continue
                    else:
                        continue

    @classmethod
    def socket(cls, foo, bar) -> SocketTCP:
        """Crea un socketTCP, los parámetros se mantienen para igualar a la API de sockets de python"""
        return cls()

    def listen(self, workers: int) -> None:
        pass

    def close(self) -> None:
        """Cierra la conexión (Host A)"""
        print("Closing Connection (Host A)")
        assert self._seq_id is not None
        
        # crea secuencia de FIN
        fin_seg = Segment(self._seq_id, FIN)
        closed_normally = False
        
        # Reintentar hasta 3 veces esperando FIN+ACK
        for attempt in range(3):
            print(f"DEBUG: Host A sending FIN (Attempt {attempt + 1})")
            self._socket.sendto(fin_seg.to_bytes(), self._conn_addr)
            try:
                msg, _ = self._socket.recvfrom(16)
            except TimeoutError:
                print("DEBUG: Host A timeout waiting for FIN+ACK. Retrying FIN...")
                continue
            # Segmento recibido!
            recv_seg = Segment.from_bytes(msg)
            if recv_seg.flags == FIN + ACK and recv_seg.SEQ == self._seq_id + 1:
                closed_normally = True
                break
        # Segmento recibido dentro de los 3 intentos
        if closed_normally:
            fin_seg.SEQ = self._seq_id + 2
            fin_seg.flags = ACK
            self._seq_id = fin_seg.SEQ
            
            # Enviar el ACK final 3 veces espaciadas por timeout
            sleep_time = self._timeout if self._timeout is not None else 0.1
            for ack_attempt in range(3):
                print(f"DEBUG: Host A retransmitting final ACK (Attempt {ack_attempt + 1})")
                self._socket.sendto(fin_seg.to_bytes(), self._conn_addr)
                time.sleep(sleep_time)
            print("Closing Connection (Host A) successfully.")
        else:
            print("WARNING: Host A failed to receive FIN+ACK after 3 attempts. Assuming connection closed by remote.")
        
        self._conn_addr = ('notvalid', 8080)
        self._socket.close()

    def recv_close(self) -> None:
        """Maneja el fin de conexión (Host B)"""
        for attempt in range(3):
            try:
                msg, _ = self._socket.recvfrom(16)
            except TimeoutError:
                print("DEBUG: Host B timeout waiting for FIN. Assuming connection closed by remote.")
                self._socket.close()
                return
            
            recv_seg = SocketTCP.parse_segment(msg)
            # Secuencia de FIN recibida por el canal de comunicación
            if recv_seg.flags == FIN and recv_seg.SEQ == self._seq_id:
                # Configurar FIN + ACK y aumentar número de secuencia
                recv_seg.flags = FIN + ACK
                recv_seg.SEQ += 1
                
                # Enviar FIN+ACK y esperar ACK final hasta 3 timeouts
                for ack_attempt in range(3):
                    self._socket.sendto(recv_seg.to_bytes(), self._conn_addr)
                    try:
                        msg_ack, _ = self._socket.recvfrom(16)
                    except TimeoutError:
                        print(f"DEBUG: Host B timeout waiting for final ACK (Attempt {ack_attempt + 1}). Retrying FIN+ACK...")
                        continue
                    
                    ack_seg = Segment.from_bytes(msg_ack)
                    if ack_seg.SEQ == recv_seg.SEQ + 1 and ack_seg.flags == ACK:
                        print("Closing Connection (Host B) successfully.")
                        self._socket.close()
                        return
                
                print("WARNING: Host B failed to receive final ACK after 3 attempts. Assuming connection closed by remote.")
                self._socket.close()
                return

        print("WARNING: Host B failed to receive FIN after 3 attempts. Assuming connection closed by remote.")
        self._socket.close()

    def send(self, message: bytes) -> None:
        """Manda un mensaje por el canal de comunicación establecido usando STOP & WAIT"""
        if not self._seq_id:
            raise Exception("No connection established")
        
        # Usa Stop & Wait para mandar el primer segmento indicando el
        # largo del mensaje, y luego, lo usa para mandar iterativamente
        # el mensaje en paquetes pequeños
        def _stop_and_wait(packet: bytes, expected_seq: int):
            # Bucle hasta recibir segmentos adecuados
            while True:
                self._socket.sendto(packet, self._conn_addr)
                try:
                    recv_msg, _ = self._socket.recvfrom(16)
                except TimeoutError:
                    print("DEBUG: Sender timeout. Retrying packet...")
                    continue
                recv_seg = Segment.from_bytes(recv_msg)
                if recv_seg.SEQ == expected_seq and recv_seg.flags == ACK:
                    break # ACK recibido y secuencia correcta
           
        seg = Segment(seq=self._seq_id)

        # Primer Segmento: largo de mensaje
        # Si el mensaje es grande, se debe mandar
        # también en pedazos para evitar overflow del segmento
        header = str(len(message)).encode()
        chunks = [header] + [message[i:i+16] for i in range(0, len(message), 16)]
        for chunk in chunks:
            seg.DTA_LEN = len(chunk)
            expected_seq = seg.SEQ + len(chunk)
            _stop_and_wait(seg.to_bytes() + chunk, expected_seq)
            seg.SEQ = expected_seq
        
        self._seq_id = seg.SEQ
        
    def recv(self, buff_size: int) -> bytes:
        def _recv_seg() -> tuple[Segment, bytes]:
            while True:
                try:
                    recv_msg, _ = self._socket.recvfrom(5 + 16) # Largo de los headers: 5
                except TimeoutError:
                    continue
                
                recv_seg = Segment.from_bytes(recv_msg)
                dta = recv_msg[5:]
                # Secuencia requerida para mandar ACK
                ack_seq = recv_seg.SEQ + recv_seg.DTA_LEN 
                # Mensaje nuevo <=> la secuencia recibida coincide con la guardada
                is_new = recv_seg.SEQ == self._seq_id
                # Mensaje duplicado <=> la secuencia de ACK coincide con la guardada
                is_dup = ack_seq == self._seq_id
                
                print(f"DEBUG: SEQ={recv_seg.SEQ} DTA_LEN={recv_seg.DTA_LEN} esperado={self._seq_id} dta={dta!r}")
                if not (is_new or is_dup): # mensaje de externo
                    continue
                
                # Manda ACK (ya sea nuevo o duplicado)
                ack = Segment(seq=ack_seq, flags=ACK)
                try:
                    # Si el mensaje recibido es nuevo retorna el segmento y los datos
                    # en la próxima llamada a _recv_seg se vuelve a mandar si no llegó la primera vez
                    self._socket.sendto(ack.to_bytes(), self._conn_addr)
                except Exception as e:
                    print(f"DEBUG: Failed to send ACK: {e}. Retrying ACK...")
                    continue
                
                if is_new:
                    return recv_seg, dta
                
        # Primer segmento recibido contiene los datos a recibir después
        if self._remaining == 0 and len(self._buffer) == 0:
            recv_seg, dta = _recv_seg()
            assert self._seq_id is not None
            self._seq_id += len(dta)
            self._remaining = int(dta)
            
        target = min(self._remaining + len(self._buffer), buff_size)
        while len(self._buffer) < target:
            # recibe los datos
            recv_seg, dta = _recv_seg()
            assert self._seq_id is not None
            assert recv_seg.DTA_LEN == len(dta)
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
    def parse_segment(seg: bytes, offset: int = 0) -> Segment:
        """Parsea bytes recibidos a un segmento"""
        return Segment.from_bytes(seg, offset)
