from collections.abc import Iterator
from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from itertools import cycle
from pathlib import Path
from typing import NamedTuple


class NetworkArea(NamedTuple):
    """Área de la red: conjunto de direcciones de destino que cubre una entrada de la tabla de rutas.
    Entradas con igual área son caminos alternativos y se alternan con round-robin.
    Es inmutable y hasheable, por lo que sirve como llave de diccionario.
    """
    DST_IP: str
    """IP de destino del área"""
    DST_IP_RANGE: int
    """Rango de IPs de destino. ej: 24 establece el rango a.b.c.d/24"""
    DST_PORT_RANGE: tuple[int, int]
    """Rango de puertos de destino: ej: (8880, 8882), entonces el rango es {8880,8881,8882}"""


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
    MTU: int
    """Cantidad máxima de bytes (header + mensaje) que pasan por el enlace hacia el siguiente salto"""

    @property
    def FWD_ADDR(self) -> tuple[str, int]:
        return (self.FWD_IP, self.FWD_PORT)

    @property
    def AREA(self) -> NetworkArea:
        """Área de la red que cubre la entrada: rutas con igual área son caminos alternativos."""
        return NetworkArea(self.DST_IP, self.DST_IP_RANGE, self.DST_PORT_RANGE)

    def __contains__(self, addr: tuple[str, int]) -> bool:
        """Devuelve True si la dirección IP de addr pertenece a '{self.DST_IP}/{self.DST_IP_RANGE}' 
        y el puerto pertenece a self.DST_PORT_RANGE
        """
        ip, port = addr
        network = ip_network(f"{self.DST_IP}/{self.DST_IP_RANGE}", strict=False)
        low, high = self.DST_PORT_RANGE
        return ip_address(ip) in network and low <= port <= high

class RouterTable:
    
    def __init__(self, table_path: Path):
        self.TABLE = []
        with open(table_path, encoding="utf-8") as f:
            for line in f:
                line = line.split("#", 1)[0].strip()  # quita comentarios y espacios
                if not line:
                    continue
                # formato: <ip>/<rango> <puerto_min> <puerto_max> <fwd_ip> <fwd_puerto> <mtu>
                cidr, port_min, port_max, fwd_ip, fwd_port, mtu = line.split()
                dst_ip, ip_range = cidr.split("/")
                self.TABLE.append(
                    RouterEntry(
                        DST_IP=dst_ip,
                        DST_IP_RANGE=int(ip_range),
                        DST_PORT_RANGE=(int(port_min), int(port_max)),
                        FWD_IP=fwd_ip,
                        FWD_PORT=int(fwd_port),
                        MTU=int(mtu),
                    )
                )
        # agrupa las rutas por área y las recorre en una lista circular (round-robin)
        areas: dict[NetworkArea, list[RouterEntry]] = {}
        for r_entry in self.TABLE:
            areas.setdefault(r_entry.AREA, []).append(r_entry)
        self.ROUND_ROBIN: dict[NetworkArea, Iterator[RouterEntry]] = {
            area: cycle(entries) for area, entries in areas.items()
        }

    def check(self, dst_addr: tuple[str, int]) -> tuple[tuple[str, int], int] | None:
        """Retorna el siguiente salto hacia dst_addr y el MTU de ese enlace, alternando con round-robin
        entre las rutas de su área.
        """
        for r_entry in self.TABLE:
            if dst_addr in r_entry:
                route = next(self.ROUND_ROBIN[r_entry.AREA])
                return route.FWD_ADDR, route.MTU # --> ((next_hop_IP, next_hop_PORT), MTU)
        return None
