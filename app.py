import streamlit as st
import matplotlib.pyplot as plt

from funciones_muro import (
    DatosMuro,
    validar_datos_muro,
    generar_puntos_muro,
    dibujar_muro,
    resumen_geometria,
)

st.set_page_config(
    page_title="Diseño de muro de contención",
    page_icon="🧱",
    layout="wide"
)

st.title("Diseño preliminar de muro de contención de hormigón armado")
st.caption("Módulo inicial: ingreso dinámico de geometría y dibujo del muro")

st.sidebar.header("Unidades")
unidades = st.sidebar.selectbox(
    "Sistema de unidades",
    ["m", "cm"],
    index=0
)

factor = 1.0 if unidades == "m" else 0.01
st.sidebar.info(
    "Si ingresas en cm, el programa convierte internamente a metros para graficar."
)

st.sidebar.header("Geometría principal")

H = st.sidebar.number_input(
    "Altura del fuste H",
    min_value=0.50,
    value=4.00,
    step=0.10,
    help="Altura desde la cara superior de la zapata hasta la coronación del muro."
)

B = st.sidebar.number_input(
    "Ancho total de zapata B",
    min_value=0.50,
    value=2.80,
    step=0.10,
    help="Ancho total de la cimentación: puntera + espesor del fuste + talón."
)

Df = st.sidebar.number_input(
    "Espesor de zapata hz",
    min_value=0.10,
    value=0.40,
    step=0.05,
    help="Espesor vertical de la zapata."
)

puntera = st.sidebar.number_input(
    "Longitud de puntera",
    min_value=0.10,
    value=0.80,
    step=0.05,
    help="Distancia desde la cara frontal del fuste hasta el borde delantero de la zapata."
)

t_base = st.sidebar.number_input(
    "Espesor del fuste en la base",
    min_value=0.10,
    value=0.35,
    step=0.05,
    help="Espesor del fuste en su unión con la zapata."
)

t_corona = st.sidebar.number_input(
    "Espesor del fuste en la corona",
    min_value=0.10,
    value=0.25,
    step=0.05,
    help="Espesor superior del fuste."
)

st.sidebar.header("Suelo y relleno")

altura_relleno_sobre_zapata = st.sidebar.number_input(
    "Altura de relleno detrás del muro",
    min_value=0.00,
    value=4.00,
    step=0.10,
    help="Altura de relleno medida desde la cara superior de la zapata."
)

pendiente_relleno_h = st.sidebar.number_input(
    "Pendiente relleno: horizontal",
    min_value=0.10,
    value=2.00,
    step=0.10,
    help="Para una pendiente V:H. Ejemplo: 1V:2H."
)

pendiente_relleno_v = st.sidebar.number_input(
    "Pendiente relleno: vertical",
    min_value=0.00,
    value=0.00,
    step=0.10,
    help="Para relleno horizontal usa 0. Para 1V:2H coloca V=1 y H=2."
)

st.sidebar.header("Llave de corte")

usar_llave = st.sidebar.checkbox(
    "Incluir llave de corte",
    value=True
)

ancho_llave = st.sidebar.number_input(
    "Ancho de llave",
    min_value=0.05,
    value=0.25,
    step=0.05,
    disabled=not usar_llave
)

profundidad_llave = st.sidebar.number_input(
    "Profundidad de llave",
    min_value=0.05,
    value=0.35,
    step=0.05,
    disabled=not usar_llave
)

pos_llave = st.sidebar.number_input(
    "Posición de llave desde el borde frontal",
    min_value=0.10,
    value=1.70,
    step=0.05,
    disabled=not usar_llave,
    help="Distancia horizontal desde el borde frontal de la zapata hasta el eje de la llave."
)

datos = DatosMuro(
    H=H * factor,
    B=B * factor,
    hz=Df * factor,
    puntera=puntera * factor,
    t_base=t_base * factor,
    t_corona=t_corona * factor,
    altura_relleno=altura_relleno_sobre_zapata * factor,
    pendiente_h=pendiente_relleno_h,
    pendiente_v=pendiente_relleno_v,
    usar_llave=usar_llave,
    ancho_llave=ancho_llave * factor,
    profundidad_llave=profundidad_llave * factor,
    pos_llave=pos_llave * factor,
)

col_izq, col_der = st.columns([1.05, 1.30])

with col_izq:
    st.subheader("Datos ingresados")
    errores = validar_datos_muro(datos)

    if errores:
        st.error("Corrige los siguientes datos antes de continuar:")
        for error in errores:
            st.write(f"• {error}")
    else:
        st.success("La geometría ingresada es válida para dibujo preliminar.")

    st.dataframe(
        resumen_geometria(datos),
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "Este módulo solo dibuja la geometría. Luego se pueden agregar: "
        "empuje activo, estabilidad por volcamiento/deslizamiento, presiones de contacto, "
        "diseño a flexión/cortante y acero."
    )

with col_der:
    st.subheader("Vista dinámica del muro")

    if not errores:
        geometria = generar_puntos_muro(datos)
        fig, ax = plt.subplots(figsize=(9, 6))
        dibujar_muro(ax, datos, geometria, tamano_texto=tamano_texto_cotas)

        st.pyplot(fig, clear_figure=True)
    else:
        st.warning("El dibujo se mostrará cuando la geometría sea válida.")
