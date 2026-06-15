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
- `funciones_muro.py`: funciones separadas para validación, generación de geometría, dibujo, resumen y conversiones.
- `README.md`: instrucciones de instalación y ejecución.

## Instalación

```bash
pip install streamlit matplotlib pandas
```

## Ejecución

```bash
streamlit run app.py
```

## Alcance actual

Este primer módulo solo dibuja la geometría y organiza los datos de entrada. Luego se pueden agregar módulos para:

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
- cuantías mínimas y detallado de acero.
```


## Ajuste del tamaño del dibujo

En la barra lateral de la aplicación se agregó la sección:

```text
Visualización del dibujo
```

Desde ahí se puede modificar:

- `Ancho del dibujo en pantalla [px]`
- `Alto relativo de la figura`
- `Tamaño de texto de cotas`

Esto evita que el gráfico se vea demasiado grande en Streamlit Cloud y reduce la sobreposición de los textos inferiores de puntera, talón y ancho total de zapata.
