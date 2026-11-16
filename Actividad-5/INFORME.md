## Informe Actividad 5
**Gerald Ponce Díaz**

**github**: https://github.com/Gerlad64/Actividades-Redes-CC4303-


### Documentación y diseño

| Archivo | Contenido |
| :--- | :--- |
| `router.py` | **Punto de entrada.** Función `network`: el router y su loop de recepción y *forwarding*. |
| `router_table.py` | `RouterTable`, `RouterEntry` y `NetworkArea`: lectura de la tabla de rutas, búsqueda y round-robin. `RouterTable.check` cumple el rol de `check_routes`. |
| `packet/packet.py` | `Packet`: header IP en bytes. `Packet.from_bytes` cumple el rol de `parse_packet` y `Packet.to_bytes` el de `create_packet`. |
| `packet/send.py` | Script emisor de mensajes (función `send`). |
| `prueba_router.py` | Script de pruebas por archivo (Parte II, paso 4): envía cada línea de `stdin` como un paquete. |
| `config.py` | `ROUTES_PATH` (carpeta de las tablas de rutas), `SOCK_BUFFER_SIZE` (bytes que recibe un router por paquete) y `BANNER`. |
| `routes/` | Tablas de rutas (`rutas_Rn_vk.txt`). |
| `test_network.py` | Pruebas: levanta los routers con `fork` y les envía paquetes. |
| `mensajes.txt` | Archivo de 30 líneas que se envía con `prueba_router.py`. |
| `results/` | Salidas de las pruebas sin TTL y con TTL. |

#### Tabla de rutas: similitudes y diferencias con una tabla real

Como en una tabla real, cada línea asocia una red de destino en notación CIDR
con un siguiente salto (*gateway*): el router solo conoce a quién entregar el
paquete, no el camino completo, y si ningún destino calza el paquete se descarta.

La principal diferencia es que aquí los hosts se agrupan por rangos de puertos, ya
que todos comparten la IP `127.0.0.1`. En una red real el puerto es de la capa de
transporte y el router no lo mira. Además, aquí se usa la primera línea que calza,
mientras que un router real elige el prefijo más largo (*longest prefix match*), y
la tabla es un archivo estático en vez de llenarse con protocolos de ruteo como
OSPF o BGP.

#### Script emisor de mensajes

`packet/send.py` construye un paquete con la dirección del router de destino final
y lo envía a un router de entrada, que no necesariamente es el destino:

```python
def send(dst_ip: str, dst_port: int, msg: str, via_ip: str, via_port: int, ttl: int = 64) -> None:
```

`(dst_ip, dst_port)` va en el header e indica a dónde debe *llegar* el paquete.
`(via_ip, via_port)` es el router al que el socket lo entrega. Separarlos permite
inyectar un paquete en cualquier punto de la red y observar su *forwarding*.

Recibe los datos por `sys.argv`, en el mismo orden que `send`. Se ejecuta como
módulo desde `Actividad-5/`, porque importa `Packet` desde el paquete `packet`.
El `ttl` (Parte II) es un sexto argumento opcional que vale 64 (*nix) si no se
entrega, así las pruebas de la Parte I no cambian:

```bash
python3 -m packet.send <ip_destino> <puerto_destino> <mensaje> <ip_envio> <puerto_envio> [ttl]
python3 -m packet.send 127.0.0.1 8882 "hola R2!" 127.0.0.1 8881
```

`send` también se importa desde `test_network.py` para enviar paquetes a los
routers creados con `fork`.

#### Script de pruebas por archivo (Parte II, paso 4)

`prueba_router.py` lee un archivo línea por línea desde `stdin` y envía cada línea
como un paquete, todas con el mismo destino y TTL, al mismo router inicial:

```bash
python3 prueba_router.py <ip_destino> <puerto_destino> <ttl> <ip_router_inicial> <puerto_router_inicial> < archivo
python3 prueba_router.py 127.0.0.1 8885 10 127.0.0.1 8881 < mensajes.txt
```

El enunciado no indica cómo se entrega el archivo, así que se usa `stdin` para no
agregar un argumento a su firma. El header va en tres argumentos y no como
`127.0.0.1;8885;10`, porque sin comillas bash interpreta `;` como separador de
comandos. A diferencia de `send`, que espera 0,3 s por envío, aquí las líneas se
envían seguidas para poder observar el orden de llegada (prueba 2 con TTL).

#### Round-robin

El round-robin está en `RouterTable` (`router_table.py`). Cada entrada define un
*área de la red* (`NetworkArea`). Entradas con la misma área son caminos
alternativos hacia los mismos routers. Al leer la tabla, las entradas se agrupan
por área y cada grupo queda en una lista circular (`itertools.cycle`):

```python
areas: dict[NetworkArea, list[RouterEntry]] = {}
for r_entry in self.TABLE:
    areas.setdefault(r_entry.AREA, []).append(r_entry)
self.ROUND_ROBIN = {area: cycle(entries) for area, entries in areas.items()}
```

`check` recorre la tabla en orden y, en la primera entrada que contiene el destino,
retorna el siguiente salto de la lista circular de su área:

```python
return next(self.ROUND_ROBIN[r_entry.AREA]).FWD_ADDR
```

Se eligió esta forma por tres razones:
- **Rutas por área:** cada área tiene su propio `cycle`, así que recuerda por
  separado la última ruta usada. En `R2`, los paquetes hacia `R1` y hacia `R5`
  alternan cada uno sin afectar al otro.
- **Número de rutas:** `cycle` sirve para cualquier cantidad de rutas, y un área
  con una sola ruta siempre retorna la misma.
- **Archivos de rutas:** no cambia su formato, basta con repetir el rango de
  destino con otro salto.

#### Router default

El router default está en `(127.0.0.1, 7000)`, conectado a los 5 routers del paso
8. Se agregó cambiando solo las tablas (`routes/rutas_R{1..5}_v5.txt` y
`routes/rutas_default_v5.txt`), sin código nuevo. Cada `rutas_Rn_v5.txt` es
`rutas_Rn_v3.txt` con una línea más al final, que calza con cualquier IP
(`0.0.0.0/0`) y puerto (`0-65535`). Por ejemplo, la tabla de `R2`:

```text
# archivo rutas_R2_v5.txt
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8883 8885 127.0.0.1 8883
127.0.0.1/24 8883 8885 127.0.0.1 8884
0.0.0.0/0 0 65535 127.0.0.1 7000
```

El router default tiene una ruta directa a cada router y ninguna ruta default
propia, así que descarta lo que no es para la red:

```text
# archivo rutas_default_v5.txt
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8882 8882 127.0.0.1 8882
127.0.0.1/24 8883 8883 127.0.0.1 8883
127.0.0.1/24 8884 8884 127.0.0.1 8884
127.0.0.1/24 8885 8885 127.0.0.1 8885
```

**¿En qué posición de la tabla debería ir la ruta default?** En la última línea.
`RouterTable.check` usa la primera entrada que contiene el destino. Como la ruta
default contiene cualquier destino, si estuviera antes que otra ruta, esa ruta
nunca se usaría. Al final, solo se usa cuando ninguna otra calza.


### Clases y estructuras

#### `Packet` (`packet/packet.py`)

```python
class Packet(ctypes.BigEndianStructure):
    IP: int
    PORT: int
    TTL: int

    _fields_ = [
        ("IP", ctypes.c_uint32),
        ("PORT", ctypes.c_uint16),
        ("TTL", ctypes.c_uint8)
    ]
    _pack_ = 1

    def __init__(self, ip: int, port: int, msg: bytes = b'', ttl: int = 64) -> None:
        super().__init__(ip, port, ttl)
        self.msg: bytes = msg
```

El header ocupa 7 bytes. `BigEndianStructure` escribe los campos en orden de red
y `_pack_ = 1` evita bytes de relleno entre campos.

| Atributo | Tipo | Por qué |
| :--- | :--- | :--- |
| `IP` | `c_uint32` | Una IPv4 `a.b.c.d` son 4 bytes. Como entero de 32 bits big endian, el 1er byte es `a` y el 4to es `d`, como pide el enunciado. `socket.inet_aton`/`inet_ntoa` hacen la conversión con el string. |
| `PORT` | `c_uint16` | Los puertos van de 0 a 65535, justo lo que cabe en 2 bytes sin signo. |
| `TTL` | `c_uint8` | El enunciado pide un entero entre 1 y 255 en 1 byte. Un byte sin signo cubre ese rango y también el 0 con que se descarta el paquete. |
| `msg` | `bytes` | Tiene largo variable, así que no va en `_fields_`. Es `bytes` porque es lo que entrega y recibe el socket. |

`from_bytes` lee los 7 bytes del header y deja el resto en `msg`. `to_bytes`
concatena el header (`bytes(memoryview(self))`) con `msg`. `ADDR` entrega el
destino como `(ip, puerto)`, el formato de los sockets y de la tabla de rutas.

#### `RouterEntry`, `NetworkArea` y `RouterTable` (`router_table.py`)

`RouterEntry` es una línea de la tabla de rutas. Es un `dataclass` porque solo
guarda datos, y `__contains__` permite escribir `dst_addr in r_entry`:

```python
@dataclass
class RouterEntry:
    DST_IP:   str
    DST_IP_RANGE: int
    DST_PORT_RANGE: tuple[int, int]
    FWD_IP: str
    FWD_PORT: int
```

| Atributo | Tipo | Por qué |
| :--- | :--- | :--- |
| `DST_IP` | `str` | Se usa con `ipaddress.ip_network(f"{DST_IP}/{DST_IP_RANGE}")`, que recibe strings. |
| `DST_IP_RANGE` | `int` | Es el largo del prefijo CIDR (por ejemplo, 24). |
| `DST_PORT_RANGE` | `tuple[int, int]` | Los dos extremos del rango de puertos, incluidos. Una tupla es inmutable, así que sirve como parte de una llave de diccionario (`NetworkArea`). |
| `FWD_IP`, `FWD_PORT` | `str`, `int` | El siguiente salto. `FWD_ADDR` los junta en `(ip, puerto)`, listo para `socket.sendto`. |

`NetworkArea` (propiedad `RouterEntry.AREA`) agrupa los tres campos de destino.
Hereda de `NamedTuple` para leerse por nombre y seguir siendo una tupla hasheable:
dos áreas con los mismos valores son la misma llave.

| Atributo de `RouterTable` | Tipo | Por qué |
| :--- | :--- | :--- |
| `TABLE` | `list[RouterEntry]` | Una lista mantiene el orden del archivo, y las rutas se revisan en orden descendente. |
| `ROUND_ROBIN` | `dict[NetworkArea, Iterator[RouterEntry]]` | Un `cycle` por área guarda por separado en qué ruta quedó cada área. |


### Flujo

El loop de `network` (`router.py`) implementa la recepción y *forwarding* de la
Parte I, paso 7, y la validación y decremento del TTL de la Parte II, pasos 2 y 3:

```python
if packet.TTL == 0:
    print(f"Se recibió paquete {packet_str} con TTL 0")
elif packet.ADDR == router_addr:
    print("paquete recibido:" + packet.msg.decode())
elif (next_hop := table.check(packet.ADDR)) is not None:
    packet.TTL -= 1
    packet.sendto(sock, *next_hop)
    print(f"redirigiendo paquete {packet_str} con destino final {packet.ADDR} desde {router_addr} hacia {next_hop}")
else:
    print(f"No hay rutas hacia {packet.ADDR} para paquete {packet_str}")
```


### Dependencias y entorno

- Probado con Python 3.15.2 en macOS. Requiere Python 3.13 o superior.
- Solo usa la biblioteca estándar: `socket`, `sys`, `ctypes`, `dataclasses`,
  `ipaddress`, `itertools`, `pathlib`, `typing` y `collections.abc`. Las pruebas
  también usan `os`, `signal`, `subprocess` y `time`.
- `test_network.py` usa `os.fork`, que solo existe en sistemas tipo Unix.


### Configuración y ejecución

`config.py` tiene la configuración de los routers:
- `ROUTES_PATH`: carpeta de las tablas de rutas (`routes/`). Por eso
  `router.py` recibe solo el nombre del archivo.
- `SOCK_BUFFER_SIZE = 1024`: bytes máximos que recibe un router por paquete
  (7 de header y hasta 1017 de mensaje).

Cada línea de una tabla de rutas tiene el formato:

```text
<red>/<prefijo> <puerto_inicial> <puerto_final> <ip_siguiente_salto> <puerto_siguiente_salto>
```

Todos los comandos se ejecutan desde `Actividad-5/`. Por ejemplo, para el ejemplo
1, un router por terminal y el envío en una tercera:

```bash
python3 router.py 127.0.0.1 8881 rutas_R1_v1.txt
python3 router.py 127.0.0.1 8882 rutas_R2_v1.txt
python3 -m packet.send 127.0.0.1 8882 "hola R2!" 127.0.0.1 8881
```

Para correr todas las pruebas:

```bash
python3 test_network.py
```

Desde la raíz del repositorio, el código pasa `ty check Actividad-5/` y
`ruff check Actividad-5/`.


### Pruebas

#### Pruebas de los pasos

Cada función de `test_network.py` levanta los routers con `fork`, envía paquetes
con `send` y detiene los routers con `SIGINT`:

| Función | Paso | Qué verifica |
| :--- | :--- | :--- |
| `example_1` | Parte I, paso 7 | Ejemplo 1 (R1 <-> R2): *forwarding*, entrega local y destino sin ruta. |
| `example_2` | Parte I, paso 7 | Ejemplo 2 (R1 <-> R2 <-> R3): lo mismo, con un salto intermedio. |
| `round_robin_1` | Parte I, paso 8, Test 1 | R2 cicla entre R3 y R4 para paquetes de R1 a R5. |
| `round_robin_2` | Parte I, paso 8, Test 2 | Con R0 y R6, R2 cicla por separado en cada área (R1 → R5 y R5 → R1 intercalados). |
| `default_router` | Parte I, paso 9 | Los paquetes hacia `(127.0.0.1, 9000)` y `(10.0.0.1, 8881)` terminan en el router default; uno de R1 a R5 no pasa por él. |
| `ttl_drop` | Parte II, pasos 2 y 3 | En el ejemplo 2, de R1 a R3: con TTL 1 lo descarta R2, con TTL 2 lo descarta R3 y con TTL 3 llega. |
| `bad_routes`, `hops_5_routers`, `hops_7_routers` | Pruebas sin TTL | Ver [Pruebas Mini-Internet sin TTL](#pruebas-mini-internet-sin-ttl). |
| `bad_routes_ttl`, `file_order` | Pruebas con TTL | Ver [Pruebas Mini-Internet con TTL](#pruebas-mini-internet-con-ttl). |

Para correr una sola:

```bash
python3 -c "import test_network as t; t.ttl_drop()"
```

#### Pruebas Mini-Internet sin TTL

Estas pruebas se ejecutaron sobre el tag de git `Actividad-5-Parte-I`, que marca
el código antes de implementar el TTL. Para reproducirlas, **desde la raíz del
repositorio** (`PYTHONUNBUFFERED=1` hace que los saltos se impriman en orden real):

```bash
mkdir /tmp/parte1 && git archive Actividad-5-Parte-I Actividad-5 | tar -x -C /tmp/parte1
cp Actividad-5/test_network.py /tmp/parte1/Actividad-5/
cp Actividad-5/routes/rutas_R2_v2_error.txt /tmp/parte1/Actividad-5/routes/
cd /tmp/parte1/Actividad-5
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.bad_routes()"
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.hops_5_routers()"
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.hops_7_routers()"
```

Con el código actual (TTL 64 por defecto) solo cambia la prueba 1, porque el ciclo
se corta a los 64 saltos. En las tablas siguientes, un salto es un envío entre dos
routers.

**1. Tabla de rutas de `R2` mal configurada** (`results/bad_routers.txt`). En la
red del ejemplo 2, `R2` usa `routes/rutas_R2_v2_error.txt`:

```text
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8883 8883 127.0.0.1 8881
```

- Un paquete de `R3` a `R1` llega normal (`R3 -> R2 -> R1`), porque la primera
  línea sigue correcta.
- Un paquete de `R1` a `R3` nunca llega: `R2` lo devuelve a `R1` por la segunda
  línea, y rebota entre ambos hasta que se detienen los routers.

Sin TTL, un error en una sola tabla basta para que un paquete circule para siempre
y cargue la red.

**2. Red de 5 routers (`rutas_R{1..5}_v3.txt`), 6 paquetes de `R1` a `R5`**
(`results/hops_5_routers.txt`).

| Paquete | Saltos | Camino |
| :--- | :---: | :--- |
| #0, #2, #4 | 7 | R1 → R2 → R3 → R2 → R4 → R2 → R3 → R5 |
| #1, #3, #5 | 3 | R1 → R2 → R4 → R5 |

- **¿Cuántos saltos dan?** 7 o 3. Los 6 paquetes llegan a `R5`.
- **¿Siempre la misma cantidad?** No, se alternan. `R3` y `R4` alternan entre `R2`
  y `R5` para llegar a `R5`, así que la mitad de las veces devuelven el paquete a
  `R2`. Round-robin no evita estos ciclos: el paquete llega porque la alternancia
  termina sacándolo.
- **¿Comparado con el mínimo?** El mínimo es 3 saltos. La mitad de los paquetes
  lo usa y la otra mitad da más del doble.

**3. Red de 7 routers del Test 2 del paso 8 (`rutas_R{0..6}_v4.txt`), 6 paquetes
de `R1` a `R5`** (`results/hops_7_routers.txt`). Se agrega `R0` (8880), conectado
a `R1` y `R2`, y `R6` (8886), conectado a `R2` y `R3`.

| Paquete | Saltos | Camino |
| :--- | :---: | :--- |
| #0 | 8 | R1 → R2 → R3 → R2 → R4 → R2 → R6 → R3 → R5 |
| #1 | 5 | R1 → R2 → R3 → R2 → R4 → R5 |
| #2 | 5 | R1 → R2 → R6 → R2 → R3 → R5 |
| #3 | 8 | R1 → R2 → R4 → R2 → R6 → R3 → R2 → R3 → R5 |
| #4 | 3 | R1 → R2 → R4 → R5 |
| #5 | 10 | R1 → R2 → R6 → R2 → R3 → R2 → R4 → R2 → R6 → R3 → R5 |

Los 6 paquetes llegan, pero los saltos varían más (de 3 a 10) y no hay un patrón
corto. `R2` alterna entre 3 caminos hacia `R5`, y `R3`, `R4` y `R6` también pueden
devolver el paquete a `R2`. `R6` no acorta el camino, así que el mínimo sigue
siendo 3, y solo 1 de los 6 paquetes lo logra. Más caminos alternativos sin TTL
significan más saltos innecesarios.

Archivos de rutas creados para esta red (en `routes/`):

```text
# archivo rutas_R0_v4.txt
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8882 8886 127.0.0.1 8882

# archivo rutas_R1_v4.txt
127.0.0.1/24 8880 8880 127.0.0.1 8880
127.0.0.1/24 8882 8886 127.0.0.1 8882

# archivo rutas_R2_v4.txt
127.0.0.1/24 8880 8881 127.0.0.1 8881
127.0.0.1/24 8880 8881 127.0.0.1 8880
127.0.0.1/24 8883 8886 127.0.0.1 8883
127.0.0.1/24 8883 8886 127.0.0.1 8884
127.0.0.1/24 8883 8886 127.0.0.1 8886

# archivo rutas_R3_v4.txt
127.0.0.1/24 8880 8882 127.0.0.1 8882
127.0.0.1/24 8880 8882 127.0.0.1 8886
127.0.0.1/24 8884 8885 127.0.0.1 8882
127.0.0.1/24 8884 8885 127.0.0.1 8885
127.0.0.1/24 8886 8886 127.0.0.1 8886

# archivo rutas_R4_v4.txt
127.0.0.1/24 8880 8883 127.0.0.1 8882
127.0.0.1/24 8880 8883 127.0.0.1 8885
127.0.0.1/24 8885 8886 127.0.0.1 8882
127.0.0.1/24 8885 8886 127.0.0.1 8885

# archivo rutas_R5_v4.txt
127.0.0.1/24 8880 8884 127.0.0.1 8884
127.0.0.1/24 8880 8884 127.0.0.1 8883
127.0.0.1/24 8886 8886 127.0.0.1 8883

# archivo rutas_R6_v4.txt
127.0.0.1/24 8880 8882 127.0.0.1 8882
127.0.0.1/24 8883 8885 127.0.0.1 8883
127.0.0.1/24 8883 8885 127.0.0.1 8882
```

#### Pruebas Mini-Internet con TTL

Estas pruebas usan el código actual. Desde `Actividad-5/`:

```bash
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.bad_routes_ttl()"
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.file_order()"
```

**1. Tabla de rutas de `R2` mal configurada, con TTL 10**
(`results/bad_routers_ttl.txt`). Es la prueba 1 sin TTL, con paquetes que salen
con TTL 10.

- El paquete de `R3` a `R1` llega igual que antes (`R3 → R2 → R1`).
- El paquete de `R1` a `R3` sigue rebotando entre `R1` y `R2`, pero cada router le
  resta 1 al TTL. Después de 10 saltos `R1` lo descarta:
  `Se recibió paquete 127.0.0.1;8883;0;hola R3! con TTL 0`.

La diferencia es que sin TTL el paquete circulaba hasta detener los routers, y con
TTL el ciclo dura como máximo 10 saltos. El error de la tabla sigue, pero el
paquete perdido ya no carga la red para siempre.

**2. Orden de los paquetes en la red de 5 routers** (`results/order_5_routers.txt`).
Con las tablas `rutas_R{1..5}_v3.txt`, `prueba_router.py` envía las 30 líneas de
`mensajes.txt` de `R1` a `R5` con TTL 10. `R5` recibió 28, en este orden:

```text
03 07 11 04 15 08 12 19 16 20 01 23 26 27 29 02 13 06 21 14 24 25 30 09 18 22 17 10
```

- **Los paquetes llegan desordenados.** Varios están en la red al mismo tiempo y
  round-robin los manda por caminos de 3, 5, 7 o 9 saltos. Uno que sale después
  por un camino más corto llega antes: el mensaje 01 dio 5 saltos y llegó 11°.
- **Se pierden paquetes.** Los mensajes 05 y 28 rebotaron entre `R2`, `R3` y `R4`
  hasta agotar el TTL.
- La capa de red no garantiza orden ni entrega. Eso le corresponde a una capa
  superior, como TCP.

El orden exacto puede cambiar entre ejecuciones. En el archivo de resultados
algunas líneas aparecen unidas, porque varios routers escriben a la vez en la
misma salida.


### Uso de IA

En esta actividad se experimentó con el uso de agentes de IA, por lo que se incluyó el 
archivo `AGENTS.md` en la raíz del proyecto. Los agentes ayudaron a escribir código y documentación
de manera más rápida, aún así, siempre bajo mi guía, con mi aprobación y entendimiento y siguiendo el diseño que
más me acomoda.
