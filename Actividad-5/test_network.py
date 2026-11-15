import os
import signal
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


if __name__ == "__main__":
    example_1()
    example_2()
    round_robin_1()
    round_robin_2()
    default_router()
