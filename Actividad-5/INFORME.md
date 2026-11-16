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
| `bad_routers.txt`, `hops_5_routers.txt`, `hops_7_routers.txt` | Salidas de las pruebas sin TTL. |
| `bad_routers_ttl.txt`, `order_5_routers.txt` | Salidas de las pruebas con TTL. |

Un router se levanta con:

```bash
python3 router.py <router_IP> <router_puerto> <archivo_rutas>
```

#### Tabla de rutas: similitudes y diferencias con una tabla real

**Similitudes:**
- Cada línea asocia una red de destino con un siguiente salto (*gateway*), igual
  que las columnas `Destination` y `Gateway` de una tabla real.
- El router solo conoce el siguiente salto, no el camino completo hasta el destino.
- La red de destino se escribe en notación CIDR (`127.0.0.1/24`).
- Si ningún destino calza, el paquete se descarta. Igual que en una tabla real,
  se puede agregar una ruta default (`0.0.0.0/0`) para no descartarlo (paso 9).

**Diferencias:**
- **Rangos de puertos en vez de rangos de IP.** Todos los routers comparten la IP
  `127.0.0.1`, así que los hosts de una red se agrupan por rango de puertos. En
  una red real el puerto es de la capa de transporte y el router no lo mira.
- **Elección de la ruta.** Aquí se usa la primera línea que calza, en orden. Un
  router real usa la ruta con el prefijo más largo (*longest prefix match*), sin
  importar el orden de las líneas.
- **Columnas.** Una tabla real también indica la interfaz de salida, una métrica
  y flags. Aquí solo hay destino y siguiente salto.
- **Origen de las rutas.** Aquí la tabla es un archivo estático escrito a mano.
  Una tabla real también se llena con protocolos de ruteo (RIP, OSPF, BGP) y se
  actualiza si cae un enlace. Por eso, un error como el de la prueba 1 de las
  pruebas sin TTL queda fijo hasta que alguien edite el archivo.
- **Redes conectadas directamente.** Una tabla real incluye automáticamente las
  redes de sus interfaces. Aquí cada vecino necesita su propia línea.
- **Varios caminos.** Aquí se alterna por paquete con round-robin (paso 8). Un
  router real que reparte carga entre caminos suele mantener los paquetes de un
  mismo flujo por el mismo camino para no desordenarlos.

#### Script emisor de mensajes

El script emisor está en `packet/send.py`. Construye un paquete IP con la
dirección del router de destino final y lo envía a un router de entrada,
que no necesariamente es el mismo destino.

La función principal es `send`:

```python
def send(dst_ip: str, dst_port: int, msg: str, via_ip: str, via_port: int) -> None:
```

| Argumento  | Descripción |
| :--- | :--- |
| `dst_ip`   | IP del router de destino final. Se escribe en los 4 bytes de IP del header. |
| `dst_port` | Puerto del router de destino final. Se escribe en los 2 bytes de puerto del header. |
| `msg`      | Mensaje en `string`. Se codifica en bytes y va después del header. |
| `via_ip`   | IP del router al que se envía el paquete (IP de envío). |
| `via_port` | Puerto del router al que se envía el paquete (puerto de envío). |

Se separan `(dst_ip, dst_port)` de `(via_ip, via_port)` porque el header indica
a dónde debe *llegar* el paquete, mientras que el socket lo entrega al primer
router del camino. Así se puede inyectar un paquete en cualquier punto de la red
y observar cómo se *forwardea* hasta su destino.

`send` crea un `Packet` (de `packet/packet.py`) con la dirección de destino final
y el mensaje, abre un socket UDP y lo envía con `Packet.sendto` hacia
`(via_ip, via_port)`:

```python
Packet(int.from_bytes(socket.inet_aton(dst_ip)), dst_port, msg.encode()).sendto(sock, via_ip, via_port)
```

**Forma de entregar la información al script:** el script recibe los datos como
argumentos de línea de comandos (`sys.argv`), en el mismo orden que los
parámetros de `send`. Se ejecuta como módulo desde `Actividad-5/`, porque importa
`Packet` desde el paquete `packet`:

```bash
python3 -m packet.send <ip_destino> <puerto_destino> <mensaje> <ip_envio> <puerto_envio>
```

Por ejemplo, para enviar `hola R2!` a `R2 (127.0.0.1, 8882)` entrando a la red por
`R1 (127.0.0.1, 8881)`, como en el ejemplo 1:

```bash
python3 -m packet.send 127.0.0.1 8882 "hola R2!" 127.0.0.1 8881
```

Si el mensaje tiene espacios, se escribe entre comillas para que la terminal lo
entregue como un solo argumento. Además, `send` se puede importar desde otro
código (`from packet.send import send`), como hace `test_network.py` para enviar
paquetes a los routers creados con `fork`.

**Parámetro `ttl` (Parte II):** en la Parte II se agregó a `send` el parámetro
`ttl`, que se escribe en el byte de TTL del header. Si no se entrega, vale 64,
el valor usado en *nix:

```python
def send(dst_ip: str, dst_port: int, msg: str, via_ip: str, via_port: int, ttl: int = 64) -> None:
```

Por línea de comandos va como sexto argumento opcional:

```bash
python3 -m packet.send 127.0.0.1 8883 hola 127.0.0.1 8881 1
```

El valor por defecto mantiene las pruebas de la Parte I sin cambios, porque no
necesitan indicar un TTL.

#### Script de pruebas por archivo (Parte II, paso 4)

`prueba_router.py` lee un archivo línea por línea desde la entrada estándar
(`stdin`) y envía cada línea como un paquete IP. Todos los paquetes llevan el
mismo destino y TTL, y se envían al mismo router inicial:

```bash
python3 prueba_router.py <ip_destino> <puerto_destino> <ttl> <ip_router_inicial> <puerto_router_inicial> < archivo
```

Por ejemplo, para enviar `mensajes.txt` de `R1` a `R5` con TTL 10:

```bash
python3 prueba_router.py 127.0.0.1 8885 10 127.0.0.1 8881 < mensajes.txt
```

El enunciado no indica cómo se entrega el archivo, así que se lee con `stdin`
y una redirección `<`. Así se mantiene la firma del enunciado, sin un argumento
extra para el nombre del archivo. El enunciado escribe el header como un solo
argumento `127.0.0.1;8885;10`. Aquí van como tres argumentos separados por
espacios, igual que en `send.py`. Sin comillas, bash interpreta `;` como
separador de comandos, y el argumento original no llegaría completo al script.

A diferencia de `send`, que espera 0,3 s después de cada envío,
`prueba_router.py` envía todas las líneas seguidas por un solo socket. Si
esperara, cada paquete llegaría antes de que saliera el siguiente y no se
podría observar el orden de llegada (prueba 2 con TTL).

#### Round-robin

El round-robin está en `RouterTable` (`router_table.py`). Cada entrada de la tabla
define un *área de la red* (`NetworkArea`, ver
[Clases y estructuras](#clases-y-estructuras)). Si dos o más entradas tienen la
misma área, son caminos alternativos hacia ese mismo conjunto de routers.

Al leer la tabla, las entradas se agrupan por área y cada grupo queda en una lista
circular (`itertools.cycle`):

```python
areas: dict[NetworkArea, list[RouterEntry]] = {}
for r_entry in self.TABLE:
    areas.setdefault(r_entry.AREA, []).append(r_entry)
self.ROUND_ROBIN = {area: cycle(entries) for area, entries in areas.items()}
```

`check` sigue recorriendo la tabla en orden. Cuando encuentra la primera entrada
que contiene el destino, retorna el siguiente salto de la lista circular de su área:

```python
return next(self.ROUND_ROBIN[r_entry.AREA]).FWD_ADDR
```

Se eligió esta forma por tres razones:
- **Rutas por área:** como cada área tiene su propio `cycle`, recuerda por separado
  la última ruta usada. En `R2`, los paquetes hacia `R1` y hacia `R5` alternan cada
  uno entre sus caminos sin afectar al otro.
- **Número de rutas:** `cycle` sirve para cualquier cantidad de rutas por área, y
  un área con una sola ruta siempre retorna la misma.
- **Archivos de rutas:** no cambia su formato, porque basta con repetir el rango
  de destino con otro salto.

Las tablas del Test 2 del paso 8 (`routes/rutas_R{0..6}_v4.txt`) agregan `R0`
(puerto 8880), conectado a `R1` y `R2`, y `R6` (puerto 8886), conectado a `R2` y
`R3`. En esa red, `R2` tiene 2 caminos hacia el área `8880-8881` (vía `R1` y `R0`)
y 3 caminos hacia el área `8883-8886` (vía `R3`, `R4` y `R6`).

En las pruebas se observa que, sin TTL, un paquete puede rebotar entre routers
antes de llegar (por ejemplo `R2 -> R3 -> R2 -> R4 -> R2 -> R3 -> R5`). Round-robin
no evita los ciclos: un paquete solo llega porque la alternancia termina sacándolo
del ciclo.

#### Router default

El router default está en `(127.0.0.1, 7000)` y está conectado a los 5 routers de
la red del paso 8. Se agregó cambiando solo las tablas de rutas
(`routes/rutas_R{1..5}_v5.txt` y `routes/rutas_default_v5.txt`), sin código nuevo.

Cada tabla `rutas_Rn_v5.txt` es la tabla `rutas_Rn_v3.txt` con una línea más al
final, la ruta default:

```text
0.0.0.0/0 0 65535 127.0.0.1 7000
```

La red `0.0.0.0/0` contiene todas las IP y el rango `0-65535` todos los puertos,
así que esta ruta calza con cualquier destino. Por ejemplo, la tabla de `R2` queda:

```text
# archivo rutas_R2_v5.txt
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8883 8885 127.0.0.1 8883
127.0.0.1/24 8883 8885 127.0.0.1 8884
0.0.0.0/0 0 65535 127.0.0.1 7000
```

El router default tiene una ruta directa hacia cada router de la red, y ninguna ruta
default propia: un paquete que llega a él sin ser para él no tiene a dónde ir y se
descarta.

```text
# archivo rutas_default_v5.txt
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8882 8882 127.0.0.1 8882
127.0.0.1/24 8883 8883 127.0.0.1 8883
127.0.0.1/24 8884 8884 127.0.0.1 8884
127.0.0.1/24 8885 8885 127.0.0.1 8885
```

**¿En qué posición de la tabla debería ir la ruta default?** En la última línea.
`RouterTable.check` recorre la tabla en orden y usa la primera entrada que contiene
el destino. Como la ruta default contiene cualquier destino, si estuviera antes que
otra ruta, esa ruta nunca se usaría y todo el tráfico se iría al router default.
Al final, solo se usa cuando ninguna otra ruta calza.

En la prueba, un paquete hacia `(127.0.0.1, 9000)` entra por `R1` y otro hacia
`(10.0.0.1, 8881)` entra por `R5`. Ambos se envían directo al router default, que
no tiene ruta para ellos. Un paquete de `R1` a `R5` sigue usando las rutas de la
red, sin pasar por el default.


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

El header ocupa 7 bytes: 4 de IP, 2 de puerto y 1 de TTL. Hereda de
`ctypes.BigEndianStructure` para que los campos se escriban en orden de red
(*big endian*), y `_pack_ = 1` evita que `ctypes` agregue bytes de relleno entre
campos.

| Atributo | Tipo | Por qué |
| :--- | :--- | :--- |
| `IP` | `c_uint32` | Una IPv4 `a.b.c.d` son 4 bytes. Guardada como entero de 32 bits big endian, el 1er byte es `a` y el 4to es `d`, como pide el enunciado. `socket.inet_aton`/`inet_ntoa` hacen la conversión con el string. |
| `PORT` | `c_uint16` | Los puertos van de 0 a 65535, justo lo que cabe en 2 bytes sin signo. |
| `TTL` | `c_uint8` | El enunciado pide un entero entre 1 y 255 en 1 byte. Un byte sin signo cubre ese rango y también el 0 con que se descarta el paquete. |
| `msg` | `bytes` | El mensaje tiene largo variable, así que no puede ir en `_fields_`. Se guarda como `bytes` porque es lo que entrega y recibe el socket. |

`from_bytes` lee los 7 bytes del header y deja el resto en `msg`. `to_bytes`
concatena el header (`bytes(memoryview(self))`) con `msg`. `ADDR` entrega el
destino como `(ip, puerto)`, el mismo formato que usan los sockets y la tabla de
rutas.

#### `RouterEntry`, `NetworkArea` y `RouterTable` (`router_table.py`)

`RouterEntry` es una línea de la tabla de rutas:

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

`RouterEntry` es un `dataclass` porque solo guarda datos y así se evita escribir
el `__init__`. `__contains__` permite escribir `dst_addr in r_entry`.

`NetworkArea` agrupa los tres campos de destino (`DST_IP`, `DST_IP_RANGE`,
`DST_PORT_RANGE`). Se construye en la propiedad `RouterEntry.AREA` y hereda de
`NamedTuple` por dos razones:
- **Legibilidad:** el tipo se lee como `NetworkArea` y no como
  `tuple[str, int, tuple[int, int]]`, y sus campos se acceden por nombre.
- **Llave de diccionario:** sigue siendo una tupla inmutable y hasheable, así que
  dos áreas con los mismos valores son la misma llave.

`RouterTable` tiene dos atributos:

| Atributo | Tipo | Por qué |
| :--- | :--- | :--- |
| `TABLE` | `list[RouterEntry]` | Una lista mantiene el orden del archivo, y las rutas se revisan en orden descendente. |
| `ROUND_ROBIN` | `dict[NetworkArea, Iterator[RouterEntry]]` | Un `cycle` por área guarda por separado en qué ruta quedó cada área. |


### Flujo

Cada router (`network` en `router.py`) abre un socket UDP en
`(router_IP, router_puerto)`, carga su tabla de rutas y queda en un loop
bloqueante con `recvfrom`. Por cada paquete recibido:

1. Lo convierte con `Packet.from_bytes`.
2. Si `TTL == 0`, lo descarta e imprime `Se recibió paquete ... con TTL 0`.
3. Si el destino del header es el propio router, imprime el mensaje sin headers.
4. Si no, busca el siguiente salto con `RouterTable.check`. Si hay ruta, resta 1
   al TTL y reenvía el paquete por el mismo socket. Si no hay ruta, imprime
   `No hay rutas hacia ...` y lo descarta.

```python
if packet.TTL == 0:
    print(f"Se recibió paquete {packet_str} con TTL 0")
elif packet.ADDR == router_addr:
    print("paquete recibido:" + packet.msg.decode())
elif (next_hop := table.check(packet.ADDR)) is not None:
    packet.TTL -= 1
    packet.sendto(sock, *next_hop)
```

El TTL se revisa antes que el destino. Por eso un paquete también se descarta si
llega a su destino con TTL 0, y para recorrer *n* saltos necesita un TTL de al
menos *n*+1.

`recvfrom(SOCK_BUFFER_SIZE)` recibe hasta 1024 bytes (`config.py`): 7 de header
y hasta 1017 de mensaje. Un mensaje más largo se corta.

El loop termina con `Ctrl+C` (`KeyboardInterrupt`), que cierra el socket.


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
- `SOCK_BUFFER_SIZE = 1024`: bytes máximos que recibe un router por paquete.

Cada línea de una tabla de rutas tiene el formato:

```text
<red>/<prefijo> <puerto_inicial> <puerto_final> <ip_siguiente_salto> <puerto_siguiente_salto>
```

Todos los comandos se ejecutan desde `Actividad-5/`. Por ejemplo, para el ejemplo
1, en dos terminales:

```bash
python3 router.py 127.0.0.1 8881 rutas_R1_v1.txt
python3 router.py 127.0.0.1 8882 rutas_R2_v1.txt
```

En una tercera terminal, para enviar un mensaje:

```bash
python3 -m packet.send 127.0.0.1 8882 "hola R2!" 127.0.0.1 8881
```

O, para enviar un archivo línea por línea:

```bash
python3 prueba_router.py 127.0.0.1 8882 10 127.0.0.1 8881 < mensajes.txt
```

Para correr todas las pruebas:

```bash
python3 test_network.py
```

Desde la raíz del repositorio, el código pasa:

```bash
ty check Actividad-5/
ruff check Actividad-5/
```


### Pruebas

#### Pruebas de los pasos

Cada función de `test_network.py` levanta los routers con `fork`, envía paquetes
con `send` y detiene los routers con `SIGINT`:

| Función | Paso | Qué verifica |
| :--- | :--- | :--- |
| `example_1` | Parte I, paso 7 | Ejemplo 1 (R1 ↔ R2): *forwarding*, entrega local y destino sin ruta. |
| `example_2` | Parte I, paso 7 | Ejemplo 2 (R1 ↔ R2 ↔ R3): lo mismo, con un salto intermedio. |
| `round_robin_1` | Parte I, paso 8, Test 1 | R2 cicla entre R3 y R4 para paquetes de R1 a R5. |
| `round_robin_2` | Parte I, paso 8, Test 2 | Con R0 y R6, R2 cicla por separado en cada área (R1 → R5 y R5 → R1 intercalados). |
| `default_router` | Parte I, paso 9 | Destinos fuera de la red terminan en el router default. |
| `ttl_drop` | Parte II, pasos 2 y 3 | En el ejemplo 2, de R1 a R3: con TTL 1 lo descarta R2, con TTL 2 lo descarta R3 y con TTL 3 llega. |
| `bad_routes`, `hops_5_routers`, `hops_7_routers` | Pruebas sin TTL | Ver [Pruebas Mini-Internet sin TTL](#pruebas-mini-internet-sin-ttl). |
| `bad_routes_ttl`, `file_order` | Pruebas con TTL | Ver [Pruebas Mini-Internet con TTL](#pruebas-mini-internet-con-ttl). |

Para correr una sola:

```bash
python3 -c "import test_network as t; t.ttl_drop()"
```

#### Pruebas Mini-Internet sin TTL

Estas pruebas se ejecutaron sobre el código del tag `Actividad-5-Parte-I`, que no
tiene TTL. Con el código actual (TTL 64 por defecto) la prueba 1 cambia: el ciclo
se corta a los 64 saltos. Las pruebas 2 y 3 no cambian, porque ningún paquete da
más de 10 saltos.

Las funciones están en `test_network.py` (`bad_routes`, `hops_5_routers` y
`hops_7_routers`). Para reproducirlas sin TTL, **desde la raíz del repositorio**:

```bash
mkdir /tmp/parte1 && git archive Actividad-5-Parte-I Actividad-5 | tar -x -C /tmp/parte1
cp Actividad-5/test_network.py /tmp/parte1/Actividad-5/
cp Actividad-5/routes/rutas_R2_v2_error.txt /tmp/parte1/Actividad-5/routes/
cd /tmp/parte1/Actividad-5
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.bad_routes()"
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.hops_5_routers()"
PYTHONUNBUFFERED=1 python3 -c "import test_network as t; t.hops_7_routers()"
```

Los primeros 4 comandos arman una carpeta con la actividad en el momento en que
el TTL todavía no estaba implementado. Ese momento está marcado con el tag de git
`Actividad-5-Parte-I`.

`PYTHONUNBUFFERED=1` hace que cada router imprima apenas recibe un paquete, así
las líneas salen en el orden real de los saltos.

En las tablas siguientes, un salto es un envío entre dos routers.

**1. Tabla de rutas de `R2` mal configurada.** En la red del ejemplo 2, `R2` usa
`routes/rutas_R2_v2_error.txt`:

```text
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8883 8883 127.0.0.1 8881
```

- Un paquete de `R3` a `R1` llega normal (`R3 -> R2 -> R1`), porque la primera
  línea sigue correcta.
- Un paquete de `R1` a `R3` nunca llega. `R1` lo envía a `R2`, y `R2` lo
  devuelve a `R1` por la segunda línea. El paquete rebota entre `R1` y `R2`
  hasta que se detienen los routers.

Sin TTL, un error en una sola tabla basta para que un paquete quede circulando
para siempre y cargue la red.

El resultado de este experimento se encuentra en `bad_routers.txt`.

**2. Red de 5 routers (`rutas_R{1..5}_v3.txt`), 6 paquetes de `R1` a `R5`.**

| Paquete | Saltos | Camino |
| :--- | :---: | :--- |
| #0, #2, #4 | 7 | R1 → R2 → R3 → R2 → R4 → R2 → R3 → R5 |
| #1, #3, #5 | 3 | R1 → R2 → R4 → R5 |

- **¿Cuántos saltos dan?** 7 o 3. Los 6 paquetes llegan a `R5`.
- **¿Siempre la misma cantidad?** No, se alternan 7 y 3. `R3` y `R4` alternan
  entre `R2` y `R5` para llegar a `R5`, así que la mitad de las veces devuelven
  el paquete a `R2`. El patrón se repite porque el estado de round-robin de cada
  router lo comparten todos los paquetes que pasan por él.
- **¿Comparado con el mínimo?** El mínimo es 3 saltos (`R1 → R2 → R3 → R5` o
  `R1 → R2 → R4 → R5`). La mitad de los paquetes usa el camino mínimo y la otra
  mitad da más del doble de saltos.

El resultado de este experimento se encuentra en `hops_5_routers.txt`.

**3. Red de 7 routers del Test 2 del paso 8 (`rutas_R{0..6}_v4.txt`), 6 paquetes
de `R1` a `R5`.**

| Paquete | Saltos | Camino |
| :--- | :---: | :--- |
| #0 | 8 | R1 → R2 → R3 → R2 → R4 → R2 → R6 → R3 → R5 |
| #1 | 5 | R1 → R2 → R3 → R2 → R4 → R5 |
| #2 | 5 | R1 → R2 → R6 → R2 → R3 → R5 |
| #3 | 8 | R1 → R2 → R4 → R2 → R6 → R3 → R2 → R3 → R5 |
| #4 | 3 | R1 → R2 → R4 → R5 |
| #5 | 10 | R1 → R2 → R6 → R2 → R3 → R2 → R4 → R2 → R6 → R3 → R5 |

Los 6 paquetes llegan, pero la cantidad de saltos varía más que en la red de 5
routers (de 3 a 10) y no se ve un patrón corto. Ahora `R2` alterna entre 3
caminos hacia `R5` (`R3`, `R4` y `R6`), y `R3`, `R4` y `R6` también pueden
devolver el paquete a `R2`. El mínimo sigue siendo 3 saltos, porque `R6` no
acorta el camino (`R1 → R2 → R6 → R3 → R5` son 4). Solo 1 de los 6 paquetes lo
logra. Agregar routers y caminos alternativos sin TTL aumenta los saltos
innecesarios.

El resultado de este experimento se encuentra en `hops_7_routers.txt`.

Archivos de rutas creados para esta red:

```text
# archivo rutas_R0_v4.txt
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8882 8886 127.0.0.1 8882
```

```text
# archivo rutas_R1_v4.txt
127.0.0.1/24 8880 8880 127.0.0.1 8880
127.0.0.1/24 8882 8886 127.0.0.1 8882
```

```text
# archivo rutas_R2_v4.txt
127.0.0.1/24 8880 8881 127.0.0.1 8881
127.0.0.1/24 8880 8881 127.0.0.1 8880
127.0.0.1/24 8883 8886 127.0.0.1 8883
127.0.0.1/24 8883 8886 127.0.0.1 8884
127.0.0.1/24 8883 8886 127.0.0.1 8886
```

```text
# archivo rutas_R3_v4.txt
127.0.0.1/24 8880 8882 127.0.0.1 8882
127.0.0.1/24 8880 8882 127.0.0.1 8886
127.0.0.1/24 8884 8885 127.0.0.1 8882
127.0.0.1/24 8884 8885 127.0.0.1 8885
127.0.0.1/24 8886 8886 127.0.0.1 8886
```

```text
# archivo rutas_R4_v4.txt
127.0.0.1/24 8880 8883 127.0.0.1 8882
127.0.0.1/24 8880 8883 127.0.0.1 8885
127.0.0.1/24 8885 8886 127.0.0.1 8882
127.0.0.1/24 8885 8886 127.0.0.1 8885
```

```text
# archivo rutas_R5_v4.txt
127.0.0.1/24 8880 8884 127.0.0.1 8884
127.0.0.1/24 8880 8884 127.0.0.1 8883
127.0.0.1/24 8886 8886 127.0.0.1 8883
```

```text
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

**1. Tabla de rutas de `R2` mal configurada, con TTL 10.** Es la misma prueba 1
sin TTL (`rutas_R2_v2_error.txt`), pero los paquetes salen con TTL 10.

- El paquete de `R3` a `R1` llega igual que antes (`R3 → R2 → R1`).
- El paquete de `R1` a `R3` sigue sin llegar y rebota entre `R1` y `R2`, pero
  ahora cada router le resta 1 al TTL. Después de 10 saltos llega a `R1` con
  TTL 0 y `R1` lo descarta:
  `Se recibió paquete 127.0.0.1;8883;0;hola R3! con TTL 0`.

La diferencia es que, sin TTL, el paquete circulaba hasta que se detenían los
routers. Con TTL el ciclo dura como máximo 10 saltos. El error de la tabla
sigue ahí, pero el paquete perdido ya no carga la red para siempre.

El resultado de este experimento se encuentra en `bad_routers_ttl.txt`.

**2. Orden de los paquetes en la red de 5 routers.** Con las tablas
`rutas_R{1..5}_v3.txt`, `prueba_router.py` envía las 30 líneas de `mensajes.txt`
de `R1` a `R5` con TTL 10. `R5` recibió 28, en este orden:

```text
03 07 11 04 15 08 12 19 16 20 01 23 26 27 29 02 13 06 21 14 24 25 30 09 18 22 17 10
```

- **Los paquetes llegan desordenados.** Como se envían seguidos, varios están
  en la red al mismo tiempo. Round-robin los manda por caminos de distinto
  largo: los que llegaron dieron 3, 5, 7 o 9 saltos. Un paquete que sale
  después, pero toma un camino más corto, llega antes. Por ejemplo, el mensaje
  01 dio 5 saltos y llegó en el lugar 11.
- **Se pierden paquetes.** Los mensajes 05 y 28 rebotaron entre `R2`, `R3` y
  `R4` hasta agotar el TTL y se descartaron sin llegar a `R5`.
- La capa de red no garantiza orden ni entrega. Reordenar y recuperar paquetes
  le corresponde a una capa superior, como TCP.

Como los paquetes se cruzan en los routers, el orden exacto puede cambiar entre
ejecuciones.

El resultado de este experimento se encuentra en `order_5_routers.txt`. Algunas
líneas aparecen unidas, porque varios routers escriben al mismo tiempo en la
misma salida.


### Uso de IA

[completar]
