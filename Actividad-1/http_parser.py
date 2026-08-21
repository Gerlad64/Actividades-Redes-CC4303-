from __future__ import annotations

import socket
from dataclasses import dataclass

from http_exceptions import InvalidHTTPMessage
from socket_utils import recv_head, recv_n_bytes


@dataclass
class HTTP:
    """ dataclass HTTP
    clase de datos que almacena una petición/respuesta http válida parseada
    Attributes:
        start_line (str): La línea de inicio del protocolo HTTP
        headers (dict[str, str]): Diccionario que almacena el head, mapea el tipo de header con su contenido
        body (str): El cuerpo de la respuesta HTTP en texto plano.
    """
    start_line: str
    headers: dict[str, str]
    body: str

    def __post_init__(self):
        """ Rutina post-inicialización que asegura que `start_line`, `headers` sean válidos según
        el protocolo HTTP.

        :return:
        """
        prohibited_chars: list[str] = ["\r", "\n"]
        found_header = [c for c in prohibited_chars if c in self.headers]
        found_content = [c for c in prohibited_chars if c in self.headers.values()]

        for header, content in self.headers.items():
            if found_header:
                found = ", ".join(repr(f) for f in found_header)
                raise InvalidHTTPMessage(f"{found} found in header: {header!r}")
            if found_content:
                found = ", ".join(repr(f) for f in found_content)
                raise InvalidHTTPMessage(f"{found} found in header: {content!r}")

        self.headers = {
            k.strip(): v.strip() for k, v in self.headers.items()
        }

    @classmethod
    def from_html(cls, html: str, status_code: int = 200, phrase: str = "OK") -> HTTP:
        """ Crea un mensaje HTTP a partir de un documento html
        Args:
            html: (str): string con el documento html
            status_code (int, optional): El código de estado de la respuesta HTTP
            phrase (str, optional): Frase después del código de estado de la respuesta
        Returns:
            HTTP: Objeto HTTP con `start_line` inicializado como `HTTP/1.1 {status_code} {phrase}`, `headers`
            con Content-Type y Content-Lenght inicializados según el html y `body` contiene el `html`
        """
        start_line = f"HTTP/1.1 {status_code} {phrase}"
        headers = {
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": str(len(html.encode()))
        }
        return cls(start_line, headers, html)

    @classmethod
    def from_bytes(cls, http_message: bytes) -> HTTP:
        """ Parsea los bytes de un mensaje HTTP
        Args:
            http_message (bytes): bytes del mensaje HTTP
        Returns:
            HTTP: El mensaje HTTP parseado en un objeto :class:`HTTP`
        """
        decoded_http_message: str = http_message.decode()
        parsed_by_rn = decoded_http_message.split("\r\n")
        # Como mínimo: start_line\r\n\r\n --> [start_line, '', '']
        if len(parsed_by_rn) < 3:
            raise InvalidHTTPMessage(f"Unexpected HTTP message. Received:\n {decoded_http_message}")

        # Penúltimo elemento existe y debe ser ''
        if parsed_by_rn[-2] != '':
            raise InvalidHTTPMessage(f"Missing \\r\\n\\r\\n before body. Received:\n {decoded_http_message}")

        start_line = parsed_by_rn[0]
        body = parsed_by_rn[-1]

        # * función lambda genera [h, c], 'h' a la izquierda de ':', 'c' a la derecha
        #   si no es capaz de hacer split, el header no es válido
        # * el resultado de map es [[h1, c1], [h2, c2], ...] o []
        headers = dict(map(
            lambda s: s.split(":", 1),
            parsed_by_rn[1:-2]
        ))

        return HTTP( start_line, headers, body )

    @classmethod
    def from_request(cls, conn_socket: socket.socket, buff_size: int) -> HTTP:
        """ Recibe una solicitud HTTP del socket tcp de la conexión
        y retorna un objeto HTTP.

        Returns:
            La solicitud HTTP *parseada* en el objeto HTTP. Si los headers incluyen
            `Content-Length`, entonces, se retorna el objeto con el parámetro `body`
            inicializado con el contenido del cuerpo recibido.
        """
        # se reciben los headers, con la posibilidad de recibir parte
        # del body (mirar docstring recv_head)
        head_bytes, body_bytes = recv_head(conn_socket, buff_size)
        # se crea objeto HTTP para la request
        http = cls.from_bytes(head_bytes)

        # Se recibe el cuerpo HTTP si Content-Length está en los headers
        if "Content-Length" in http.headers:
            body_remainder: bytes = recv_n_bytes(
                conn_socket,
                buff_size,
                nbytes=int(http.headers["Content-Length"]) - len(body_bytes)
            )[0]
            http.body = (body_bytes + body_remainder).decode()
            print("------body-------")
            print(http.body)

        return http

    def create_message(self) -> str:
        """ método para crear un mensaje http válido

        Crea y retorna un mensaje http a partir de los datos
        `start_line` `headers` y `body` almacenados en el objeto HTTP.

        Dado que los datos almacenados en el objeto son válidos, el mensaje retornado
        también lo será.
        """
        # Une los strings de la lista resultante con \r\n
        # supone que content no tiene espacios ni saltos de linea al inicio
        return (
                "\r\n".join(
                    [self.start_line] +
                    [ header + ": " + content for header, content in self.headers.items() ] +
                    ["\r\n", self.body]
                )
        )
    def send_to(self, conn_socket: socket.socket, address: tuple[str, int], buffer_size: int) -> HTTP:
        """ Establece una conexión tcp y manda un mensaje HTTP con los datos guardados en el objeto.
        Retorna un objeto HTTP con la respuesta del mensaje.

        **Consideraciones**:
            - El socket **no** debe tener una conexión activa
            - La conexión **no** es cerrada al finalizar la función
            - Se agrega (o **sobreescribe**) el header "Host" con la direción (ip y puerto) en `address`

        Args:
            conn_socket: Socket tcp. Este socket **no** debe tener una conexión activa al llamar a este método.
            address: dirección donde se mandará la solicitud
            buffer_size: tamaño del buffer de recepción
        """
        conn_socket.connect(address)
        self.headers["Host"] = f"{address[0]}:{address[1]}"
        conn_socket.send(self.create_message().encode())
        http_response = HTTP.from_request(conn_socket, buffer_size)

        return http_response

