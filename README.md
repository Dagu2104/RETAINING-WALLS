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
