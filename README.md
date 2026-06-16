# Programa para diseño de muro de contención

Base de cálculo inicial: ejemplo de muro de contención de hormigón armado del PDF Caltrans BDP 11.2, sección 11.2.2.

## Unidades adoptadas

- Longitudes: `m`
- Capacidad admisible del suelo: `ton/m²`
- Cohesión: `ton/m²`
- Peso unitario del suelo: `ton/m³`
- Peso unitario del hormigón: `ton/m³`
- Resistencia del hormigón f'c: `kg/cm²`
- Fluencia del acero fy: `kg/cm²`

## Archivos

- `app.py`: interfaz principal de Streamlit.
- `funciones_muro.py`: funciones de geometría, dibujo, diagrama de fuerzas, verificación del PDF y memoria Word.
- `requirements.txt`: librerías necesarias.
- `README.md`: instrucciones.

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

## Qué incluye esta versión

- Dibujo dinámico de la geometría del muro.
- Dibujo didáctico de fuerzas:
  - `ΣW`
  - `khΣW`
  - `PA / PAE`
  - `PP / PPE`
  - `V`
  - `Rf`
- Verificación de resultados principales contra el ejemplo del PDF:
  - Extreme Event
  - Service
  - Strength Ia
  - Strength Ib
- Memoria preliminar en Word.

## Nota técnica

La verificación usa los valores reportados en el PDF para el método trial wedge, pesos, brazos de momento y resultados de estabilidad externa.  
En una etapa posterior se puede programar el método trial wedge de forma general para que `PA`, `PAE`, `δA`, `PP` y `PPE` se calculen automáticamente a partir de la geometría y el suelo.


## Método Trial Wedge

Esta versión incorpora una pestaña llamada `Trial Wedge`.

El programa:
1. Ensaya varias superficies de falla con distintos ángulos `α`.
2. Calcula la geometría y peso de cada cuña.
3. Calcula el empuje `P` para cada cuña.
4. Toma el mayor valor como `PA`.

También genera:
- dibujo de la cuña crítica;
- curva `P` vs `α`;
- tabla de todas las cuñas ensayadas.

Esta primera implementación es estática, para suelo sin cohesión, por metro longitudinal de muro. La siguiente etapa puede ampliar el método para caso sísmico `PAE`.


## Armado dinámico del fuste

Se agregó la pestaña `Armado fuste`.

El programa recalcula dinámicamente:

- `PA` mediante Trial Wedge.
- Presión triangular equivalente en la base.
- Cortante factorizado del fuste.
- Momento factorizado en la base del fuste.
- Acero vertical principal requerido.
- Acero horizontal de temperatura/retracción.
- Separación sugerida para barras.
- Esquema didáctico del armado.

La demanda sigue el criterio mostrado en el PDF para el fuste: el empuje activo actúa a `H/3` desde la base del fuste y el momento máximo se calcula en la base.


## Zapata dinámica

Se agregó la pestaña `Zapata`.

El programa recalcula dinámicamente:

- Resultante vertical.
- Excentricidad.
- Presiones de contacto `qmax` y `qmin`.
- Estado frente a `qa`.
- Momento preliminar de puntera.
- Momento preliminar de talón.
- Acero requerido y provisto en puntera y talón.
- Esquema didáctico del armado de zapata.

Este módulo es preliminar y debe depurarse con los siguientes pasos del PDF para llegar al detallado final completo.


## Zapata con cortante y anclaje

Se amplió la pestaña `Zapata`.

Ahora incluye:
- Presiones de contacto.
- Flexión de puntera.
- Flexión de talón.
- Cortante crítico de puntera a distancia `d` desde la cara del fuste.
- Cortante crítico de talón a distancia `d` desde la cara posterior del fuste.
- Comparación `Vu` contra `φVc`.
- Acero mínimo por temperatura/retracción.
- Acero requerido y provisto.
- Separación práctica.
- Longitud de desarrollo preliminar.
- Estado global de zapata: `OK` o `Revisar`.

La siguiente etapa recomendada es programar la llave de corte y luego el resumen general de cumplimiento.


## Llave de corte y deslizamiento

Se agregó la pestaña `Llave y deslizamiento`.

Incluye las tres partes solicitadas:

1. **Deslizamiento**
   - Empuje horizontal actuante.
   - Resistencia por fricción basal.
   - Resistencia total.
   - Relación `R/H`.
   - Estado `OK` o `No cumple`.

2. **Resistencia pasiva**
   - Cálculo dinámico de `Kp`.
   - Resistencia pasiva frente a la zapata.
   - Resistencia pasiva total con llave.
   - Incremento de resistencia por la llave.

3. **Detalle de armado de llave**
   - Presión pasiva sobre llave.
   - Momento y cortante de llave.
   - Acero requerido.
   - Acero provisto.
   - Separación.
   - Cortante `Vu` vs `φVc`.
   - Longitud de desarrollo preliminar.
   - Esquema didáctico.


## Detalle general de armado

Se agregó una nueva pestaña llamada `Detalle general`.

Esta pestaña muestra en una sola imagen:

- Armado de la pantalla o fuste.
- Armado de la zapata:
  - puntera;
  - talón.
- Armado del dentellón:
  - barras longitudinales;
  - estribos cerrados.
- Un detalle ampliado del dentellón para visualizar mejor el arreglo del acero.

Además, se mejoró la terminología visible en la interfaz para usar **dentellón**
en lugar de **llave**, que es el término más apropiado en este contexto.


## Corrección de importación Streamlit Cloud

Esta versión cambia el `app.py` para importar el módulo completo:

```python
import funciones_muro as fm
```

Esto evita errores de `ImportError` cuando Streamlit Cloud queda con una versión desfasada del archivo `funciones_muro.py` o cuando el import nombrado falla al arrancar.

Subir siempre juntos:
- `app.py`
- `funciones_muro.py`
- `README.md`
- `requirements.txt`

Luego hacer `Manage app → Reboot app`.


## Motor dinámico de validación PDF

Se cambió la validación del ejemplo PDF para que no dependa de resultados finales
quemados.

Ahora el flujo es:

1. `crear_caso_pdf_caltrans()`
   - Define los insumos del ejemplo:
     - partes del muro;
     - pesos;
     - brazos;
     - PA, PAE y δ obtenidos en el PDF por Trial Wedge;
     - factores de carga;
     - resistencias de apoyo.

2. `calcular_estabilidad_externa_desde_caso(caso)`
   - Calcula dinámicamente:
     - resultante vertical;
     - momentos;
     - x;
     - e;
     - B';
     - q;
     - resistencia de apoyo;
     - resistencia a deslizamiento.

3. `tabla_comparacion_pdf()`
   - Compara los resultados dinámicos calculados contra los resultados publicados
     en el PDF.

Así, el programa ya no fuerza `x`, `e`, `B'`, `q` ni `R` para que cuadren con el PDF;
los calcula a partir de los insumos del caso.


## Ubicación dinámica del dentellón y momentos

Se agregó una opción en la barra lateral para definir la ubicación del dentellón:

- `Bajo pantalla`
- `Según PDF / hacia talón`
- `Personalizada`

La posición del dentellón ya no afecta solo el dibujo. Ahora también entra en el
cálculo de momentos estabilizantes:

```text
M_dentellón = W_dentellón · x_dentellón
```

Por tanto, al mover el dentellón se recalculan:

- momento estabilizante total;
- momento neto;
- posición de la resultante `x`;
- excentricidad `e`;
- presiones `qmax` y `qmin`;
- revisión de contacto y estabilidad asociada.

También se agregó una tabla específica de `Momentos estabilizantes y desestabilizantes`
dentro de las pestañas de zapata y dentellón.


## Corrección AttributeError tabla_momentos_estabilidad

Se corrigió el error:

```text
AttributeError: module 'funciones_muro' has no attribute 'tabla_momentos_estabilidad'
```

La función ahora está garantizada dentro de `funciones_muro.py` y `app.py` verifica
su existencia antes de llamarla. Además, la tabla funciona aunque el dentellón esté
desactivado, usando momento cero para ese componente.


## Corrección del armado del dentellón

Se corrigió el criterio de armado del dentellón.

Antes la app revisaba erróneamente una longitud de desarrollo vertical usando:

```text
profundidad del dentellón - recubrimiento
```

Eso no corresponde cuando el dentellón se detalla como viga corrida. En ese caso:

- las barras principales son **longitudinales**, acostadas a lo largo del muro;
- los elementos transversales son **estribos cerrados**;
- la longitud de desarrollo longitudinal se revisa en extremos, empalmes o continuidad
  a lo largo del muro, no con la profundidad vertical del dentellón.

Nuevo criterio:

- Si el dentellón es pequeño, se considera monolítico con la zapata, como en el PDF.
- Si el dentellón es profundo, la app propone un detalle tipo viga corrida:
  - longitudinales `nØ`;
  - estribos cerrados `Ø @ separación`;
  - verificación de cortante;
  - sin fallo automático por `ld` vertical.


## Ajuste: dentellón pequeño sin armado independiente

Se ajustó la app para que cuando el dentellón sea pequeño no diseñe ni muestre
acero independiente del dentellón. En ese caso solo se considera como parte
monolítica de la zapata para:

- peso propio;
- momentos estabilizantes;
- resistencia pasiva;
- deslizamiento.

Solo cuando el dentellón supera el umbral de profundidad para ser tratado como
viga corrida, la app muestra:

- barras longitudinales;
- estribos cerrados;
- cortante;
- acero longitudinal requerido/provisto.


## Cambios solicitados

- Se eliminó la imagen de la pestaña **Dentellón y deslizamiento**.
- En esa pestaña ahora se muestra solo un **resumen del armado del dentellón**.
- En la última pestaña se reemplazó la imagen única anterior por un conjunto de
  detalles didácticos:
  - pantalla del muro: vista frontal y corte;
  - zapata: vista superior y corte;
  - dentellón: vista en corte.


## Corrección final: dentellón como llave de corte

Se corrigió el criterio de diseño local del dentellón:

- Ya no se diseña como cantiléver gobernado por flexión.
- Se trata como llave de corte.
- Si el dentellón es pequeño, se considera monolítico con la zapata y no se arma independientemente.
- Si el dentellón requiere armado independiente:
  - los longitudinales se calculan con acero mínimo tipo ACI;
  - los estribos se calculan por cortante;
  - la separación adoptada queda limitada a máximo 10 cm para el dentellón.
- La vista en corte de la pantalla ahora muestra dos capas de acero:
  - cara posterior hacia el relleno;
  - cara frontal.


## Fix AttributeError tabla_resumen_armado_dentellon

Se corrigió el error:

```text
AttributeError: module 'funciones_muro' has no attribute 'tabla_resumen_armado_dentellon'
```

La app ahora verifica que la función exista antes de llamarla y el archivo `funciones_muro.py`
incluye la función correspondiente. Para evitar errores en Streamlit Cloud, subir siempre juntos:

- `app.py`
- `funciones_muro.py`
- `README.md`
- `requirements.txt`

Luego reiniciar la app desde **Manage app → Reboot app**.


## Ajuste de detalle del dentellón

Se actualizó el gráfico del dentellón para que:
- el estribo cerrado suba hasta el top de la zapata;
- los aceros longitudinales también lleguen al top de la zapata;
- cuando la profundidad del dentellón sea mayor a 0.80 m, se muestren aceros distribuidos en ambas caras laterales.


## Ajuste visual del dentellón

Se eliminó el dibujo de barras laterales como puntos dentro del dentellón. Ahora:
- el acero mínimo longitudinal se muestra solo en los extremos de la sección;
- el estribo cerrado sube hasta el top de la zapata;
- si la profundidad del dentellón es mayor a 0.80 m, solo se muestra una nota indicando que debe incluirse acero adicional distribuido en las caras laterales para control de agrietamiento.


## Dashboard inicial de verificaciones

Se agregó en la primera pestaña un resumen tipo semáforo para que el usuario vea rápidamente si el diseño cumple o requiere revisión, sin entrar pestaña por pestaña.

El resumen incluye:

- presión admisible del suelo;
- flexión y cortante del fuste;
- estado global de zapata;
- cortante de puntera y talón;
- anclaje de puntera y talón;
- deslizamiento;
- armado del dentellón.

Si todo está correcto se muestra `DISEÑO CUMPLE`. Si alguna revisión falla se muestra `DISEÑO CON OBSERVACIONES`.


## Corrección altura de relleno

Se corrigió el comportamiento de `altura_relleno`.

Antes, si el relleno tenía pendiente, la línea de terreno se dibujaba siempre desde la corona del muro (`H`), por lo que cambiar `altura_relleno` no se veía claramente en el gráfico.

Ahora:

- la línea del relleno parte desde la altura real ingresada por el usuario;
- `calcular_y_terreno()` usa `altura_relleno` como elevación inicial;
- el Trial Wedge usa esa altura real;
- el diseño del fuste usa una altura activa de relleno para momentos y cortantes;
- el peso de suelo sobre el talón se calcula con un trapecio real según la línea de terreno;
- por tanto, al modificar la altura de relleno cambian PA, momentos, cortantes, presiones de contacto y armado.


## Corrección puntera cero

Se permitió ingresar `Longitud de puntera = 0.00 m`.

Antes la interfaz tenía `min_value=0.10`, por eso Streamlit impedía colocar cero. Esa restricción era una decisión de interfaz para evitar geometrías degeneradas, pero no es obligatorio que un muro tenga puntera frontal.

Con esta corrección:

- la puntera puede ser 0.00 m;
- se mantiene la validación de que no sea negativa;
- el talón debe seguir siendo positivo para que exista zapata hacia el relleno;
- los cálculos y gráficos se mantienen dinámicos.


## Revisión general solicitada

Se corrigieron/ajustaron los puntos observados:

- `altura_relleno` ahora modifica el gráfico y los cálculos.
- `puntera = 0.00 m` está permitida.
- La tabla de momentos separa explícitamente la zapata en puntera, zona bajo fuste y talón.
- El fuste ya no muestra `nan`; si la sección no alcanza se indica `No cumple`.
- El talón ya no se fuerza a momento cero: se usa carga neta firmada y se diseña con el valor absoluto del momento.
- Se quitaron las tarjetas de anclaje de puntera y talón del dashboard.
- La tabla de zapata ya no usa anclaje como estado global.
- En cortante de puntera/talón, si no existe sección crítica porque L≤d, se indica `No aplica` en lugar de mostrar un OK engañoso con Vu/φVc = 0.
- El valor de φVc del fuste depende del peralte efectivo d, por lo que cambia al modificar el espesor de base del fuste.


## Separaciones manuales de armado

Se agregaron controles para ingresar directamente la separación de barras:

- separación vertical del fuste;
- separación horizontal del fuste;
- separación de puntera;
- separación de talón.

La app ya no solo calcula una separación automática. Ahora usa la separación ingresada para obtener:

```text
As provisto = Ab * 100 / s
```

y compara `As provisto` contra `As requerido`.

En la pestaña Zapata también se agregaron métricas superiores para mostrar el armado:

- As puntera requerido;
- Ø puntera @ separación;
- As talón requerido;
- Ø talón @ separación.


## Separación única de zapata

Se reemplazaron los campos separados:

- Separación puntera;
- Separación talón.

Ahora existe un solo campo:

```text
Separación zapata [cm]
```

Ese valor se aplica simultáneamente al armado de la puntera y al armado del talón. Los diámetros pueden seguir siendo diferentes, pero la separación es común porque ambos forman parte de la misma zapata.


## Armado de zapata por cara superior e inferior

Se corrigió el criterio de entrada del armado de zapata.

Antes se manejaba como:

- diámetro puntera;
- diámetro talón;
- una separación común de zapata.

Ahora se maneja por **caras del elemento zapata**:

- diámetro acero inferior zapata;
- separación acero inferior zapata;
- diámetro acero superior zapata;
- separación acero superior zapata.

Internamente:
- la puntera se asocia al acero inferior;
- el talón se asocia al acero superior.

Esto permite que una cara tenga mayor acero que la otra cuando el momento crítico sea distinto.


## Corrección de NaN en acero inferior cuando no hay puntera

Se corrigió el criterio de diseño de la zapata:

- La app sigue calculando momentos de puntera y talón por separado.
- Pero el acero se diseña y reporta por cara:
  - cara inferior;
  - cara superior.
- La cara inferior toma el momento de puntera cuando existe. Si `puntera = 0`, no se coloca `NaN`; se asigna el acero mínimo por cara de la zapata.
- La cara superior toma el momento del talón.
- Así el elemento zapata siempre tiene acero inferior y superior, aunque una de las zonas no tenga voladizo geométrico.


## Zapata por signo del momento y relleno sobre puntera

Se actualizó el criterio de diseño de la zapata:

- Se siguen calculando puntera y talón por separado.
- Ya no se asigna ciegamente puntera=inferior y talón=superior.
- Ahora se calcula la carga neta y el signo del momento:
  - si la zona trabaja con tracción inferior, la demanda entra al acero inferior;
  - si trabaja con tracción superior, la demanda entra al acero superior.
- Se agregó la entrada `Altura de relleno sobre puntera [m]`.
- Ese relleno se incluye como carga vertical sobre la puntera y puede reducir o invertir el momento de la puntera.


## Corrección: momentos independientes en zapata

Se corrigió el diseño de zapata para no usar solo la carga neta.

Ahora se calculan momentos independientes por cada carga:

- Puntera:
  - reacción del suelo hacia arriba → acero inferior;
  - relleno sobre puntera hacia abajo → acero superior.
- Talón:
  - reacción del suelo hacia arriba → acero inferior;
  - relleno sobre talón hacia abajo → acero superior.

Luego se suma la demanda que tracciona la misma cara y se diseña:

- acero inferior de zapata;
- acero superior de zapata.

También se corrigieron las llamadas de la pestaña Zapata para que usen las separaciones manuales ingresadas por el usuario. Antes en esa pestaña se estaba usando la separación automática en algunas llamadas.


## Corrección final: momento neto con signo

Se corrigió la lógica de flexión de zapata:

- En puntera se combinan simultáneamente:
  - reacción del suelo hacia arriba;
  - peso propio de zapata hacia abajo;
  - relleno sobre puntera hacia abajo.
- En talón se combinan simultáneamente:
  - reacción del suelo hacia arriba;
  - peso propio de zapata hacia abajo;
  - relleno sobre talón hacia abajo.
- Para cada tramo se obtiene un momento resultante con signo.
- El signo determina si la tracción está en cara inferior o superior.
- Cada cara se diseña con el mayor momento que la tracciona.
- Si una cara no tiene momento de diseño, mantiene acero mínimo.


## Corrección TypeError en fuste por caras

Se corrigió el error de Streamlit en la pestaña Detalle general / Armado fuste.

Causa probable: `app.py` estaba llamando nuevos argumentos del fuste por caras, pero Streamlit podía seguir usando una versión antigua de `funciones_muro.py` en caché o no sincronizada.

Corrección aplicada:

- Se agregó una llamada robusta `calcular_fuste_app()`.
- La app filtra automáticamente los argumentos aceptados por la versión cargada de `funciones_muro.py`.
- Se agregaron alias de salida para evitar errores si todavía existe una versión anterior en caché.
- La función final del fuste también acepta `**kwargs` como protección adicional.

Recomendación: subir los 4 archivos juntos y ejecutar `Manage app → Reboot app`.


## Corrección RecursionError

Se corrigió el `RecursionError` causado por el wrapper `calcular_fuste_app`.

Causa: el reemplazo automático cambió accidentalmente la llamada interna del wrapper y quedó así:

```python
resultado = calcular_fuste_app(**kwargs_filtrados)
```

Eso hacía que la función se llamara a sí misma indefinidamente.

Corrección:

```python
resultado = fm.calcular_diseno_fuste_dinamico(**kwargs_filtrados)
```

Con esto el wrapper vuelve a llamar correctamente a la función del módulo `funciones_muro.py`.
