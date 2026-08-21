from pathlib import Path

BASE_DIR: Path = Path(__file__).parent
HTML_PATH: Path = BASE_DIR / 'index-gta.html'
PROXY_JSON_PATH: Path = BASE_DIR / 'proxy.json'

SERVER_NAME: str = "http_server.py/Actividad-1"
SERVER_CONNECTION: str = "close"
SERVER_ADDRESS: tuple[str, int] = ('10.192.1.3', 8080)
SERVER_BUFFER_SIZE: int = 4
SERVER_WORKERS: int = 4



