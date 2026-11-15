from dataclasses import dataclass
from pathlib import Path


@dataclass
class RouterEntry:
    DST_IP:   str
    """IP de destino en la tabla de rutas"""
    DST_IP_RANGE: int
    """Rango de IPs de destino. ej: 24 establece el rango a.b.c.d/24"""
    DST_PORT_RANGE: tuple[int, int]
    """Rango de puertos de destino: ej: (8880, 8882), entonces el rango es {8880,8881,8882}"""
    FWD_IP: str
    """IP de forwarding"""
    FWD_PORT: int
    """Puerto de forwarding"""

    @property
    def FWD_ADDR(self) -> tuple[str, int]:
        return (self.FWD_IP, self.FWD_PORT)

    def __contains__(self, addr: tuple[str, int]) -> bool:
        """Devuelve True si la dirección IP de addr pertenece a '{self.DST_IP}/{self.DST_IP_RANGE}' 
        y el puerto pertenece a self.DST_PORT_RANGE
        """
        #TODO
        return False

@dataclass
class RouterTable:
    TABLE: list[RouterEntry]
    
    def __init__(self, table_path: Path):
        pass

    def check_table(self, dst_addr: tuple[str, int]) -> tuple[str, int] | None:
        for r_entry in self.TABLE:
            if dst_addr in r_entry:
                return r_entry.FWD_ADDR # --> (next_hop_IP, next_hop_ PORT)
        return None