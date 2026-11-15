## Informe Actividad 5
**Gerald Ponce Díaz**

**github**: https://github.com/Gerlad64/Actividades-Redes-CC4303-


### Documentación y Diseño

#### Script Emisor de Mensajes

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

#### Round-Robin

El round-robin está en `RouterTable` (`router_table.py`). Cada entrada de la tabla
define un *área de la red*, que se representa con la clase `NetworkArea`:

```python
class NetworkArea(NamedTuple):
    DST_IP: str
    DST_IP_RANGE: int
    DST_PORT_RANGE: tuple[int, int]
```

Sus atributos tienen los mismos nombres que en `RouterEntry`, que la construye
en la propiedad `RouterEntry.AREA`. Si dos o más entradas tienen la misma área,
son caminos alternativos hacia ese mismo conjunto de routers.

`NetworkArea` hereda de `NamedTuple` por dos razones:
- **Legibilidad:** el tipo se lee como `NetworkArea` y no como
  `tuple[str, int, tuple[int, int]]`, y sus campos se acceden por nombre.
- **Llave de diccionario:** sigue siendo una tupla inmutable y hasheable, así que
  dos áreas con los mismos valores son la misma llave.

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

#### Router Default

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


### Similitudes y Diferencias con Tablas de Rutas Reales

En esta versión se utilizan rangos de puertos en lugar de rangos de IP para simular
routers, ya que todo se trabaja de manera local y no existen interfaces de red