from __future__ import annotations

from dataclasses import dataclass

from http_exceptions import InvalidHTTPMessage


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
        pass

    @classmethod
    def parse_from_bytes(cls, http_message: bytes) -> HTTP:
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


