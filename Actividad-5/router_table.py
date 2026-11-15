from dataclasses import dataclass
from ipaddress import ip_address, ip_network
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
                # formato: <ip>/<rango> <puerto_min> <puerto_max> <fwd_ip> <fwd_puerto>
                cidr, port_min, port_max, fwd_ip, fwd_port = line.split()
                dst_ip, ip_range = cidr.split("/")
                self.TABLE.append(
                    RouterEntry(
                        DST_IP=dst_ip,
                        DST_IP_RANGE=int(ip_range),
                        DST_PORT_RANGE=(int(port_min), int(port_max)),
                        FWD_IP=fwd_ip,
                        FWD_PORT=int(fwd_port),
                    )
                )

    def check_table(self, dst_addr: tuple[str, int]) -> tuple[str, int] | None:
        for r_entry in self.TABLE:
            if dst_addr in r_entry:
                return r_entry.FWD_ADDR # --> (next_hop_IP, next_hop_ PORT)
        return None