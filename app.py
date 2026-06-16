import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO

import funciones_muro as fm

st.set_page_config(
    page_title="Diseño de muro de contención",
    page_icon="🧱",
    layout="wide"
)

st.title("Diseño de muro de contención de hormigón armado")
st.caption("Base de cálculo: ejemplo de muro de contención de hormigón armado del PDF Caltrans BDP 11.2. Se agregó un detalle general de armado con pantalla, zapata y dentellón.")

st.sidebar.header("Sistema de unidades usado")
st.sidebar.info(
    """
    **Longitudes:** m  
    **Resistencia del suelo:** ton/m²  
    **Hormigón f'c:** kg/cm²  
    **Acero fy:** kg/cm²  
    **Pesos unitarios:** ton/m³
    """
)

st.sidebar.header("Geometría principal del muro")

H = st.sidebar.number_input("Altura del fuste H [m]", min_value=0.50, value=4.00, step=0.10)
B = st.sidebar.number_input("Ancho total de zapata B [m]", min_value=0.50, value=5.79, step=0.10)
hz = st.sidebar.number_input("Espesor de zapata hz [m]", min_value=0.10, value=0.61, step=0.05)
puntera = st.sidebar.number_input("Longitud de puntera [m]", min_value=0.00, value=1.68, step=0.05)
t_base = st.sidebar.number_input("Espesor del fuste en la base [m]", min_value=0.10, value=0.72, step=0.05)
t_corona = st.sidebar.number_input("Espesor del fuste en la corona [m]", min_value=0.10, value=0.29, step=0.01)

st.sidebar.header("Relleno y terreno")

altura_relleno = st.sidebar.number_input("Altura de relleno detrás del muro [m]", min_value=0.00, value=6.19, step=0.10)
pendiente_h = st.sidebar.number_input("Pendiente del relleno: H", min_value=0.10, value=2.00, step=0.10)
pendiente_v = st.sidebar.number_input("Pendiente del relleno: V", min_value=0.00, value=1.00, step=0.10)

st.sidebar.header("Dentellón")

usar_llave = st.sidebar.checkbox("Incluir dentellón", value=True)
ancho_llave = st.sidebar.number_input("Ancho de dentellón [m]", min_value=0.05, value=0.61, step=0.05, disabled=not usar_llave)
profundidad_llave = st.sidebar.number_input("Profundidad de dentellón [m]", min_value=0.05, value=0.23, step=0.05, disabled=not usar_llave)

modo_dentellon = st.sidebar.selectbox(
    "Ubicación del dentellón",
    ["Bajo pantalla", "Según PDF / hacia talón", "Personalizada"],
    index=2,
    disabled=not usar_llave,
    help="La ubicación modifica el brazo de su peso propio y, por tanto, los momentos estabilizantes."
)

pos_bajo_pantalla = puntera + t_base / 2.0
talon_tmp = max(B - puntera - t_base, 0.0)
pos_pdf_talon = min(max(puntera + t_base + 0.70 * talon_tmp, ancho_llave / 2.0), B - ancho_llave / 2.0)

if modo_dentellon == "Bajo pantalla":
    pos_llave = pos_bajo_pantalla
    st.sidebar.caption(f"Posición automática: {pos_llave:.2f} m desde el borde frontal.")
elif modo_dentellon == "Según PDF / hacia talón":
    pos_llave = pos_pdf_talon
    st.sidebar.caption(f"Posición automática: {pos_llave:.2f} m desde el borde frontal.")
else:
    pos_llave = st.sidebar.number_input(
        "Posición del eje del dentellón desde el borde frontal [m]",
        min_value=0.00,
        value=4.27,
        step=0.05,
        disabled=not usar_llave
    )

st.sidebar.header("Propiedades del suelo")

qa = st.sidebar.number_input("Capacidad admisible del suelo qa [ton/m²]", min_value=1.00, value=23.90, step=0.50)
gamma_suelo = st.sidebar.number_input("Peso unitario del suelo γs [ton/m³]", min_value=0.50, value=1.92, step=0.05)
phi = st.sidebar.number_input("Ángulo de fricción interna φ [grados]", min_value=0.00, max_value=50.00, value=34.00, step=0.50)
cohesion = st.sidebar.number_input("Cohesión c [ton/m²]", min_value=0.00, value=0.00, step=0.10)
mu = st.sidebar.number_input("Coeficiente de fricción suelo-hormigón μ [-]", min_value=0.10, value=0.67, step=0.05)

st.sidebar.header("Materiales")

fc = st.sidebar.number_input("Resistencia del hormigón f'c [kg/cm²]", min_value=140.00, value=281.00, step=10.00)
fy = st.sidebar.number_input("Fluencia del acero fy [kg/cm²]", min_value=2800.00, value=4218.00, step=100.00)
gamma_hormigon = st.sidebar.number_input("Peso unitario del hormigón γc [ton/m³]", min_value=1.50, value=2.40, step=0.05)

st.sidebar.header("Vista del dibujo")
mostrar_cotas = st.sidebar.checkbox("Mostrar cotas", value=True)
mostrar_ejes = st.sidebar.checkbox("Mostrar ejes y grilla", value=True)
mostrar_fuerzas = st.sidebar.checkbox("Mostrar diagrama de fuerzas", value=True)

st.sidebar.header("Trial Wedge")
numero_cunas = st.sidebar.slider(
    "Número de superficies de falla a ensayar",
    min_value=30,
    max_value=500,
    value=180,
    step=10
)


st.sidebar.header("Diseño del armado")
recubrimiento_cm = st.sidebar.number_input(
    "Recubrimiento para diseño [cm]",
    min_value=3.0,
    value=7.5,
    step=0.5
)
diametro_vertical_mm = st.sidebar.selectbox(
    "Diámetro barra vertical principal [mm]",
    [10, 12, 14, 16, 18, 20, 22, 25, 28, 32],
    index=3
)
sep_vertical_fuste_cm = st.sidebar.number_input(
    "Separación vertical fuste [cm]",
    min_value=5.0,
    max_value=40.0,
    value=15.0,
    step=2.5
)
diametro_horizontal_mm = st.sidebar.selectbox(
    "Diámetro barra horizontal [mm]",
    [10, 12, 14, 16, 18, 20, 22, 25],
    index=1
)
sep_horizontal_fuste_cm = st.sidebar.number_input(
    "Separación horizontal fuste [cm]",
    min_value=5.0,
    max_value=40.0,
    value=20.0,
    step=2.5
)
separacion_max_cm = st.sidebar.number_input(
    "Separación máxima automática [cm]",
    min_value=10.0,
    value=30.0,
    step=2.5,
    help="Solo se usa como límite cuando la app calcula separaciones automáticas. Las separaciones manuales ingresadas arriba se revisan con As provisto."
)

diametro_zapata_inferior_mm = st.sidebar.selectbox(
    "Diámetro acero inferior zapata [mm]",
    [10, 12, 14, 16, 18, 20, 22, 25, 28, 32],
    index=3,
    help="Se aplica al acero inferior de la zapata. Normalmente controla la puntera."
)
sep_zapata_inferior_cm = st.sidebar.number_input(
    "Separación acero inferior zapata [cm]",
    min_value=5.0,
    max_value=40.0,
    value=20.0,
    step=2.5
)
diametro_zapata_superior_mm = st.sidebar.selectbox(
    "Diámetro acero superior zapata [mm]",
    [10, 12, 14, 16, 18, 20, 22, 25, 28, 32],
    index=3,
    help="Se aplica al acero superior de la zapata. Normalmente controla el talón."
)
sep_zapata_superior_cm = st.sidebar.number_input(
    "Separación acero superior zapata [cm]",
    min_value=5.0,
    max_value=40.0,
    value=20.0,
    step=2.5
)
diametro_llave_mm = st.sidebar.selectbox(
    "Diámetro longitudinal dentellón [mm]",
    [10, 12, 14, 16, 18, 20, 22, 25],
    index=1
)
diametro_estribo_dentellon_mm = st.sidebar.selectbox(
    "Diámetro estribo dentellón [mm]",
    [8, 10, 12],
    index=0
)

datos = fm.DatosMuro(
    H=H,
    B=B,
    hz=hz,
    puntera=puntera,
    t_base=t_base,
    t_corona=t_corona,
    altura_relleno=altura_relleno,
    pendiente_h=pendiente_h,
    pendiente_v=pendiente_v,
    usar_llave=usar_llave,
    ancho_llave=ancho_llave,
    profundidad_llave=profundidad_llave,
    pos_llave=pos_llave,
    qa=qa,
    gamma_suelo=gamma_suelo,
    phi=phi,
    cohesion=cohesion,
    mu=mu,
    fc=fc,
    fy=fy,
    gamma_hormigon=gamma_hormigon,
)

errores = fm.validar_datos_muro(datos)

col_izq, col_der = st.columns([0.33, 1.67])

with col_izq:
    if errores:
        st.error("Corrige los datos de entrada:")
        for error in errores:
            st.write(f"• {error}")
    else:
        memoria_bytes = fm.generar_memoria_word(datos, incluir_pdf=True)
        st.download_button(
            label="Descargar memoria preliminar Word",
            data=memoria_bytes,
            file_name="memoria_muro_contencion.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    with st.expander("Verificación dinámica con ejemplo del PDF"):
        resultados_pdf = fm.calcular_verificacion_caltrans_pdf()
        st.write("Se calculan los estados límite del ejemplo Caltrans usando los valores del PDF.")
        st.dataframe(fm.tabla_comparacion_pdf(resultados_pdf), use_container_width=True, hide_index=True)

    with st.expander("Fuerzas del ejemplo PDF"):
        st.dataframe(fm.tabla_fuerzas_pdf(), use_container_width=True, hide_index=True)

with col_der:
    if not errores:
        geometria = fm.generar_puntos_muro(datos)

        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Geometría", "Fuerzas", "Trial Wedge", "Armado fuste", "Zapata", "Dentellón y deslizamiento", "Detalle general"])

        with tab1:
            st.subheader("Resumen rápido del diseño")

            # Se calculan aquí los estados principales para que el usuario no tenga
            # que entrar a cada pestaña solo para saber si el diseño cumple.
            try:
                resultado_fuste_inicio = fm.calcular_diseno_fuste_dinamico(
                    datos,
                    numero_cunas=numero_cunas,
                    recubrimiento_cm=recubrimiento_cm,
                    diametro_vertical_mm=float(diametro_vertical_mm),
                    diametro_horizontal_mm=float(diametro_horizontal_mm),
                    separacion_max_cm=separacion_max_cm,
                    sep_vertical_manual_cm=sep_vertical_fuste_cm,
                    sep_horizontal_manual_cm=sep_horizontal_fuste_cm
                )

                resultado_zapata_inicio = fm.calcular_diseno_zapata_definitivo(
                    datos,
                    numero_cunas=numero_cunas,
                    recubrimiento_cm=recubrimiento_cm,
                    diametro_puntera_mm=float(diametro_zapata_inferior_mm),
                    diametro_talon_mm=float(diametro_zapata_superior_mm),
                    separacion_max_cm=separacion_max_cm,
                    sep_puntera_manual_cm=sep_zapata_inferior_cm,
                    sep_talon_manual_cm=sep_zapata_superior_cm
                )

                resultado_dentellon_inicio = fm.calcular_deslizamiento_y_llave(
                    datos,
                    numero_cunas=numero_cunas,
                    recubrimiento_cm=recubrimiento_cm,
                    diametro_llave_mm=float(diametro_llave_mm),
                    separacion_max_cm=separacion_max_cm,
                    diametro_estribo_mm=float(diametro_estribo_dentellon_mm)
                )

                def estado_es_ok(valor):
                    txt = str(valor).lower()
                    if "no cumple" in txt or "revisar" in txt or "error" in txt:
                        return False
                    return True

                def tarjeta_estado(titulo, valor, detalle=""):
                    ok = estado_es_ok(valor)
                    color = "#16a34a" if ok else "#dc2626"
                    fondo = "#ecfdf5" if ok else "#fef2f2"
                    borde = "#86efac" if ok else "#fecaca"
                    icono = "✅" if ok else "⚠️"
                    return f"""
                    <div style="
                        border:1px solid {borde};
                        background:{fondo};
                        border-radius:14px;
                        padding:14px 16px;
                        min-height:112px;
                        box-shadow:0 1px 3px rgba(0,0,0,0.06);
                    ">
                        <div style="font-size:14px;color:#475569;margin-bottom:8px;">{titulo}</div>
                        <div style="font-size:26px;font-weight:800;color:{color};line-height:1.1;">{icono} {valor}</div>
                        <div style="font-size:13px;color:#64748b;margin-top:8px;">{detalle}</div>
                    </div>
                    """

                presiones_inicio = resultado_zapata_inicio["presiones"]

                estados_dashboard = [
                    {
                        "Grupo": "Estabilidad externa",
                        "Verificación": "Presión admisible del suelo",
                        "Estado": presiones_inicio["estado_q"],
                        "Detalle": f"qmax = {presiones_inicio['qmax_ton_m2']:.2f} ton/m² / qa = {presiones_inicio['q_adm_ton_m2']:.2f} ton/m²",
                    },
                    {
                        "Grupo": "Pantalla / fuste",
                        "Verificación": "Flexión del fuste",
                        "Estado": "OK" if resultado_fuste_inicio["As_vertical_prov_cm2_m"] >= resultado_fuste_inicio["As_vertical_req_cm2_m"] else "Revisar",
                        "Detalle": f"As prov. = {resultado_fuste_inicio['As_vertical_prov_cm2_m']:.2f} cm²/m / As req. = {resultado_fuste_inicio['As_vertical_req_cm2_m']:.2f} cm²/m",
                    },
                    {
                        "Grupo": "Pantalla / fuste",
                        "Verificación": "Cortante del fuste",
                        "Estado": resultado_fuste_inicio["estado_cortante"],
                        "Detalle": f"Vu = {resultado_fuste_inicio['Vu_ton_m']:.2f} ton/m / φVc = {resultado_fuste_inicio['phi_Vc_ton_m']:.2f} ton/m",
                    },
                    {
                        "Grupo": "Zapata",
                        "Verificación": "Estado global de zapata",
                        "Estado": resultado_zapata_inicio["estado_global_zapata"],
                        "Detalle": "Incluye flexión, cortante y presión de contacto. No se califica anclaje en dashboard.",
                    },
                    {
                        "Grupo": "Zapata",
                        "Verificación": "Cortante puntera",
                        "Estado": resultado_zapata_inicio["cortante_puntera"]["estado"],
                        "Detalle": f"Vu/φVc = {resultado_zapata_inicio['cortante_puntera']['relacion']:.2f}",
                    },
                    {
                        "Grupo": "Zapata",
                        "Verificación": "Cortante talón",
                        "Estado": resultado_zapata_inicio["cortante_talon"]["estado"],
                        "Detalle": f"Vu/φVc = {resultado_zapata_inicio['cortante_talon']['relacion']:.2f}",
                    },
                    {
                        "Grupo": "Dentellón",
                        "Verificación": "Deslizamiento",
                        "Estado": resultado_dentellon_inicio["estado_deslizamiento"],
                        "Detalle": f"R/H = {resultado_dentellon_inicio['FS_deslizamiento']:.2f}",
                    },
                    {
                        "Grupo": "Dentellón",
                        "Verificación": "Armado dentellón",
                        "Estado": resultado_dentellon_inicio["estado_armado_dentellon"],
                        "Detalle": resultado_dentellon_inicio["criterio_armado_dentellon"],
                    },
                ]

                cumple_todo = all(estado_es_ok(e["Estado"]) for e in estados_dashboard)
                estado_general = "DISEÑO CUMPLE" if cumple_todo else "DISEÑO CON OBSERVACIONES"
                color_general = "#16a34a" if cumple_todo else "#dc2626"
                fondo_general = "#ecfdf5" if cumple_todo else "#fef2f2"
                borde_general = "#86efac" if cumple_todo else "#fecaca"
                icono_general = "✅" if cumple_todo else "⚠️"

                st.markdown(
                    f"""
                    <div style="
                        border:2px solid {borde_general};
                        background:{fondo_general};
                        border-radius:18px;
                        padding:18px 22px;
                        margin-bottom:18px;
                        box-shadow:0 2px 6px rgba(0,0,0,0.08);
                    ">
                        <div style="font-size:15px;color:#475569;margin-bottom:6px;">Estado global del modelo actual</div>
                        <div style="font-size:34px;font-weight:900;color:{color_general};line-height:1.1;">{icono_general} {estado_general}</div>
                        <div style="font-size:14px;color:#64748b;margin-top:8px;">
                            Resumen automático de estabilidad, fuste, zapata, anclajes, deslizamiento y dentellón.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                c1, c2, c3, c4 = st.columns(4)
                metricas = [
                    ("qmax", f"{presiones_inicio['qmax_ton_m2']:.2f}", "ton/m²"),
                    ("qa", f"{presiones_inicio['q_adm_ton_m2']:.2f}", "ton/m²"),
                    ("R/H", f"{resultado_dentellon_inicio['FS_deslizamiento']:.2f}", "deslizamiento"),
                    ("PA", f"{resultado_fuste_inicio['PA_ton_m']:.2f}", "ton/m"),
                ]
                for col, met in zip([c1, c2, c3, c4], metricas):
                    with col:
                        st.metric(met[0], met[1], met[2])

                st.markdown("#### Semáforo de verificaciones")
                cols = st.columns(3)
                for idx_estado, item in enumerate(estados_dashboard):
                    with cols[idx_estado % 3]:
                        st.markdown(
                            tarjeta_estado(
                                item["Verificación"],
                                item["Estado"],
                                item["Detalle"]
                            ),
                            unsafe_allow_html=True
                        )

                with st.expander("Ver tabla resumen de verificaciones"):
                    st.dataframe(estados_dashboard, use_container_width=True, hide_index=True)

            except Exception as e:
                st.warning("No se pudo generar el resumen automático. Revisa los datos de entrada o entra a cada pestaña para ver el error específico.")
                st.code(str(e))

            st.divider()
            st.subheader("Geometría del muro")

            fig, ax = plt.subplots(figsize=(8.2, 5.6), dpi=130)
            fm.dibujar_muro(
                ax,
                datos,
                geometria,
                tamano_texto=8,
                mostrar_cotas=mostrar_cotas,
                mostrar_ejes=mostrar_ejes
            )
            buffer_figura = BytesIO()
            fig.savefig(buffer_figura, format="png", bbox_inches="tight")
            buffer_figura.seek(0)
            st.image(buffer_figura, width=760)
            plt.close(fig)

        with tab2:
            if mostrar_fuerzas:
                fig_f, ax_f = plt.subplots(figsize=(8.2, 5.6), dpi=130)
                fm.dibujar_diagrama_fuerzas(
                    ax_f,
                    datos,
                    geometria,
                    mostrar_ejes=mostrar_ejes
                )
                buffer_fuerzas = BytesIO()
                fig_f.savefig(buffer_fuerzas, format="png", bbox_inches="tight")
                buffer_fuerzas.seek(0)
                st.image(buffer_fuerzas, width=760)
                plt.close(fig_f)
            else:
                st.info("Activa 'Mostrar diagrama de fuerzas' en la barra lateral.")

        with tab3:
            tabla_trial, resultado_trial = fm.calcular_trial_wedge_activo(datos, geometria, numero_cunas=numero_cunas)

            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.metric("PA estático por Trial Wedge", f"{resultado_trial['PA_ton_m']:.3f} ton/m")
                st.metric("Ángulo crítico α", f"{resultado_trial['alfa_grados']:.2f}°")
                st.metric("Peso de cuña crítica W", f"{resultado_trial['peso_cuna_ton_m']:.3f} ton/m")

            with col_b:
                st.write("Resultado crítico")
                st.dataframe(
                    tabla_trial.loc[tabla_trial["P [ton/m]"].idxmax()].to_frame().T,
                    use_container_width=True,
                    hide_index=True
                )

            fig_cuna, ax_cuna = plt.subplots(figsize=(8.2, 5.6), dpi=130)
            fm.dibujar_trial_wedge_critico(ax_cuna, datos, geometria, resultado_trial, mostrar_ejes=mostrar_ejes)
            buffer_cuna = BytesIO()
            fig_cuna.savefig(buffer_cuna, format="png", bbox_inches="tight")
            buffer_cuna.seek(0)
            st.image(buffer_cuna, width=760)
            plt.close(fig_cuna)

            fig_curva, ax_curva = plt.subplots(figsize=(8.2, 4.2), dpi=130)
            fm.graficar_curva_trial_wedge(ax_curva, tabla_trial)
            buffer_curva = BytesIO()
            fig_curva.savefig(buffer_curva, format="png", bbox_inches="tight")
            buffer_curva.seek(0)
            st.image(buffer_curva, width=760)
            plt.close(fig_curva)

            with st.expander("Ver todas las cuñas ensayadas"):
                st.dataframe(tabla_trial, use_container_width=True, hide_index=True)


        with tab4:
            resultado_fuste = fm.calcular_diseno_fuste_dinamico(
                datos,
                numero_cunas=numero_cunas,
                recubrimiento_cm=recubrimiento_cm,
                diametro_vertical_mm=float(diametro_vertical_mm),
                diametro_horizontal_mm=float(diametro_horizontal_mm),
                separacion_max_cm=separacion_max_cm
            )

            col_f1, col_f2, col_f3 = st.columns(3)
            col_f1.metric("Mu fuste", f"{resultado_fuste['Mu_ton_m_m']:.3f} ton·m/m")
            col_f2.metric("As vertical req.", f"{resultado_fuste['As_vertical_req_cm2_m']:.2f} cm²/m")
            col_f3.metric(
                "Armado vertical",
                f"Ø{resultado_fuste['diametro_vertical_mm']:.0f} @ {resultado_fuste['separacion_vertical_cm']:.1f} cm"
            )

            st.dataframe(fm.tabla_diseno_fuste(resultado_fuste), use_container_width=True, hide_index=True)

            fig_arm, ax_arm = plt.subplots(figsize=(8.2, 5.6), dpi=130)
            fm.dibujar_armado_fuste(ax_arm, datos, geometria, resultado_fuste, mostrar_ejes=mostrar_ejes)
            buffer_arm = BytesIO()
            fig_arm.savefig(buffer_arm, format="png", bbox_inches="tight")
            buffer_arm.seek(0)
            st.image(buffer_arm, width=760)
            plt.close(fig_arm)

            st.caption(
                "El armado se recalcula dinámicamente con la geometría, propiedades del suelo, f'c, fy, "
                "diámetros y separaciones ingresadas. La app compara As provisto contra As requerido."
            )


        with tab5:
            resultado_zapata = fm.calcular_diseno_zapata_definitivo(
                datos,
                numero_cunas=numero_cunas,
                recubrimiento_cm=recubrimiento_cm,
                diametro_puntera_mm=float(diametro_zapata_inferior_mm),
                diametro_talon_mm=float(diametro_zapata_superior_mm),
                separacion_max_cm=separacion_max_cm
            )

            presiones = resultado_zapata["presiones"]

            col_z1, col_z2, col_z3, col_z4 = st.columns(4)
            col_z1.metric("Estado zapata", resultado_zapata["estado_global_zapata"])
            col_z2.metric("qmax", f"{presiones['qmax_ton_m2']:.2f} ton/m²")
            col_z3.metric("Mu puntera", f"{resultado_zapata['Mu_puntera_ton_m_m']:.3f} ton·m/m")
            col_z4.metric("Mu talón", f"{resultado_zapata['Mu_talon_ton_m_m']:.3f} ton·m/m")

            col_za1, col_za2, col_za3, col_za4 = st.columns(4)
            col_za1.metric("As inferior req.", f"{resultado_zapata['As_puntera_req_cm2_m']:.2f} cm²/m")
            col_za2.metric(
                "Armado inferior",
                f"Ø{resultado_zapata['diametro_puntera_mm']:.0f} @ {resultado_zapata['sep_puntera_cm']:.1f} cm"
            )
            col_za3.metric("As superior req.", f"{resultado_zapata['As_talon_req_cm2_m']:.2f} cm²/m")
            col_za4.metric(
                "Armado superior",
                f"Ø{resultado_zapata['diametro_talon_mm']:.0f} @ {resultado_zapata['sep_talon_cm']:.1f} cm"
            )

            st.caption(
                "El armado de la zapata se controla por caras: acero inferior y acero superior. "
                "La puntera usa el acero inferior y el talón usa el acero superior, porque los momentos críticos pueden estar en caras opuestas."
            )

            st.subheader("1. Presiones de contacto")
            st.dataframe(fm.tabla_presiones_contacto(presiones), use_container_width=True, hide_index=True)

            st.subheader("1.1 Momentos estabilizantes y desestabilizantes")
            st.write(
                "La posición del dentellón entra en el cálculo mediante su brazo x. "
                "Al moverlo, cambia M = W·x y se recalculan x, e, qmax y qmin."
            )
            if hasattr(fm, "tabla_momentos_estabilidad"):
                st.dataframe(fm.tabla_momentos_estabilidad(presiones), use_container_width=True, hide_index=True)
            else:
                st.warning("Actualiza funciones_muro.py: falta tabla_momentos_estabilidad().")

            fig_q, ax_q = plt.subplots(figsize=(8.2, 5.6), dpi=130)
            fm.dibujar_presiones_contacto(ax_q, datos, geometria, presiones, mostrar_ejes=mostrar_ejes)
            buffer_q = BytesIO()
            fig_q.savefig(buffer_q, format="png", bbox_inches="tight")
            buffer_q.seek(0)
            st.image(buffer_q, width=760)
            plt.close(fig_q)

            st.subheader("2. Diseño de puntera y talón")
            st.dataframe(fm.tabla_diseno_zapata_definitivo(resultado_zapata), use_container_width=True, hide_index=True)

            fig_z, ax_z = plt.subplots(figsize=(8.2, 5.6), dpi=130)
            fm.dibujar_detalle_zapata_definitivo(ax_z, datos, geometria, resultado_zapata, mostrar_ejes=mostrar_ejes)
            buffer_z = BytesIO()
            fig_z.savefig(buffer_z, format="png", bbox_inches="tight")
            buffer_z.seek(0)
            st.image(buffer_z, width=760)
            plt.close(fig_z)

            st.info(
                "Esta pestaña ya incluye flexión, cortante a distancia d desde la cara del fuste, "
                "acero mínimo, acero provisto y revisión preliminar de longitud de desarrollo."
            )


        with tab6:
            resultado_llave = fm.calcular_deslizamiento_y_llave(
                datos,
                numero_cunas=numero_cunas,
                recubrimiento_cm=recubrimiento_cm,
                diametro_llave_mm=float(diametro_llave_mm),
                separacion_max_cm=separacion_max_cm,
                diametro_estribo_mm=float(diametro_estribo_dentellon_mm)
            )

            col_l1, col_l2, col_l3, col_l4 = st.columns(4)
            col_l1.metric("Estado global", resultado_llave["estado_global"])
            col_l2.metric("Deslizamiento", resultado_llave["estado_deslizamiento"])
            col_l3.metric("R / H", f"{resultado_llave['FS_deslizamiento']:.2f}")
            col_l4.metric("PP diseño", f"{resultado_llave['PP_diseno_ton_m']:.2f} ton/m")

            st.subheader("1. Deslizamiento")
            st.write(
                "Se compara el empuje horizontal factorizado contra la resistencia por fricción "
                "más la resistencia pasiva disponible."
            )

            st.subheader("2. Resistencia pasiva")
            st.write(
                "Se calcula la resistencia pasiva frente a la zapata y la llave. "
                "El dentellón aumenta la altura pasiva disponible y por tanto incrementa PP."
            )

            st.subheader("3. Criterio de diseño del dentellón")
            st.write(
                "El dentellón se revisa como llave de corte. Si es pequeño se considera monolítico con la zapata; "
                "si requiere armado independiente, se colocan longitudinales mínimos tipo ACI y estribos calculados por cortante."
            )

            st.dataframe(fm.tabla_deslizamiento_llave(resultado_llave), use_container_width=True, hide_index=True)

            st.subheader("4. Resumen de armado del dentellón")
            if hasattr(fm, "tabla_resumen_armado_dentellon"):
                st.dataframe(fm.tabla_resumen_armado_dentellon(resultado_llave), use_container_width=True, hide_index=True)
            else:
                st.warning(
                    "No se encontró tabla_resumen_armado_dentellon() en funciones_muro.py. "
                    "Sube también el archivo funciones_muro.py actualizado."
                )

            st.subheader("5. Efecto de la ubicación del dentellón en momentos")
            if hasattr(fm, "tabla_momentos_estabilidad"):
                st.dataframe(fm.tabla_momentos_estabilidad(resultado_llave["presiones"]), use_container_width=True, hide_index=True)
            else:
                st.warning("Actualiza funciones_muro.py: falta tabla_momentos_estabilidad().")

            st.info(
                "En esta pestaña ya no se muestra la imagen del dentellón. "
                "Solo se deja el resumen del armado y las verificaciones numéricas."
            )


        with tab7:
            resultado_fuste = fm.calcular_diseno_fuste_dinamico(
                datos,
                numero_cunas=numero_cunas,
                recubrimiento_cm=recubrimiento_cm,
                diametro_vertical_mm=float(diametro_vertical_mm),
                diametro_horizontal_mm=float(diametro_horizontal_mm),
                separacion_max_cm=separacion_max_cm
            )

            resultado_zapata = fm.calcular_diseno_zapata_definitivo(
                datos,
                numero_cunas=numero_cunas,
                recubrimiento_cm=recubrimiento_cm,
                diametro_puntera_mm=float(diametro_zapata_inferior_mm),
                diametro_talon_mm=float(diametro_zapata_superior_mm),
                separacion_max_cm=separacion_max_cm
            )

            resultado_dentellon = fm.calcular_deslizamiento_y_llave(
                datos,
                numero_cunas=numero_cunas,
                recubrimiento_cm=recubrimiento_cm,
                diametro_llave_mm=float(diametro_llave_mm),
                separacion_max_cm=separacion_max_cm,
                diametro_estribo_mm=float(diametro_estribo_dentellon_mm)
            )

            st.subheader("Detalles didácticos de armado")
            st.write(
                "Se muestran vistas separadas de cada componente del muro: "
                "pantalla (frontal y corte), zapata (superior y corte) y dentellón (corte)."
            )

            fig_det = plt.figure(figsize=(11.0, 12.0), dpi=130, constrained_layout=True)
            gs = fig_det.add_gridspec(3, 2)

            ax_pf = fig_det.add_subplot(gs[0, 0])
            ax_pc = fig_det.add_subplot(gs[0, 1])
            ax_zs = fig_det.add_subplot(gs[1, 0])
            ax_zc = fig_det.add_subplot(gs[1, 1])
            ax_dc = fig_det.add_subplot(gs[2, 0])
            ax_tx = fig_det.add_subplot(gs[2, 1])

            fm.dibujar_detalle_pantalla_frontal(ax_pf, datos, resultado_fuste)
            fm.dibujar_detalle_pantalla_corte(ax_pc, datos, geometria, resultado_fuste)
            fm.dibujar_detalle_zapata_planta(ax_zs, datos, resultado_zapata)
            fm.dibujar_detalle_zapata_corte(ax_zc, datos, geometria, resultado_zapata)
            fm.dibujar_detalle_dentellon_corte(ax_dc, datos, geometria, resultado_dentellon)

            ax_tx.axis("off")
            resumen_txt = [
                "RESUMEN GENERAL",
                f"Pantalla: Ø{resultado_fuste['diametro_vertical_mm']:.0f} @ {resultado_fuste['separacion_vertical_cm']:.1f} cm (ambas caras)",
                f"Pantalla: Ø{resultado_fuste['diametro_horizontal_mm']:.0f} @ {resultado_fuste['separacion_horizontal_cm']:.1f} cm (horizontal)",
                f"Puntera: Ø{resultado_zapata['diametro_puntera_mm']:.0f} @ {resultado_zapata['sep_puntera_cm']:.1f} cm",
                f"Talón: Ø{resultado_zapata['diametro_talon_mm']:.0f} @ {resultado_zapata['sep_talon_cm']:.1f} cm",
            ]
            if resultado_dentellon.get("requiere_detalle_viga", False):
                resumen_txt.append(
                    f"Dentellón: {resultado_dentellon['n_barras_long_dentellon']}Ø{resultado_dentellon['diametro_llave_mm']:.0f} + Estr. Ø{resultado_dentellon['diametro_estribo_mm']:.0f} @ {resultado_dentellon['sep_estribo_dentellon_cm']:.1f} cm"
                )
            else:
                resumen_txt.append("Dentellón: pequeño, monolítico con zapata, sin armado independiente")

            ax_tx.text(0.02, 0.98, "\n".join(resumen_txt), ha="left", va="top", fontsize=10)

            buffer_det = BytesIO()
            fig_det.savefig(buffer_det, format="png", bbox_inches="tight")
            buffer_det.seek(0)
            st.image(buffer_det, width=980)
            plt.close(fig_det)

            st.caption(
                "Estos detalles se actualizan dinámicamente con los diámetros, separaciones, geometría "
                "y resultados de diseño de cada componente."
            )

    else:
        st.warning("El dibujo se mostrará cuando la geometría sea válida.")
