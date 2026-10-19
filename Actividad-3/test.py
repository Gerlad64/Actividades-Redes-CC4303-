import subprocess
import sys
import time

def run_integration_test():
    print("Iniciando servidor TCP...")
    # Levantar el servidor TCP en segundo plano
    server_proc = subprocess.Popen(
        [sys.executable, "serverTCP.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Dar un instante para que el socket del servidor abra el puerto
    time.sleep(1)

    print("Ejecutando cliente TCP...")
    try:
        # Ejecutar el cliente con un timeout máximo de 10 segundos
        client_proc = subprocess.run(
            [sys.executable, "clientTCP.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
    except subprocess.TimeoutExpired:
        print("ERROR: El cliente se quedó esperando infinitamente (Timeout).")
        server_proc.kill()
        sys.exit(1)

    # Esperar a que el servidor termine automáticamente tras atender al cliente
    try:
        server_stdout, server_stderr = server_proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        print("ERROR: El servidor no se cerró y se quedó esperando infinitamente.")
        server_proc.kill()
        sys.exit(1)

    # Verificar que ambos terminaron con código 0
    if client_proc.returncode != 0:
        print(f"ERROR en clientTCP.py:\n{client_proc.stderr}")
        sys.exit(1)

    if server_proc.returncode != 0:
        print(f"ERROR en serverTCP.py:\n{server_stderr}")
        sys.exit(1)

    print("PRUEBA EXITOSA: Servidor y cliente terminaron correctamente sin errores.")
    sys.exit(0)

if __name__ == "__main__":
    run_integration_test()