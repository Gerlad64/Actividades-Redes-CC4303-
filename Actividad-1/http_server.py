import socket
from http_parser import HTTP
from config import *
from proxy_config import ProxyConfig
import sys




with open(HTML_PATH, "r", encoding='utf-8') as html_file:
    html = html_file.read()

with open(STATUS_404_PATH, "r", encoding='utf-8') as html_file:
    STATUS_404 = html_file.read()

with open(STATUS_403_PATH, "r", encoding='utf-8') as html_file:
    STATUS_403 = html_file.read()

STATUS_403 = STATUS_403.replace(
    'src="/',
    f'src="http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}/'
)

STATUS_404 = STATUS_404.replace(
    'src="/',
    f'src="http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}/'

)

proxy_config: ProxyConfig = ProxyConfig.from_path_to_json(PROXY_JSON_PATH)
headers = {
    "Connection": SERVER_CONNECTION,
    "X-ElQuePregunta": proxy_config.user
}

def http_proxy_request(start_line: str) -> HTTP:
    return HTTP(start_line, headers, "")


if __name__ == '__main__':

    tcp_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(SERVER_ADDRESS)

    tcp_socket.listen(SERVER_WORKERS)

    while True:
        new_socket, new_addr = tcp_socket.accept()
        http_req: HTTP = HTTP.from_request(new_socket, SERVER_BUFFER_SIZE)
        print("Received Request:", http_req.create_message(), sep='\n')

        # Lógica Proxy
        if http_req.headers.get("Host", f"{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}") != f"{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}":

            # Primero verifica que el sitio no esté prohibido
            if proxy_config.is_forbidden(http_req.start_line):
                http_res = HTTP.from_html(STATUS_403, 403, "Forbidden")
            else:
                # Crear socket para conexión con servidor de destino
                proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Obtiene la dirección a partir del header
                # la clase HTTP asegura que está bien formateado
                # la dirección puede ser un dominio sin puerto, ya que por defecto es el 80
                address = http_req.headers["Host"].split(":")
                ip = address[0]

                port = 80 if len(address) == 1 else int(address[1])

                print("Proxy Request:", http_proxy_request(http_req.start_line).create_message(), sep='\n')
                # Se manda el mensaje http desde el proxy y se recibe una respuesta
                http_res: HTTP = http_proxy_request(http_req.start_line).send_to(
                    conn_socket=proxy_socket,
                    address=(ip, port),
                    buffer_size=SERVER_BUFFER_SIZE
                )
                # Se termina la conexión
                proxy_socket.close()
                http_res = proxy_config.apply(http_res)
            print("Sending Response:", http_res.create_message(), sep='\n')
            # Se manda el http recibido desde el proxy
            new_socket.send(http_res.create_message().encode())

        else: # Si no se realiza una petición a un sitio externo, se retorna
            route = http_req.start_line.split()[1][len(f"http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}/"):]
            print("route: ",route)
            if len(route) <= 1:
                response_bytes = HTTP.from_html(
                    html,
                ).create_message_bytes()
                print("Sending Response:", response_bytes.decode().split('\r\n\r\n', 1)[0], sep='\n')
            else:
                response_bytes = HTTP.from_file(
                    BASE_DIR / Path(route),
                    STATUS_404
                ).create_message_bytes()
            new_socket.send(response_bytes)

        print("Closing connection")
        new_socket.close()
