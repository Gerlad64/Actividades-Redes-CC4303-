import socket
from http_parser import HTTP


def recv_full_msg(conn_socket: socket.socket, buff_size: int, end: str) -> bytes:
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

    # finalmente retornamos el mensaje
    return full_msg

def recv_head(conn_socket: socket.socket, buff_size: int) -> bytes:
    return recv_full_msg(conn_socket, buff_size, "\r\n\r\n")

if __name__ == '__main__':

    tcp_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = ('10.192.1.3', 8080)
    tcp_socket.bind(address)

    tcp_socket.listen(3)

    while True:
        new_socket, new_addr = tcp_socket.accept()
        head_bytes: bytes = recv_head(new_socket, 4)
        http_req: HTTP = HTTP.from_bytes(head_bytes)
        print("Received Request:", http_req.create_message(), sep='\n')
