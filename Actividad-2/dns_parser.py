from __future__ import annotations

import ctypes
from dataclasses import dataclass


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
        return bytes(self)

    @classmethod
    def from_bytes(cls, dns_bytes: bytes, offset: int = 0) -> Header:
        if len(dns_bytes) - offset < 12:
            raise Exception("Expected 12 bytes")
            
        return Header.from_buffer_copy(dns_bytes, offset)

 
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

    def __init__(self, qname: bytes = b'\x0000', *args, **kwargs):
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
            raise Exception("Expected at least 3 bytes")
        name_end = dns_bytes.find(b'\x00', offset) + 1       # Índice donde finaliza qname
        qname = dns_bytes[offset:name_end]                   # qname encontrado
        question = cls.from_buffer_copy(dns_bytes, name_end) # Question con qtype y qclass asignados
        question.qname = qname
        return question


class ResourceRecord(ctypes.BigEndianStructure):
    """ Clase `ResourceRecord`, hereda de BigEndianStructure"""
    atype:    int
    aclass:   int
    ttl:      int
    rdlength: int

    
    _fields_ = [
        ("atype", ctypes.c_uint16),
        ("aclass", ctypes.c_uint16),
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

    def __bytes__(self) -> bytes:
        return (
            self.name
            + bytes(memoryview(self))
            + self.rddta
        )
    def to_bytes(self) -> bytes:
        return bytes(self)

    @classmethod
    def from_bytes(cls, dns_bytes: bytes, offset: int = 0) -> Answer:
       if len(dns_bytes) - offset < 12: # name + type + ... + rdlength
           raise Exception("Expected at least 12 bytes") 

#        if (dns_bytes[offset] & 0xC0) != 0xC0:
#            raise NotImplementedError(
#                "Not implemented when the first two bits of name are not b11 (i.e. name is not a pointer)"
#            )
           
       answer = cls.from_buffer_copy(dns_bytes, offset + 2)
       answer.name = dns_bytes[offset:offset + 2]
       answer.rddta = dns_bytes[offset + 12: offset + 12 + answer.rdlength]

       return answer
          
@dataclass
class DNS:
    header:     Header
    question:   Question
    answer:     ResourceRecord | None
    authority:  ResourceRecord | None
    additional: ResourceRecord | None

    def to_bytes(self) -> bytes:
        answer = b'' if self.answer is None else self.answer.to_bytes()
        return self.header.to_bytes() + self.question.to_bytes() + answer

    @classmethod
    def from_bytes(cls, dns_bytes: bytes) -> DNS:
        h = Header.from_bytes(dns_bytes)
        q = Question.from_bytes(dns_bytes, len(h.to_bytes()))
        qlen = len(q.to_bytes()) + len(h.to_bytes())
        a = None if len(dns_bytes) == qlen else Answer.from_bytes(dns_bytes, qlen)
        return cls(h, q, a)