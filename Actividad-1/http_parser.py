from __future__ import annotations

import socket
from dataclasses import dataclass
from pathlib import Path

from http_exceptions import InvalidHTTPMessage
from socket_utils import recv_head, recv_n_bytes

MIME_TYPES = {
        "html": "text/html",
        "txt": "text/plain",
        "css": "text/css",
        "js": "application/javascript",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "json": "application/json"
}

@dataclass
class HTTP:
    """ dataclass HTTP
    clase de datos que almacena una petición/respuesta http válida parseada
    Attributes:
        start_line (str): La línea de inicio del protocolo HTTP
        headers (dict[str, str]): Diccionario que almacena el head, mapea el tipo de header con su contenido
        _body (str | bytes): El cuerpo de la respuesta HTTP en texto plano o bytes.
    """
    start_line: str
    headers: dict[str, str]
    _body: str | bytes

    @property
    def body(self) -> str:
        """ Accede al cuerpo del mensaje HTTP cuando contiene texto plano """
        if isinstance(self._body, str):
            return self._body
        raise TypeError(
            "No puedes acceder a '.body' porque contiene datos binarios (bytes)"
            "Usa la propiedad '.body_bytes' en su lugar."
        )
    @body.setter
    def body(self, body: str) -> None:
        """ Setter de la propiedad body. Se usa para colocar texto plano en el body HTTP"""
        self._body = body

    @property
    def body_bytes(self) -> bytes:
        """ Accede al cuerpo del mensaje HTTP cuando contiene bytes """
        if isinstance(self._body, bytes):
            return self._body

        return self._body.encode()

    @body_bytes.setter
    def body_bytes(self, body: bytes) -> None:
        """ Setter de la propiedad body. Se usa para colocar bytes en el body HTTP """
        self._body = body

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
        self.start_line = self.start_line.strip()

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
    def from_file(cls, path: Path, not_found_html: str | None = None, raise_error = False) -> HTTP:
        """ Crea un mensaje HTTP a partir de un archivo
        Detecta el tipo de archivo y asigna un Content-Type adecuado.

        **todo**: Manejar cuando el archivo no es encontrado

        Args:
            path: Ruta al archivo
            not_found_html: (str | None) Página html a mostrar si no se encuentra el archivo
            raise_error: bool, si es True, entonces se lanzará un error si no se encuentra un archivo en `path`
        Returns:
            HTTP: Objeto HTTP con `start_line` inicializado como `HTTP/1.1 {status_code} {phrase}`, `headers`
            con Content-Type y Content-Lenght inicializados según el archivo y `body` contiene su contenido.
        """
        try:
            # 1. Seguimos leyendo en binario ('rb') porque si no, los .png darán error
            with open(path, 'rb') as f:
                body = f.read()

            # 2. Extraer la extensión manualmente usando operaciones de string
            path_str = str(path)
            if "." in path_str:
                # rsplit('.', 1) corta por el último punto que encuentre
                ext = path_str.rsplit(".", 1)[-1].lower()
            else:
                ext = ""

            # 3. Buscar en el diccionario. Si no existe, usamos octet-stream (binario genérico)
            content_type = MIME_TYPES.get(ext, "application/octet-stream")

            start_line = "HTTP/1.1 200 OK"
            headers = {
                "Content-Type": content_type,
                "Content-Length": str(len(body))
            }

            return cls(start_line=start_line, headers=headers, _body=body)

        except FileNotFoundError:
            if raise_error:
                raise FileNotFoundError(f"No existe archivo {path}")
            if not_found_html is not None:
                return cls.from_html(not_found_html, 404, "Not Found")

            body = b"<h1>404 - Archivo no encontrado</h1>"
            start_line = "HTTP/1.1 404 Not Found"
            headers = {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Length": str(len(body))
            }
            return cls(start_line=start_line, headers=headers, _body=body)

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
    def create_message_bytes(self) -> bytes:
        return (
                "\r\n".join(
                    [self.start_line] +
                    [ header + ": " + content for header, content in self.headers.items() ] +
                    ["\r\n"]
                ).encode() + self.body_bytes
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

