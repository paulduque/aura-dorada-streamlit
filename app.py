# app.py
# Sistema completo con estilo moderno (dashboard)

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet

# ==========================
# CONFIGURACIÓN
# ==========================
st.set_page_config(page_title="Aura Dorada", layout="wide")
ARCHIVO = Path("data/Atenciones clientes.xlsx")

# ==========================
# ESTILOS CSS
# ==========================
st.markdown("""
<style>
/* Fondo general de la app */
[data-testid="stAppViewContainer"],
[data-testid="stToolbar"],
.css-18e3th9,
.css-1d391kg {
    background-color: #f5dfe1 !important;  /* fondo rosa principal */
}

/* Sidebar con otro tono */
[data-testid="stSidebar"] {
    background-color: #fff2f3 !important;  /* rosa más oscuro/pastel */
    color: #34495e;
}

/* Subtítulos */
h2, h3 {
    color: #34495e;
    font-family: 'Arial', sans-serif;
}

/* Botones estilo moderno */
div.stButton > button {
    background-color: #5dade2;
    color: white;
    border-radius: 8px;
    height: 40px;
    width: 100%;
    font-weight: bold;
    border: none;
}
div.stButton > button:hover {
    background-color: #3498db;
    cursor: pointer;
}

/* Inputs */
input {
    border-radius: 6px;
    border: 1px solid #dcdcdc;
    padding: 5px;
}

/* DataFrames estilo dashboard */
.stDataFrame div.row_widget {
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    background-color: #F8C8CC !important;
}

/* Expanders / Cards */
.stExpander {
    background-color: #F8C8CC !important;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)



# ==========================
# UTILIDADES EXCEL
# ==========================
HOJAS = {
    "CLIENTES": ["ID","NOMBRE","TELEFONO","EMAIL"],
    "CITAS": ["ID","FECHA","HORA","CLIENTE","TRATAMIENTO","ESTADO"],
    "PAGOS": ["ID","FECHA","CLIENTE","TRATAMIENTO","MONTO"]
}

def init_excel():
    if not ARCHIVO.exists():
        ARCHIVO.parent.mkdir(exist_ok=True)
        with pd.ExcelWriter(ARCHIVO, engine="openpyxl") as w:
            for h,c in HOJAS.items():
                pd.DataFrame(columns=c).to_excel(w, sheet_name=h, index=False)

def importar_clientes_desde_sheet1():
    try:
        sheet1 = pd.read_excel(ARCHIVO, sheet_name="Sheet1")
    except:
        return

    if "NOMBRE" not in sheet1.columns:
        return

    clientes = pd.read_excel(ARCHIVO, sheet_name="CLIENTES")

    for nombre in sheet1["NOMBRE"].dropna().unique():
        if nombre not in clientes["NOMBRE"].values:
            clientes.loc[len(clientes)] = [
                1 if clientes.empty else int(clientes.ID.max()) + 1,
                nombre,
                "",
                ""
            ]

    with pd.ExcelWriter(
        ARCHIVO,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace"
    ) as w:
        clientes.to_excel(w, sheet_name="CLIENTES", index=False)

def load(sheet):
    init_excel()
    importar_clientes_desde_sheet1()
    try:
        return pd.read_excel(ARCHIVO, sheet_name=sheet)
    except ValueError:
        cols = HOJAS.get(sheet, [])
        df = pd.DataFrame(columns=cols)
        save(df, sheet)
        return df

def save(df, sheet):
    with pd.ExcelWriter(ARCHIVO, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df.to_excel(w, sheet_name=sheet, index=False)

def new_id(df):
    return 1 if df.empty else int(df.ID.max())+1

def load_historial():
    try:
        df = pd.read_excel(ARCHIVO, sheet_name="Sheet1")
        df.columns = df.columns.str.strip().str.upper()
        return df
    except:
        return pd.DataFrame()
    
def load_tratamientos():
    try:
        df = pd.read_excel(ARCHIVO, sheet_name="Sheet1")
        df.columns = df.columns.str.strip().str.upper()

        # Convertir columnas numéricas
        for col in ["VALOR", "ANTICIPO", "SESIONES", "ATENDIDO", "POR ATENDER"]:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.strip()
                )
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # 🧮 RECALCULAR SALDO (NO USAR FÓRMULA EXCEL)
        df["SALDO"] = df["VALOR"] - df["ANTICIPO"]

        # 🏷️ RECALCULAR ESTADO
        def calcular_estado(row):
            if row.get("ES_PAQUETE", "").strip().upper() == "SI" and row["VALOR"] == 0:
                return "incluido"
            if row["SALDO"] <= 0:
                return "pagado"
            return "por pagar"

        df["ESTADO"] = df.apply(calcular_estado, axis=1)

        return df

    except Exception as e:
        st.error(f"Error cargando tratamientos: {e}")
        return pd.DataFrame()

def save_tratamientos(df):
    with pd.ExcelWriter(
        ARCHIVO,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace"
    ) as w:
        df.to_excel(w, sheet_name="Sheet1", index=False)


# ==========================
# MENU
# ==========================
menu = st.sidebar.radio("Menú", ["Dashboard","Agenda","Clientes","Pagos","Reportes"])

# ==========================
# DASHBOARD PRINCIPAL
# ==========================
if menu == "Dashboard":
    from PIL import Image

    # --- Cargar logo ---
    logo = Image.open("assets/logohorizontal.png")

    # --- Centrar logo usando columnas ---
    col1, col2, col3 = st.columns([1, 2, 1])  # La columna central es más ancha
    with col2:
        st.image(logo, width=300)  # Ajusta el tamaño

    # --- Título debajo del logo ---
    st.title("Panel de Control")
    pagos = load("PAGOS")
    citas = load("CITAS")
    clientes = load("CLIENTES")

    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes Registrados", len(clientes))
    col2.metric("Citas Agendadas", len(citas[citas.ESTADO=="AGENDADA"]))
    col3.metric("Total Pagos", f"${pagos.MONTO.sum():.2f}")

    st.markdown("### Últimas Citas")
    st.dataframe(citas.sort_values(["FECHA","HORA"], ascending=False).head(10), width='stretch')

# ==========================
# AGENDA VISUAL
# ==========================
elif menu == "Agenda":
    citas = load("CITAS")
    st.subheader("📅 Agenda de Citas")

    fecha_sel = st.date_input("Filtrar por fecha", datetime.today())
    citas_dia = citas[citas.FECHA == pd.to_datetime(fecha_sel)]
    st.dataframe(citas_dia.sort_values("HORA"), width='stretch')

    st.markdown("### ➕ Nueva cita")
    clientes = load("CLIENTES")
    lista_clientes = clientes["NOMBRE"].tolist()
    lista_clientes.insert(0, "➕ Nuevo cliente")

    with st.form("cita"):
        fecha = st.date_input("Fecha")
        hora = st.time_input("Hora")
        cliente_sel = st.selectbox("Cliente", lista_clientes)

        if cliente_sel == "➕ Nuevo cliente":
            nuevo_nombre = st.text_input("Nombre del cliente")
            nuevo_tel = st.text_input("Teléfono")
            nuevo_email = st.text_input("Email")
            cliente_final = nuevo_nombre
        else:
            cliente_final = cliente_sel

        tratamiento = st.text_input("Tratamiento")
        guardar = st.form_submit_button("Agendar")

    if guardar:
        if cliente_sel == "➕ Nuevo cliente":
            if nuevo_nombre.strip() == "":
                st.error("Debes ingresar el nombre del cliente")
                st.stop()
            clientes.loc[len(clientes)] = [new_id(clientes), nuevo_nombre, nuevo_tel, nuevo_email]
            save(clientes, "CLIENTES")
        citas.loc[len(citas)] = [new_id(citas), fecha, hora, cliente_final, tratamiento, "AGENDADA"]
        save(citas, "CITAS")
        st.success("Cita creada correctamente")
        st.rerun()

# ==========================
# CLIENTES CRUD
# ==========================
elif menu == "Clientes":
    df = load("CLIENTES")
    # historial = load_historial()
    historial = load_tratamientos()
    if "FECHA" in historial.columns:
        historial["FECHA"] = pd.to_datetime(historial["FECHA"], errors="coerce")


    st.subheader("👤 Clientes")

    if df.empty:
        st.info("No hay clientes registrados todavía.")
    else:
        cliente = st.selectbox("Seleccionar cliente", df.NOMBRE)

        fila = df[df.NOMBRE == cliente].index[0]

        nombre = st.text_input("Nombre", df.loc[fila, "NOMBRE"])
        tel = st.text_input("Teléfono", df.loc[fila, "TELEFONO"])
        email = st.text_input("Email", df.loc[fila, "EMAIL"])

        # =========================
        # HISTORIAL DE TRATAMIENTOS
        # =========================
        st.markdown("### 🧾 Historial de tratamientos")

        historial = load_tratamientos()

        if historial.empty:
            st.info("No existe historial de tratamientos.")
        else:
            hist_cliente = historial.loc[
                historial["NOMBRE"] == cliente
            ].copy()

            if hist_cliente.empty:
                st.warning("Este cliente no tiene tratamientos registrados.")
            else:
                if "FECHA" in hist_cliente.columns:
                    hist_cliente["FECHA"] = pd.to_datetime(
                        hist_cliente["FECHA"], errors="coerce"
                    )

                # Métricas
                col1, col2, col3 = st.columns(3)

                col1.metric("Tratamientos", len(hist_cliente))
                col2.metric(
                    "Saldo pendiente",
                    f"${hist_cliente['SALDO'].sum():.2f}"
                )
                col3.metric(
                    "Sesiones atendidas",
                    int(hist_cliente["ATENDIDO"].sum())
                )

                st.dataframe(
                    hist_cliente[[
                        "FECHA",
                        "TRATAMIENTO",
                        "TIPO",
                        "SESIONES",
                        "ATENDIDO",
                        "POR ATENDER",
                        "VALOR",
                        "ANTICIPO",
                        "SALDO",
                        "ESTADO",
                        "OBSERVACIONES"
                    ]].sort_values("FECHA", ascending=False),
                    width='stretch'
                )


        # =========================
        # ACCIONES CLIENTE
        # =========================
        with st.expander("✏️ Actualizar / 🗑️ Eliminar Cliente"):
            col1, col2 = st.columns(2)

            if col1.button("Actualizar"):
                df.loc[fila, ["NOMBRE", "TELEFONO", "EMAIL"]] = [nombre, tel, email]
                save(df, "CLIENTES")
                st.success("Cliente actualizado")
                st.rerun()

            if col2.button("Eliminar"):
                df = df.drop(fila)
                save(df, "CLIENTES")
                st.warning("Cliente eliminado")
                st.rerun()


# ==========================
# PAGOS CRUD
# ==========================
elif menu == "Pagos":
    st.subheader("💳 Registrar pagos / abonos")

    tratamientos = load_tratamientos()
    clientes = load("CLIENTES")
    
    if tratamientos.empty:
        st.warning("No existen tratamientos registrados.")
        st.stop()

    cliente = st.selectbox("Cliente", clientes.NOMBRE)

    # Filtrar tratamientos con saldo pendiente
    pendientes = tratamientos[
        (tratamientos["NOMBRE"] == cliente) &
        (
            (tratamientos["SALDO"] > 0) |
            (tratamientos["ESTADO"] == "por pagar")
        )
    ]

    # Excluir incluidos
    pendientes = pendientes[pendientes["ESTADO"] != "incluido"]


    if pendientes.empty:
        st.info("Este cliente no tiene pagos pendientes.")
        st.stop()

    # Mostrar tratamientos pendientes
    pendientes["DESCRIPCION"] = (
        pendientes["TRATAMIENTO"] +
        " | Saldo: $" + pendientes["SALDO"].astype(str) +
        " | Estado: " + pendientes["ESTADO"]
    )

    tratamiento_sel = st.selectbox(
        "Tratamiento pendiente",
        pendientes["DESCRIPCION"]
    )

    fila = pendientes[pendientes["DESCRIPCION"] == tratamiento_sel].index[0]

    st.markdown("### 📄 Detalle del tratamiento")
    col1, col2, col3 = st.columns(3)

    col1.metric("Valor total", f"${tratamientos.loc[fila,'VALOR']}")
    col2.metric("Anticipo", f"${tratamientos.loc[fila,'ANTICIPO']}")
    col3.metric("Saldo actual", f"${tratamientos.loc[fila,'SALDO']}")

    with st.form("abono"):
        monto = st.number_input(
            "Monto del abono",
            min_value=1.0,
            max_value=float(tratamientos.loc[fila, "SALDO"])
        )

        guardar = st.form_submit_button("Registrar pago")

    if guardar:
        tratamientos.loc[fila, "ANTICIPO"] += monto
        tratamientos.loc[fila, "SALDO"] -= monto

        if tratamientos.loc[fila, "SALDO"] <= 0:
            tratamientos.loc[fila, "SALDO"] = 0
            tratamientos.loc[fila, "ESTADO"] = "Pagado"
        else:
            tratamientos.loc[fila, "ESTADO"] = "Por pagar"

        save_tratamientos(tratamientos)

        st.success("Pago registrado correctamente")
        st.rerun()


# ==========================
# REPORTES
# ==========================
elif menu == "Reportes":
    pagos = load("PAGOS")
    st.subheader("📊 Reportes Mensuales")

    mes = st.selectbox("Mes", range(1,13))
    anio = st.selectbox("Año", range(2024,2031))

    pagos["FECHA"] = pd.to_datetime(pagos.FECHA)
    rep = pagos[(pagos.FECHA.dt.month==mes) & (pagos.FECHA.dt.year==anio)]

    st.dataframe(rep, width='stretch')
    st.metric("Total", f"${rep.MONTO.sum():.2f}")

    col1, col2 = st.columns(2)
    if col1.button("Exportar Excel"):
        rep.to_excel(f"reporte_{mes}_{anio}.xlsx", index=False)
        st.success("Excel generado")
    if col2.button("Exportar PDF"):
        pdf = SimpleDocTemplate(f"reporte_{mes}_{anio}.pdf")
        styles = getSampleStyleSheet()
        elems = [Paragraph(f"Reporte {mes}/{anio}", styles['Title'])]
        table = Table([rep.columns.tolist()] + rep.values.tolist())
        elems.append(table)
        pdf.build(elems)
        st.success("PDF generado")
