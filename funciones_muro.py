from dataclasses import dataclass
from io import BytesIO
from datetime import datetime
import math

import pandas as pd
from matplotlib.patches import Polygon, FancyArrowPatch
from docx import Document


FT_A_M = 0.3048
KIP_A_TON = 0.45359237
KSF_A_TON_M2 = 4.882427636


@dataclass
class DatosMuro:
    """
    Almacena los datos geométricos, geotécnicos y de materiales del muro.

    Unidades de entrada:
    - Longitudes: m
    - Capacidad admisible del suelo qa: ton/m²
    - Peso unitario del suelo y hormigón: ton/m³
    - Cohesión del suelo: ton/m²
    - Resistencia del hormigón f'c: kg/cm²
    - Fluencia del acero fy: kg/cm²
    - Ángulo de fricción interna: grados
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
    qa: float
    gamma_suelo: float
    phi: float
    cohesion: float
    mu: float
    fc: float
    fy: float
    gamma_hormigon: float


def validar_datos_muro(datos: DatosMuro) -> list[str]:
    """
    Revisa que los datos ingresados sean geométrica y físicamente coherentes.
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
        errores.append("La suma puntera + espesor del fuste en la base no puede superar el ancho total de zapata.")
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

    if datos.qa <= 0:
        errores.append("La capacidad admisible del suelo qa debe ser mayor que cero.")
    if datos.gamma_suelo <= 0:
        errores.append("El peso unitario del suelo debe ser mayor que cero.")
    if datos.gamma_hormigon <= 0:
        errores.append("El peso unitario del hormigón debe ser mayor que cero.")
    if datos.fc <= 0:
        errores.append("La resistencia del hormigón f'c debe ser mayor que cero.")
    if datos.fy <= 0:
        errores.append("La fluencia del acero fy debe ser mayor que cero.")
    if datos.phi < 0 or datos.phi > 50:
        errores.append("El ángulo de fricción interna debería estar entre 0° y 50°.")
    if datos.cohesion < 0:
        errores.append("La cohesión no puede ser negativa.")
    if datos.mu <= 0:
        errores.append("El coeficiente de fricción debe ser mayor que cero.")

    return errores


def calcular_talon(datos: DatosMuro) -> float:
    """
    Calcula la longitud del talón de la zapata en metros.
    """
    return datos.B - datos.puntera - datos.t_base


def generar_puntos_muro(datos: DatosMuro) -> dict:
    """
    Genera las coordenadas principales del muro para graficarlo.
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
        geometria["llave"] = [
            (x1, -datos.hz),
            (x2, -datos.hz),
            (x2, -datos.hz - datos.profundidad_llave),
            (x1, -datos.hz - datos.profundidad_llave),
        ]

    return geometria


def calcular_linea_relleno(datos: DatosMuro, geometria: dict) -> list[tuple[float, float]]:
    """
    Calcula la línea superior del relleno detrás del muro.
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
    """
    poligono = Polygon(
        puntos,
        closed=True,
        fill=False,
        linewidth=2.2,
        label=etiqueta
    )
    ax.add_patch(poligono)


def dibujar_cotas_principales(ax, datos: DatosMuro, tamano_texto: int = 8):
    """
    Dibuja cotas principales del muro.
    """
    talon = calcular_talon(datos)

    y_cota_puntera_talon = -datos.hz - 0.18
    y_texto_puntera_talon = -datos.hz - 0.26

    y_cota_total = -datos.hz - 1.35
    y_texto_total = -datos.hz - 1.48

    ax.annotate(
        "",
        xy=(-0.25, 0),
        xytext=(-0.25, datos.H),
        arrowprops=dict(arrowstyle="<->", linewidth=1.0)
    )
    ax.text(-0.33, datos.H / 2, f"H = {datos.H:.2f} m", rotation=90, va="center", ha="right", fontsize=tamano_texto)

    ax.annotate(
        "",
        xy=(0, y_cota_puntera_talon),
        xytext=(datos.puntera, y_cota_puntera_talon),
        arrowprops=dict(arrowstyle="<->", linewidth=0.9)
    )
    ax.text(datos.puntera / 2, y_texto_puntera_talon, f"Puntera = {datos.puntera:.2f} m", ha="center", va="top", fontsize=tamano_texto)

    x_ini_talon = datos.puntera + datos.t_base
    ax.annotate(
        "",
        xy=(x_ini_talon, y_cota_puntera_talon),
        xytext=(datos.B, y_cota_puntera_talon),
        arrowprops=dict(arrowstyle="<->", linewidth=0.9)
    )
    ax.text(x_ini_talon + talon / 2, y_texto_puntera_talon, f"Talón = {talon:.2f} m", ha="center", va="top", fontsize=tamano_texto)

    ax.annotate(
        "",
        xy=(0, y_cota_total),
        xytext=(datos.B, y_cota_total),
        arrowprops=dict(arrowstyle="<->", linewidth=1.0)
    )
    ax.text(datos.B / 2, y_texto_total, f"B = {datos.B:.2f} m", ha="center", va="top", fontsize=tamano_texto)

    ax.annotate(
        "",
        xy=(datos.B + 0.18, 0),
        xytext=(datos.B + 0.18, -datos.hz),
        arrowprops=dict(arrowstyle="<->", linewidth=0.9)
    )
    ax.text(datos.B + 0.25, -datos.hz / 2, f"hz = {datos.hz:.2f} m", rotation=90, va="center", ha="left", fontsize=tamano_texto)


def configurar_ejes_muro(ax, datos: DatosMuro, mostrar_ejes: bool = True):
    """
    Configura límites, escala y apariencia del gráfico del muro.
    """
    margen_x = max(datos.B * 0.25, 0.80)
    margen_y = max(datos.H * 0.20, 0.80)

    y_min = -datos.hz - (datos.profundidad_llave if datos.usar_llave else 0) - max(margen_y, 2.10)
    y_max = max(datos.H, datos.altura_relleno) + margen_y

    ax.set_xlim(-margen_x, datos.B + margen_x)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal", adjustable="box")

    if mostrar_ejes:
        ax.grid(True, linestyle=":", linewidth=0.7)
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
    else:
        ax.axis("off")


def dibujar_muro(
    ax,
    datos: DatosMuro,
    geometria: dict,
    tamano_texto: int = 8,
    mostrar_cotas: bool = True,
    mostrar_ejes: bool = True
):
    """
    Dibuja el muro completo sin leyenda.
    """
    dibujar_poligono(ax, geometria["zapata"], "Zapata")
    dibujar_poligono(ax, geometria["fuste"], "Fuste")

    if datos.usar_llave and "llave" in geometria:
        dibujar_poligono(ax, geometria["llave"], "Llave de corte")

    linea_relleno = calcular_linea_relleno(datos, geometria)
    xs = [p[0] for p in linea_relleno]
    ys = [p[1] for p in linea_relleno]
    ax.plot(xs, ys, linewidth=2)

    ax.plot([0, datos.B], [0, 0], linestyle="--", linewidth=1)

    if mostrar_cotas:
        dibujar_cotas_principales(ax, datos, tamano_texto=tamano_texto)

    ax.set_title("Geometría del muro de contención")
    configurar_ejes_muro(ax, datos, mostrar_ejes=mostrar_ejes)


def flecha(ax, inicio, fin, texto, dx=0.0, dy=0.0, tamano=9):
    """
    Dibuja una flecha con etiqueta.
    """
    arrow = FancyArrowPatch(
        inicio,
        fin,
        arrowstyle="->",
        mutation_scale=14,
        linewidth=1.8
    )
    ax.add_patch(arrow)
    ax.text(fin[0] + dx, fin[1] + dy, texto, fontsize=tamano, ha="center", va="center")


def dibujar_diagrama_fuerzas(ax, datos: DatosMuro, geometria: dict, mostrar_ejes: bool = True):
    """
    Dibuja un diagrama didáctico de las fuerzas principales del PDF:
    ΣW, khΣW, PA/PAE, PP/PPE, V y Rf.

    El objetivo es visual, no reemplaza el cálculo numérico.
    """
    dibujar_muro(
        ax,
        datos,
        geometria,
        tamano_texto=8,
        mostrar_cotas=False,
        mostrar_ejes=mostrar_ejes
    )

    x_centro = datos.B * 0.58
    y_centro = datos.H * 0.45

    # Peso total.
    flecha(ax, (x_centro, y_centro + 0.90), (x_centro, y_centro + 0.25), "ΣW", dx=0.18, dy=0.05)

    # Fuerza sísmica inercial.
    flecha(ax, (x_centro + 0.80, y_centro + 0.80), (x_centro + 0.20, y_centro + 0.80), "khΣW", dx=-0.20, dy=0.18)

    # Empuje activo.
    x_dorso = geometria["x_dorso_fuste_base"]
    flecha(
        ax,
        (datos.B + 0.65, datos.H * 0.38),
        (x_dorso + 0.08, datos.H * 0.32),
        "PA / PAE",
        dx=0.20,
        dy=0.25
    )

    # Empuje pasivo.
    flecha(
        ax,
        (-0.65, -datos.hz * 0.45),
        (0.05, -datos.hz * 0.45),
        "PP / PPE",
        dx=-0.10,
        dy=-0.25
    )

    # Reacción vertical.
    flecha(
        ax,
        (datos.B * 0.42, -datos.hz - 0.90),
        (datos.B * 0.42, -datos.hz - 0.15),
        "V",
        dx=0.15,
        dy=0.00
    )

    # Fricción en base.
    flecha(
        ax,
        (datos.B * 0.45, -datos.hz - 0.10),
        (datos.B * 0.70, -datos.hz - 0.10),
        "Rf",
        dx=0.20,
        dy=0.12
    )

    ax.set_title("Diagrama didáctico de fuerzas")


def convertir_resistencias_a_sistema_interno(datos: DatosMuro) -> pd.DataFrame:
    """
    Convierte resistencias y pesos a unidades alternativas útiles para cálculo.
    """
    fc_ton_m2 = datos.fc * 10.0
    fy_ton_m2 = datos.fy * 10.0
    qa_kg_cm2 = datos.qa / 10.0

    filas = [
        ("f'c", datos.fc, "kg/cm²", fc_ton_m2, "ton/m²"),
        ("fy", datos.fy, "kg/cm²", fy_ton_m2, "ton/m²"),
        ("qa", datos.qa, "ton/m²", qa_kg_cm2, "kg/cm²"),
        ("γ suelo", datos.gamma_suelo, "ton/m³", datos.gamma_suelo, "ton/m³"),
        ("γ hormigón", datos.gamma_hormigon, "ton/m³", datos.gamma_hormigon, "ton/m³"),
        ("c", datos.cohesion, "ton/m²", datos.cohesion, "ton/m²"),
    ]

    return pd.DataFrame(
        filas,
        columns=["Parámetro", "Valor ingresado", "Unidad ingresada", "Valor convertido", "Unidad convertida"]
    )


def resumen_geometria(datos: DatosMuro) -> pd.DataFrame:
    """
    Construye una tabla resumen con geometría, suelo y materiales.
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
        ("Capacidad admisible qa", datos.qa, "ton/m²"),
        ("Peso unitario del suelo γs", datos.gamma_suelo, "ton/m³"),
        ("Ángulo de fricción φ", datos.phi, "grados"),
        ("Cohesión c", datos.cohesion, "ton/m²"),
        ("Coeficiente de fricción μ", datos.mu, "-"),
        ("Resistencia hormigón f'c", datos.fc, "kg/cm²"),
        ("Fluencia acero fy", datos.fy, "kg/cm²"),
        ("Peso unitario hormigón γc", datos.gamma_hormigon, "ton/m³"),
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


def tabla_fuerzas_pdf() -> pd.DataFrame:
    """
    Devuelve la tabla base del PDF para el ejemplo de muro de contención.

    Valores tomados de las tablas 11.2.2-1, 11.2.2-2, 11.2.2-3,
    11.2.2-4 y 11.2.2-5 del ejemplo Caltrans.
    """
    filas = [
        ("ΣW", 50.01, "kip", "Peso total muro + suelo sobre zapata"),
        ("PA", 17.54, "kip", "Empuje activo estático por trial wedge"),
        ("δA", 9.74, "grados", "Ángulo de acción del empuje activo"),
        ("PAE", 31.56, "kip", "Empuje activo sísmico por trial wedge"),
        ("PP", 9.97, "kip", "Empuje pasivo estático"),
        ("PPE", 8.00, "kip", "Empuje pasivo sísmico"),
        ("kh", 0.28, "-", "Coeficiente sísmico usado"),
        ("B", 19.00, "ft", "Ancho de zapata del ejemplo"),
    ]
    return pd.DataFrame(filas, columns=["Parámetro", "Valor PDF", "Unidad", "Descripción"])


def calcular_verificacion_caltrans_pdf() -> dict:
    """
    Reproduce los resultados principales del ejemplo Caltrans para verificar el programa.

    Esta función usa directamente los valores reportados en el PDF:
    - pesos de las partes 1 a 8,
    - brazos de momento,
    - PA, PAE, δA,
    - kh,
    - PP y PPE,
    - anchos efectivos y resistencias de apoyo reportadas.
    """
    # Pesos y brazos de las partes 1 a 8, tabla 11.2.2-2 / 11.2.2-3.
    pesos = [3.23, 2.48, 7.12, 0.22, 1.82, 29.37, 1.32, 4.45]
    brazos_extremo = [5.97, 6.92, 9.50, 14.00, 7.42, 13.44, 2.75, 14.83]
    brazos_servicio = [5.97, 6.92, 9.50, 14.00, 7.42, 13.44, 2.75, 14.83]
    brazos_inercia = [14.00, 10.17, 1.25, 0.38, 17.17, 13.50, 3.50, 26.48]

    B = 19.0
    delta = math.radians(9.74)
    PA = 17.54
    PAE = 31.56
    kh = 0.28

    # Extreme event: tabla 11.2.2-2.
    w_sum = sum(pesos)
    pae_v = PAE * math.sin(delta)
    pae_h = PAE * math.cos(delta)

    m_pesos_ext = sum(w * a for w, a in zip(pesos, brazos_extremo))
    m_pae_v = pae_v * 19.0
    m_pae_h = -pae_h * 10.15
    m_inercia = -sum(kh * w * a for w, a in zip(pesos, brazos_inercia))

    V_ext = w_sum + pae_v
    M_const_ext = m_pesos_ext + m_pae_v + m_pae_h + m_inercia
    x_ext = M_const_ext / V_ext
    e_ext = B / 2 - x_ext
    Bp_ext = B - 2 * e_ext
    q_ext = V_ext / Bp_ext
    qr_ext = 0.8 * 33.22

    # Service: tabla 11.2.2-3.
    pa_v = PA * math.sin(delta)
    pa_h = PA * math.cos(delta)
    m_pesos_serv = sum(w * a for w, a in zip(pesos, brazos_servicio))
    M_const_serv = m_pesos_serv + pa_v * 19.0 - pa_h * 10.65
    V_serv = w_sum + pa_v
    x_serv = M_const_serv / V_serv
    e_serv = B / 2 - x_serv
    Bp_serv = B - 2 * e_serv
    q_gross_serv = V_serv / Bp_serv
    q_net_serv = q_gross_serv - 0.54

    # Strength Ia: tabla 11.2.2-4.
    factores_ia = [1.25, 1.25, 1.25, 1.25, 1.35, 1.35, 1.35, 1.35]
    cargas_ia = [w * f for w, f in zip(pesos, factores_ia)]
    M_ia = sum(c * a for c, a in zip(cargas_ia, brazos_extremo))
    V_ia = sum(cargas_ia) + 1.50 * pa_v
    M_ia = M_ia + 1.50 * pa_v * 19.0 - 1.50 * pa_h * 10.15
    x_ia = M_ia / V_ia
    Bp_ia = 2 * x_ia
    q_ia = V_ia / Bp_ia
    qr_ia = 0.55 * 57.78

    # Strength Ib: tabla 11.2.2-5.
    factores_ib = [0.90, 0.90, 0.90, 0.90, 1.00, 1.00, 1.00, 1.00]
    cargas_ib = [w * f for w, f in zip(pesos, factores_ib)]
    V_ib = sum(cargas_ib) + 1.50 * pa_v
    M_ib = sum(c * a for c, a in zip(cargas_ib, brazos_extremo)) + 1.50 * pa_v * 19.0 - 1.50 * pa_h * 10.15
    x_ib = M_ib / V_ib
    e_ib = B / 2 - x_ib
    Rf = V_ib * math.tan(math.radians(34.0))
    Rp = 0.50 * 9.97 * math.cos(math.radians(22.67))
    R_total = Rf + Rp
    Q_activo = 1.50 * PA * math.cos(delta)

    return {
        "Extreme Event": {
            "x_ft": x_ext,
            "x_pdf": 3.52,
            "e_ft": e_ext,
            "e_pdf": 5.98,
            "Bp_ft": Bp_ext,
            "Bp_pdf": 7.03,
            "q_ksf": q_ext,
            "q_pdf": 7.87,
            "qr_ksf": qr_ext,
            "qr_pdf": 26.58,
        },
        "Service": {
            "x_ft": x_serv,
            "x_pdf": 8.79,
            "e_ft": e_serv,
            "e_pdf": 0.70,
            "Bp_ft": Bp_serv,
            "Bp_pdf": 17.59,
            "qnet_ksf": q_net_serv,
            "qnet_pdf": 2.47,
        },
        "Strength Ia": {
            "x_ft": x_ia,
            "x_pdf": 8.50,
            "Bp_ft": Bp_ia,
            "Bp_pdf": 17.00,
            "q_ksf": q_ia,
            "q_pdf": 4.16,
            "qr_ksf": qr_ia,
            "qr_pdf": 31.78,
        },
        "Strength Ib": {
            "x_ft": x_ib,
            "x_pdf": 7.44,
            "e_ft": e_ib,
            "e_pdf": 2.06,
            "Q_kip": Q_activo,
            "Q_pdf": 25.94,
            "R_kip": R_total,
            "R_pdf": 40.50,
        }
    }


def tabla_comparacion_pdf(resultados: dict) -> pd.DataFrame:
    """
    Convierte el diccionario de verificación Caltrans en una tabla de comparación.
    """
    filas = []
    for estado, datos_estado in resultados.items():
        claves = sorted([k[:-4] for k in datos_estado if k.endswith("_pdf")])
        for clave in claves:
            calculado_key = clave
            pdf_key = f"{clave}_pdf"
            calculado = datos_estado.get(calculado_key)
            pdf = datos_estado.get(pdf_key)
            if calculado is None or pdf is None:
                continue
            diferencia = calculado - pdf
            filas.append((
                estado,
                clave,
                round(calculado, 3),
                round(pdf, 3),
                round(diferencia, 3),
                "OK" if abs(diferencia) <= max(0.05, abs(pdf) * 0.015) else "Revisar"
            ))

    return pd.DataFrame(filas, columns=["Estado límite", "Variable", "Calculado", "PDF", "Diferencia", "Estado"])




def area_poligono(puntos: list[tuple[float, float]]) -> float:
    """
    Calcula el área de un polígono mediante la fórmula del polígono o fórmula de Gauss.

    Se usa para obtener el área de cada cuña de suelo ensayada en el método Trial Wedge.
    El resultado se entrega en m² por metro de longitud del muro.
    """
    area = 0.0
    n = len(puntos)
    for i in range(n):
        x1, y1 = puntos[i]
        x2, y2 = puntos[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def calcular_y_terreno(datos: DatosMuro, geometria: dict, x: float) -> float:
    """
    Calcula la elevación del terreno de relleno para una coordenada horizontal x.

    El terreno se modela como una línea recta que parte desde la coronación posterior
    del fuste. Si pendiente_v = 0, el relleno es horizontal.
    """
    x0 = geometria["x_dorso_fuste_corona"]
    y0 = datos.H

    if datos.pendiente_v == 0:
        return datos.altura_relleno

    pendiente = datos.pendiente_v / datos.pendiente_h
    return y0 + pendiente * (x - x0)


def calcular_trial_wedge_activo(datos: DatosMuro, geometria: dict, numero_cunas: int = 180) -> tuple[pd.DataFrame, dict]:
    """
    Calcula el empuje activo estático mediante el método Trial Wedge.

    Procedimiento implementado según la lógica del PDF:
    1. Se asumen varias superficies de falla con diferentes ángulos alfa.
    2. Para cada superficie se define una cuña de suelo detrás del muro.
    3. Se calcula el peso W de la cuña.
    4. Se calcula el empuje P asociado a esa cuña.
    5. Se selecciona como PA la cuña que produce el mayor empuje.

    Alcance de esta primera versión:
    - suelo sin cohesión;
    - análisis estático;
    - terreno de relleno lineal;
    - cálculo por metro longitudinal de muro;
    - empuje aplicado sobre un plano vertical en el extremo del talón.

    La expresión de equilibrio usada es la forma clásica de cuña de Coulomb
    aplicada por tanteos. Para relleno irregular, el peso de la cuña se obtiene
    geométricamente.
    """
    phi = math.radians(datos.phi)

    # Plano vertical donde se evalúa el empuje activo: extremo posterior de la zapata.
    x_muro = datos.B
    y_base = -datos.hz
    y_superior = calcular_y_terreno(datos, geometria, x_muro)

    # Pendiente del relleno usada como dirección aproximada del empuje.
    beta = math.atan(datos.pendiente_v / datos.pendiente_h) if datos.pendiente_v > 0 else 0.0

    # Se evita ensayar ángulos menores al ángulo de fricción.
    alfa_min = max(math.degrees(phi) + 1.0, math.degrees(beta) + 2.0)
    alfa_max = 89.0

    filas = []
    mejor = {
        "PA_ton_m": 0.0,
        "alfa_grados": None,
        "delta_grados": math.degrees(beta),
        "peso_cuna_ton_m": 0.0,
        "area_cuna_m2": 0.0,
        "x_interseccion_m": None,
        "y_interseccion_m": None,
        "poligono_cuna": None,
    }

    for i in range(numero_cunas):
        alfa_g = alfa_min + (alfa_max - alfa_min) * i / max(numero_cunas - 1, 1)
        alfa = math.radians(alfa_g)

        tan_alfa = math.tan(alfa)
        tan_beta = math.tan(beta)

        # Intersección entre superficie de falla y terreno.
        denominador = tan_alfa - tan_beta
        if denominador <= 0:
            continue

        x_inter = x_muro + (y_superior - y_base) / denominador
        if x_inter <= x_muro:
            continue

        y_inter = y_base + tan_alfa * (x_inter - x_muro)

        poligono = [
            (x_muro, y_base),
            (x_muro, y_superior),
            (x_inter, y_inter),
        ]

        area = area_poligono(poligono)
        W = datos.gamma_suelo * area

        numerador = math.sin(alfa - phi)
        denominador_p = math.sin(math.pi / 2.0 + beta + phi - alfa)

        if denominador_p <= 0 or numerador <= 0:
            P = 0.0
        else:
            P = W * numerador / denominador_p

        filas.append({
            "α [grados]": alfa_g,
            "Área cuña [m²/m]": area,
            "W [ton/m]": W,
            "δ asumido [grados]": math.degrees(beta),
            "P [ton/m]": P,
            "x intersección [m]": x_inter,
            "y intersección [m]": y_inter,
        })

        if P > mejor["PA_ton_m"]:
            mejor = {
                "PA_ton_m": P,
                "alfa_grados": alfa_g,
                "delta_grados": math.degrees(beta),
                "peso_cuna_ton_m": W,
                "area_cuna_m2": area,
                "x_interseccion_m": x_inter,
                "y_interseccion_m": y_inter,
                "poligono_cuna": poligono,
            }

    return pd.DataFrame(filas), mejor


def dibujar_trial_wedge_critico(ax, datos: DatosMuro, geometria: dict, resultado_trial: dict, mostrar_ejes: bool = True):
    """
    Dibuja la cuña crítica obtenida con el método Trial Wedge.

    Se muestra la geometría del muro, la superficie del terreno y la superficie
    de falla que generó el mayor empuje PA.
    """
    dibujar_muro(
        ax,
        datos,
        geometria,
        tamano_texto=8,
        mostrar_cotas=False,
        mostrar_ejes=mostrar_ejes
    )

    poligono = resultado_trial.get("poligono_cuna")
    if poligono:
        cuna = Polygon(
            poligono,
            closed=True,
            fill=False,
            linewidth=2.0,
            linestyle="--"
        )
        ax.add_patch(cuna)

        x0, y0 = poligono[0]
        x2, y2 = poligono[2]
        ax.plot([x0, x2], [y0, y2], linewidth=2.0, linestyle="--")
        ax.text(
            (x0 + x2) / 2,
            (y0 + y2) / 2,
            f"α = {resultado_trial['alfa_grados']:.1f}°",
            fontsize=9,
            ha="center",
            va="bottom"
        )

    ax.set_title("Cuña crítica por Trial Wedge")


def graficar_curva_trial_wedge(ax, tabla_trial: pd.DataFrame):
    """
    Grafica la relación entre el ángulo de falla α y el empuje P.

    El máximo de esta curva corresponde al empuje activo PA adoptado.
    """
    ax.plot(tabla_trial["α [grados]"], tabla_trial["P [ton/m]"], linewidth=2)
    ax.set_xlabel("Ángulo de superficie de falla α [grados]")
    ax.set_ylabel("Empuje P [ton/m]")
    ax.set_title("Búsqueda de PA mediante Trial Wedge")
    ax.grid(True, linestyle=":", linewidth=0.7)

def agregar_tabla_dataframe(documento: Document, tabla: pd.DataFrame):
    """
    Inserta un DataFrame como tabla Word.
    """
    tabla_word = documento.add_table(rows=1, cols=len(tabla.columns))
    tabla_word.style = "Table Grid"

    encabezados = tabla_word.rows[0].cells
    for i, columna in enumerate(tabla.columns):
        encabezados[i].text = str(columna)

    for _, fila in tabla.iterrows():
        celdas = tabla_word.add_row().cells
        for i, valor in enumerate(fila):
            if isinstance(valor, float):
                celdas[i].text = f"{valor:.3f}"
            else:
                celdas[i].text = str(valor)


def generar_memoria_word(datos: DatosMuro, incluir_pdf: bool = True) -> bytes:
    """
    Genera una memoria preliminar de cálculo en formato Word.
    """
    documento = Document()

    documento.add_heading("Memoria de cálculo - Muro de contención de hormigón armado", level=0)
    documento.add_paragraph("Documento generado automáticamente desde la aplicación de diseño de muro de contención.")
    documento.add_paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    documento.add_heading("1. Unidades adoptadas", level=1)
    documento.add_paragraph("Longitudes: m")
    documento.add_paragraph("Capacidad admisible del suelo y cohesión: ton/m²")
    documento.add_paragraph("Pesos unitarios: ton/m³")
    documento.add_paragraph("Resistencia del hormigón f'c y fluencia del acero fy: kg/cm²")

    documento.add_heading("2. Datos de entrada", level=1)
    agregar_tabla_dataframe(documento, resumen_geometria(datos))

    documento.add_heading("3. Conversiones internas", level=1)
    agregar_tabla_dataframe(documento, convertir_resistencias_a_sistema_interno(datos))

    if incluir_pdf:
        documento.add_heading("4. Verificación con ejemplo Caltrans BDP 11.2", level=1)
        documento.add_paragraph(
            "Se incluye una tabla de comparación con los resultados principales del ejemplo de muro de contención "
            "de hormigón armado del PDF usado como base de cálculo."
        )
        agregar_tabla_dataframe(documento, tabla_comparacion_pdf(calcular_verificacion_caltrans_pdf()))

    documento.add_heading("5. Método Trial Wedge", level=1)
    documento.add_paragraph(
        "El método Trial Wedge ensaya varias superficies de falla. Para cada cuña se calcula "
        "su peso y el empuje correspondiente. El mayor valor se adopta como empuje activo PA."
    )

    documento.add_heading("6. Alcance actual", level=1)
    documento.add_paragraph(
        "Esta versión incorpora geometría, diagrama de fuerzas y verificación de estabilidad externa "
        "contra los resultados del ejemplo del PDF. En las siguientes etapas se ampliará el cálculo "
        "para diseño interno del fuste, zapata, puntera, talón y llave de corte."
    )

    buffer = BytesIO()
    documento.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# Lista explícita de nombres que app.py puede importar desde este módulo.
__all__ = [
    "DatosMuro",
    "validar_datos_muro",
    "generar_puntos_muro",
    "dibujar_muro",
    "dibujar_diagrama_fuerzas",
    "calcular_trial_wedge_activo",
    "dibujar_trial_wedge_critico",
    "graficar_curva_trial_wedge",
    "calcular_verificacion_caltrans_pdf",
    "tabla_comparacion_pdf",
    "tabla_fuerzas_pdf",
    "generar_memoria_word",
    "resumen_geometria",
    "convertir_resistencias_a_sistema_interno",
]
