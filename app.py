import streamlit as st
import pdfplumber
import pandas as pd
import io
import os

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

    for archivo in uploaded_files:
        tablas = extraer_tablas_pdf(archivo)
        nombre_archivo = os.path.splitext(os.path.basename(archivo.name))[0]

        for i, tabla in enumerate(tablas):
            df = pd.DataFrame(tabla)

            if len(df) < 2:
                continue

            encabezado = df.iloc[1].astype(str)
            df_limpio = df[2:].copy()
            df_limpio.columns = encabezado
            df_limpio["Folio"] = nombre_archivo

            tablas_totales.append(df_limpio)

    if tablas_totales:
        df_final = pd.concat(tablas_totales, ignore_index=True)

        # Eliminar filas que comienzan con 'Productos'
        df_final = df_final[~df_final.iloc[:, 0].str.startswith('Productos', na=False)]

        # Eliminar filas que comienzan con 'Estado' desde la segunda fila
        df_final = df_final.loc[~(df_final.index > 0) | ~df_final.iloc[:, 0].str.startswith('Estado', na=False)]

        # Limpiar y convertir a texto general
        df_limpio = limpiar_dataframe(df_final)

        # ✅ Limpiar la columna "Lote" quitando saltos de línea y espacios extra
        for col in df_limpio.columns:
            if "Lote" in col:
                df_limpio[col] = df_limpio[col].str.replace(r"[\n\r\s]+", "", regex=True)

        # ✅ Formatear correctamente la columna "Cantidad / Peso"
        for col in df_limpio.columns:
            if "Cantidad" in col and "Peso" in col:
                df_limpio[col] = df_limpio[col].str.replace(",", ".", regex=False)
                df_limpio[col] = pd.to_numeric(df_limpio[col], errors="coerce")

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
