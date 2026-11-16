import os
import random
import signal
import socket
import sys
import time

from packet.fragmentation import fragment_IP_packet
from packet.packet import HEADER_SIZE, Packet
from packet.send import send
from router import network

IP = "127.0.0.1"
IP_INT = int.from_bytes(socket.inet_aton(IP))


def start_routers(routers: list[tuple[int, str]]) -> list[int]:
    """Hace fork de un proceso por router y retorna sus pids.
    Params:
        routers: lista de tuplas (puerto, tabla_de_rutas). Cada router se levanta en (IP, puerto)
            y usa el archivo tabla_de_rutas, buscado dentro de routes/ (ej: (8881, "rutas_R1_v3_mtu.txt"))
    Returns:
        pids de los procesos hijos, en el mismo orden que `routers`, para luego detenerlos con `stop_routers`
    """
    pids = []
    for port, routes in routers:
        pid = os.fork()
        if pid == 0:
            network(IP, port, routes)
            sys.stdout.flush()
            os._exit(0)
        pids.append(pid)
    time.sleep(0.5)
    return pids


def stop_routers(pids: list[int]) -> None:
    """Detiene los routers con SIGINT (KeyboardInterrupt) y espera a que terminen.
    Params:
        pids: pids de los procesos de los routers, tal como los retorna `start_routers`
    """
    for pid in pids:
        os.kill(pid, signal.SIGINT)
    for pid in pids:
        os.waitpid(pid, 0)


def start_5_routers() -> list[int]:
    """Levanta la topología de 5 routers con MTU (rutas_R{1..5}_v3_mtu.txt): Ri escucha en (IP, 8880 + i)."""
    return start_routers([(8880 + i, f"rutas_R{i}_v3_mtu.txt") for i in range(1, 6)])


def message(size: int) -> str:
    """Mensaje ASCII de `size` bytes. Cada 10 bytes lleva su posición ("000-----010-----020-..."),
    así se ve a simple vista si el mensaje reensamblado está completo y en orden.
    """
    return "".join(f"{i:03d}-------" for i in range(0, size, 10))[:size]


def mtu_routes() -> None:
    """Paso 2: topología de 5 routers con las tablas con MTU. Envía paquetes pequeños entre pares de
    routers para comprobar que el forwarding no falla al recibir la tupla (next_hop_address, MTU).
    """
    print("\n===== Paso 2: tablas de rutas con MTU =====", flush=True)
    pids = start_5_routers()
    send(IP, 8882, "hola R2!", IP, 8881)
    send(IP, 8881, "hola R1!", IP, 8882)
    send(IP, 8884, "hola R4!", IP, 8883)
    send(IP, 8881, "hola R1!", IP, 8885)
    send(IP, 8889, "sin ruta", IP, 8881)
    stop_routers(pids)


def manual_reassembly() -> None:
    """Paso 7: genera las listas de fragmentos de dos paquetes con distinto ID y las envía manualmente,
    directo a R5, en orden, en desorden e intercalando ID. R5 debe imprimir ambos mensajes en los tres casos.
    """
    print("\n===== Paso 7: reensamblaje en el router de destino =====", flush=True)
    pids = start_routers([(8885, "rutas_R5_v3_mtu.txt")])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg_a = f"[paquete A] {message(100)}".encode()
    msg_b = f"[paquete B] {message(70)}".encode()
    fragments_a = fragment_IP_packet(Packet(IP_INT, 8885, msg_a, packet_id=1).to_bytes(), 50)
    fragments_b = fragment_IP_packet(Packet(IP_INT, 8885, msg_b, packet_id=2).to_bytes(), 50)
    shuffled_a = random.Random(0).sample(fragments_a, len(fragments_a))
    shuffled_b = random.Random(1).sample(fragments_b, len(fragments_b))
    # intercala: uno de A, uno de B, ... y al final los que sobran de A
    interleaved = [f for pair in zip(shuffled_a, shuffled_b) for f in pair] + shuffled_a[len(shuffled_b):]

    cases = [
        ("en orden", fragments_a + fragments_b),
        ("en desorden", shuffled_a + shuffled_b),
        ("intercalando ID (y en desorden)", interleaved),
    ]
    for name, fragments in cases:
        sent = [(Packet.from_bytes(f).ID, Packet.from_bytes(f).OFFSET) for f in fragments]
        print(f"\n>>> enviando fragmentos {name} a R5, como (ID, Offset): {sent}", flush=True)
        for fragment in fragments:
            sock.sendto(fragment, (IP, 8885))
        time.sleep(0.3)
    sock.close()
    stop_routers(pids)


def small_packet() -> None:
    """Pruebas para el informe 1: paquete pequeño de R1 a R5 que no requiere fragmentación
    (127.0.0.1;8885;10;347;0;5;0;hola!). Se envía 4 veces para ver el round-robin, y una vez con TTL 2
    para ver que el TTL se descuenta en cada salto y el paquete se descarta al llegar a 0.
    """
    print("\n===== Informe 1: TTL, round-robin y paquetes sin fragmentar =====", flush=True)
    pids = start_5_routers()
    for _ in range(4):
        send(IP, 8885, "hola!", IP, 8881, ttl=10, packet_id=347)
    send(IP, 8885, "hola!", IP, 8881, ttl=2, packet_id=347)
    stop_routers(pids)


def fragmentation(times: int = 6, ttl: int = 64) -> None:
    """Pruebas para el informe 2: envía `times` veces un paquete IP de 150 bytes totales de R1 a R5.
    Cada envío usa un ID distinto, para que los fragmentos de paquetes distintos no se mezclen en R5.
    """
    print(f"\n===== Informe 2: paquete de 150 bytes de R1 a R5, TTL {ttl} =====", flush=True)
    pids = start_5_routers()
    for i in range(times):
        send(IP, 8885, message(150 - HEADER_SIZE), IP, 8881, ttl=ttl, packet_id=i + 1)
    time.sleep(0.5)
    stop_routers(pids)


def fragmentation_other_routers(ttl: int = 64) -> None:
    """Pruebas para el informe 2: envía el mismo paquete de 150 bytes hacia R5 desde R2, R3 y R4
    (dos veces desde cada uno, para ver ambas rutas del round-robin), y uno de R5 a R1.
    """
    print(f"\n===== Informe 2: paquete de 150 bytes desde otros routers, TTL {ttl} =====", flush=True)
    pids = start_5_routers()
    packet_id = 1
    for via_port in (8882, 8882, 8883, 8883, 8884, 8884):
        send(IP, 8885, message(150 - HEADER_SIZE), IP, via_port, ttl=ttl, packet_id=packet_id)
        packet_id += 1
    send(IP, 8881, message(150 - HEADER_SIZE), IP, 8885, ttl=ttl, packet_id=packet_id)
    send(IP, 8881, message(150 - HEADER_SIZE), IP, 8885, ttl=ttl, packet_id=packet_id + 1)
    time.sleep(0.5)
    stop_routers(pids)


if __name__ == "__main__":
    mtu_routes()
    manual_reassembly()
    small_packet()
    fragmentation()
    fragmentation_other_routers()
