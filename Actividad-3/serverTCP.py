#import socket
import os
from time import sleep

from config import *
from socketTCP import SocketTCP as socket

if __name__ == '__main__':
    """ TESTS de socketTCP por el lado del servidor"""
    
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.bind(SERVER_ADDRESS)
    #sock.listen(1)

    #conn_sock, addr = sock.accept()
    #print(addr)
    #sock.close()
    
    # SERVER
    print("Server: test de Conexión")
    server_socketTCP = socket.socket(1, 1)
    server_socketTCP.bind(SERVER_ADDRESS)
    connection_socketTCP, new_address = server_socketTCP.accept()
    client_addr = connection_socketTCP._conn_addr
    assert client_addr == new_address
    server_addr = connection_socketTCP._bind_addr
    with open("server-addr.txt", "w") as f:
        f.write(f"{client_addr}-{server_addr}")
    sleep(0.5)
    with open("client-addr.txt", "r") as f:
        result = f.readline() == f"{client_addr}-{server_addr}"
        
    os.remove("client-addr.txt") 
    assert result
    print("Server: test: recibiendo mensajes pequeños")
    connection_socketTCP.settimeout(SERVER_TIMEOUT)
    # test 1
    buff_size = 16
    full_message = connection_socketTCP.recv(buff_size)
    print("Test 1 received:", full_message)
    if full_message == b"Mensje de len=16": print("Test 1: Passed")
    else: print("Test 1: Failed")
    
    # test 2
    buff_size = 19
    full_message = connection_socketTCP.recv(buff_size)
    print("Test 2 received:", full_message)
    if full_message == b"Mensaje de largo 19": print("Test 2: Passed")
    else: print("Test 2: Failed")
    
    # test 3
    buff_size = 14
    message_part_1 = connection_socketTCP.recv(buff_size)
    message_part_2 = connection_socketTCP.recv(buff_size)
    print("Test 3 received:", message_part_1 + message_part_2)
    if (message_part_1 + message_part_2) == b"Mensaje de largo 19": print("Test 3: Passed")
    else: print("Test 3: Failed")
    
    print("Client: test: cerrando la conexión")
    connection_socketTCP.recv_close()

    sock = socket()
    closed = False
    try:
        sock._socket.bind(server_addr)
        closed = True
    except OSError:
        print("Dirección no liberada: Conexión no fue cerrada")
    finally:
       sock._socket.close() 
       
    assert closed
    
    sleep(0.5)
    connection_socketTCP, new_address = server_socketTCP.accept()
    
    def recv_n_bytes(conn_socket: socket, buff_size: int, nbytes: int) -> tuple[bytes, bytes]:
        """ Recibe un mensaje en una conexión tcp de hasta `nbytes`
        Args:
            conn_socket: Socket tcp de la conexión
            buff_size: Tamaño del buffer a usar en recv
            nbytes: La cantidad de bytes que se espera recibir. Debe ser mayor a 0
        Returns:
            2-tupla con los bytes recibidos, donde el primer elemento corresponden
            a los `nbytes` primeros bytes, y el segundo elemento corresponde al resto de
            bytes que eventualmente se pudieron haber recibido.
            Si no se recibió ninguno adicional entonces es `b""`
    
        """
        # recibimos la primera parte del mensaje
        recv_msg: bytes = conn_socket.recv(buff_size)
        full_msg: bytes = recv_msg
    
        # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
        def ready(): return len(full_msg) >= nbytes
    
        # entramos a un while para recibir el resto y seguimos esperando información
        # mientras el buffer no contenga secuencia de fin de mensaje
        while not ready():
            # recibimos un nuevo trozo del mensaje
            # y lo añadimos al mensaje "completo"
            full_msg += conn_socket.recv(buff_size)
    
        # finalmente retornamos el mensaje
        return full_msg[:nbytes], full_msg[nbytes:]
        
    
    connection_socketTCP.settimeout(SERVER_TIMEOUT)
    quijote_bytes, _ = recv_n_bytes(connection_socketTCP, 1024, 124111)
    assert len(quijote_bytes) == 124111
    with open("quijote.txt", "r", encoding="utf-8") as file:
        file.readline()
        quijote = file.read()
    assert quijote_bytes.decode() == quijote
    print("TODOS LOS TESTS PASARON")
    
