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
        nombre_archivo = archivo.name
        tablas = extraer_tablas_pdf(archivo)

        for tabla in tablas:
            df = pd.DataFrame(tabla)
            if df.shape[0] >= 2:
                nuevo_encabezado = df.iloc[1].astype(str)
                df_limpio = df.iloc[2:].copy()
                df_limpio.columns = nuevo_encabezado

                # Agregar columna con el nombre del archivo (folio)
                df_limpio["Folio"] = nombre_archivo

                # Formatear columna 'Cantidad / Peso' si existe
                for col in df_limpio.columns:
                    if "Cantidad" in col and "Peso" in col:
                        df_limpio[col] = (
                            df_limpio[col]
                            .astype(str)
                            .str.replace(".", "", regex=False)  # elimina puntos de miles
                            .str.replace(",", ".", regex=False)  # convierte coma en punto decimal si fuera necesario
                        )
                        # Convertimos a float y luego a string con ',' como separador decimal
                        df_limpio[col] = pd.to_numeric(df_limpio[col], errors='coerce').round(2)
                        df_limpio[col] = df_limpio[col].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                tablas_totales.append(df_limpio)

    if tablas_totales:
        df_final = pd.concat(tablas_totales, ignore_index=True)

        # Eliminar filas que comienzan con 'Productos'
        df_final = df_final[~df_final.iloc[:, 0].str.startswith('Productos', na=False)]

        # Eliminar filas que comienzan con 'Estado' desde la segunda fila
        df_final = df_final.loc[~(df_final.index > 0) | ~df_final.iloc[:, 0].str.startswith('Estado', na=False)]

        df_limpio = limpiar_dataframe(df_final)

        # Convertir todo a string para evitar problemas de tipos
        df_limpio = df_limpio.applymap(str)

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
