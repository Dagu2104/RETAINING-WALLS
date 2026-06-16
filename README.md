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
