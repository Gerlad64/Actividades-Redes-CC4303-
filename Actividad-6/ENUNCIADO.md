## Actividad: Fragmentación (6 pts totales)



* **Entrega y repositorio:** Todas las actividades del semestre deben alojarse en un repositorio de GitHub accesible para el equipo docente, subiendo a U-Cursos únicamente el archivo PDF del informe/documentación.


* **Contexto de evaluación:** Durante las semanas 11 y 12 se deben realizar dos actividades (*Forwarding básico* y *Fragmentación*), cuyo promedio corresponderá a la nota final de la unidad de Redes IP. Para esta actividad se necesita una copia del código de *Forwarding básico* **con TTL**.


* **Material previo requerido:** Ver el video *Asignación de direcciones y fragmentación*.



### Distribución de puntaje



* **Informe:** 1.5 pts.


* **Código:** 4.5 pts, desglosados según funcionalidad:


* **(+1.0 pt)** Se manejan correctamente los cambios del *header* (`HEAD`).


* **(+1.8 pts)** Los paquetes son fragmentados correctamente (incluyendo la re-fragmentación de un fragmento si es necesario).


* **(+1.7 pts)** Los paquetes se reensamblan correctamente al llegar a su destino.





---

### Conceptos previos



* **Maximum Transmission Unit (MTU):** Cantidad máxima de información (en bytes) que se puede enviar entre dos *routers* a través del enlace que los une. Si un paquete IP supera el MTU del enlace, el *router* debe fragmentarlo en trozos más pequeños (*fragmentos IP*), cada uno con su propio *header*, cumpliendo que $\text{tamaño\_header} + \text{tamaño\_datos} \le \text{MTU}$. Como cada enlace puede tener un MTU distinto, un fragmento IP puede volver a fragmentarse en saltos posteriores.


* **Fragmentación:** Proceso de dividir un datagrama o fragmento en trozos más pequeños para que quepan por un enlace con MTU menor. Cada fragmento lleva su propio *header* con los campos necesarios para llegar a destino y reensamblar el datagrama original: *Identification Number* (`ID`), *Offset* y *More Fragment Flag* (`FLAG`).


* **Ancho de banda:** Cantidad máxima de datos que puede viajar por la red en un intervalo de tiempo (medida en bytes/s, MB/s, GB/s, etc.).


* **Throughput:** Cantidad efectiva o real de datos enviados a través de la red en un intervalo de tiempo, la cual puede ser inferior al ancho de banda.



---

### Implementación (Código: 4.5 pts)



Trabajando sobre una copia del código de *Forwarding básico* con TTL y considerando la topología de 5 *routers* con enlaces con MTU definido:

```text
    MTU=100         MTU=50

R1 <------->   R2  <------->  R3

                ^              ^

        MTU=80  |              | MTU=55

                v              v

               R4 <---------> R5

                     MTU=140

```



Implemente los siguientes 7 pasos:

1. **Actualizar estructura del *header* (`parse_packet` y `create_packet`):** Modifique ambas funciones para soportar los campos `Dirección IP`, `Puerto`, `TTL`, `ID`, `Offset`, `Tamaño` y `FLAG`:


* **`Tamaño`:** Tamaño del `[mensaje]` en bytes *sin considerar el header*, almacenado en **4 bytes**.


* **`FLAG`:** Toma valor `1` si quedan más fragmentos después del actual y `0` si es el último fragmento del datagrama original. Siempre contiene 1 dígito y su representación en bytes (carácter, entero o bit) queda a elección.


* **`ID`:** Campo numérico para identificar todos los fragmentos pertenecientes a un mismo paquete IP (tamaño en bytes a elección).


* **`Offset`:** Indica el inicio de la secuencia de bytes del fragmento respecto al datagrama IP original (tamaño en bytes a elección). Por simplicidad, se calcula directamente en **bytes** y no en octetos.


* *Test:* Verificar que `create_packet(parse_packet(IP_packet_v1)) == IP_packet_v1` utilizando la nueva estructura de *headers*.




2. **Actualizar `check_routes` para leer el MTU:** Modifique la función para extraer el MTU de cada línea de la tabla de rutas y retornarlo junto con la dirección del siguiente salto (por ejemplo, `return next_hop_address, MTU`), adaptando el resto del código para recibir esta tupla sin errores.


* Formato de cada entrada en las tablas de rutas:





```text
+---------------------------------------------+--------------------------------------+-------+
|             Network destination             |               Gateway                |  MTU  |
+---------------------------------------------+--------------------------------------+-------+
|[Red (CIDR)] [Puerto_Inicial] [Puerto_final]  [IP_Para_llegar] [Puerto_para_llegar]  [MTU]  |
+---------------------------------------------+--------------------------------------+-------+

```



* *Test:* Ejecutar la topología de 5 *routers* con las tablas con MTU y comprobar que el envío de paquetes entre dos *routers* no falla.



3. **Crear `fragment_IP_packet(IP_packet, MTU)`:** Debe recibir un paquete IP completo (en bytes, con *headers* incluidos) y el `MTU` del enlace, retornando siempre una lista de uno o más fragmentos:


* Si $\text{tamaño\_completo}(IP\_packet) \le \text{MTU}$, el paquete no requiere fragmentación y se retorna `[IP_packet]`.


* Si $\text{tamaño\_completo}(IP\_packet) > \text{MTU}$, se divide en fragmentos de tamaño total menor o igual al `MTU`, recalculando `Offset`, `Tamaño` y `FLAG` para cada uno, cumpliendo que $\text{len}(\text{trozo\_mensaje\_en\_bytes}) = \text{MTU} - \text{tamaño\_header\_en\_bytes}$ (excepto posiblemente el último fragmento).


* *Test:* Comprobar que retorna una lista de largo 1 cuando el paquete cabe en el MTU y una lista con la cantidad esperada de fragmentos cuando lo supera.




4. **Integrar fragmentación en el *forwarding*:** En la sección del *router* que reenvía paquetes que no son para él, llame primero a `fragment_IP_packet(IP_packet, MTU)` usando el MTU entregado por `check_routes` y luego envíe cada fragmento retornado hacia `next_hop_address`.


5. **Crear `reassemble_IP_packet(fragment_list)`:** Debe reconstruir el paquete IP original a partir de una lista de fragmentos (que puede llegar desordenada, por lo que debe ordenarse según `Offset`):


* Si `len(fragment_list) == 1`, debe distinguir entre un paquete completo sin fragmentar (`Offset == 0` y `FLAG == 0`) y una lista incompleta de un solo fragmento.


* Si la lista de fragmentos aún está incompleta (faltan fragmentos intermedios o el fragmento final con `FLAG == 0`), debe retornar `None`.


* *Test:* Comprobar que `reassemble_IP_packet(fragment_IP_packet(IP_packet_v1, MTU)) == IP_packet_v1`.




6. **Almacenar fragmentos recibidos por ID:** Cuando un paquete o fragmento tiene como destino el *router* actual (no se *forwardea*), guárdelo en un diccionario cuya llave sea el `ID` del paquete y cuyo valor sea la lista de fragmentos acumulados para ese `ID`.


7. **Intentar reensamblaje en cada recepción:** Cada vez que el *router* reciba un fragmento destinado a él y lo agregue al diccionario, debe invocar `reassemble_IP_packet` sobre la lista de ese `ID`. Si retorna `None`, continúa esperando; si retorna el paquete reconstruido, imprime el mensaje sin *headers*.


* *Test:* Generar listas de fragmentos para dos paquetes con distinto `ID` y enviarlos manualmente en orden, en desorden e intercalando `ID`, verificando que ambos mensajes se reensamblan correctamente.





---

### Pruebas para el informe (Informe: 1.5 pts)



Utilizando la configuración de 5 *routers* con MTU:

1. **Verificación de TTL, *round-robin* y paquetes sin fragmentar:** Envíe desde `R1` hacia `R5` (usando el script de envío de *forwarding básico*) un paquete pequeño que no requiera fragmentación con los campos: `IP = 127.0.0.1`, `Puerto = 8885`, `TTL = 10`, `ID = 347`, `Offset = 0`, `Tamaño = 5`, `FLAG = 0`, `mensaje = "hola!"`, verificando que el TTL y el balanceo *round-robin* siguen operando correctamente.


2. **Pruebas de fragmentación y re-fragmentación:** Envíe varias veces un paquete IP de **150 bytes totales** desde `R1` hacia `R5` y verifique que la fragmentación y el reensamblaje sean exitosos. Responda brevemente en el informe:


* ¿Cómo cambia el comportamiento si se envían desde otros *routers*?


* ¿El código logra re-fragmentar un fragmento en fragmentos más pequeños cuando pasa por un enlace con menor MTU?





---

### Tablas de rutas con MTU (Topología de 5 *routers*)



```text
    MTU=100         MTU=50

R1 <------->   R2  <------->  R3

                ^              ^

        MTU=80  |              | MTU=55

                v              v

               R4 <---------> R5

                     MTU=140

```



```text
# archivo rutas_R1_v3_mtu.txt
127.0.0.1/24 8882 8885 127.0.0.1 8882 100

```



```text
# archivo rutas_R2_v3_mtu.txt
127.0.0.1/24 8881 8881 127.0.0.1 8881 100
127.0.0.1/24 8883 8885 127.0.0.1 8883 50
127.0.0.1/24 8883 8885 127.0.0.1 8884 80

```



```text
# archivo rutas_R3_v3_mtu.txt
127.0.0.1/24 8881 8882 127.0.0.1 8882 50
127.0.0.1/24 8881 8882 127.0.0.1 8885 55
127.0.0.1/24 8884 8885 127.0.0.1 8882 50
127.0.0.1/24 8884 8885 127.0.0.1 8885 55

```



```text
# archivo rutas_R4_v3_mtu.txt
127.0.0.1/24 8881 8883 127.0.0.1 8882 80
127.0.0.1/24 8881 8883 127.0.0.1 8885 140
127.0.0.1/24 8885 8885 127.0.0.1 8882 80
127.0.0.1/24 8885 8885 127.0.0.1 8885 140

```



```text
# archivo rutas_R5_v3_mtu.txt
127.0.0.1 8881 8884 127.0.0.1 8884 140
127.0.0.1 8881 8884 127.0.0.1 8883 55

```