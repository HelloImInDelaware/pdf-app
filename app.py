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

        df_final = df_final[~df_final.iloc[:, 0].str.startswith('Productos', na=False)]
        df_final = df_final.loc[~(df_final.index > 0) | ~df_final.iloc[:, 0].str.startswith('Estado', na=False)]

        df_limpio = limpiar_dataframe(df_final)

        # ✅ Limpiar columna N° 5 (índice 4) quitando saltos de línea
        if df_limpio.shape[1] > 4:
            df_limpio.iloc[:, 4] = (
                df_limpio.iloc[:, 4]
                .astype(str)
                .str.replace(r"[\n\r]+", "", regex=True)
                .str.replace(u"\u2028", "", regex=True)
                .str.replace(u"\u000b", "", regex=True)
                .str.replace(u"\u000c", "", regex=True)
                .str.strip()
    )


        # Formatear correctamente la columna "Cantidad / Peso"
        for col in df_limpio.columns:
            if "Cantidad" in col and "Peso" in col:
                df_limpio[col] = df_limpio[col].str.replace(",", ".", regex=False)
                df_limpio[col] = pd.to_numeric(df_limpio[col], errors="coerce")

        # Descargar como Excel
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
