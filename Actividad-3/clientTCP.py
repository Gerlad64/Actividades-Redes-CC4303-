#import socket
import os
from time import sleep, time

from config import *
from socketTCP import SocketTCP as socket

if __name__ == '__main__':
    """ TESTS de socketTCP por el lado del cliente"""
    #client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #client_sock.connect(SERVER_ADDRESS)
    #client_sock.close()

    # CLIENT
    print("Client: test de Conexión")
    client_socketTCP = socket.socket(1,2)
    client_socketTCP.connect(SERVER_ADDRESS)
    client_addr = client_socketTCP._bind_addr
    server_addr = client_socketTCP._conn_addr
    with open("client-addr.txt", "w") as f:
        f.write(f"{client_addr}-{server_addr}")
    sleep(0.5)
    with open("server-addr.txt", "r") as f:
        result = f.readline() == f"{client_addr}-{server_addr}"
    os.remove("server-addr.txt") 
    assert result
    print("Client: test: mandando mensajes pequeños")
    
    # test 1
    message = b"Mensje de len=16"
    client_socketTCP.send(message)
    # test 2
    message = b"Mensaje de largo 19"
    client_socketTCP.send(message)
    # test 3
    print(client_socketTCP._conn_addr)
    message = b"Mensaje de largo 19"
    client_socketTCP.send(message)
    sleep(0.5)
    print("Client: test: cerrando la conexión")
    client_socketTCP.close()

    # Utiliza el socket udp detrás de socketTCP
    # para no importar socket original con otro nombre
    sock = socket()
    closed = False
    try:
        sock._socket.bind(client_addr)
        closed = True
    except OSError:
        print("Dirección no liberada: Conexión no fue cerrada")
    finally:
       sock._socket.close() 
       
    assert closed
    sleep(0.5)
    print("Client: test: mandando mensaje grande")
    
    with open("quijote.txt", "r", encoding="utf-8") as file:
        file.readline()
        quijote = file.read()
            
    sleep(0.5)
    client_socketTCP = socket()
    client_socketTCP.connect(SERVER_ADDRESS)
    client_socketTCP.send(quijote.encode())
