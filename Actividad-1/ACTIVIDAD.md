# Actividad: Construir un Proxy

## Descripción General
El objetivo es construir un **proxy** para filtrar contenido web. La actividad se divide en dos partes, aunque **solo se entregará la versión final de la parte 2**.

*   **Puntaje:** 4.5 pts (Código) + 1.5 pts (Informe).
*   **Requisito de Informe:** Debe incluir una declaración explícita sobre el uso o no uso de IA/LLMs, especificando qué modelo y en qué partes se utilizó.

---

## Criterios de Evaluación (Puntaje por funcionalidad)
Para obtener el puntaje completo, el código debe cumplir con:
1.  **+0.5**: El cliente recibe una respuesta.
2.  **+1.0**: El proxy bloquea correctamente los sitios prohibidos.
3.  **+1.2**: Se reemplazan correctamente las palabras según el JSON utilizado.
4.  **+0.5**: Se modifican correctamente los headers.
5.  **+1.3**: Se manejan correctamente mensajes más grandes que el buffer del socket.

---

## Requisitos Técnicos y Entorno
*   **Librería permitida:** Solo se permite el uso de la librería `sockets` de Python. No se permiten otras librerías para el manejo de protocolos.
*   **Entorno:** El código debe ejecutarse en una máquina virtual (VM) y asociarse a su IP (`IP_VM`). Si hay problemas, se puede usar `localhost` (127.0.0.1).
*   **Protocolo:** HTTP utiliza sockets orientados a conexión. Los clientes usan `connect()`, los servidores usan `accept()`.

---

Aquí tienes las instrucciones de las **Partes 1 y 2** incluyendo los tests correspondientes para cada paso:

## Parte 1 (Preparación)
*Esta parte no es necesaria para la entrega, pero es fundamental para el desarrollo del proyecto.*

El objetivo es construir un servidor HTTP básico que sea capaz de leer e interpretar mensajes.

1. **Parseo y Creación de Mensajes:** Desarrolle la función `parse_HTTP_message(http_message: bytes)` para transformar un mensaje en una estructura de datos, y `create_HTTP_message()` para convertir esa estructura nuevamente a bytes.
    *   **Test:** Use su navegador para obtener un 'request' y úselo para probar que las funciones programadas funcionen correctamente (Nota: el código no responderá nada aún).

2. **Respuesta HTTP Básica:** Ejecute el comando `% curl -i cc4303.bachmann.cl` para ver una respuesta real. Use esa respuesta como guía para crear su propia respuesta a la petición recibida en el paso anterior (debe incluir un pequeño HTML y headers consistentes con el tipo y largo de contenido).
    *   **Test:** Haga que su código responda al navegador y verifique que se muestre correctamente. Luego, use `curl` desde su máquina local para verificar que también recibe una respuesta satisfactoria.

3. **Header Personalizado:** Modifique su servidor para agregar el header `X-ElQuePregunta` con su nombre como valor.
    *   **Test:** Pruebe que se agrega correctamente usando `curl IP_VM:[puerto_server_http] -i`.

4. **Configuración mediante JSON:** Haga que el servidor lea archivos JSON o de configuración (nombre y ubicación recibidos como argumentos). Por ahora, úselo para dejar en una variable su nombre para parametrizar al usuario.
    *   **Test:** Pruebe que su servidor puede tomar su nombre desde el archivo JSON y usarlo para añadir el header `X-ElQuePregunta`.

---

## Parte 2 (Entrega Final)
En esta etapa, convertirá el servidor anterior en un **Proxy** con funciones de bloqueo y reemplazo de contenido.

**Requisito previo:** Antes de modificar el código, debe dibujar un diagrama del flujo de funcionamiento del proxy e identificar cuántos sockets necesitará para comunicarse entre cliente, proxy y servidor. (Debe adjuntarse al informe).

1. **Proxy de Tránsito:** Modifique su servidor para que actúe como intermediario. Debe recibir una request, enviarla íntegramente al servidor, recibir la respuesta y enviársela al cliente sin modificarla.
    *   **Test:** Use `curl` para verificar que el proxy logra transferir mensajes de forma exitosa. Compare los resultados entre pedir una página con y sin proxy:
        *   `% curl example.com` (Sin proxy)
        *   `% curl example.com -x IP_VM:8000` (Con proxy)

2. **Bloqueo de Dominios:** Si el nombre de dominio solicitado está en la lista de bloqueados (según el JSON del material), debe devolver un código de error **403** junto con un HTML que muestre una imagen alojada localmente por usted (se sugiere usar gatos).
    *   **Test 1:** Use `curl` para intentar acceder a una página prohibida y verifique que retorne el error 403 con su HTML. Verifique que páginas no prohibidas sigan funcionando.
    *   **Test 2:** Configure su proxy momentáneamente como proxy de su navegador y vea que efectivamente se muestra la imagen local. (Recuerde quitar la configuración al terminar).

3. **Inyección de Headers de Identificación:** Si el destino NO está bloqueado, agregue a la request que sale desde el proxy hacia el servidor real el header `X-ElQuePregunta` con su nombre.
    *   **Test:** Use `curl` para acceder a `cc4303.bachmann.cl` a través de su proxy y verifique que el mensaje de bienvenida cambie en comparación con la petición sin pasar por su proxy.

4. **Reemplazo de Contenido (Censura):** Busque las palabras prohibidas (`forbidden_words`) definidas en el JSON y reemplácelas automáticamente en el cuerpo del mensaje (String A $\rightarrow$ String B).
    *   **Test:** Use `curl` para acceder a `cc4303.bachmann.cl/replace` a través de su proxy y verifique que las palabras sean reemplazadas correctamente y sin errores en el contenido.

5. **Manejo de Buffers Pequeños:** Modifique su código para recibir mensajes utilizando sockets cuyo buffer de recepción sea más pequeño que el tamaño del mensaje total recibido (ejemplo: `recv_buffer = 50`).
    *   **Test:** Pruebe que su proxy sigue funcionando cuando el tamaño del buffer es pequeño.

*Nota: Para los puntos 2, 3 y 4, debe responder en el informe sobre cómo sabe si llegó el mensaje completo, qué pasa si los headers no caben en el buffer, cómo sabe si el HEAD o el BODY llegaron completos.*---

## Pruebas Finales (Validación)
Deberás probar tu proxy utilizando un navegador configurado con tu IP/puerto como proxy:
1.  **Prueba de Bloqueo:** Verificar que `http://cc4303.bachmann.cl/secret` devuelva el error 403 y la imagen local.
2.  **Prueba de Reemplazo:** Verificar que en `http://cc4303.bachmann.cl/` y `/replace` las palabras prohibidas hayan sido censuradas correctamente.
3.  **Pruebas de Buffer:** 
    *   (1) Buffer menor al mensaje, pero mayor que el área de headers.
    *   (2) Buffer menor al área de headers, pero mayor que la *start line*.

---

## Entregables del Informe
Para la entrega del informe (PDF), debes incluir:
1.  **Documentación técnica:** Explicar cómo funciona tu código y qué decisiones de diseño tomaste.
2.  **Diagrama de flujo:** El diagrama solicitado en la Parte 2 con una breve explicación.
3.  **Enlace al repositorio:** Un enlace a tu repositorio de GitHub donde esté el código.
4.  **Instrucciones de ejecución:** Explicar claramente cómo ejecutar tu proxy y cómo realizar las pruebas sugeridas.
5.  **Respuestas solicitadas:** Las respuestas sobre el manejo de buffers y los ciclos de comunicación para la imagen de bloqueo.
