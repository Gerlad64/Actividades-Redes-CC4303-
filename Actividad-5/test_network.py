import os
import signal
import subprocess
import sys
import time

from packet.send import send
from router import network

IP = "127.0.0.1"


def start_routers(routers: list[tuple[int, str]]) -> list[int]:
    """Hace fork de un proceso por router y retorna sus pids.
    Params:
        routers: lista de tuplas (puerto, tabla_de_rutas). Cada router se levanta en (IP, puerto)
            y usa el archivo tabla_de_rutas, buscado dentro de routes/ (ej: (8881, "rutas_R1_v1.txt"))
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


def example_1() -> None:
    """Paso 7, ejemplo 1: red de 2 routers (R1 <-> R2).
    Tablas de rutas:
        R1 (8881): rutas_R1_v1.txt
        R2 (8882): rutas_R2_v1.txt
    """
    print("\n===== Ejemplo 1: R1 <-> R2 =====", flush=True)
    pids = start_routers([(8881, "rutas_R1_v1.txt"), (8882, "rutas_R2_v1.txt")])
    send(IP, 8882, "hola R2!", IP, 8881)
    send(IP, 8881, "hola R1!", IP, 8882)
    send(IP, 8881, "hola", IP, 8881)
    send(IP, 8884, "hola", IP, 8881)
    stop_routers(pids)


def example_2() -> None:
    """Paso 7, ejemplo 2: red de 3 routers (R1 <-> R2 <-> R3).
    Tablas de rutas:
        R1 (8881): rutas_R1_v2.txt
        R2 (8882): rutas_R2_v2.txt
        R3 (8883): rutas_R3_v2.txt
    """
    print("\n===== Ejemplo 2: R1 <-> R2 <-> R3 =====", flush=True)
    pids = start_routers([
        (8881, "rutas_R1_v2.txt"),
        (8882, "rutas_R2_v2.txt"),
        (8883, "rutas_R3_v2.txt"),
    ])
    send(IP, 8883, "hola R3!", IP, 8881)
    send(IP, 8881, "hola R1!", IP, 8883)
    send(IP, 8882, "hola R2!", IP, 8883)
    send(IP, 8884, "hola", IP, 8881)
    send(IP, 8884, "hola", IP, 8882)
    stop_routers(pids)


def round_robin_1() -> None:
    """Paso 8, Test 1: red de 5 routers. Envía varios paquetes de R1 a R5 para verificar que R2 cicla
    entre los caminos posibles.
    Tablas de rutas:
        R1 (8881): rutas_R1_v3.txt
        R2 (8882): rutas_R2_v3.txt
        R3 (8883): rutas_R3_v3.txt
        R4 (8884): rutas_R4_v3.txt
        R5 (8885): rutas_R5_v3.txt
    """
    print("\n===== Paso 8, Test 1: red de 5 routers =====", flush=True)
    pids = start_routers([(8880 + i, f"rutas_R{i}_v3.txt") for i in range(1, 6)])
    for i in range(4):
        send(IP, 8885, f"R1->R5 #{i}", IP, 8881)
    stop_routers(pids)


def round_robin_2() -> None:
    """Paso 8, Test 2: red de 5 routers más R0 (conectado a R1 y R2) y R6 (conectado a R2 y R3).
    Intercala paquetes de R1 a R5 y de R5 a R1 para verificar que R2 cicla dentro de cada área de la red.
    Tablas de rutas:
        R0 (8880): rutas_R0_v4.txt
        R1 (8881): rutas_R1_v4.txt
        R2 (8882): rutas_R2_v4.txt
        R3 (8883): rutas_R3_v4.txt
        R4 (8884): rutas_R4_v4.txt
        R5 (8885): rutas_R5_v4.txt
        R6 (8886): rutas_R6_v4.txt
    """
    print("\n===== Paso 8, Test 2: red de 7 routers (R0 y R6) =====", flush=True)
    pids = start_routers([(8880 + i, f"rutas_R{i}_v4.txt") for i in range(7)])
    for i in range(4):
        send(IP, 8885, f"R1->R5 #{i}", IP, 8881)
        send(IP, 8881, f"R5->R1 #{i}", IP, 8885)
    stop_routers(pids)


def default_router() -> None:
    """Paso 9: red de 5 routers con un router default en (IP, 7000) conectado a todos ellos.
    Envía paquetes a direcciones fuera de la red y verifica que terminan en el router default.
    Tablas de rutas:
        R1 (8881): rutas_R1_v5.txt
        R2 (8882): rutas_R2_v5.txt
        R3 (8883): rutas_R3_v5.txt
        R4 (8884): rutas_R4_v5.txt
        R5 (8885): rutas_R5_v5.txt
        default (7000): rutas_default_v5.txt
    """
    print("\n===== Paso 9: router default =====", flush=True)
    pids = start_routers([(8880 + i, f"rutas_R{i}_v5.txt") for i in range(1, 6)] + [(7000, "rutas_default_v5.txt")])
    send(IP, 9000, "fuera", IP, 8881)
    send("10.0.0.1", 8881, "fuera", IP, 8885)
    send(IP, 7000, "a default", IP, 8883)
    send(IP, 8885, "R1->R5", IP, 8881)
    stop_routers(pids)


def bad_routes() -> None:
    """Pruebas sin TTL, prueba 1: ejemplo 2 con la tabla de R2 mal configurada (8883 se envía a R1).
    El paquete de R1 a R3 queda rebotando entre R1 y R2; el de R3 a R1 llega normal.
    Tablas de rutas:
        R1 (8881): rutas_R1_v2.txt
        R2 (8882): rutas_R2_v2_error.txt
        R3 (8883): rutas_R3_v2.txt
    """
    print("\n===== Pruebas sin TTL 1: tabla de R2 mal configurada =====", flush=True)
    pids = start_routers([
        (8881, "rutas_R1_v2.txt"),
        (8882, "rutas_R2_v2_error.txt"),
        (8883, "rutas_R3_v2.txt"),
    ])
    send(IP, 8881, "hola R1!", IP, 8883)
    send(IP, 8883, "hola R3!", IP, 8881)
    stop_routers(pids)


def hops_5_routers() -> None:
    """Pruebas sin TTL, prueba 2: red de 5 routers. Envía 6 paquetes de R1 a R5 para contar sus saltos.
    Tablas de rutas: rutas_R{1..5}_v3.txt
    """
    print("\n===== Pruebas sin TTL 2: saltos en red de 5 routers =====", flush=True)
    pids = start_routers([(8880 + i, f"rutas_R{i}_v3.txt") for i in range(1, 6)])
    for i in range(6):
        send(IP, 8885, f"R1->R5 #{i}", IP, 8881)
    stop_routers(pids)


def hops_7_routers() -> None:
    """Pruebas sin TTL, prueba 3: red de 7 routers del Test 2 del paso 8. Envía 6 paquetes de R1 a R5
    para contar sus saltos.
    Tablas de rutas: rutas_R{0..6}_v4.txt
    """
    print("\n===== Pruebas sin TTL 3: saltos en red de 7 routers =====", flush=True)
    pids = start_routers([(8880 + i, f"rutas_R{i}_v4.txt") for i in range(7)])
    for i in range(6):
        send(IP, 8885, f"R1->R5 #{i}", IP, 8881)
    stop_routers(pids)


def ttl_drop() -> None:
    """Parte II, pasos 2 y 3: red de 3 routers del ejemplo 2 (R1 <-> R2 <-> R3).
    Un paquete con TTL=1 de R1 a R3 sale de R1 con TTL=0 y R2 lo descarta.
    Con TTL=2 R3 lo recibe con TTL=0 y también lo descarta; con TTL=3 llega a R3 (el TTL baja en 1 por salto).
    Tablas de rutas:
        R1 (8881): rutas_R1_v2.txt
        R2 (8882): rutas_R2_v2.txt
        R3 (8883): rutas_R3_v2.txt
    """
    print("\n===== Parte II: TTL (R1 <-> R2 <-> R3) =====", flush=True)
    pids = start_routers([
        (8881, "rutas_R1_v2.txt"),
        (8882, "rutas_R2_v2.txt"),
        (8883, "rutas_R3_v2.txt"),
    ])
    send(IP, 8883, "hola", IP, 8881, ttl=1)
    send(IP, 8883, "hola", IP, 8881, ttl=2)
    send(IP, 8883, "hola", IP, 8881, ttl=3)
    stop_routers(pids)


def bad_routes_ttl() -> None:
    """Pruebas con TTL, prueba 1: igual que `bad_routes`, pero con TTL inicial 10.
    El paquete de R1 a R3 rebota entre R1 y R2 hasta que su TTL llega a 0 y se descarta.
    Tablas de rutas:
        R1 (8881): rutas_R1_v2.txt
        R2 (8882): rutas_R2_v2_error.txt
        R3 (8883): rutas_R3_v2.txt
    """
    print("\n===== Pruebas con TTL 1: tabla de R2 mal configurada, TTL=10 =====", flush=True)
    pids = start_routers([
        (8881, "rutas_R1_v2.txt"),
        (8882, "rutas_R2_v2_error.txt"),
        (8883, "rutas_R3_v2.txt"),
    ])
    send(IP, 8881, "hola R1!", IP, 8883, ttl=10)
    send(IP, 8883, "hola R3!", IP, 8881, ttl=10)
    stop_routers(pids)


def file_order() -> None:
    """Pruebas con TTL, prueba 2: red de 5 routers. Envía mensajes.txt de R1 a R5 con prueba_router.py
    (TTL 10) para observar el orden en que llegan los paquetes.
    Tablas de rutas: rutas_R{1..5}_v3.txt
    """
    print("\n===== Pruebas con TTL 2: orden de paquetes en red de 5 routers =====", flush=True)
    pids = start_routers([(8880 + i, f"rutas_R{i}_v3.txt") for i in range(1, 6)])
    with open("mensajes.txt", encoding="utf-8") as f:
        subprocess.run([sys.executable, "prueba_router.py", IP, "8885", "10", IP, "8881"], stdin=f, check=True)
    time.sleep(1)
    stop_routers(pids)


if __name__ == "__main__":
    example_1()
    example_2()
    round_robin_1()
    round_robin_2()
    default_router()
    bad_routes()
    hops_5_routers()
    hops_7_routers()
    ttl_drop()
    bad_routes_ttl()
    file_order()
