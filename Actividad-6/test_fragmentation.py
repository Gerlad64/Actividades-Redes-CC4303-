import random
import socket

from config import ROUTES_PATH
from packet.fragmentation import fragment_IP_packet, reassemble_IP_packet
from packet.packet import HEADER_SIZE, Packet
from router_table import RouterTable

IP = int.from_bytes(socket.inet_aton("127.0.0.1"))
MSG = bytes(range(132))
"""Mensaje de 132 bytes: con el header de 18 bytes forma un paquete IP de 150 bytes totales"""
IP_PACKET_V1 = Packet(IP, 8885, MSG, ttl=10, packet_id=347).to_bytes()


def test_header() -> None:
    """Paso 1: create_packet(parse_packet(IP_packet_v1)) == IP_packet_v1 con la nueva estructura de headers."""
    assert HEADER_SIZE == 18
    assert len(IP_PACKET_V1) == 150
    packet = Packet.from_bytes(IP_PACKET_V1)
    assert packet.to_bytes() == IP_PACKET_V1
    assert (packet.ADDR, packet.TTL, packet.ID, packet.OFFSET, packet.SIZE, packet.FLAG, packet.msg) == (
        ("127.0.0.1", 8885), 10, 347, 0, 132, 0, MSG
    )
    # el mismo round-trip con un fragmento intermedio: Offset y FLAG distintos de 0
    fragment = Packet(IP, 8885, b"hola!", ttl=10, packet_id=347, offset=82, flag=1).to_bytes()
    assert fragment == bytes([127, 0, 0, 1]) + bytes([0x22, 0xB5, 10, 0x01, 0x5B, 0, 0, 0, 82, 0, 0, 0, 5, 1]) + b"hola!"
    assert Packet.from_bytes(fragment).to_bytes() == fragment


def test_check_routes() -> None:
    """Paso 2: check retorna (next_hop_address, MTU) y sigue alternando con round-robin."""
    table = RouterTable(ROUTES_PATH / "rutas_R2_v3_mtu.txt")
    assert table.check(("127.0.0.1", 8881)) == (("127.0.0.1", 8881), 100)
    assert table.check(("127.0.0.1", 8885)) == (("127.0.0.1", 8883), 50)
    assert table.check(("127.0.0.1", 8885)) == (("127.0.0.1", 8884), 80)
    assert table.check(("127.0.0.1", 8885)) == (("127.0.0.1", 8883), 50)
    assert table.check(("127.0.0.1", 9000)) is None


def test_fragment() -> None:
    """Paso 3: lista de largo 1 si el paquete cabe en el MTU, y la cantidad esperada de fragmentos si no."""
    assert fragment_IP_packet(IP_PACKET_V1, 150) == [IP_PACKET_V1]
    assert fragment_IP_packet(IP_PACKET_V1, 1000) == [IP_PACKET_V1]

    # MTU 100: trozos de 100 - 18 = 82 bytes -> ceil(132 / 82) = 2 fragmentos, de 82 y 50 bytes de mensaje
    fragments = [Packet.from_bytes(f) for f in fragment_IP_packet(IP_PACKET_V1, 100)]
    assert [(f.OFFSET, f.SIZE, f.FLAG) for f in fragments] == [(0, 82, 1), (82, 50, 0)]
    assert [f.msg for f in fragments] == [MSG[:82], MSG[82:]]
    assert all((f.ADDR, f.TTL, f.ID) == (("127.0.0.1", 8885), 10, 347) for f in fragments)

    # MTU 50: trozos de 32 bytes -> ceil(132 / 32) = 5 fragmentos, todos de tamaño total <= MTU
    fragments = fragment_IP_packet(IP_PACKET_V1, 50)
    assert [len(f) for f in fragments] == [50, 50, 50, 50, 22]
    assert [Packet.from_bytes(f).FLAG for f in fragments] == [1, 1, 1, 1, 0]

    # el mensaje calza justo en los trozos: el último fragmento también queda completo
    exact = Packet(IP, 8885, bytes(64), packet_id=1).to_bytes()
    assert [len(f) for f in fragment_IP_packet(exact, 50)] == [50, 50]


def test_refragment() -> None:
    """Paso 3: re-fragmentación. Un fragmento intermedio (FLAG 1) se divide manteniendo offsets absolutos
    y FLAG 1 en su último trozo, porque después de él vienen más fragmentos del paquete original.
    """
    first, last = fragment_IP_packet(IP_PACKET_V1, 100)
    refragmented = [Packet.from_bytes(f) for f in fragment_IP_packet(first, 50)]
    assert [(f.OFFSET, f.SIZE, f.FLAG) for f in refragmented] == [(0, 32, 1), (32, 32, 1), (64, 18, 1)]
    refragmented = [Packet.from_bytes(f) for f in fragment_IP_packet(last, 50)]
    assert [(f.OFFSET, f.SIZE, f.FLAG) for f in refragmented] == [(82, 32, 1), (114, 18, 0)]


def test_reassemble() -> None:
    """Paso 5: reassemble_IP_packet(fragment_IP_packet(IP_packet_v1, MTU)) == IP_packet_v1."""
    for mtu in (19, 50, 55, 80, 100, 140, 150, 200):
        assert reassemble_IP_packet(fragment_IP_packet(IP_PACKET_V1, mtu)) == IP_PACKET_V1

    # fragmentos desordenados
    fragments = fragment_IP_packet(IP_PACKET_V1, 50)
    random.Random(0).shuffle(fragments)
    assert reassemble_IP_packet(fragments) == IP_PACKET_V1

    # fragmentos re-fragmentados por enlaces con MTU cada vez menor (100 -> 80 -> 50), desordenados
    fragments = [f3 for f1 in fragment_IP_packet(IP_PACKET_V1, 100)
                 for f2 in fragment_IP_packet(f1, 80)
                 for f3 in fragment_IP_packet(f2, 50)]
    random.Random(1).shuffle(fragments)
    assert reassemble_IP_packet(fragments) == IP_PACKET_V1


def test_reassemble_incomplete() -> None:
    """Paso 5: retorna None si faltan fragmentos, y distingue un paquete completo de un fragmento solo."""
    assert reassemble_IP_packet([IP_PACKET_V1]) == IP_PACKET_V1  # Offset == 0 y FLAG == 0
    fragments = fragment_IP_packet(IP_PACKET_V1, 50)
    assert reassemble_IP_packet([fragments[0]]) is None   # un solo fragmento: Offset == 0 pero FLAG == 1
    assert reassemble_IP_packet([fragments[-1]]) is None  # un solo fragmento: FLAG == 0 pero Offset != 0
    assert reassemble_IP_packet(fragments[1:]) is None    # falta el primero
    assert reassemble_IP_packet(fragments[:-1]) is None   # falta el final (FLAG == 0)
    assert reassemble_IP_packet(fragments[:2] + fragments[3:]) is None  # falta uno intermedio
    # la lista se va completando de a un fragmento, como en el router: solo reensambla con el último
    for i in range(1, len(fragments)):
        assert reassemble_IP_packet(fragments[:i]) is None
    assert reassemble_IP_packet(fragments) == IP_PACKET_V1


if __name__ == "__main__":
    for test in (test_header, test_check_routes, test_fragment, test_refragment, test_reassemble,
                 test_reassemble_incomplete):
        test()
        print(f"{test.__name__}: OK")
