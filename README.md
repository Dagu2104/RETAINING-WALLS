# Programa inicial para diseño de muro de contención

Este proyecto contiene una interfaz en Streamlit para ingresar la geometría y datos básicos de un muro de contención de hormigón armado.

## Unidades adoptadas

Se usan unidades comunes en Ecuador:

- Longitudes: `m`
- Capacidad admisible del suelo: `ton/m²`
- Cohesión: `ton/m²`
- Peso unitario del suelo: `ton/m³`
- Peso unitario del hormigón: `ton/m³`
- Resistencia del hormigón f'c: `kg/cm²`
- Fluencia del acero fy: `kg/cm²`

## Archivos

- `app.py`: interfaz principal de Streamlit.
- `funciones_muro.py`: funciones separadas para validación, generación de geometría, dibujo, resumen, conversiones y memoria Word.
- `requirements.txt`: librerías necesarias para ejecutar la app en local o en Streamlit Cloud.
- `README.md`: instrucciones de instalación y ejecución.

## Instalación local

```bash
pip install -r requirements.txt
```

## Ejecución local

```bash
streamlit run app.py
```

## Uso en Streamlit Cloud

Si subes el proyecto a GitHub y luego lo conectas con Streamlit Cloud, asegúrate de incluir el archivo:

```text
requirements.txt
```

Ese archivo instala automáticamente las librerías necesarias:

- `streamlit`
- `matplotlib`
- `pandas`
- `python-docx`

## Ajuste del tamaño del dibujo

En la barra lateral de la aplicación se agregó la sección:

```text
Visualización del dibujo
```

Desde ahí se puede modificar:

- `Ancho del dibujo en pantalla [px]`
- `Alto relativo de la figura`
- `Tamaño de texto de cotas`

Esto evita que el gráfico se vea demasiado grande en Streamlit Cloud.

## Ajuste de la posición de las cotas

La posición de las flechas y textos se controla en `funciones_muro.py`, dentro de la función:

```python
dibujar_cotas_principales(...)
```

Para bajar o subir la cota del ancho total de la zapata `B`, modifica:

```python
y_cota_total = -datos.hz - 0.90
y_texto_total = -datos.hz - 1.00
```

Mientras más grande sea el número que se resta, más abajo queda la cota.

## Alcance actual

Este primer módulo dibuja la geometría, organiza los datos de entrada y genera una memoria preliminar en Word.

Luego se pueden agregar módulos para:

- coeficiente activo Ka;
- empuje activo Pa;
- empuje sísmico;
- estabilidad por volcamiento;
- estabilidad por deslizamiento;
- presiones de contacto;
- diseño a flexión del fuste;
- diseño a cortante;
- diseño de puntera y talón;
- diseño de llave de corte;
- cuantías mínimas y detallado de acero;
- memoria de cálculo completa en Word con procedimiento paso a paso.


## Corrección de NameError

Si aparece un error relacionado con `tamano_texto_cotas`, significa que `app.py` está llamando a esa variable pero no existía el control en la barra lateral.

Esta versión ya incluye en `app.py`:

```python
tamano_texto_cotas = st.sidebar.slider(...)
```

y la llamada correcta:

```python
dibujar_muro(ax, datos, geometria, tamano_texto=tamano_texto_cotas)
```
