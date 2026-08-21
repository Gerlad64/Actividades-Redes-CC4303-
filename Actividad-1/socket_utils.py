import socket



def recv_full_msg(conn_socket: socket.socket, buff_size: int, end: str) -> tuple[bytes, bytes]:
    """ Recibe un mensaje en una conexión tcp hasta encontrar la secuencia `end`.

    Si existen más bytes luego de `end` estos **también serán recibidos**

    Args:
        conn_socket: Socket tcp de la conexión
        buff_size: Tamaño del buffer a usar en recv
        end: Secuencia de término del mensaje
    Returns:
        2-tupla con los bytes recibidos, donde el primer elemento corresponden
        a los bytes hasta la secuencia `end` inclusiva, y el segundo elemento
        corresponde al resto de bytes que eventualmente se pudieron haber recibido.
        Si no se recibió ninguno adicional entonces es `b""`
    """
    # recibimos la primera parte del mensaje
    recv_msg: bytes = conn_socket.recv(buff_size)
    full_msg: bytes = recv_msg

    # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
    def is_end_of_msg(): return full_msg.find(end.encode()) != -1

    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras el buffer no contenga secuencia de fin de mensaje
    while not is_end_of_msg():
        # recibimos un nuevo trozo del mensaje
        # y lo añadimos al mensaje "completo"
        full_msg += conn_socket.recv(buff_size)

    full_msg, remainder = full_msg.split(end.encode(), 1)
    # Se incluye la secuencia de terminación en
    # el mensaje final
    full_msg += end.encode()
    # finalmente retornamos el mensaje
    return full_msg, remainder

def recv_n_bytes(conn_socket: socket.socket, buff_size: int, nbytes: int) -> tuple[bytes, bytes]:
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

def recv_head(conn_socket: socket.socket, buff_size: int) -> tuple[bytes, bytes]:
    """ Recibe los headers de un mensaje http en bytes

    Args:
        conn_socket: Socket tcp de la conexión
        buff_size: Tamaño del buffer a usar en recv
    Returns:
        2-tupla con los bytes recibido. El primer elemento son los headers en bytes,
        incluyendo `\r\n\r\n`. El segundo elemento corresponde a una parte del `body` si
        es que se recibieron bytes adicionales, de lo contrario, `b""`
    """
    return recv_full_msg(conn_socket, buff_size, "\r\n\r\n")
