## Actividad: Forwarding básico (6 pts totales)

Durante las semanas 11 y 12 usted deberá realizar 2 actividades: **(1) Forwarding básico** y **(2) Fragmentación**. Para realizar la actividad de fragmentación necesitará una copia de su actividad de Forwarding Básico **CON TTL**.

En esta actividad vamos a simular nuestro propio mini-Internet usando sockets. Vea primero los videos de *Capa de red* y *Direcciones IP*.

Note que, si bien esta actividad tiene 2 partes, se espera que entregue un único informe y que solo entregue el código final resultante de esta actividad. **El puntaje se reparte como: 2 pts Informe + 4 pts código**.

**Desglose de puntaje por funcionalidad del código** (si su código pasa las pruebas debería cumplir con estos puntos):

* **(+1.2)** Forwarding correcto [Parte I].


* **(+0.3)** Los routers imprimen el mensaje solo si está dirigido hacia ellos (no hay problema con imprimir mensajes de debug) [Parte I].


* **(+1.0)** Round-robin se implementa correctamente [Parte I].


* **(+0.5)** El código maneja correctamente el nuevo header TTL [Parte II].


* **(+0.5)** El TTL se actualiza correctamente [Parte II].


* **(+0.5)** Los paquetes se descartan según su TTL cuando corresponde [Parte II].



---

### Antes de comenzar



* **Capa de red:** Para simular un mini-Internet necesitaremos simular el comportamiento de la *capa de red*. Esto significa que, a diferencia de capas superiores, aquí ya no asumimos que los datos simplemente llegan de un punto A a un punto B de forma directa, sino que estos pasan por routers intermedios.


* **Routers:** Los routers son equipos físicos que se encargan de redirigir datos entre las distintas redes que conforman el Internet.


* **Estructura de nuestro mini-Internet:** Antes de comenzar vea la guía entregada en la sección anterior *Simulando un mini-Internet*, la cual indica cómo vamos a simular *routers*, *tablas de rutas* y *paquetes IP*.


* **Round-robin:** *Round-robin* es un algoritmo de scheduling de procesos donde se ordenan los procesos en una **lista circular** y se van ejecutando en orden (equivale a ordenarlos en una lista común, ejecutarlos en orden y, luego del último elemento, volver a comenzar desde el inicio). En el contexto de esta actividad usaremos *round-robin* para visitar elementos de un conjunto siguiendo este algoritmo.


* **Time-To-Live (`TTL`):** El *Time-To-Live* o tiempo de vida se refiere a la cantidad de *saltos* o *hops* que puede dar un paquete IP antes de ser descartado por la red, disminuyendo en 1 cada vez que el paquete pasa por un router. Si un router recibe un paquete con `TTL = 0`, lo descarta y no lo vuelve a *forwardear*, evitando así que paquetes perdidos queden dando vueltas para siempre causando congestión. Este campo no tiene un valor estándar y varía según el sistema operativo:


* **`*nix` (Linux/Unix):** 64


* **Windows:** 128


* **Solaris/AIX:** 254





---

### Actividad



Usando como guía la estructura de mini-Internet de la sección *Simulando un mini-Internet*, en esta actividad vamos a simular nuestro propio mini-Internet usando sockets UDP o no orientados a conexión. **Comenzaremos creando nuestro mini-Internet sin considerar TTL y luego consideraremos que sí hay TTL**.

#### Parte I: Mini-Internet sin TTL (Código 2.5 pts)



Cree el código necesario para manejar sus routers usando la sección *Simulando un mini-Internet* como guía, siguiendo estos pasos:

1. **Comparación de tablas de rutas:** Antes de comenzar a programar, describa brevemente en su informe las similitudes y diferencias entre la tabla de rutas utilizada para esta actividad versus una tabla de rutas real.


2. **Parámetros por línea de comandos:** Cree un código que reciba como parámetros la `IP` y `puerto` donde va a estar escuchando el *router*, y el nombre del archivo que contiene su tabla de rutas usando `sys.argv`:


```bash
% python3 router.py router_IP router_puerto router_rutas.txt

```


Para echar a correr `R1` y `R2` como en el ejemplo 1 de *Simulando un mini-Internet*, habría que abrir 2 terminales (o usar directamente `fork`) y ejecutar:


```bash
# Router R1
% python3 router.py 127.0.0.1 8881 rutas_R1_v1.txt

# Router R2
% python3 router.py 127.0.0.1 8882 rutas_R2_v1.txt

```


> **Test:** Verifique que su código obtiene correctamente los parámetros ejecutando 2 instancias de su código router en terminales distintas.
> 
> 


3. **Socket bloqueante:** Dentro de su código haga que un socket no orientado a conexión escuche de forma bloqueante (forma tradicional donde el socket bloquea el funcionamiento del código hasta recibir algo) en el par `(router_IP, router_puerto)` recibido como parámetro.


4. **Codificación de paquetes en bytes:** Considerando como base la estructura de paquete IP de *Simulando un mini-Internet*, cree su propia estructura para codificar la información utilizando únicamente bytes:


* **Dirección IPv4:** Utilizar 4 bytes consecutivos para representar la estructura `a.b.c.d` (1er byte = `a`, 2do = `b`, 3ro = `c`, 4to = `d`).


* **Puerto:** Utilizar un `int` de Python transformado a 2 bytes para representar el puerto.




Con esto el header ocupa **6 bytes** (4 bytes para IP, 2 bytes para puerto) y los bytes restantes representan el mensaje. Implemente las siguientes funciones:


* `parse_packet(IP_packet: bytes)`: Extrae los headers y datos del paquete en bytes recibido por el socket y los pasa a una estructura de datos conveniente.


* `create_packet(parsed_IP_packet)`: Recibe la estructura de datos retornada por `parse_packet` y crea un paquete IP en bytes según la estructura definida.




> **Test:** Verifique la conversión de ida y vuelta entre bytes y estructura parseada:
> 
> 
> ```python
> IP_packet_v1 = packet_in_bytes # creado manualmente según su estructura
> parsed_IP_packet = parse_packet(IP_packet_v1)
> IP_packet_v2 = create_packet(parsed_IP_packet)
> print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
> 
> ```
> 
> 


5. **Script emisor de mensajes:** Cree un script que permita enviar mensajes en el formato correcto hacia cualquier dirección. Debe recibir el par `(IP_router_final, puerto_router_final)`, el mensaje a enviar (en `string`) y el par `(IP_envío, puerto_envío)` (que no necesariamente es igual al destino final). Generará el paquete IP con los datos de destino final y lo enviará a `(IP_envío, puerto_envío)`. **La forma en que su script recibe esta información debe ser definida por usted y explicada apropiadamente en su informe**.


6. **Búsqueda en tabla de rutas:** Cree la función `check_routes(routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str, int]`, encargada de revisar en orden la tabla de rutas para indicar la dirección `(next_hop_IP, next_hop_puerto)` del siguiente salto, o retornar `None` si no encuentra una ruta apropiada.


> **Test:** Pruebe `check_routes` usando como base distintos routers del **ejemplo 2** de *Simulando un mini-Internet*, tanto con destinos dentro de la red como fuera de ella (por ejemplo, `IP_destino=127.0.0.1, puerto=8884, mensaje=hola`).
> 
> 


7. **Loop de recepción y forwarding:** Haga que el router reciba paquetes en un ciclo:


* Si el paquete es para él, debe imprimir el contenido del paquete (sin headers).


* Si no es para él, debe llamar a `check_routes` y reenviar (*forward*) el paquete al siguiente salto, imprimiendo:
`redirigiendo paquete [paquete_ip] con destino final [destination_address] desde [dirección_router_actual] hacia [dirección_next_hop]`.


* Si `check_routes` retorna `None`, debe ignorar el paquete e imprimir:
`No hay rutas hacia [destination_address] para paquete [paquete_ip]`.




> **Test:** Pruebe su código con las tablas de rutas del **ejemplo 1** (2 routers) y del **ejemplo 2** (3 routers) usando `fork` o múltiples terminales, y envíe mensajes desde una nueva terminal usando el script del paso 5.
> 
> 


8. **Red de 5 routers y Round-Robin:** Considere la estructura de 5 routers cuyas tablas de ruta están en la sección *Material e indicaciones para la actividad*.
   ```text
    R1 <------->   R2  <------->  R3
    
                   ^              ^
    
                   |              |
    
                   v              v
    
                  R4 <---------> R5
   ```
   Modifique `check_routes` para que, cuando exista más de una ruta posible para *forwardear* un paquete, alterne entre ellas usando **round-robin**. Esta funcionalidad debe funcionar para un número arbitrario de rutas posibles y recordar de forma independiente la última ruta tomada para cada 'área de la red'. **Incluya una breve descripción en su informe sobre la decisión de diseño para manejar round-robin**.


> **Test 1:** Envíe varios paquetes desde `R1` hacia `R5` y verifique que `R2` cicla entre los caminos posibles. *(Pregunta de reflexión no obligatoria para el informe: luego de implementar round-robin, ¿puede ocurrir que un paquete quede dando vueltas por su red?)*
> **Test 2:** Modifique la red de 5 routers agregando un router `R0` conectado a `R1` y `R2`, y un router `R6` conectado con `R2` y `R3`. Intercale el envío de múltiples paquetes desde `R1` a `R5` y desde `R5` a `R1`, verificando que `R2` cicla correctamente dentro de cada área de la red.
> 
> 


9. **Router default:** Agregue un router default con dirección `(127.0.0.1, 7000)` conectado a cada elemento de la red, al cual se le enviarán todos los paquetes que no vayan dirigidos a ningún otro router de la red (modificando solo las tablas de rutas, sin añadir código nuevo). **Añada en su informe** cómo queda su nueva tabla de rutas y responda: *Dada una tabla de rutas, ¿en qué posición (línea) de la tabla debería ir la ruta default?*


> **Test:** Ejecute su sistema con las nuevas tablas de rutas, envíe un paquete a una dirección fuera de la red y verifique que es enviado al router default.
> 
> 



#### Pruebas Mini-Internet sin TTL (Informe 1 pto)



1. Usando las rutas del ejemplo 2, pruebe qué ocurre si se configura mal la tabla de rutas de `rutas_R2_v2.txt` reemplazándola por el siguiente contenido y coméntelo brevemente en su informe:


```text
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8883 8883 127.0.0.1 8881

```


2. Usando las rutas de la estructura de 5 routers, envíe varios paquetes a `R1` con destino `R5` verificando el uso de *round-robin*. Anote en el informe: *¿cuántos saltos dan los paquetes? ¿siempre dan la misma cantidad de saltos? ¿cómo se compara la cantidad de saltos que dan los paquetes versus la cantidad de saltos mínima?*


3. Repita las pruebas del punto 2 utilizando la estructura creada en el **Test 2 del paso 8** (con `R0` y `R6`), escriba sus observaciones en el informe y añada los contenidos de los distintos archivos de rutas creados.



---

#### Parte II: Mini-Internet con TTL (Código 1.5 pts)



Para evitar ciclos infinitos en el ruteo (como el inducido en la parte anterior), agregaremos al header el campo **Time-To-Live (`TTL`)** como un entero entre `1` y `255`. Se sugiere añadir el `TTL` como **1 byte** al final del header original, quedando un header de **7 bytes** (4 bytes IP + 2 bytes puerto + 1 byte `TTL`) seguido por los bytes del mensaje.

1. **Actualizar parseo y creación de paquetes:** Modifique `parse_packet` y `create_packet` para manejar el nuevo campo `TTL`.


> **Test:** Verifique la conversión de ida y vuelta incluyendo `TTL`:
> 
> 
> ```python
> IP_packet_v1 = packet_in_bytes_with_ttl # creado manualmente según su estructura
> parsed_IP_packet = parse_packet(IP_packet_v1)
> IP_packet_v2_str = create_packet(parsed_IP_packet)
> IP_packet_v2 = IP_packet_v2_str.encode()
> print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
> 
> ```
> 
> 


2. **Validación de `TTL > 0`:** Haga que su código procese el mensaje **solo si `TTL > 0**`. En caso contrario, debe ignorar el paquete e imprimir:
`Se recibió paquete [paquete_ip] con TTL 0`.


3. **Decremento de `TTL`:** En caso de que el paquete deba ser reenviado, decremente el valor de `TTL` en 1 **antes** de hacer *forward*.


> **Test:** En una estructura de al menos 3 routers de la parte 1, envíe un paquete con `IP=127.0.0.1, puerto=8883, TTL=1, mensaje=hola` desde `R1` a `R3` y verifique que no llega a destino porque se descarta por `TTL`.
> 
> 


4. **Script de pruebas por archivo:** Implemente un código `prueba_router.py` que lea un archivo línea por línea, encapsule cada línea en headers IP y envíe cada paquete mediante un socket UDP recibiendo los argumentos con `sys.argv`:


```bash
% python3 prueba_router.py headers IP_router_inicial puerto_router_inicial

```


Por ejemplo, para enviar línea a línea un archivo desde `R1` hacia `R5`:


```bash
% python3 prueba_router.py 127.0.0.1;8885;10 127.0.0.1 8881

```



#### Pruebas Mini-Internet con TTL (Informe 1 pto)



1. Repita la primera prueba de la parte 1 (error inducido en la tabla de rutas) usando un `TTL` inicial de `TTL = 10` y anote brevemente en su informe qué diferencias observa.


2. Con la configuración de 5 routers, utilice el script del paso 4 con un archivo grande (de varias líneas) y anote en el informe qué ocurre con el orden de los paquetes.



---

### Material e indicaciones para la actividad



* **Tablas de rutas para caso 5 routers** (*[Imagen: Estructura de 5 routers]*, sin considerar router default):



```text
# archivo rutas_R1_v3.txt
127.0.0.1/24 8882 8885 127.0.0.1 8882

```

```text
# archivo rutas_R2_v3.txt
127.0.0.1/24 8881 8881 127.0.0.1 8881
127.0.0.1/24 8883 8885 127.0.0.1 8883
127.0.0.1/24 8883 8885 127.0.0.1 8884

```

```text
# archivo rutas_R3_v3.txt
127.0.0.1/24 8881 8882 127.0.0.1 8882
127.0.0.1/24 8881 8882 127.0.0.1 8885
127.0.0.1/24 8884 8885 127.0.0.1 8882
127.0.0.1/24 8884 8885 127.0.0.1 8885

```

```text
# archivo rutas_R4_v3.txt
127.0.0.1/24 8881 8883 127.0.0.1 8882
127.0.0.1/24 8881 8883 127.0.0.1 8885
127.0.0.1/24 8885 8885 127.0.0.1 8882
127.0.0.1/24 8885 8885 127.0.0.1 8885

```

```text
# archivo rutas_R5_v3.txt
127.0.0.1/24 8881 8884 127.0.0.1 8884
127.0.0.1/24 8881 8884 127.0.0.1 8883

```