from __future__ import annotations

import json

from dataclasses import dataclass

from pathlib import Path

from http_parser import HTTP

@dataclass
class ProxyConfig:
    user: str
    blocked: list[str]
    forbidden_words: dict[str, str]


    @classmethod
    def from_json(cls, json_data) -> ProxyConfig:
        # TODO implementar checks para evitar acceder a llave inexistente

        # forbidden_words authored by ChatGPT
        forbidden_words = {
            key: value
            for item in json_data["forbidden_words"]
            for key, value in item.items()
        }
        return ProxyConfig(user=json_data['user'], blocked=json_data['blocked'], forbidden_words=forbidden_words)

    @classmethod
    def from_path_to_json(cls, path_to_json: Path) -> ProxyConfig:
        with open(path_to_json) as json_file:
            json_data = json.load(json_file)
            return ProxyConfig.from_json(json_data)

    def is_forbidden(self, start_line: str) -> bool:
        route = start_line.split()[1]

        if route.startswith("http://"):
            route = route[len("http://") :]
        elif route.startswith("https://"):
            route = route[len("https://") :]

        return route.removesuffix("/") in self.blocked

    def apply(self, http: HTTP) -> HTTP:
        """ Retorna un nuevo objeto HTTP con las palabras prohibidas reemplazadas
        Args:
            http: Objeto HTTP al cual se aplicaran las reglas del proxy
        Returns:
            Si el `body` del objeto contenía bytes, se retorna el mismo objeto,
            si no, se retorna un nuevo objeto HTTP con las reglas aplicadas.
        """
        # Si el cuerpo son bytes, no hay nada que hacer
        if not isinstance(http.body, str):
            return http
        # Se construye el nuevo cuerpo
        # remplazando las palabras
        body = http.body
        for forbidden, replacement in self.forbidden_words.items():
            body = body.replace(forbidden, replacement)

        # Se agregaa el header "X-ElQuePregunta" y se recalculan los bytes del cuerpo
        headers = http.headers.copy()
        headers["X-ElQuePregunta"] = self.user
        headers["Content-Length"] = str(len(body.encode()))

        return HTTP(
            start_line = http.start_line,
            _body=body,
            headers = headers,
        )