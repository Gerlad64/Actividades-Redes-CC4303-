## Informe Actividad 2
**Gerald Ponce Díaz**

**github**: https://github.com/Gerlad64/Actividades-Redes-CC4303-

### Documentación y Diseño
Para poder lograr lo propuesto por la actividad se destinó el archivo `dns_parser.py` para contener toda la lógica
de parsear mensajes dns, en particular, se usó el mismo enfoque que en la actividad HTTP de usar *dataclasses*. Además,
se decidió usar la librería de python `ctypes.BigEndianStructure`, que me permitía asegurar que cada campo del mensaje 
dns con número de bytes no variable tuviera la cantidad que le corresponda. Aunque al indagar, la librería `struct` pudo
haber sido más adecuada en el contexto de redes, este enfoque fue de todas formas fue lo suficientemente útil para la tarea[^1].

[^1]Nuevamente, como estas librerías no abstraen los procesos relacionados a sockets o DNS, se considera que su uso es adecuado y permitido.

Se decidió no usar `dnslib` y crear un parser desde 0 ya que mi primera impresión con la API me pareció confusa, y la mayoría de métodos o atributos están tipados como Unknown y no tienen *docstring*. El diseño de mi implementación se encuentra explicado en la sección de abajo

El servidor dns se construye en la función main de `resolver.py`, donde tambien se define el resolver DNS.

#### Clases Header, Question, ResourceRecord y DNS
Se creó la *dataclass* `HTTP` en el archivo `http_parser.py` que tiene la siguiente estructura:
```python
class Header(ctypes.BigEndianStructure):
    """Almacena los campos del *Header* de un mensaje DNS"""
    # ...
class Question(ctypes.BigEndianStructure)
    """Almacena los campos de *Question* de un mensaje DNS"""
    # ...

class ResourceRecord(ctypes.BigEndianStructure)
    """Almacena los campos de un *Resource Record* de un mensaje DNS"""
    # ...

@dataclass
class DNS:
    header:     Header
    question:   Question | None
    answers:     list[ResourceRecord]
    authority_records:  list[ResourceRecord]
    additional_records: list[ResourceRecord]
```
El propósito de la clase DNS esta es poder interactuar con todos los campos de un mensaje desde un solo objeto.
Donde cada clase se preocupa de parsear sus campos, y proveer APIs para interactuar con ellos.

Se llegó a esta versión de la clase `DNS` a partir de prueba y error, al notar que una respuesta dns podían incluir
cero o más respuestas, authority y additional.

El propósito de esta clase es que al tener un objeto HTTP pueda estar seguro de que se puede crear
un mensaje HTTP válido a partir de los datos contenidos del objeto. Además, al ser *dataclass* su inicialización
es relativamente sencilla, siempre que los campos ingresados sean correctos.

#### Parseo mensajes DNS
Cada clase definida tiene un método
```python
@classmethod
def from_bytes(cls, dns_bytes: bytes, offset: int)
```
Que retorna el objeto de la clase con la que se está llamando al método.
Como toda la información está contenida en una sola cadena de bytes, es necesario 
agregar un offset.

Así, cuando se llama a `from_bytes` desde la clase `DNS`, esta va llamando el método,
partiendo por el header, el cual indica cuantas preguntas, respuestas, authority y additional vendrán más
adelante, iterando por el número de registros indicado y acumulando el *offset*.

#### Mandar mensajes DNS
De manera similar con el proceso de *parsing*, cada clase tiene un método
```python
def to_bytes(self) -> bytes
```
donde al llamarlo desde la clase dns, este llama al método `to_bytes` de cada campo.
El resultado es una cadena de bytes con un mensaje dns que puede ser mandado por un socket udp.


#### resolver
Se usan las herramientas provistas por mi clase para poder resolver dominios, mientras se siguen
las instrucciones de esta parte al pie de la letra.

El resolver retorna un objeto DNS que puede ser convertido a bytes y mandado al cliente.

#### Debug
Se utiliza la librería *logging* para configurar un logger con la capacidad de imprimir mensajes
informativos o de debug.

#### Dependencias y Entorno
Se probó con `python` 3.13 y 3.14 sin librerías externas, y en los sitemas operativos MacOS y Linux. 
Para otra versión de python se requiere soporte para las siguientes librerías nativas de python:
- socket
- dataclass **from** dataclasses
- Path **from** pathlib
- ctypes
- logging para imprimir logs

#### Configuración
##### Servidor
Las configuraciones del servidor se encuentran en `config.py`.
Las más relevantes son las siguiente:
- **SERVER_IP** y **SERVER_PORT**: Configura en que IP y puerto se va a servir `resolver.py`
- **SERVER_BUFFER_SIZE**: para configurar el tamaño del buffer
- **DEBUG_MODE**: True para mostrar logs de debug. False para no mostrarlos

##### Cliente
Se consume usando el comando `dig -p PORT @IP domain` 

#### Ejecución
```bash
cd Actividad-2/
```
```bash
python3 resolver.py
```
Siempre que la versión de `python` a usar sea compatible, ya sea del sistema o de un entorno.

#### Pruebas
- Se puede comprobar desde la consola del resolver que un mensaje es parseado correctamente al comparar el mensaje recibido vs
  el reconstruido con el parser.
- Hacer dig a www.uchile.cl con cloudflare y con resolver devuelve la misma IP, solo que con el resolver
- dig -p8000 @IP_VM eol.uchile.cl encuentra 11 respuestas.

### Uso de IA
Se usó para consultar sobre el protocolo DNS, debuggear, y como ayuda a definir mi diseño, es más, usar ctypes surgió como 
una de varias sugerencias de la IA, pues, yo quería que mis clases garantizara que los bytes de cada campo son los adecuados.
A partir de la sugerencia y un código base construí la arquitectura (métodos, atributos, etc) por mi cuenta.

Para generación de código, solo se usó en alguna de las funciones auxiliares en `dns_parser.py`, adaptado a mis necesidades.
