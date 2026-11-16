## Informe Actividad 6
**Gerald Ponce Díaz**

**github**: https://github.com/Gerlad64/Actividades-Redes-CC4303-


### Documentación y diseño

El código es una copia de *Forwarding básico* con TTL (Actividad 5), a la que se
le agregó fragmentación y reensamblaje.

| Archivo | Contenido |
| :--- | :--- |
| `router.py` | **Punto de entrada.** Función `network`: el router y su loop de recepción, *forwarding* con fragmentación (paso 4) y reensamblaje (pasos 6 y 7). |
| `packet/packet.py` | `Packet`: header IP en bytes (paso 1). `Packet.from_bytes` cumple el rol de `parse_packet` y `Packet.to_bytes` el de `create_packet`. |
| `packet/fragmentation.py` | `fragment_IP_packet` (paso 3) y `reassemble_IP_packet` (paso 5). |
| `router_table.py` | `RouterTable`, `RouterEntry` y `NetworkArea`: tabla de rutas con MTU y round-robin. `RouterTable.check` cumple el rol de `check_routes` (paso 2). |
| `packet/send.py` | Script emisor de mensajes (función `send`), ahora con `ID`. |
| `config.py` | `ROUTES_PATH` (carpeta de las tablas de rutas), `SOCK_BUFFER_SIZE` y `BANNER`. |
| `routes/` | Tablas de rutas con MTU (`rutas_Rn_v3_mtu.txt`). |
| `test_fragmentation.py` | Pruebas sin red de los pasos 1, 2, 3 y 5 (con `assert`). |
| `test_network.py` | Pruebas con routers: los levanta con `fork` y les envía paquetes. |
| `results/` | Salidas de las pruebas de `test_network.py`. |

#### Estructura del header

`[Dirección IP][Puerto][TTL][ID][Offset][Tamaño][FLAG][mensaje]`

| Campo | Bytes | Decisión |
| :--- | :---: | :--- |
| `Dirección IP` | 4 | Igual que en la Actividad 5. |
| `Puerto` | 2 | Igual que en la Actividad 5. |
| `TTL` | 1 | Igual que en la Actividad 5. |
| `ID` | 2 | El campo *Identification* de IPv4 es de 16 bits. Alcanza para 65536 paquetes en tránsito hacia un mismo destino. |
| `Offset` | 4 | Se mide en bytes, así que debe poder apuntar a cualquier byte de un mensaje cuyo `Tamaño` ocupa 4 bytes. Por eso usa el mismo ancho. |
| `Tamaño` | 4 | Lo fija el enunciado. Es el largo del mensaje sin el header. |
| `FLAG` | 1 | Entero `0` o `1`. En IPv4 es 1 bit, pero aquí todos los campos ocupan bytes completos y 1 byte es el mínimo. |

El header ocupa **18 bytes** fijos (`HEADER_SIZE`). El MTU más chico de la red es
50, así que cada fragmento lleva al menos 32 bytes de mensaje.

#### Tabla de rutas con MTU

Cada línea agrega el MTU del enlace como sexto campo. `RouterTable.check` retorna
`(next_hop_address, MTU)` de la ruta que elige el round-robin, o `None`:

```python
route = next(self.ROUND_ROBIN[r_entry.AREA])
return route.FWD_ADDR, route.MTU # --> ((next_hop_IP, next_hop_PORT), MTU)
```

**Diferencia con el enunciado:** en el enunciado, la tabla de `R5` viene sin
prefijo (`127.0.0.1 8881 8884 ...`), a diferencia de las otras cuatro. Se tomó
como un error de tipeo y `rutas_R5_v3_mtu.txt` usa `127.0.0.1/24`, igual que el
resto y que el formato `[Red (CIDR)]`.

#### Fragmentación (`fragment_IP_packet`)

Recibe y retorna bytes, como pide el enunciado. Si el paquete cabe en el MTU lo
retorna tal cual. Si no, corta el mensaje en trozos de `MTU - HEADER_SIZE` bytes y
le pone a cada uno un header propio:

```python
chunk_size = MTU - HEADER_SIZE
for start in range(0, packet.SIZE, chunk_size):
    chunk = packet.msg[start: start + chunk_size]
    is_last = start + chunk_size >= packet.SIZE
    fragment = Packet(packet.IP, packet.PORT, chunk, packet.TTL, packet.ID,
                      packet.OFFSET + start, packet.FLAG if is_last else 1)
```

Dos decisiones permiten **re-fragmentar un fragmento**:
- **Offset absoluto:** `packet.OFFSET + start`. El offset siempre es respecto al
  datagrama original, no respecto al fragmento que se está cortando.
- **FLAG heredado:** todos los trozos llevan `FLAG = 1`, salvo el último, que
  copia el `FLAG` del paquete recibido. Si se corta un fragmento intermedio
  (`FLAG = 1`), su último trozo sigue teniendo fragmentos después.

`IP`, `Puerto`, `TTL` e `ID` se copian sin cambios, y `Tamaño` es el largo del trozo.

#### Reensamblaje (`reassemble_IP_packet`)

Ordena los fragmentos por `Offset` y revisa que sean contiguos desde el byte 0
hasta un fragmento con `FLAG = 0`:

```python
fragments = sorted((Packet.from_bytes(fragment) for fragment in fragment_list), key=lambda f: f.OFFSET)
next_offset = 0
flag = 1
for fragment in fragments:
    if fragment.OFFSET != next_offset:  # falta el fragmento que empieza en next_offset
        return None
    next_offset += fragment.SIZE
    flag = fragment.FLAG
if flag != 0:  # falta el fragmento final
    return None
```

Con esto no hace falta un caso especial para `len(fragment_list) == 1`: un paquete
sin fragmentar (`Offset == 0` y `FLAG == 0`) pasa ambas condiciones, y un fragmento
solo falla en una de las dos. Si está completo, retorna un paquete con el mensaje
unido, `Offset = 0` y `FLAG = 0`.

Como en IP, solo reensambla el router de destino. Los routers intermedios nunca
unen fragmentos, porque cada uno puede viajar por un camino distinto.


### Clases y estructuras

#### `Packet` (`packet/packet.py`)

```python
class Packet(ctypes.BigEndianStructure):
    IP: int
    PORT: int
    TTL: int
    ID: int
    OFFSET: int
    SIZE: int
    FLAG: int
    msg: bytes

    _fields_ = [
        ("IP", ctypes.c_uint32),
        ("PORT", ctypes.c_uint16),
        ("TTL", ctypes.c_uint8),
        ("ID", ctypes.c_uint16),
        ("OFFSET", ctypes.c_uint32),
        ("SIZE", ctypes.c_uint32),
        ("FLAG", ctypes.c_uint8),
    ]
    _pack_ = 1

    def __init__(self, ip: int, port: int, msg: bytes = b'', ttl: int = 64,
                 packet_id: int = 0, offset: int = 0, flag: int = 0) -> None:
        super().__init__(ip, port, ttl, packet_id, offset, len(msg), flag)
        self.msg = msg
```

| Atributo | Tipo | Por qué |
| :--- | :--- | :--- |
| `IP` | `c_uint32` | Una IPv4 son 4 bytes. En big endian el 1er byte es `a` y el 4to es `d` de `a.b.c.d`. |
| `PORT` | `c_uint16` | Los puertos van de 0 a 65535, lo que cabe en 2 bytes sin signo. |
| `TTL` | `c_uint8` | Entero entre 0 y 255 en 1 byte. |
| `ID` | `c_uint16` | 2 bytes sin signo, como el *Identification* de IPv4. No es negativo. |
| `OFFSET` | `c_uint32` | Posición en bytes dentro del mensaje original. Usa el mismo ancho que `SIZE` para alcanzar cualquier byte. |
| `SIZE` | `c_uint32` | Los 4 bytes que pide el enunciado. No se recibe en `__init__`: siempre es `len(msg)`, así no puede quedar distinto del mensaje real. |
| `FLAG` | `c_uint8` | 1 byte con valor 0 o 1. Como entero se compara directo (`FLAG != 0`), sin convertir caracteres. |
| `msg` | `bytes` | Tiene largo variable, así que no va en `_fields_`. Es `bytes` porque es lo que entrega el socket, y porque un fragmento puede cortar un carácter de más de 1 byte. |

`from_bytes` usa `from_buffer_copy` para leer los 18 bytes del header y deja en
`msg` los `SIZE` bytes siguientes. `to_bytes` concatena el header con `msg`.
`__str__` entrega el formato legible `IP;Puerto;TTL;ID;Offset;Tamaño;FLAG;mensaje`
que se usa en los mensajes del router.

#### `RouterEntry` (`router_table.py`)

Se agregó un atributo. El resto de `router_table.py` no cambia respecto a la
Actividad 5.

| Atributo | Tipo | Por qué |
| :--- | :--- | :--- |
| `MTU` | `int` | Es una cantidad de bytes que se compara con `len(IP_packet)` y se resta con `HEADER_SIZE`. Va en la entrada porque es una propiedad del enlace hacia ese siguiente salto. |

#### Fragmentos recibidos (`router.py`)

```python
received: dict[int, list[bytes]] = {}
```

| Estructura | Tipo | Por qué |
| :--- | :--- | :--- |
| `received` | `dict[int, list[bytes]]` | La llave es el `ID`, lo que separa los fragmentos de paquetes distintos aunque lleguen intercalados. El valor es una lista porque los fragmentos se acumulan en orden de llegada y `reassemble_IP_packet` los ordena. Se guardan en `bytes` porque es lo que recibe esa función. |


### Flujo

El loop de `network` (`router.py`), para cada paquete o fragmento recibido:

```python
if packet.TTL == 0:
    print(f"Se recibió paquete {packet_str} con TTL 0")
elif packet.ADDR == router_addr:
    received.setdefault(packet.ID, []).append(msg)
    IP_packet = reassemble_IP_packet(received[packet.ID])
    if IP_packet is not None:
        del received[packet.ID]
        print("paquete recibido:" + Packet.from_bytes(IP_packet).msg.decode())
elif (route := table.check(packet.ADDR)) is not None:
    next_hop, mtu = route
    packet.TTL -= 1
    fragments = fragment_IP_packet(packet.to_bytes(), mtu)
    for fragment in fragments:
        sock.sendto(fragment, next_hop)
```

1. **TTL 0:** se descarta, igual que en la Actividad 5.
2. **Es para este router:** se guarda en `received` bajo su `ID` y se intenta
   reensamblar. Si retorna `None`, sigue esperando. Si retorna el paquete, imprime
   el mensaje sin headers y borra la entrada, para liberar esos fragmentos.
3. **No es para este router:** `check` entrega el siguiente salto y su MTU. Se
   descuenta el TTL **antes** de fragmentar, así todos los fragmentos salen con el
   TTL ya actualizado. Todos van al mismo siguiente salto, porque `check` se llama
   una vez por paquete recibido. En el router siguiente cada fragmento es un
   paquete más, y el round-robin puede separarlos.
4. **Sin ruta:** se descarta.


### Dependencias y entorno

- Probado con Python 3.15.2 en macOS. Requiere Python 3.13 o superior.
- Solo usa la biblioteca estándar: `socket`, `sys`, `ctypes`, `dataclasses`,
  `ipaddress`, `itertools`, `pathlib`, `typing` y `collections.abc`. Las pruebas
  también usan `os`, `signal`, `random` y `time`.
- `test_network.py` usa `os.fork`, que solo existe en sistemas tipo Unix.


### Configuración y ejecución

`config.py` tiene `ROUTES_PATH` (carpeta `routes/`, por eso `router.py` recibe solo
el nombre del archivo) y `SOCK_BUFFER_SIZE = 1024` (bytes máximos por paquete).

Cada línea de una tabla de rutas tiene el formato:

```text
<red>/<prefijo> <puerto_inicial> <puerto_final> <ip_siguiente_salto> <puerto_siguiente_salto> <mtu>
```

Todos los comandos se ejecutan desde `Actividad-6/`. Un router por terminal:

```bash
python3 router.py 127.0.0.1 8881 rutas_R1_v3_mtu.txt
python3 router.py 127.0.0.1 8882 rutas_R2_v3_mtu.txt
python3 router.py 127.0.0.1 8883 rutas_R3_v3_mtu.txt
python3 router.py 127.0.0.1 8884 rutas_R4_v3_mtu.txt
python3 router.py 127.0.0.1 8885 rutas_R5_v3_mtu.txt
```

El script emisor recibe el `ID` como séptimo argumento opcional (0 si no se
entrega). Siempre envía un paquete sin fragmentar (`Offset = 0`, `FLAG = 0`) y
calcula el `Tamaño`:

```bash
python3 -m packet.send <ip_destino> <puerto_destino> <mensaje> <ip_envio> <puerto_envio> [ttl] [id]
python3 -m packet.send 127.0.0.1 8885 "hola!" 127.0.0.1 8881 10 347
```

Para correr todas las pruebas:

```bash
python3 test_fragmentation.py
python3 test_network.py
```

Desde la raíz del repositorio, el código pasa `ty check Actividad-6/` y
`ruff check Actividad-6/`.


### Pruebas

#### Pruebas de los pasos

`test_fragmentation.py` prueba las funciones sin levantar routers. Usa
`IP_PACKET_V1`, un paquete de 150 bytes totales (18 de header y 132 de mensaje):

| Función | Paso | Qué verifica |
| :--- | :--- | :--- |
| `test_header` | 1 | `to_bytes(from_bytes(IP_packet_v1)) == IP_packet_v1`, el valor de cada campo y los 18 bytes exactos del header de un fragmento. |
| `test_check_routes` | 2 | En la tabla de `R2`, `check` retorna `(next_hop_address, MTU)` y alterna entre `R3` (MTU 50) y `R4` (MTU 80). |
| `test_fragment` | 3 | Lista de largo 1 si el paquete cabe. Con MTU 100 salen 2 fragmentos y con MTU 50 salen 5, todos de tamaño total menor o igual al MTU. |
| `test_refragment` | 3 | Al re-fragmentar, los offsets siguen siendo absolutos y solo el último trozo del último fragmento lleva `FLAG = 0`. |
| `test_reassemble` | 5 | `reassemble_IP_packet(fragment_IP_packet(IP_packet_v1, MTU)) == IP_packet_v1` para 8 valores de MTU, con fragmentos desordenados y re-fragmentados (100 → 80 → 50). |
| `test_reassemble_incomplete` | 5 | Retorna `None` si falta el primer fragmento, uno intermedio o el final, y con un fragmento solo. |

Funciones de `test_network.py`. Para correr una sola (`PYTHONUNBUFFERED=1` hace que
los saltos se impriman en orden real):

```bash
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.manual_reassembly()"
```

| Función | Paso | Qué verifica | Salida |
| :--- | :--- | :--- | :--- |
| `mtu_routes` | 2 | Con las tablas con MTU, llegan paquetes entre `R1` y `R2`, de `R3` a `R4` y de `R5` a `R1`. Uno sin ruta se descarta. | `results/mtu_routes.txt` |
| `manual_reassembly` | 7 | Ver abajo. | `results/manual_reassembly.txt` |
| `small_packet` | Informe 1 | Ver [prueba 1](#1-ttl-round-robin-y-paquetes-sin-fragmentar). | `results/small_packet.txt` |
| `fragmentation`, `fragmentation_other_routers` | Informe 2 | Ver [prueba 2](#2-fragmentación-y-re-fragmentación). | `results/fragmentation*.txt` |

**Paso 7.** `manual_reassembly` levanta solo `R5` y le envía directo los fragmentos
(MTU 50) de dos paquetes: A (`ID = 1`, 4 fragmentos) y B (`ID = 2`, 3 fragmentos).
Los envía tres veces: en orden, en desorden, e intercalando `ID` y en desorden. En
los tres casos `R5` imprime ambos mensajes completos. En el caso intercalado, los
fragmentos se envían como `(ID, Offset)`:

```text
[(1, 96), (2, 0), (1, 32), (2, 64), (1, 0), (2, 32), (1, 64)]
```

`R5` imprime primero B y después A, porque B se completa con su tercer fragmento
`(2, 32)` y A recién con el último `(1, 64)`.

#### Pruebas para el informe

Usan la topología de 5 routers con MTU. Desde `Actividad-6/`:

```bash
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.small_packet()"
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.fragmentation()"
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.fragmentation_other_routers()"
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.fragmentation(times=3, ttl=5)"
```

##### 1. TTL, round-robin y paquetes sin fragmentar

Se envía 4 veces el paquete `127.0.0.1;8885;10;347;0;5;0;hola!` de `R1` a `R5`
(`results/small_packet.txt`). Ocupa 23 bytes, menos que cualquier MTU.

| Envío | Camino | TTL al llegar |
| :--- | :--- | :---: |
| 1 y 3 | R1 → R2 → R3 → R2 → R4 → R2 → R3 → R5 | 3 |
| 2 y 4 | R1 → R2 → R4 → R5 | 7 |

- **Sin fragmentar:** cada salto dice `en 1 fragmento(s)` y `R5` imprime `hola!`
  apenas llega, porque el paquete tiene `Offset = 0` y `FLAG = 0`.
- **Round-robin:** `R2` alterna entre `R3` y `R4`, y los caminos de 7 y 3 saltos
  son los mismos de la Actividad 5.
- **TTL:** baja en 1 por salto. Un quinto envío con TTL 2 lo descarta `R3`:
  `Se recibió paquete 127.0.0.1;8885;0;347;0;5;0;hola! con TTL 0`.

##### 2. Fragmentación y re-fragmentación

Se envía 6 veces de `R1` a `R5` un paquete de **150 bytes totales** (132 de
mensaje), con TTL 64 e `ID` de 1 a 6 (`results/fragmentation.txt`). **Los 6
mensajes se reensamblan completos en `R5`.** El mensaje lleva su posición cada 10
bytes (`000-------010-------...`), así se ve que llega completo y en orden.

Los fragmentos se anotan como `(Offset, Tamaño)`:

| Paquete | `R1 → R2` (MTU 100) | En `R2` | Recibe `R5` |
| :--- | :--- | :--- | :--- |
| 1 | `(0, 82)` y `(82, 50)` | `(0, 82)` va a `R3` (MTU 50) y se re-fragmenta en `(0, 32)`, `(32, 32)` y `(64, 18)`. `(82, 50)` va a `R4` (MTU 80) y cabe. | 4 fragmentos |
| 2 a 6 | `(0, 82)` y `(82, 50)` | `(0, 82)` va a `R4` (MTU 80) y se re-fragmenta en `(0, 62)` y `(62, 20)`. `(82, 50)` va a `R3` (MTU 50) y se re-fragmenta en `(82, 32)` y `(114, 18)`. | 4 fragmentos |

Los fragmentos de un mismo paquete llegan por caminos distintos, de 3 a 9 saltos,
y desordenados. Por ejemplo, del paquete 1 llega primero `(32, 32)`.

**¿Cómo cambia el comportamiento si se envían desde otros routers?**
(`results/fragmentation_other_routers.txt`). Cambia cuántos fragmentos se crean y
dónde, porque depende del MTU del primer enlace que elige el round-robin. El
mensaje se reensambla en todos los casos.

| Origen → destino | Primer enlace | Primera fragmentación | Después |
| :--- | :--- | :--- | :--- |
| `R1 → R5` | `R1 → R2`, MTU 100 | 2 fragmentos (82 + 50) | Se re-fragmentan en `R2`. |
| `R2 → R5` | `R2 → R3`, MTU 50 | 5 fragmentos (4 de 32 + 4) | No se re-fragmentan: 50 es el MTU más chico. |
| `R2 → R5` | `R2 → R4`, MTU 80 | 3 fragmentos (62 + 62 + 8) | `R4` devuelve `(62, 62)` a `R2`, que lo manda a `R3` y lo re-fragmenta en 32 + 30. |
| `R3 → R5` | `R3 → R5`, MTU 55 | 4 fragmentos (3 de 37 + 21) | Llegan directo, en 1 salto. |
| `R3 → R5` | `R3 → R2`, MTU 50 | 5 fragmentos | No se re-fragmentan. |
| `R4 → R5` | `R4 → R2`, MTU 80 | 3 fragmentos (62 + 62 + 8) | `(62, 62)` se re-fragmenta en `R2 → R3`. |
| `R5 → R1` | `R5 → R4`, MTU 140 | 2 fragmentos (122 + 10) | `(0, 122)` se re-fragmenta en `R4 → R2` (MTU 80) en 62 + 60. `R1` reensambla 3 fragmentos. |

- Mientras más chico el MTU del primer enlace, más fragmentos y menos
  re-fragmentación después. Desde `R1` el primer enlace (MTU 100) es más grande
  que los dos que salen de `R2` hacia `R5` (50 y 80), así que el fragmento
  `(0, 82)`, de 100 bytes, siempre se re-fragmenta en `R2`.
- Un fragmento nunca vuelve a crecer. Los fragmentos de 32 bytes creados en un
  enlace de MTU 50 siguen de 32 bytes por los enlaces de MTU 80 o 140.
- En las dos pruebas desde `R4`, el round-robin eligió `R2` y no el enlace directo
  a `R5` (MTU 140), que habría creado 2 fragmentos.

**¿El código logra re-fragmentar un fragmento en fragmentos más pequeños cuando
pasa por un enlace con menor MTU?** Sí. En el paquete 1, `R2` recibe el fragmento
`(0, 82)` con `FLAG = 1`, que ocupa 100 bytes, y lo reenvía por el enlace de MTU 50:

```text
redirigiendo paquete 127.0.0.1;8885;63;1;0;82;1;[mensaje] con destino final ('127.0.0.1', 8885) desde ('127.0.0.1', 8882) hacia ('127.0.0.1', 8883) en 3 fragmento(s) (MTU 50)
```

Salen `(0, 32)`, `(32, 32)` y `(64, 18)`, los tres con `FLAG = 1`, porque después
viene `(82, 50)`. En los paquetes 2 a 6, el último fragmento `(82, 50)` con
`FLAG = 0` se divide en `(82, 32)` con `FLAG = 1` y `(114, 18)` con `FLAG = 0`. `R5`
reensambla igual, porque los offsets son absolutos.

**Fragmentos perdidos** (`results/fragmentation_ttl_5.txt`). Con TTL 5, de 3
paquetes enviados no se reensambla ninguno. A los tres les llega una parte de los
fragmentos a `R5`, y el resto se descarta al quedar con TTL 0. Basta perder un
fragmento para perder el paquete completo, y los fragmentos que sí llegaron quedan
guardados en `R5` esperando.

El orden exacto de los saltos puede cambiar entre ejecuciones. En los archivos de
resultados algunas líneas aparecen unidas, porque varios routers escriben a la vez
en la misma salida.


### Uso de IA

[completar]
