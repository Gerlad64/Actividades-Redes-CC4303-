from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HTTP:
    """ dataclass HttpParsed
    clase de datos que almacena una petición/respuesta http válida parseada
    """
    start_line: str
    headers: dict[str, str]
    html: str

    def __post_init__(self):
        pass

    @classmethod
    def parse_from_bytes(cls, http_message: bytes) -> HTTP:
        decoded_http_message: str = http_message.decode()
        parsed_by_rn = decoded_http_message.split("\r\n")

        # Como mínimo, start_line, \r\n, un html
        if len(parsed_by_rn) < 3:
            raise Exception("Unexpected HTTP message")

        # Penúltimo elemento existe y debe ser \r\n
        if parsed_by_rn[-2] != "\r\n":
            raise Exception(r"Missing \r\n before body")

        start_line = parsed_by_rn[0]
        html = parsed_by_rn[-1]

        # * función lambda genera [h, c], 'h' a la izquierda de ':', 'c' a la derecha
        #   si no es capaz de hacer split, el header no es válido
        # * el resultado de map es [[h1, c1], [h2, c2], ...] o []
        headers = dict(map(
            lambda s: s.split(":", 1),
            parsed_by_rn[1:-2]
        ))

        return HTTP( start_line, headers, html )

    def create_message(self) -> str:
        # Une los strings de la lista resultante con \r\n
        # supone que content no tiene espacios ni saltos de linea al inicio
        return (
                "\r\n".join(
                    [self.start_line] +
                    [ header + ": " + content for header, content in self.headers ] +
                    ["\r\n", self.html]
                )
        )


