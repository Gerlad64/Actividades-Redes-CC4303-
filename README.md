# Actividades Redes -- CC4303-1 -- Semestre Primavera 2026
**Gerald Ponce**

Este repositorio será usado para las actividades del curso de Redes.
Cada actividad se encontrará dentro de su propia carpeta, pudiendo haber excepciones
si una actividad depende código de una actividad anterior.

En este README encontraras una pequeña descripción de cada actividad y cómo
configurar y ejecutar los programas desarrollados.


## Actividad 1
El objetivo es construir un **proxy** para filtrar contenido web.

### Dependencias y Entorno
Se probó con `python` 3.13 y 3.14 sin librerías externas, y en los sitemas operativos MacOS y Linux. 
Para otra versión de python se requiere soporte para las siguientes librerías nativas de python:
- socket
- json
- dataclass **from** dataclasses
- Path **from** pathlib


### Configuración
#### Servidor
Las configuraciones del servidor se encuentran en `config.py`.
Las más relevantes son las siguiente:
- **SERVER_ADDRESS**: Configura en que IP y puerto se va a servir `http_server.py`
- **HTML_PATH**: Ruta al html de la landing page.
También se puede configurar `proxy.json` para cambiar las páginas a ser bloqueadas o filtradas.

#### Cliente
Se debe configurar ya sea el navegador o la red wifi para usar este proxy.

**OJO: Esto no funciona en la configuración de red de samsung**
Ya que el servidor no maneja la petición `CONNECT` que este realiza.

De momento solo se ha probado configurar el cliente MacOS.

### Ejecución
```bash
cd Actividad-1/
```
```bash
python3 http_server.py
```
Siempre que la versión de `python` a usar sea compatible, ya sea del sistema o de un entorno.

### Uso
Una vez ya configurado todo, puedes intentar ir a las siguientes páginas:

**Páginas filtradas/modificadas**:
- cc4304.bachmann.cl
- cc4304.bachmann.cl/replace

**Páginas bloqueadas**:
- cc4304.bachmann.cl/secret
- www.dcc.uchile.cl
- www.tiktok.com

**Páginas servidas**:
- http://\<IP-Proxy\>:\<Puerto\>/
- http://\<IP-Proxy\>:\<Puerto\>/html/index.html
- http://\<IP-Proxy\>:\<Puerto\>/html/status/403.html
- http://\<IP-Proxy\>:\<Puerto\>/html/status/404.html

### Pruebas
- `curl google.com -x IP_Proxy:Port` muestra que envía y usando el header `X-ElQuePregunta` con el usuario configurado en `proxy.json`
- Esto también se visualiza mejor ingresando a cc4304.bachmann.cl en el navegador.
- Se puede probar visitando las páginas de arriba que el filtro y bloqueo funcionan, es decir, filtran las palabras prohibidas y redirige
  a una página propia 403 forbidden.
- Si se hace curl IP_Proxy:Port, se puede probar que funciona con cualquier tamaño de buffer, en particular,
  * Buffer pequeño: tamaño 4.
  * Buffer menor al mensaje, pero mayor que el área de headers: tamaño 100 que es un poco más grande que el header pero mucho más pequeño que el
    html.Esto se comprueba viendo los headers que se imprimen en la pantalla del servidor proxy.
  * Buffer menor al área de headers, pero mayor que la start line: tamaño 20. La start_line es poco menos de 20 y el resto son más que 20.