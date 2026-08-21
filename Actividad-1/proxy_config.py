from __future__ import annotations

import json

from dataclasses import dataclass

from pathlib import Path


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
