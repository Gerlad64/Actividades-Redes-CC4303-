from __future__ import annotations

import ctypes
import socket
from dataclasses import dataclass
from enum import Enum


class Header(ctypes.BigEndianStructure):
    """ Clase `Header`, hereda de ctypes.BigEndianStructure 
    Almacena el *header* de un mensaje dns, donde
    cada campo contiene la cantidad de bits que 
    le corresponde.
    """
    id: int
    """ size: **16 bits**; type: **unsigned**
        Corresponde al número identificador aleatorio de un mensaje DNS.
        Es usado en la respuesta para saber a qué *question* corresponde.
    """
    qr: int
    """ size: **1 bit** 
        Señala si el mensaje es *question* o *ResourceRecord*.
    """
    opcode: int
    """ size: **4 bits** 
        Especifica el tipo de consulta.
    """
    aa: int
    """ size: **1 bit**
        Si es una respuesta, indica si el que respondió es autoridad del dominio preguntado antes.
    """
    tc: int
    """ size: **1 bit**
        Señala si el mensaje está truncado:
            truncado --> **0**
            no truncado --> **1**
    """
    rd: int
    """ size: **1 bit**
        Señala si se usa o no recursión:
            **con** recursión --> **0**
            **sin** recursión --> **1**
    """
    ra: int
    """ size: **1 bit**
        Si es una respuesta, indica si el que respondió acepta preguntas recursivas.
    """
    z: int
    """ size: **3 bits**
    """
    rcode: int
    """ size: **4 bit**
        Si es una respuesta, indica si hubo algún error, 0 si no hubo.
    """
    qdcount: int
    """ size: **16 bits**; type: **unsigned**
    """
    ancount: int
    """ size: **16 bits**
    """
    nscount: int
    """ size: **16 bits**
    """
    arcount: int
    """ size: **16 bits**
    """
    
    _fields_ = [
        ("id", ctypes.c_uint16),
        
        ("qr", ctypes.c_uint16, 1),
        ("opcode", ctypes.c_uint16, 4),
        ("aa", ctypes.c_uint16, 1),
        ("tc", ctypes.c_uint16, 1),
        ("rd", ctypes.c_uint16, 1),
        ("ra", ctypes.c_uint16, 1),
        ("z", ctypes.c_uint16, 3),
        ("rcode", ctypes.c_uint16, 4),
        
        ("qdcount", ctypes.c_uint16),
        ("ancount", ctypes.c_uint16),
        ("nscount", ctypes.c_uint16),
        ("arcount", ctypes.c_uint16),
    ]
    def to_bytes(self):
        """ Retorna los bytes correspondientes al *header* de un mensaje dns"""
        return bytes(self)

    @classmethod
    def from_bytes(cls, dns_bytes: bytes, offset: int = 0) -> Header:
        """ Crea un objeto `Header` a partir de los bytes de un mensaje dns.
            El tamaño del mensaje debe ser mínimo 12 bytes.

            Args:
                dns_bytes (bytes): Un mensaje dns, no necesita ser solo el header.
                offset (int): offset que indica donde comenzar a leer `dns_bytes`
            Returns:
                Un objeto Header.
        """
        if len(dns_bytes) - offset < 12:
            raise Exception("Expected 12 bytes")
            
        return Header.from_buffer_copy(dns_bytes, offset)
        
    def copy(self) -> Header:
        """ Crea y retorna una copia del objeto"""
        return Header(
            id=self.id,
            qr=self.qr,
            opcode=self.opcode,
            aa=self.aa,
            tc=self.tc,
            rd=self.rd,
            ra=self.ra,
            z=self.z,
            rcode=self.rcode,
            qdcount=self.qdcount,
            ancount=self.ancount,
            arcount=self.arcount
        )
def ip_to_str(ip: bytes):
    """ Dado una ip en bytes retorna su ip en string"""
    return ".".join(map(str, ip))

def name_to_str(name: bytes) -> str:
    """ Dado un name, devuelve su decodificación
        Args:
            name (bytes): Inicio de la secuencia que contiene una name
        Returns:
            El string representado por name
        **Example**:
        ```python
        name_to_str(0x07_65_78_61_6d_70_6c_65_03_63_6f_6d_00.to_bytes(13)) == "example.com"
        ```
    """
    labels = []
    i = 0

    while i < len(name):
        length = name[i]
        i += 1
        if length == 0:
            break
        labels.append(name[i:i+length].decode("ascii"))
        i+=length

    return ".".join(labels)
#print(name_to_str(0x07_65_78_61_6d_70_6c_65_03_63_6f_6d_00.to_bytes(13)))
def is_compressed(first_name_byte: int) -> bool:
    """ Determina si un name está en forma comprimida.

        Args:
            first_name_byte (int): El primer byte de los bytes de name
        Returns:
            True si está comprimido, es decir, los primeros dos bits son b'11'.
            False si no está comprimido en caso contrario, es decir, la secuencia
            siguiente codifica un nombre.

    """
    return (first_name_byte & 0xC0) == 0xC0

def get_offset(name_bytes: bytes) -> int:
    """ Retorna el offset cuando name está en forma comprimida """
    return ((name_bytes[0] & 0x3F) << 8) | name_bytes[1]

def decompress_name(name_bytes: bytes, dns_bytes: bytes) -> bytes:
    """ Descompresión básica de *name*.
        Verifica si los bytes pasados son un nombre o un puntero.
        En caso de ser un nombre, retorna los bytes hasta el final b'\x00'.
        Si es un puntero busca en el mensaje completo el nombre a partir del puntero.

        Args:
            name_bytes (bytes): bytes con nombre a ser descomprimido
            dns_bytes (bytes): mensaje en donde se buscará el nombre
        Returns:
            *name* en formato descomprimido, es decir, un nombre en lugar de un offset o puntero.

        **Notes**:
            - Se dice que es una implementación básica, ya que al parecer, dentro de un nombre se puede
              encontrar otro offset, por ejemplo \x03www\xC0<offset>. Esta función no maneja esos casos.
            - Caso que **sí** maneja (de ser posible) es cuando hay offset anidados de esta forma:
                    offset1 --> offset2 --> ... --> name
              ya que esta implementación utiliza recursión
    """
    if is_compressed(name_bytes[0]):
        offset = get_offset(name_bytes)
        return decompress_name(dns_bytes[offset:], dns_bytes)
    name_end = name_bytes.find(b'\x00') + 1
    return name_bytes[:name_end]
 
class Question(ctypes.BigEndianStructure):
    """ Clase `Question`, hereda de ctypes.BigEndianStructure
        Almacena el campo *question* de un mensaje dns, donde los campos
        `qtype` y `qclass` contiene la cantidad de bits 
        que le corresponden, mientras que `qname` contiene una cantidad de bits
        variable, dependiendo del dominio consultado.
    """
    qtype:  int
    qclass: int
    
    _fields_ = [
        ("qtype", ctypes.c_uint16),
        ("qclass", ctypes.c_uint16)
    ]

    def __init__(self, qname: bytes = b'\x0000', *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.qname = qname


    def _qname_from_str(self, domain: str) -> bytes:
        """ Dado un dominio, lo convierte en su qname en bytes
        Args:
            domain (str): el dominio a convertir
        Returns:
            El qname asociado al dominio.
        """
        qname: bytes = b'' # qname inicial
        split_domain: list[str] = domain.split(".") # lista de subdominios, ej ["www", "example", "com"]
        for sub_domain in split_domain:
            qname += len(sub_domain).to_bytes() + sub_domain.encode(encoding='ascii')
        qname += b'\x00' # fin del dominio

        return qname
    
    def __setattr__(self, name, value):
        if name == "qname" and isinstance(value, str): # asigna qname con un dominio
            value = self._qname_from_str(value)
                
        super().__setattr__(name, value)

    def __bytes__(self) -> bytes:
        return self.qname + bytes(memoryview(self))

    def to_bytes(self) -> bytes:
        """ Retorna el campo de *question* en bytes, con qname, qtype y qclass """
        return bytes(self)

    @classmethod
    def from_bytes(cls, dns_bytes: bytes, offset: int = 0) -> Question:
        """ Crea una estructura a partir del inicio del campo question en bytes.
        Args:
            dns_bytes (bytes): bytes que contienen el campo question
            offset (int): índice que indica donde a comenzar a leer dns_bytes
        """
        if len(dns_bytes) - offset < 3:
            raise Exception(f"Expected at least 3 bytes. Received: {len(dns_bytes) - offset}")
        name_end = dns_bytes.find(b'\x00', offset) + 1       # Índice donde finaliza qname
        qname = dns_bytes[offset:name_end]                   # qname encontrado
        question = cls.from_buffer_copy(dns_bytes, name_end) # Question con qtype y qclass asignados
        question.qname = qname
        return question
        
    def copy(self) -> Question:
        return Question(
            qname=self.qname,
            qtype=self.qtype,
            qclass=self.qclass
        )

class RegisterType(Enum):
    A     = 1
    AAAA  = 28
    CNAME = 5
    NS    = 2
    SOA   = 6

class ResourceRecord(ctypes.BigEndianStructure):
    """ Clase `ResourceRecord`, hereda de BigEndianStructure"""
    rtype:    int
    rclass:   int
    ttl:      int
    rdlength: int

    _pack_ = 1
    _fields_ = [
        ("rtype", ctypes.c_uint16),
        ("rclass", ctypes.c_uint16),
        ("ttl", ctypes.c_uint32),
        ("rdlength", ctypes.c_uint16),
    ]
    def __init__(self, name: bytes = b'\xC0\x00', rddta: bytes = b'', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: bytes = name
        self.rddta: bytes = rddta if rddta != b'' else bytes(self.rdlength)


    @property
    def offset(self) -> int:
        """ Corresponde al offset dentro de name cuando los primeros dos bits son b11.
        Returns:
            Retorna el entero correspondiente a los 14 bits siguientes a b11
        """
        return ((self.name[0] & 0x3F) << 8) | self.name[1]

    def rtype_is(self, register: str) -> bool:
        """ Chequea si el tipo de registro almacenado en `rtype` corresponde al registro
            especificado por nombre en mayúsculas.

            Args:
                register (str): Tipo de registro en mayúsculas, por ejemplo, `"A"`
            Returns:
                True si el registro `register` corresponde al registro guardado en `self.rtype`.
                False si no corresponde o si se pasó un registro que no reconocido.
        """
        if register in RegisterType.__dict__:
            return self.rtype == RegisterType[register].value
        return False

    def __bytes__(self) -> bytes:
        return (
            self.name
            + bytes(memoryview(self))
            + self.rddta
        )
    def to_bytes(self) -> bytes:
        return bytes(self)

    @classmethod
    def from_bytes(cls, dns_bytes: bytes, offset: int = 0) -> ResourceRecord:
        if len(dns_bytes) - offset < 11: # name + type + ... + rdlength
            raise Exception(f"Expected at least 12 bytes. Received: {len(dns_bytes) - offset}") 
        elif len(dns_bytes) - offset == 11:
            assert dns_bytes[offset] == 0
            
        if (dns_bytes[offset] & 0xC0) == 0xC0: # campo name es un *compression pointer*
            name = dns_bytes[offset:offset + 2]
            name_off = 2
        else: 
            name_end = dns_bytes.find(b'\x00', offset) + 1
            name = dns_bytes[offset: name_end]
            name_off = 1
            
        rr = cls.from_buffer_copy(dns_bytes, offset + name_off)
        rr.name = name
        if memoryview(dns_bytes)[offset+10+name_off-1] != rr.rdlength:
            rr.rddta = dns_bytes[offset + 10+name_off:]
            
        else:
            rr.rddta = dns_bytes[offset + 10+name_off: offset + 10+name_off + rr.rdlength]
       
        return rr

    def copy(self) -> ResourceRecord:
        return ResourceRecord(
            name=self.name,
            rddta=self.rddta,
            rtype=self.rtype,
            rclass=self.rclass,
            ttl=self.ttl,
            rdlength=self.rdlength
        )
          
@dataclass
class DNS:
    header:     Header
    question:   Question | None
    answers:     list[ResourceRecord]
    authority_records:  list[ResourceRecord]
    additional_records: list[ResourceRecord]

    def to_bytes(self) -> bytes:
        question   = b'' if self.question is None else self.question.to_bytes()
        answer     = b''.join(a.to_bytes() for a in self.answers           )
        authority  = b''.join(a.to_bytes() for a in self.authority_records )
        additional = b''.join(a.to_bytes() for a in self.additional_records)
        return self.header.to_bytes() + question + answer + authority + additional

    @classmethod
    def from_bytes(cls, dns_bytes: bytes) -> DNS:
        h = Header.from_bytes(dns_bytes)
        # ------Question
        # largo acumulado del mensaje mientras es parseado
        offset = len(h.to_bytes())
        questions: list[Question] = []
        for _ in range(h.qdcount):
            rr = Question.from_bytes(dns_bytes, offset)
            offset += len(rr.to_bytes())
            questions.append(rr)
        q = questions[0] if questions else None # Solo guarda el primer registro
        # ------Answer
        answers = []
        for _ in range(h.ancount):
            rr = ResourceRecord.from_bytes(dns_bytes, offset)
            offset += len(rr.to_bytes())
            answers.append(rr)
        #a = answers[0] if answers else None # Solo guarda el primer registro
        # ------Authority
        auths = []
        for _ in range(h.nscount):
            rr = ResourceRecord.from_bytes(dns_bytes, offset)
            offset += len(rr.to_bytes())
            auths.append(rr)
        #auth = auths[0] if auths else None # Solo guarda el primer registro
        #------Additional
        addts = []
        for _ in range(h.arcount):
            rr = ResourceRecord.from_bytes(dns_bytes, offset)
            offset += len(rr.to_bytes())
            addts.append(rr)
        #addt = addts[0] if addts else None # Solo guarda el primer registro
        return cls(h, q, answers, auths, addts)

    @classmethod
    def from_socket(cls, dns_bytes: bytes, ip: str, port: int = 53, buff_size: int = 4060) -> DNS:
        addr = (ip, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
                # usamos binascii para pasar el mensaje al formato apropiado
                # y lo enviamos
                sock.sendto(dns_bytes, addr)
                # En data quedará la respuesta a nuestra consulta
                data, _ = sock.recvfrom(buff_size)
        finally:
                sock.close()
            # Ojo que los datos de la respuesta van en hexadecimal, no en binario
        return DNS.from_bytes(data)

    def send(self, ip: str, port: int = 53, buff_size: int = 4096) -> bytes:
        addr = (ip, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
                # usamos binascii para pasar el mensaje al formato apropiado
                # y lo enviamos
                sock.sendto(self.to_bytes(), addr)
                # En data quedará la respuesta a nuestra consulta
                data, _ = sock.recvfrom(buff_size)
        finally:
                sock.close()
            # Ojo que los datos de la respuesta van en hexadecimal, no en binario
        return data

    def copy(self) -> DNS:
        return DNS(
            header    = self.header.copy(),
            question  = None if self.question is None else self.question.copy(),
            answers    =        [a.copy() for a in self.answers],
            authority_records = [a.copy() for a in self.authority_records],
            additional_records= [a.copy() for a in self.additional_records]
        )