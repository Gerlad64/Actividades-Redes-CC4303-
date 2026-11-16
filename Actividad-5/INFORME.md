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

El valor por defecto mantiene las pruebas de la Parte I sin cambios. Además,
`Packet` usa `ttl=0` por defecto, por lo que sin este valor los routers
descartarían todos los paquetes.

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


### Pruebas

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

Los primeros 4 comandos de bash configura una carpeta con la actividad en un momento
donde `ttl` todavía no estaba implementado. Este momento esta marcado mediante el tag
de git `Actividad-5-Parte-I`.

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
