from dataclasses import dataclass
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


@dataclass
class DatosMuro:
    """
    Almacena todos los datos geométricos principales del muro de contención.

    Todas las dimensiones lineales se manejan internamente en metros.
    La pendiente del relleno se define como V:H, donde pendiente_v es la parte vertical
    y pendiente_h es la parte horizontal.
    """
    H: float
    B: float
    hz: float
    puntera: float
    t_base: float
    t_corona: float
    altura_relleno: float
    pendiente_h: float
    pendiente_v: float
    usar_llave: bool
    ancho_llave: float
    profundidad_llave: float
    pos_llave: float


def validar_datos_muro(datos: DatosMuro) -> list[str]:
    """
    Revisa que la geometría ingresada sea coherente antes de dibujar el muro.

    Devuelve una lista de errores. Si la lista queda vacía, significa que la geometría
    puede graficarse sin inconsistencias básicas.
    """
    errores = []

    talon = datos.B - datos.puntera - datos.t_base

    if datos.H <= 0:
        errores.append("La altura del fuste debe ser mayor que cero.")

    if datos.B <= 0:
        errores.append("El ancho total de zapata debe ser mayor que cero.")

    if datos.hz <= 0:
        errores.append("El espesor de zapata debe ser mayor que cero.")

    if datos.t_base <= 0:
        errores.append("El espesor del fuste en la base debe ser mayor que cero.")

    if datos.t_corona <= 0:
        errores.append("El espesor del fuste en la corona debe ser mayor que cero.")

    if datos.t_corona > datos.t_base:
        errores.append("El espesor de corona no debería ser mayor que el espesor de base.")

    if datos.puntera <= 0:
        errores.append("La puntera debe ser mayor que cero.")

    if talon <= 0:
        errores.append(
            "La suma puntera + espesor del fuste en la base no puede superar el ancho total de zapata."
        )

    if datos.altura_relleno < 0:
        errores.append("La altura de relleno no puede ser negativa.")

    if datos.pendiente_h <= 0:
        errores.append("La componente horizontal de la pendiente debe ser mayor que cero.")

    if datos.usar_llave:
        borde_izq_llave = datos.pos_llave - datos.ancho_llave / 2
        borde_der_llave = datos.pos_llave + datos.ancho_llave / 2

        if datos.ancho_llave <= 0:
            errores.append("El ancho de la llave debe ser mayor que cero.")

        if datos.profundidad_llave <= 0:
            errores.append("La profundidad de la llave debe ser mayor que cero.")

        if borde_izq_llave < 0 or borde_der_llave > datos.B:
            errores.append("La llave debe quedar dentro del ancho total de la zapata.")

    return errores


def calcular_talon(datos: DatosMuro) -> float:
    """
    Calcula la longitud del talón de la zapata.

    El talón es la parte de la cimentación ubicada detrás del fuste.
    Se obtiene restando al ancho total de zapata la puntera y el espesor basal del fuste.
    """
    return datos.B - datos.puntera - datos.t_base


def generar_puntos_muro(datos: DatosMuro) -> dict:
    """
    Genera las coordenadas principales del muro para graficarlo.

    El sistema de coordenadas se toma así:
    - x = 0 en el borde frontal de la zapata.
    - y = 0 en la cara superior de la zapata.
    - La zapata se dibuja hacia abajo hasta y = -hz.
    - El fuste crece hacia arriba desde y = 0 hasta y = H.
    """
    x_frente_fuste = datos.puntera
    x_dorso_fuste_base = datos.puntera + datos.t_base
    x_dorso_fuste_corona = datos.puntera + datos.t_corona

    zapata = [
        (0, 0),
        (datos.B, 0),
        (datos.B, -datos.hz),
        (0, -datos.hz),
    ]

    fuste = [
        (x_frente_fuste, 0),
        (x_dorso_fuste_base, 0),
        (x_dorso_fuste_corona, datos.H),
        (x_frente_fuste, datos.H),
    ]

    geometria = {
        "zapata": zapata,
        "fuste": fuste,
        "x_frente_fuste": x_frente_fuste,
        "x_dorso_fuste_base": x_dorso_fuste_base,
        "x_dorso_fuste_corona": x_dorso_fuste_corona,
    }

    if datos.usar_llave:
        x1 = datos.pos_llave - datos.ancho_llave / 2
        x2 = datos.pos_llave + datos.ancho_llave / 2

        llave = [
            (x1, -datos.hz),
            (x2, -datos.hz),
            (x2, -datos.hz - datos.profundidad_llave),
            (x1, -datos.hz - datos.profundidad_llave),
        ]

        geometria["llave"] = llave

    return geometria


def calcular_linea_relleno(datos: DatosMuro, geometria: dict) -> list[tuple[float, float]]:
    """
    Calcula la línea superior del relleno detrás del muro.

    Si pendiente_v = 0, el relleno es horizontal.
    Si pendiente_v > 0, se dibuja una pendiente ascendente V:H desde la parte posterior
    del fuste hasta alcanzar la altura de relleno definida.
    """
    x_inicio = geometria["x_dorso_fuste_corona"]
    y_inicio = datos.H

    if datos.pendiente_v == 0:
        x_fin = datos.B + max(datos.B * 0.60, 1.00)
        y_fin = datos.altura_relleno
    else:
        pendiente = datos.pendiente_v / datos.pendiente_h
        delta_y = max(datos.altura_relleno - y_inicio, 0.0)
        delta_x = delta_y / pendiente if pendiente > 0 else 0.0
        x_fin = x_inicio + max(delta_x, datos.B * 0.60)
        y_fin = y_inicio + pendiente * (x_fin - x_inicio)

    return [(x_inicio, y_inicio), (x_fin, y_fin)]


def dibujar_poligono(ax, puntos: list[tuple[float, float]], etiqueta: str):
    """
    Dibuja un polígono cerrado en el eje de Matplotlib.

    Se usa para representar partes sólidas del muro: zapata, fuste y llave.
    """
    poligono = Polygon(
        puntos,
        closed=True,
        fill=False,
        linewidth=2.2,
        label=etiqueta
    )
    ax.add_patch(poligono)


def dibujar_cotas_principales(ax, datos: DatosMuro, geometria: dict | None = None, tamano_texto: int = 8):
    """
    Dibuja las cotas principales del muro.

    Las cotas inferiores se separan en distintos niveles:
    - puntera y talón quedan en un primer nivel;
    - el ancho total B queda en un segundo nivel más bajo.

    Para bajar o subir específicamente la flecha de B, modifica:
    - y_cota_total
    - y_texto_total
    """
    talon = calcular_talon(datos)

    # Cotas de puntera y talón.
    y_cota_puntera_talon = -datos.hz - 0.18
    y_texto_puntera_talon = -datos.hz - 0.26

    # Cota del ancho total B.
    # Para bajar más la flecha y el texto de B, aumenta estos valores: 1.35 y 1.48.
    y_cota_total = -datos.hz - 1.35
    y_texto_total = -datos.hz - 1.48

    # Cota vertical de altura del fuste H.
    ax.annotate(
        "",
        xy=(-0.25, 0),
        xytext=(-0.25, datos.H),
        arrowprops=dict(arrowstyle="<->", linewidth=1.0)
    )
    ax.text(
        -0.33,
        datos.H / 2,
        f"H = {datos.H:.2f} m",
        rotation=90,
        va="center",
        ha="right",
        fontsize=tamano_texto
    )

    # Cota horizontal de la puntera.
    ax.annotate(
        "",
        xy=(0, y_cota_puntera_talon),
        xytext=(datos.puntera, y_cota_puntera_talon),
        arrowprops=dict(arrowstyle="<->", linewidth=0.9)
    )
    ax.text(
        datos.puntera / 2,
        y_texto_puntera_talon,
        f"Puntera = {datos.puntera:.2f} m",
        ha="center",
        va="top",
        fontsize=tamano_texto
    )

    # Cota horizontal del talón.
    x_ini_talon = datos.puntera + datos.t_base
    ax.annotate(
        "",
        xy=(x_ini_talon, y_cota_puntera_talon),
        xytext=(datos.B, y_cota_puntera_talon),
        arrowprops=dict(arrowstyle="<->", linewidth=0.9)
    )
    ax.text(
        x_ini_talon + talon / 2,
        y_texto_puntera_talon,
        f"Talón = {talon:.2f} m",
        ha="center",
        va="top",
        fontsize=tamano_texto
    )

    # Cota horizontal del ancho total B. Está más abajo para evitar sobreposición.
    ax.annotate(
        "",
        xy=(0, y_cota_total),
        xytext=(datos.B, y_cota_total),
        arrowprops=dict(arrowstyle="<->", linewidth=1.0)
    )
    ax.text(
        datos.B / 2,
        y_texto_total,
        f"B = {datos.B:.2f} m",
        ha="center",
        va="top",
        fontsize=tamano_texto
    )

    # Cota vertical del espesor de zapata hz.
    ax.annotate(
        "",
        xy=(datos.B + 0.18, 0),
        xytext=(datos.B + 0.18, -datos.hz),
        arrowprops=dict(arrowstyle="<->", linewidth=0.9)
    )
    ax.text(
        datos.B + 0.25,
        -datos.hz / 2,
        f"hz = {datos.hz:.2f} m",
        rotation=90,
        va="center",
        ha="left",
        fontsize=tamano_texto
    )

def dibujar_muro(ax, datos: DatosMuro, geometria: dict, tamano_texto: int = 8):
    """
    Dibuja el muro completo en un eje de Matplotlib.

    Representa zapata, fuste, llave de corte opcional, línea de relleno y cotas
    principales. También ajusta escala, límites, grilla y proporción para que el
    dibujo sea legible dentro de Streamlit.
    """
    dibujar_poligono(ax, geometria["zapata"], "Zapata")
    dibujar_poligono(ax, geometria["fuste"], "Fuste")

    if datos.usar_llave and "llave" in geometria:
        dibujar_poligono(ax, geometria["llave"], "Llave de corte")

    linea_relleno = calcular_linea_relleno(datos, geometria)
    xs = [p[0] for p in linea_relleno]
    ys = [p[1] for p in linea_relleno]
    ax.plot(xs, ys, linewidth=2, label="Relleno")

    ax.plot(
        [0, datos.B],
        [0, 0],
        linestyle="--",
        linewidth=1,
        label="Nivel superior de zapata"
    )

    dibujar_cotas_principales(ax, datos, geometria, tamano_texto=tamano_texto)

    margen_x = max(datos.B * 0.25, 0.80)
    margen_y = max(datos.H * 0.20, 0.80)

    y_min = -datos.hz - (datos.profundidad_llave if datos.usar_llave else 0) - max(margen_y, 2.10)
    y_max = max(datos.H, datos.altura_relleno) + margen_y

    ax.set_xlim(-margen_x, datos.B + margen_x)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linestyle=":", linewidth=0.7)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title("Geometría del muro de contención")
    ax.legend(loc="upper right", fontsize=max(tamano_texto - 1, 7))


def resumen_geometria(datos: DatosMuro) -> pd.DataFrame:
    """
    Construye una tabla resumen con las dimensiones principales del muro.

    Esta tabla se muestra en Streamlit para que el usuario pueda verificar rápidamente
    los valores ingresados y las dimensiones derivadas, como el talón.
    """
    talon = calcular_talon(datos)

    filas = [
        ("Altura del fuste H", datos.H, "m"),
        ("Ancho total de zapata B", datos.B, "m"),
        ("Espesor de zapata hz", datos.hz, "m"),
        ("Puntera", datos.puntera, "m"),
        ("Talón calculado", talon, "m"),
        ("Espesor fuste base", datos.t_base, "m"),
        ("Espesor fuste corona", datos.t_corona, "m"),
        ("Altura de relleno", datos.altura_relleno, "m"),
        ("Pendiente relleno V:H", f"{datos.pendiente_v:.2f}:{datos.pendiente_h:.2f}", "-"),
    ]

    if datos.usar_llave:
        filas.extend([
            ("Ancho de llave", datos.ancho_llave, "m"),
            ("Profundidad de llave", datos.profundidad_llave, "m"),
            ("Posición eje de llave", datos.pos_llave, "m"),
        ])
    else:
        filas.append(("Llave de corte", "No incluida", "-"))

    return pd.DataFrame(filas, columns=["Parámetro", "Valor", "Unidad"])
