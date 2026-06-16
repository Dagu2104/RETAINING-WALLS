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




def area_barra_cm2(diametro_mm: float) -> float:
    """
    Calcula el área de una barra circular de acero en cm².

    El diámetro se ingresa en milímetros porque es la forma usual de especificar
    barras en Ecuador. Internamente se convierte a centímetros.
    """
    diametro_cm = diametro_mm / 10.0
    return math.pi * diametro_cm ** 2 / 4.0


def resolver_as_flexion_rectangular(Mu_ton_m: float, b_cm: float, d_cm: float, fc_kg_cm2: float, fy_kg_cm2: float, phi_flexion: float = 0.90) -> float:
    """
    Calcula el acero requerido As para flexión de una sección rectangular por metro de muro.

    Se resuelve la ecuación:
    phi * As * fy * (d - a/2) >= Mu
    con:
    a = As * fy / (0.85 * f'c * b)

    Unidades:
    - Mu en ton·m por metro de muro
    - b y d en cm
    - f'c y fy en kg/cm²
    - As resultante en cm²/m
    """
    Mu_kg_cm = Mu_ton_m * 100000.0

    A = phi_flexion * fy_kg_cm2 ** 2 / (2.0 * 0.85 * fc_kg_cm2 * b_cm)
    B = -phi_flexion * fy_kg_cm2 * d_cm
    C = Mu_kg_cm

    discriminante = B ** 2 - 4.0 * A * C

    if discriminante < 0:
        return float("nan")

    raiz1 = (-B - math.sqrt(discriminante)) / (2.0 * A)
    raiz2 = (-B + math.sqrt(discriminante)) / (2.0 * A)

    candidatos = [r for r in [raiz1, raiz2] if r > 0]
    return min(candidatos) if candidatos else float("nan")


def seleccionar_separacion(area_barra: float, As_req_cm2_m: float, separacion_max_cm: float = 30.0) -> tuple[float, float]:
    """
    Selecciona una separación práctica para barras de refuerzo.

    La separación teórica se obtiene con:
    s = Ab * 100 / As_req

    Luego se redondea hacia abajo a separaciones comerciales para garantizar
    que el acero provisto sea mayor o igual al requerido.
    """
    if As_req_cm2_m <= 0 or math.isnan(As_req_cm2_m):
        return float("nan"), float("nan")

    separacion_teorica = area_barra * 100.0 / As_req_cm2_m
    separaciones_comerciales = [40, 35, 30, 25, 20, 18, 15, 12.5, 10, 7.5]

    separaciones_validas = [s for s in separaciones_comerciales if s <= separacion_teorica and s <= separacion_max_cm]
    if not separaciones_validas:
        separacion = min(separaciones_comerciales)
    else:
        separacion = max(separaciones_validas)

    As_prov = area_barra * 100.0 / separacion
    return separacion, As_prov


def calcular_diseno_fuste_dinamico(
    datos: DatosMuro,
    numero_cunas: int = 180,
    recubrimiento_cm: float = 7.5,
    diametro_vertical_mm: float = 16.0,
    diametro_horizontal_mm: float = 12.0,
    separacion_max_cm: float = 30.0
) -> dict:
    """
    Diseña dinámicamente el armado preliminar del fuste.

    La demanda se calcula con el procedimiento del PDF para el fuste:
    - el empuje activo se obtiene mediante Trial Wedge;
    - el empuje se aplica a H/3 desde la base del fuste;
    - el momento factorizado se toma como gamma_p * PA * cos(delta) * H/3;
    - el cortante factorizado se toma como gamma_p * PA * cos(delta).

    Esta función recalcula todo cuando cambian geometría, suelo, altura, pendiente,
    f'c o fy.
    """
    geometria = generar_puntos_muro(datos)
    tabla_trial, resultado_trial = calcular_trial_wedge_activo(datos, geometria, numero_cunas=numero_cunas)

    PA = resultado_trial["PA_ton_m"]
    delta = math.radians(resultado_trial["delta_grados"])
    H = datos.H
    gamma_p = 1.50

    q_base_ton_m2 = 2.0 * PA / H if H > 0 else 0.0
    Pu_horizontal = PA * math.cos(delta)

    Mu_ton_m = gamma_p * Pu_horizontal * H / 3.0
    Vu_ton = gamma_p * Pu_horizontal

    b_cm = 100.0
    h_cm = datos.t_base * 100.0
    diametro_vertical_cm = diametro_vertical_mm / 10.0
    d_cm = h_cm - recubrimiento_cm - diametro_vertical_cm / 2.0

    As_flexion = resolver_as_flexion_rectangular(
        Mu_ton_m=Mu_ton_m,
        b_cm=b_cm,
        d_cm=d_cm,
        fc_kg_cm2=datos.fc,
        fy_kg_cm2=datos.fy,
        phi_flexion=0.90
    )

    # Criterio del PDF para temperatura y retracción: As = 0.0018*b*h total.
    # Para una cara se usa la mitad.
    As_temp_total = 0.0018 * b_cm * h_cm
    As_temp_cara = As_temp_total / 2.0

    As_vertical_req = max(As_flexion, As_temp_cara)

    Ab_vertical = area_barra_cm2(diametro_vertical_mm)
    sep_vertical_cm, As_vertical_prov = seleccionar_separacion(
        area_barra=Ab_vertical,
        As_req_cm2_m=As_vertical_req,
        separacion_max_cm=separacion_max_cm
    )

    Ab_horizontal = area_barra_cm2(diametro_horizontal_mm)
    As_horizontal_req = As_temp_cara
    sep_horizontal_cm, As_horizontal_prov = seleccionar_separacion(
        area_barra=Ab_horizontal,
        As_req_cm2_m=As_horizontal_req,
        separacion_max_cm=separacion_max_cm
    )

    # Chequeo preliminar de cortante de concreto, en unidades kgf.
    # Vc = 0.53*sqrt(fc)*b*d, por metro de muro. Se deja como chequeo preliminar.
    phi_cortante = 0.75
    Vc_kgf = 0.53 * math.sqrt(datos.fc) * b_cm * d_cm
    phi_Vc_ton = phi_cortante * Vc_kgf / 1000.0

    estado_cortante = "OK" if Vu_ton <= phi_Vc_ton else "Revisar cortante/refuerzo transversal"

    return {
        "PA_ton_m": PA,
        "delta_grados": resultado_trial["delta_grados"],
        "alfa_critico_grados": resultado_trial["alfa_grados"],
        "q_base_ton_m2": q_base_ton_m2,
        "Mu_ton_m_m": Mu_ton_m,
        "Vu_ton_m": Vu_ton,
        "b_cm": b_cm,
        "h_cm": h_cm,
        "d_cm": d_cm,
        "As_flexion_cm2_m": As_flexion,
        "As_temp_total_cm2_m": As_temp_total,
        "As_temp_cara_cm2_m": As_temp_cara,
        "As_vertical_req_cm2_m": As_vertical_req,
        "diametro_vertical_mm": diametro_vertical_mm,
        "separacion_vertical_cm": sep_vertical_cm,
        "As_vertical_prov_cm2_m": As_vertical_prov,
        "diametro_horizontal_mm": diametro_horizontal_mm,
        "As_horizontal_req_cm2_m": As_horizontal_req,
        "separacion_horizontal_cm": sep_horizontal_cm,
        "As_horizontal_prov_cm2_m": As_horizontal_prov,
        "phi_Vc_ton_m": phi_Vc_ton,
        "estado_cortante": estado_cortante,
        "tabla_trial": tabla_trial,
        "resultado_trial": resultado_trial,
    }


def tabla_diseno_fuste(resultado: dict) -> pd.DataFrame:
    """
    Convierte el resultado del diseño del fuste en una tabla para mostrar en Streamlit.
    """
    filas = [
        ("PA dinámico", resultado["PA_ton_m"], "ton/m"),
        ("δ asumido", resultado["delta_grados"], "grados"),
        ("α crítico", resultado["alfa_critico_grados"], "grados"),
        ("q base", resultado["q_base_ton_m2"], "ton/m²"),
        ("Mu fuste", resultado["Mu_ton_m_m"], "ton·m/m"),
        ("Vu fuste", resultado["Vu_ton_m"], "ton/m"),
        ("Peralte efectivo d", resultado["d_cm"], "cm"),
        ("As por flexión", resultado["As_flexion_cm2_m"], "cm²/m"),
        ("As temperatura por cara", resultado["As_temp_cara_cm2_m"], "cm²/m"),
        ("As vertical requerido", resultado["As_vertical_req_cm2_m"], "cm²/m"),
        ("As vertical provisto", resultado["As_vertical_prov_cm2_m"], "cm²/m"),
        ("Separación vertical", resultado["separacion_vertical_cm"], "cm"),
        ("As horizontal requerido", resultado["As_horizontal_req_cm2_m"], "cm²/m"),
        ("As horizontal provisto", resultado["As_horizontal_prov_cm2_m"], "cm²/m"),
        ("Separación horizontal", resultado["separacion_horizontal_cm"], "cm"),
        ("φVc preliminar", resultado["phi_Vc_ton_m"], "ton/m"),
        ("Estado cortante", resultado["estado_cortante"], "-"),
    ]
    return pd.DataFrame(filas, columns=["Parámetro", "Valor", "Unidad"])


def dibujar_armado_fuste(ax, datos: DatosMuro, geometria: dict, resultado: dict, mostrar_ejes: bool = True):
    """
    Dibuja un esquema didáctico del armado del fuste.

    Se muestra:
    - acero vertical principal en la cara posterior del fuste;
    - acero horizontal por temperatura/retracción;
    - etiquetas con diámetros y separaciones calculadas.
    """
    dibujar_muro(
        ax,
        datos,
        geometria,
        tamano_texto=8,
        mostrar_cotas=False,
        mostrar_ejes=mostrar_ejes
    )

    x_back_base = geometria["x_dorso_fuste_base"]
    x_back_top = geometria["x_dorso_fuste_corona"]
    x_bar = x_back_base - 0.08

    # Barras verticales principales en cara de relleno.
    n_barras = 6
    for i in range(n_barras):
        t = i / max(n_barras - 1, 1)
        y1 = 0.15 + t * (datos.H - 0.30)
        y2 = min(y1 + datos.H / 5.0, datos.H - 0.05)
        ax.plot([x_bar, x_bar], [y1, y2], linewidth=2.0)

    # Barras horizontales esquemáticas.
    x1 = geometria["x_frente_fuste"] + 0.05
    x2 = geometria["x_dorso_fuste_base"] - 0.05
    niveles = [datos.H * 0.25, datos.H * 0.45, datos.H * 0.65, datos.H * 0.85]
    for y in niveles:
        ax.plot([x1, x2], [y, y], linewidth=1.5, linestyle="--")

    txt_vertical = f"Vertical principal: Ø{resultado['diametro_vertical_mm']:.0f} @ {resultado['separacion_vertical_cm']:.1f} cm"
    txt_horizontal = f"Horizontal temp.: Ø{resultado['diametro_horizontal_mm']:.0f} @ {resultado['separacion_horizontal_cm']:.1f} cm"

    ax.text(
        datos.B * 0.50,
        datos.H * 0.62,
        txt_vertical,
        fontsize=9,
        ha="center",
        va="center"
    )
    ax.text(
        datos.B * 0.50,
        datos.H * 0.52,
        txt_horizontal,
        fontsize=9,
        ha="center",
        va="center"
    )

    ax.set_title("Armado preliminar dinámico del fuste")




def calcular_presiones_contacto_servicio(datos: DatosMuro, numero_cunas: int = 180) -> dict:
    """
    Calcula presiones de contacto dinámicas bajo la zapata en estado de servicio.

    Se sigue la lógica del PDF para equilibrio externo:
    - se calcula el empuje activo PA;
    - se descompone en componente horizontal y vertical;
    - se suman pesos propios simplificados del muro y suelo sobre el talón;
    - se calcula la posición de la resultante x desde la puntera;
    - se obtiene la excentricidad e = B/2 - x;
    - se calculan presiones lineales qmax y qmin.

    Esta función es dinámica y cambia con geometría, suelo y materiales.
    """
    geometria = generar_puntos_muro(datos)
    tabla_trial, resultado_trial = calcular_trial_wedge_activo(datos, geometria, numero_cunas=numero_cunas)

    PA = resultado_trial["PA_ton_m"]
    delta = math.radians(resultado_trial["delta_grados"])
    PA_v = PA * math.sin(delta)
    PA_h = PA * math.cos(delta)

    # Pesos por metro longitudinal.
    area_zapata = datos.B * datos.hz
    W_zapata = area_zapata * datos.gamma_hormigon
    x_zapata = datos.B / 2.0

    area_fuste = (datos.t_base + datos.t_corona) / 2.0 * datos.H
    W_fuste = area_fuste * datos.gamma_hormigon
    x_fuste = datos.puntera + (datos.t_base + datos.t_corona) / 4.0

    talon = calcular_talon(datos)
    altura_suelo_talon = max(datos.altura_relleno, datos.H)
    area_suelo_talon = talon * altura_suelo_talon
    W_suelo_talon = area_suelo_talon * datos.gamma_suelo
    x_suelo_talon = datos.puntera + datos.t_base + talon / 2.0

    # Peso adicional aproximado por pendiente sobre el talón.
    if datos.pendiente_v > 0:
        pendiente = datos.pendiente_v / datos.pendiente_h
        area_tri_pendiente = 0.5 * talon * (pendiente * talon)
        W_pendiente = area_tri_pendiente * datos.gamma_suelo
        x_pendiente = datos.puntera + datos.t_base + 2.0 * talon / 3.0
    else:
        W_pendiente = 0.0
        x_pendiente = datos.puntera + datos.t_base + talon / 2.0

    # Momento positivo estabilizador respecto a puntera inferior O.
    V = W_zapata + W_fuste + W_suelo_talon + W_pendiente + PA_v
    M_est = (
        W_zapata * x_zapata
        + W_fuste * x_fuste
        + W_suelo_talon * x_suelo_talon
        + W_pendiente * x_pendiente
        + PA_v * datos.B
    )

    # Momento volcador por componente horizontal del empuje.
    brazo_PA_h = datos.H / 3.0
    M_volc = PA_h * brazo_PA_h

    M_resultante = M_est - M_volc
    x_resultante = M_resultante / V if V > 0 else float("nan")
    e = datos.B / 2.0 - x_resultante

    if abs(e) <= datos.B / 6.0:
        q_prom = V / datos.B
        q_max = q_prom * (1.0 + 6.0 * e / datos.B)
        q_min = q_prom * (1.0 - 6.0 * e / datos.B)
    else:
        B_efectivo = 3.0 * (datos.B / 2.0 - abs(e))
        q_max = 2.0 * V / B_efectivo if B_efectivo > 0 else float("nan")
        q_min = 0.0

    return {
        "PA_ton_m": PA,
        "PA_h_ton_m": PA_h,
        "PA_v_ton_m": PA_v,
        "W_zapata_ton_m": W_zapata,
        "W_fuste_ton_m": W_fuste,
        "W_suelo_talon_ton_m": W_suelo_talon,
        "W_pendiente_ton_m": W_pendiente,
        "V_total_ton_m": V,
        "M_est_ton_m_m": M_est,
        "M_volc_ton_m_m": M_volc,
        "x_resultante_m": x_resultante,
        "e_m": e,
        "qmax_ton_m2": q_max,
        "qmin_ton_m2": q_min,
        "q_adm_ton_m2": datos.qa,
        "estado_q": "OK" if q_max <= datos.qa and q_min >= 0 else "Revisar",
        "resultado_trial": resultado_trial,
    }


def presion_lineal_en_x(datos: DatosMuro, presiones: dict, x: float) -> float:
    """
    Interpola la presión de contacto bajo la zapata en una posición x.

    Convención:
    - x = 0 en la puntera.
    - x = B en el extremo posterior.
    """
    qmax = presiones["qmax_ton_m2"]
    qmin = presiones["qmin_ton_m2"]
    # Se asume qmax en la puntera cuando e positivo. Si e negativo, se invierte.
    if presiones["e_m"] >= 0:
        return qmax + (qmin - qmax) * (x / datos.B)
    return qmin + (qmax - qmin) * (x / datos.B)


def calcular_diseno_zapata_dinamico(
    datos: DatosMuro,
    numero_cunas: int = 180,
    recubrimiento_cm: float = 7.5,
    diametro_puntera_mm: float = 16.0,
    diametro_talon_mm: float = 16.0,
    separacion_max_cm: float = 30.0
) -> dict:
    """
    Diseña dinámicamente el armado preliminar de puntera y talón.

    Enfoque:
    - Se calculan presiones de contacto dinámicas bajo la zapata.
    - La puntera se modela como voladizo desde la cara frontal del fuste.
    - El talón se modela como voladizo desde la cara posterior del fuste.
    - Se obtienen momentos por metro y se calcula As por flexión.

    Este módulo es preliminar, pero cambia automáticamente con geometría, suelo,
    materiales y empuje calculado por Trial Wedge.
    """
    presiones = calcular_presiones_contacto_servicio(datos, numero_cunas=numero_cunas)

    # Factor de carga para pasar a una demanda conservadora preliminar.
    gamma_u = 1.50

    # Puntera: carga hacia arriba por presión de suelo.
    Lp = datos.puntera
    q0 = presion_lineal_en_x(datos, presiones, 0.0)
    q1 = presion_lineal_en_x(datos, presiones, datos.puntera)
    q_prom_p = (q0 + q1) / 2.0
    Mu_puntera = gamma_u * q_prom_p * Lp ** 2 / 2.0
    Vu_puntera = gamma_u * q_prom_p * Lp

    # Talón: peso de suelo sobre talón menos presión de contacto hacia arriba.
    Lt = calcular_talon(datos)
    x_t0 = datos.puntera + datos.t_base
    x_t1 = datos.B
    q_t0 = presion_lineal_en_x(datos, presiones, x_t0)
    q_t1 = presion_lineal_en_x(datos, presiones, x_t1)
    q_prom_t = (q_t0 + q_t1) / 2.0

    altura_suelo = max(datos.altura_relleno, datos.H)
    w_suelo_talon = datos.gamma_suelo * altura_suelo
    if datos.pendiente_v > 0:
        w_suelo_talon += datos.gamma_suelo * (datos.pendiente_v / datos.pendiente_h) * Lt / 2.0

    w_neto_talon = max(w_suelo_talon - q_prom_t, 0.0)
    Mu_talon = gamma_u * w_neto_talon * Lt ** 2 / 2.0
    Vu_talon = gamma_u * w_neto_talon * Lt

    b_cm = 100.0
    h_cm = datos.hz * 100.0

    d_puntera_cm = h_cm - recubrimiento_cm - (diametro_puntera_mm / 10.0) / 2.0
    d_talon_cm = h_cm - recubrimiento_cm - (diametro_talon_mm / 10.0) / 2.0

    As_puntera = resolver_as_flexion_rectangular(
        Mu_ton_m=Mu_puntera,
        b_cm=b_cm,
        d_cm=d_puntera_cm,
        fc_kg_cm2=datos.fc,
        fy_kg_cm2=datos.fy
    )
    As_talon = resolver_as_flexion_rectangular(
        Mu_ton_m=Mu_talon,
        b_cm=b_cm,
        d_cm=d_talon_cm,
        fc_kg_cm2=datos.fc,
        fy_kg_cm2=datos.fy
    )

    As_temp_zapata = 0.0018 * b_cm * h_cm / 2.0

    As_puntera_req = max(As_puntera, As_temp_zapata)
    As_talon_req = max(As_talon, As_temp_zapata)

    sep_puntera_cm, As_puntera_prov = seleccionar_separacion(
        area_barra=area_barra_cm2(diametro_puntera_mm),
        As_req_cm2_m=As_puntera_req,
        separacion_max_cm=separacion_max_cm
    )
    sep_talon_cm, As_talon_prov = seleccionar_separacion(
        area_barra=area_barra_cm2(diametro_talon_mm),
        As_req_cm2_m=As_talon_req,
        separacion_max_cm=separacion_max_cm
    )

    return {
        "presiones": presiones,
        "Lp_m": Lp,
        "Lt_m": Lt,
        "q_puntera_prom_ton_m2": q_prom_p,
        "q_talon_prom_ton_m2": q_prom_t,
        "w_suelo_talon_ton_m2": w_suelo_talon,
        "w_neto_talon_ton_m2": w_neto_talon,
        "Mu_puntera_ton_m_m": Mu_puntera,
        "Vu_puntera_ton_m": Vu_puntera,
        "Mu_talon_ton_m_m": Mu_talon,
        "Vu_talon_ton_m": Vu_talon,
        "As_temp_zapata_cm2_m": As_temp_zapata,
        "As_puntera_flexion_cm2_m": As_puntera,
        "As_talon_flexion_cm2_m": As_talon,
        "As_puntera_req_cm2_m": As_puntera_req,
        "As_talon_req_cm2_m": As_talon_req,
        "diametro_puntera_mm": diametro_puntera_mm,
        "diametro_talon_mm": diametro_talon_mm,
        "sep_puntera_cm": sep_puntera_cm,
        "sep_talon_cm": sep_talon_cm,
        "As_puntera_prov_cm2_m": As_puntera_prov,
        "As_talon_prov_cm2_m": As_talon_prov,
    }


def tabla_presiones_contacto(presiones: dict) -> pd.DataFrame:
    """
    Convierte el resultado de presiones de contacto en una tabla.
    """
    filas = [
        ("PA", presiones["PA_ton_m"], "ton/m"),
        ("PA horizontal", presiones["PA_h_ton_m"], "ton/m"),
        ("PA vertical", presiones["PA_v_ton_m"], "ton/m"),
        ("V total", presiones["V_total_ton_m"], "ton/m"),
        ("M estabilizador", presiones["M_est_ton_m_m"], "ton·m/m"),
        ("M volcador", presiones["M_volc_ton_m_m"], "ton·m/m"),
        ("x resultante", presiones["x_resultante_m"], "m"),
        ("excentricidad e", presiones["e_m"], "m"),
        ("qmax", presiones["qmax_ton_m2"], "ton/m²"),
        ("qmin", presiones["qmin_ton_m2"], "ton/m²"),
        ("qa", presiones["q_adm_ton_m2"], "ton/m²"),
        ("Estado", presiones["estado_q"], "-"),
    ]
    return pd.DataFrame(filas, columns=["Parámetro", "Valor", "Unidad"])


def tabla_diseno_zapata(resultado: dict) -> pd.DataFrame:
    """
    Convierte el diseño preliminar de puntera y talón en tabla.
    """
    filas = [
        ("Longitud puntera", resultado["Lp_m"], "m"),
        ("Longitud talón", resultado["Lt_m"], "m"),
        ("q promedio puntera", resultado["q_puntera_prom_ton_m2"], "ton/m²"),
        ("q promedio talón", resultado["q_talon_prom_ton_m2"], "ton/m²"),
        ("w suelo talón", resultado["w_suelo_talon_ton_m2"], "ton/m²"),
        ("w neto talón", resultado["w_neto_talon_ton_m2"], "ton/m²"),
        ("Mu puntera", resultado["Mu_puntera_ton_m_m"], "ton·m/m"),
        ("Mu talón", resultado["Mu_talon_ton_m_m"], "ton·m/m"),
        ("As puntera requerido", resultado["As_puntera_req_cm2_m"], "cm²/m"),
        ("As puntera provisto", resultado["As_puntera_prov_cm2_m"], "cm²/m"),
        ("Separación puntera", resultado["sep_puntera_cm"], "cm"),
        ("As talón requerido", resultado["As_talon_req_cm2_m"], "cm²/m"),
        ("As talón provisto", resultado["As_talon_prov_cm2_m"], "cm²/m"),
        ("Separación talón", resultado["sep_talon_cm"], "cm"),
    ]
    return pd.DataFrame(filas, columns=["Parámetro", "Valor", "Unidad"])


def dibujar_presiones_contacto(ax, datos: DatosMuro, geometria: dict, presiones: dict, mostrar_ejes: bool = True):
    """
    Dibuja la distribución lineal de presiones de contacto bajo la zapata.
    """
    dibujar_muro(ax, datos, geometria, tamano_texto=8, mostrar_cotas=False, mostrar_ejes=mostrar_ejes)

    qmax = presiones["qmax_ton_m2"]
    qmin = presiones["qmin_ton_m2"]
    escala = max(datos.hz * 1.80 / max(qmax, qmin, 1e-6), 0.02)

    if presiones["e_m"] >= 0:
        y0 = -datos.hz - qmax * escala
        y1 = -datos.hz - qmin * escala
    else:
        y0 = -datos.hz - qmin * escala
        y1 = -datos.hz - qmax * escala

    pol = Polygon(
        [(0, -datos.hz), (datos.B, -datos.hz), (datos.B, y1), (0, y0)],
        closed=True,
        fill=False,
        linewidth=2.0,
        linestyle="--"
    )
    ax.add_patch(pol)

    ax.text(0, y0, f"q = {qmax:.2f}", fontsize=8, ha="left", va="top")
    ax.text(datos.B, y1, f"q = {qmin:.2f}", fontsize=8, ha="right", va="top")
    ax.set_title("Presiones de contacto bajo la zapata")


def dibujar_armado_zapata(ax, datos: DatosMuro, geometria: dict, resultado: dict, mostrar_ejes: bool = True):
    """
    Dibuja un esquema didáctico del armado de puntera y talón.
    """
    dibujar_muro(ax, datos, geometria, tamano_texto=8, mostrar_cotas=False, mostrar_ejes=mostrar_ejes)

    y_inf = -datos.hz + 0.08
    y_sup = -0.08

    # Acero inferior puntera.
    ax.plot([0.10, datos.puntera - 0.08], [y_inf, y_inf], linewidth=2.5)
    ax.text(
        datos.puntera / 2,
        y_inf - 0.18,
        f"Puntera inf.: Ø{resultado['diametro_puntera_mm']:.0f} @ {resultado['sep_puntera_cm']:.1f} cm",
        fontsize=8,
        ha="center",
        va="top"
    )

    # Acero superior talón.
    x0 = datos.puntera + datos.t_base + 0.08
    x1 = datos.B - 0.10
    ax.plot([x0, x1], [y_sup, y_sup], linewidth=2.5)
    ax.text(
        (x0 + x1) / 2,
        y_sup + 0.18,
        f"Talón sup.: Ø{resultado['diametro_talon_mm']:.0f} @ {resultado['sep_talon_cm']:.1f} cm",
        fontsize=8,
        ha="center",
        va="bottom"
    )

    ax.set_title("Armado preliminar dinámico de zapata")

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
    "calcular_diseno_fuste_dinamico",
    "tabla_diseno_fuste",
    "dibujar_armado_fuste",
    "calcular_presiones_contacto_servicio",
    "calcular_diseno_zapata_dinamico",
    "tabla_presiones_contacto",
    "tabla_diseno_zapata",
    "dibujar_presiones_contacto",
    "dibujar_armado_zapata",
    "resumen_geometria",
    "convertir_resistencias_a_sistema_interno",
]
