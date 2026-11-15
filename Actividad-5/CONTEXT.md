## Simulando un mini-Internet

> En esta actividad vamos a **simular nuestro propio mini-Internet** a nivel de la **capa de red**. Como vimos en los videos, en esta capa tenemos ***routers***, ***tablas de ruta***, y el *Internet Protocol* (IP) con sus propios ***headers***. A continuación veremos **cómo** vamos a simular nuestro mini-Internet.

> **Note que aquí describiremos todo en texto o *strings*, sin embargo en la actividad final deberá manejar sus headers utilizando directamente bytes.**

### Routers

Para simular los routers usaremos **sockets UDP**. La capa de red se encuentra "*debajo*" de la capa de transporte y por lo tanto no tiene protocolos de transporte confiable como TCP. Para nuestro mini-Internet, **cada router se simulará usando un proceso pesado distinto con un socket asociado a un par** `(**`IP,puerto`**`)` **específico**. Cada router deberá contener una **tabla de rutas** para consultar hacia dónde debe re-dirigir (o *forwardear*) los mensajes que reciba. En caso de que el mensaje tenga como destino el mismo router que lo recibió, dicho router debe imprimir el mensaje en pantalla, **omitiendo *headers***.

En nuestro mini-Internet simularemos una red de forma local sobre una única IP por propósitos pedagógicos, por lo que para representar "rangos de IPs" utilizaremos **rangos de puertos**. *Sin embargo*, en la vida real, las redes se componen de varias direcciones IP y los puertos son utilizados para distinguir procesos.

### Headers

Similar a las actividades de TCP simplificado, aquí usaremos nuestra propia estructura de *headers*. Esto facilitará un poco las cosas, pues acceder a los headers IP de los sockets requiere permisos de administrador y/o conocimiento extenso de bajo nivel. Para esta actividad usaremos la siguiente estructura para nuestros paquetes IP:

**`[Dirección IP];[Puerto];[mensaje]`**

Aquí el ";" se utiliza para delimitar visualmente los campos, y para poder entregarlos de forma legible a un script, sin embargo a la hora de programar los headers se espera que usted codifique cada campo con una cantidad fija de bytes.

Dentro de la estructura anterior, la **`[Dirección IP]`** y el **`[Puerto]`** corresponden al par **`(IP, puerto)`** en el que se encuentra escuchando el router al cuál va dirigido el **`[mensaje]`** (recuerde que su router se simula con un socket UDP asociado al par **`(IP, puerto)`**). De esta forma si, por ejemplo, tenemos el router **`R1`** asociado a **`(127.0.0.1, 8881)`** y le enviamos el paquete **`127.0.0.1;8881;hola`** usando **`netcat`** como se muestra a continuación:

```bash
 % nc -u 127.0.0.1 8881 << EOF
 % 127.0.0.1;8881;hola
 % EOF

 # con '<< EOF' le indicamos al comando que debe terminar cuando ingresemos EOF, esto es estándar de bash.
 # Si no utiliza '<< EOF' su mensaje se enviará luego del primer salto de línea.
```

Vamos a ver que **`R1`** imprime en pantalla "**`hola`**", pues ve que llega un mensaje cuyo destino se corresponde con su propia dirección. Si en cambio le enviamos el mensaje **`127.0.0.1;8882;hola`** nuestro router **`R1`** como se muestra a continuación:

```bash
 % nc -u 127.0.0.1 8881 << EOF  # lo que vamos a enviar va a la dirección (127.0.0.1, 8881)
 % 127.0.0.1;8882;hola          # pero el header indica que la dirección de destino es en realidad (127.0.0.1, 8882)
 % EOF

 # con '<< EOF' le indicamos al comando que debe terminar cuando ingresemos EOF, esto es estándar de bash.
 # Si no utiliza '<< EOF' su mensaje se enviará luego del primer salto de línea.
```

El router **`R1`** va ver que el mensaje **no está dirigido hacia él**, sino que al router asociado a **`(127.0.0.1,8882)`**, por lo que deberá **consultar su tabla de rutas** para hacer ***forward*** y enviarlo por la ruta que corresponda.

### Tabla de rutas

**Cada router** o nodo de nuestro mini-Internet **debe tener su propia tabla de rutas**. Esta tabla de rutas debe indicar el camino por el cual se deben *forwardear* los mensajes en caso de ser necesario. En nuestra simulación la tabla de rutas corresponderá a un archivo **`.txt`** asociado al router. Este archivo contendrá líneas indicando cuál es el **siguiente router** al que se le debe enviar el mensaje para que llegue a su destino final. **Cada línea tendrá la siguiente nomenclatura**:

| Destination Network | Gateway |
| :--- | :--- |
| `[Red (CIDR)] [Puerto_Inicial] [Puerto_final]` | `[IP_siguiente_salto] [Puerto_siguiente_salto]` |

**Esta línea se traduce como**: "Todo lo que reciba en el rango de direcciones IP = **`[Red (CIDR)]`** y el rango de puertos = **`([Puerto_Inicial],[Puerto_final])`** debo enviarlo al par **`([IP_siguiente_salto],[Puerto_siguiente_salto])`** para que continúe su camino". El área de **`Destination Network`** es la red de destino y el área de **`Gateway`** corresponde al *siguiente salto* para llegar a la red de destino. En nuestro mini-Internet **el rango de direcciones IP** **`[Red (CIDR)]`** **corresponde a dirección: `127.0.0.1/24`** o direcciones asociadas a localhost.

**Notemos** que el **`[Puerto_Inicial]`** y el **`[Puerto_final]`** **no son el origen y destino**, sino la forma que tenemos de **agrupar los hosts de la red** que pertenecen a la misma IP pero que están escuchando en distintos puertos. Luego si tenemos **`[Puerto_Inicial]=8881`** y **`[Puerto_final]=8883`**, tenemos que la ruta considera el rango de puertos de destino **`{8881,8882,8883}`**.

> **Importante:** No olvide que aquí estamos simulando una red de forma local sobre una única IP por propósitos pedagógicos. Esta es la razón para utilizar un rango de puertos en vez de un rango de direcciones IP. Sin embargo, en la vida real, las redes se componen de varias direcciones IP y los puertos son utilizados para distinguir procesos.

### Ejemplos:

---

**Ejemplo 1:**

Supongamos que nuestro mini-Internet contiene solo 2 routers conectados entre sí: **`R1`** asociado a **`(127.0.0.1,8881)`** y **`R2`** asociado a **`(127.0.0.1,8882)`** como se muestra en la figura:

```text
R1 <------> R2
```

Si a **`R1`** le llega el paquete "**`127.0.0.1;8882;hola R2!`**" este verá que dicho mensaje no está dirigido a él (**`R1`**). Luego, dado que el mensaje no es para él, **`R1`** va a mirar su tabla de rutas para saber por dónde *forwardear* dicho mensaje. En este caso la tabla de rutas de **`R1`** se verá como:

```text
 # archivo rutas_R1_v1.txt

 127.0.0.1/24 8882 8882 127.0.0.1 8882
```

Donde la línea "**`127.0.0.1/24 8882 8882 127.0.0.1 8882`**" indica que si recibo un mensaje que se dirige al grupo de IPs **`127.0.0.1/24`** con un puerto en el conjunto **`{8882}`** (equivalente al rango (8882,8882)), entonces debe reenviarlo o hacer *forward* hacia la dirección **`(127.0.0.1,8882)`**.

Dado que nuestro Internet solo contiene a **`R1`** y **`R2`** conectados entre sí, la tabla de rutas de **`R2`** se verá como:

```text
 # archivo rutas_R2_v1.txt

 127.0.0.1/24 8881 8881 127.0.0.1 8881
```

De esta forma si ejecutamos:

```bash
 % nc -u 127.0.0.1 8881 << EOF
 127.0.0.1;8882;hola R2!
 EOF
 %
```

El router **`R1`** va a ver que el paquete no es para él, así que va a mirar su tabla de rutas y ver que el paquete debe ir hacia **`R2`**. Una vez **`R2`** reciba el paquete va a ver que este sí es para él (**`R2`**) por lo que va imprimir el contenido del mensaje en pantalla (sin headers), o sea, **`R2`** va a imprimir "**`hola R2!`**"*.*

---

**Ejemplo 2:** Suponga que ahora nuestro mini-Internet contiene sólo 3 routers conectados entre sí: **`R1`** asociado a **`(127.0.0.1,8881)`**, **`R2`** asociado a **`(127.0.0.1,8882)`** y **`R3`** asociado a **`(127.0.0.1,8883)`** como se muestra en la figura:

```text
R1 <------> R2 <------> R3
```

**Agregar un nuevo router significa que *todas* las tablas de ruta cambian**. Por ejemplo, en este caso la tabla de rutas de **`R1`** va a ser:

```text
 # archivo rutas_R1_v2.txt

 127.0.0.1/24 8882 8883 127.0.0.1 8882
```

**Lo que se traduce a:** "Para llegar a una dirección con IP **`127.0.0.0/24`** y puerto en el conjunto **`{8882,8883}`** (equivalente al rango (8882,8883)), debo hacer *forward* hacia **`(127.0.0.1,8882)`**". Equivalentemente esto lo podemos interpretar como "si algo llega a **`R1`** y va dirigido a **`R2`** o **`R3`**, entonces debemos hacer *forward* por **`R2`**".

La tabla de rutas de **`R3`** sería:

```text
 # archivo rutas_R3_v2.txt

 127.0.0.1/24 8881 8882 127.0.0.1 8882
```

Es decir que "para llegar a **`R1`** y **`R2`**, debo reenviar todo por **`R2`**".

Finalmente la tabla de rutas de **`R2`** sería:

```text
 # archivo rutas_R2_v2.txt

 127.0.0.1/24 8881 8881 127.0.0.1 8881
 127.0.0.1/24 8883 8883 127.0.0.1 8883
```

Notemos que en este caso tenemos **dos líneas** en la *tabla de rutas*. Estas se deben **chequear** en **orden descendente**. Si el **`Network destination`** de la primera fila no contiene el par IP y puerto de destino, entonces paso a la siguiente línea. Este proceso **se repite hasta encontrar una ruta para enviar el paquete** **o quedarse sin más rutas posibles**. En caso de que el destino del paquete **no coincida con ninguna línea** de la *tabla de rutas*, **este es descartado**.