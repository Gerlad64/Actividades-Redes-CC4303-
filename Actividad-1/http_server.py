import socket
from http_parser import HTTP
from config import *


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

with open(HTML_PATH, "r", encoding='utf-8') as html_file:
    html = html_file.read()

HTTP_RESPONSE: HTTP = HTTP.from_html(html)
HTTP_RESPONSE.headers["Server"] = SERVER_NAME
HTTP_RESPONSE.headers["Connection"] = SERVER_CONNECTION

if __name__ == '__main__':

    tcp_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(SERVER_ADDRESS)

    tcp_socket.listen(SERVER_WORKERS)

    while True:
        new_socket, new_addr = tcp_socket.accept()
        head_bytes: bytes = recv_head(new_socket, SERVER_BUFFER_SIZE)
        http_req: HTTP = HTTP.from_bytes(head_bytes)
        print("Received Request:", http_req.create_message(), sep='\n')

        response_msg = HTTP_RESPONSE.create_message()
        print("Sending Response:", response_msg.split('\r\n\r\n', 1)[0], sep='\n')
        new_socket.send(response_msg.encode())
        print("Closing connection")
        new_socket.close()
