# Manual de Usuario del Visor de Dominios (Domain Visor)

Este manual proporciona una guía detallada sobre el funcionamiento, la interfaz y las capacidades de navegación del **Visor de Dominios**, una herramienta interactiva diseñada en Python con PyQt6 para la visualización y edición en tiempo real de arquitecturas complejas de infraestructuras (compuestas de superdominios, dominios, años y conexiones).

---

## 1. Introducción

El **Visor de Dominios** es una aplicación de escritorio que permite representar de forma gráfica y jerárquica la distribución de distintas entidades temporales u organizativas (años y bloques de dominios) y sus interconexiones lógicas (cables). Además de visualizar, incluye un potente editor interactivo que actualiza de manera automática el archivo de infraestructura subyacente.

---

## 2. Archivos Clave del Sistema

- **`render_domains.pyw`**: El punto de entrada principal del programa. Ejecuta la interfaz gráfica o exporta la escena de forma headless usando el comando `--png_export <ruta.png>`.
- **`__structure__/infrastructure.json`**: Almacena de forma estructurada los superdominios, los dominios dentro de ellos, sus rangos de años y la lista de conexiones (cables).
- **`__structure__/container.json`**: Almacena configuraciones generales, como el título del contenedor.

---

## 3. Interfaz de Usuario

La ventana principal del Visor de Dominios se divide en dos secciones principales mediante un divisor ajustable (**Splitter**):

### A. Panel Izquierdo: Editor de JSON (`JSONEditorPanel`)
Este panel permite ver y modificar la estructura lógica de los datos de manera jerárquica:
- **Árbol de Propiedades**: Muestra de forma organizada todas las claves, objetos y arreglos de la infraestructura.
- **Edición Interactiva**: Puedes hacer doble clic en cualquier clave o valor de tipo primitivo para modificarlo en el acto. Al presionar *Enter*, los cambios se guardan automáticamente en `infrastructure.json` y la vista gráfica de la derecha se re-renderiza de inmediato.
- **Menú Contextual (Clic Derecho)**:
  - Al hacer clic derecho en un elemento u área vacía del árbol, aparecerá un menú moderno para añadir nuevos pares Clave-Valor, Objetos vacíos o Listas vacías, o bien para eliminar el elemento seleccionado de forma segura.

### B. Panel Derecho: Vista Gráfica de la Escena (`QGraphicsView`)
Este panel representa de forma visual y con un atractivo diseño oscuro (Dark Mode) la infraestructura definida en el JSON:
- **Superdominios**: Grandes contenedores grises con bordes redondeados y un título centrado en la parte superior.
- **Dominios**: Bloques rectangulares de colores agrupados en columnas dentro de sus respectivos superdominios. Los colores cambian de forma inteligente según el "rol" del dominio (p. ej., azul, rosa/magenta, morado).
- **Años**: Cada año se representa de manera limpia y centrada verticalmente como una fila dentro de su bloque de dominio.
- **Puertos de Conexión**: Pequeños círculos blancos situados a la izquierda y derecha de cada año para el anclaje de las líneas de conexión.

### C. Botón Flotante de Mostrar/Ocultar Editor
En la esquina inferior izquierda de la vista gráfica, flota un botón moderno estilizado con la apariencia del tema oscuro.
- **Flecha apuntando a la izquierda (`◀`)**: Indica que el editor de JSON está visible. Al hacer clic en él, el panel izquierdo se colapsa/oculta por completo para maximizar el área de visualización del gráfico, y la flecha cambia a dirección opuesta (`▶`).
- **Flecha apuntando a la derecha (`▶`)**: Indica que el editor está oculto. Al pulsarlo, el panel izquierdo vuelve a aparecer con sus dimensiones originales.
- **Memoria de Estado**: La aplicación recuerda si dejaste el editor abierto o cerrado de forma persistente entre ejecuciones (gracias a `QSettings`), cargando tu preferencia automáticamente en el próximo inicio.

---

## 4. Navegación e Interacción Gráfica

La visualización gráfica cuenta con mecánicas avanzadas de interacción que hacen muy fluida la navegación:

### A. Centrado Automático Inteligente
- Al iniciar la aplicación, la cámara se posiciona y enfoca automáticamente en el **centro exacto de los elementos dibujados** (el contenedor de dominios), asegurando que el gráfico nunca empiece recortado o fuera de pantalla.

### B. Control de Zoom
Puedes ajustar la escala del gráfico (desde `0.2x` hasta `5.0x`) con múltiples opciones intuitivas:
- **Rueda del Ratón**: Desplazar la rueda hacia arriba realiza un zoom-in enfocado en la posición del cursor, y hacia abajo realiza un zoom-out.
- **Atajos de Teclado**:
  - `Ctrl + +` o `Ctrl + =` para acercar (Zoom In).
  - `Ctrl + -` para alejar (Zoom Out).
  - `Ctrl + 0` para restablecer el zoom a la escala original por defecto (`1.0x`).

### C. Desplazamiento y Paneo (Panning)
- **Modo Arrastre de Mano**: No necesitas usar las barras de desplazamiento tradicionales. Puedes hacer clic izquierdo en cualquier parte vacía del lienzo gráfico y mantenerlo pulsado para arrastrar (arrastre estilo mano, `ScrollHandDrag`) y moverte libremente por toda la escena.

### D. Interacción con Conexiones (Cables)
- **Cursor de Mano**: Al colocar el puntero del ratón sobre cualquier cable de conexión, el cursor cambia automáticamente a una **mano apuntadora** interactiva (`PointingHandCursor`), indicando que es un elemento seleccionable/interactivo.
- **Área de Colisión Optimizada (Hitbox)**: Los cables cuentan con una hitbox invisible de 10px de ancho, por lo que es sumamente fácil pasar el ratón sobre ellos sin necesidad de apuntar con precisión quirúrgica.
- **Tooltips Informativos**: Al pasar el ratón sobre un cable, emerge un mensaje emergente (tooltip) detallando el nombre de la conexión y los años de origen y destino implicados.

---

## 5. Tipos de Cables y Reglas de Diseño

Para facilitar la lectura visual rápida de las redes de conexiones, se han establecido colores específicos y grosores diferenciados para ciertos cables claves:

| Tipo de Conexión (`range_type`) | Color Representado | Grosor del Cable | Descripción Visual |
| :--- | :--- | :--- | :--- |
| **`deuterolazo_de_andrea_cloe`** | Rosa Fuerte (`#ff1493`) | Semi-grueso (`4.0px`) | Destaca de forma muy visible en rosa vibrante. |
| **`exolazo`** | Azul Celeste (`#00bfff`) | Semi-grueso (`4.0px`) | Destaca de forma muy visible en azul brillante. |
| **`mesolazo_domain_to_domain`** | Blanco Puro (`#ffffff`) | Estándar (`2.0px`) | Utiliza una trayectoria de cruce especial redondeada. |
| **Estándar / Otros** | Gris Claro (`#d0d0d0`) | Estándar (`2.0px`) | Curva suave en forma de "S" entre los puertos. |

### Márgenes Simétricos
Para dar un aspecto limpio, ordenado y espacioso, la escena cuenta con márgenes de seguridad calibrados:
- **Margen Izquierdo**: `100.0px`
- **Margen Superior**: `40.0px`
- **Margen Derecho**: `100.0px`
- **Margen Inferior**: `100.0px`

Esto garantiza que incluso con muchos superdominios o dominios largos, el lienzo gráfico siempre mantendrá un encuadre estéticamente agradable.
