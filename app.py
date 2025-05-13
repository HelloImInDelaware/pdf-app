import streamlit as st
import pdfplumber
import pandas as pd
import io

st.set_page_config(page_title="Extractor de Tablas PDF", layout="wide")

st.title("📄 Extracción de Tablas desde Múltiples PDFs")
st.markdown("Carga uno o varios archivos PDF para extraer sus tablas en un solo Excel.")

uploaded_files = st.file_uploader("Selecciona uno o más archivos PDF", type="pdf", accept_multiple_files=True)

def extraer_tablas_pdf(file):
    tablas_pdf = []
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            tablas = pagina.extract_tables()
            for tabla in tablas:
                df = pd.DataFrame(tabla)
                # Validar que la tabla tiene contenido útil
                if df.shape[1] > 1:
                    tablas_pdf.append(df)
    return tablas_pdf

def limpiar_dataframe(df):
    df = df.reset_index(drop=True)
    df = df.applymap(lambda x: str(x) if not isinstance(x, (list, dict, set)) else str(x))
    df = df.fillna("")
    return df

if uploaded_files:
    tablas_totales = []
    encabezado = None

    for archivo in uploaded_files:
        tablas = extraer_tablas_pdf(archivo)

        for i, tabla in enumerate(tablas):
            if encabezado is None:
                encabezado = tabla.iloc[0]
                df_limpio = tabla[1:].copy()
                df_limpio.columns = encabezado
            else:
                df_limpio = tabla[1:].copy()
                df_limpio.columns = encabezado

            tablas_totales.append(df_limpio)

    if tablas_totales:
        df_final = pd.concat(tablas_totales, ignore_index=True)
        df_limpio = limpiar_dataframe(df_final)

        st.subheader("📊 Vista previa de las primeras filas extraídas:")
        st.dataframe(df_limpio.head(20))

        # Botón para descargar como Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_limpio.to_excel(writer, index=False, sheet_name='TablasPDF')
        excel_data = output.getvalue()

        st.download_button(
            label="⬇️ Descargar Excel",
            data=excel_data,
            file_name="tablas_extraidas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No se encontraron tablas válidas en los archivos PDF.")
