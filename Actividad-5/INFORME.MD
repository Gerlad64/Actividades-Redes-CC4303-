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


### Similitudes y Diferencias con Tablas de Rutas Reales

En esta versión se utilizan rangos de puertos en lugar de rangos de IP para simular
routers, ya que todo se trabaja de manera local y no existen interfaces de red