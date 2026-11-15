import os
import signal
import sys
import time

from packet.send import send
from router import network

IP = "127.0.0.1"


def start_routers(routers: list[tuple[int, str]]) -> list[int]:
    """Hace fork de un proceso por router y retorna sus pids."""
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
    """Detiene los routers con SIGINT (KeyboardInterrupt) y espera a que terminen."""
    for pid in pids:
        os.kill(pid, signal.SIGINT)
    for pid in pids:
        os.waitpid(pid, 0)


def example_1() -> None:
    print("\n===== Ejemplo 1: R1 <-> R2 =====", flush=True)
    pids = start_routers([(8881, "rutas_R1_v1.txt"), (8882, "rutas_R2_v1.txt")])
    send(IP, 8882, "hola R2!", IP, 8881)
    send(IP, 8881, "hola R1!", IP, 8882)
    send(IP, 8881, "hola", IP, 8881)
    send(IP, 8884, "hola", IP, 8881)
    stop_routers(pids)


def example_2() -> None:
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
    print("\n===== Paso 8, Test 1: red de 5 routers =====", flush=True)
    pids = start_routers([(8880 + i, f"rutas_R{i}_v3.txt") for i in range(1, 6)])
    for i in range(4):
        send(IP, 8885, f"R1->R5 #{i}", IP, 8881)
    stop_routers(pids)


def round_robin_2() -> None:
    print("\n===== Paso 8, Test 2: red de 7 routers (R0 y R6) =====", flush=True)
    pids = start_routers([(8880 + i, f"rutas_R{i}_v4.txt") for i in range(7)])
    for i in range(4):
        send(IP, 8885, f"R1->R5 #{i}", IP, 8881)
        send(IP, 8881, f"R5->R1 #{i}", IP, 8885)
    stop_routers(pids)


if __name__ == "__main__":
    example_1()
    example_2()
    round_robin_1()
    round_robin_2()
