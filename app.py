import streamlit as st
import pandas as pd
import pdfplumber
import io
import base64

st.set_page_config(page_title="Procesador de PDFs", layout="centered")

st.title("📄 Procesador de PDFs (Tablas a Excel)")
st.write("""
Sube uno o más archivos PDF. El sistema extraerá todas las tablas de todas las páginas
y generará un archivo Excel con los datos combinados en una sola hoja.
""")

uploaded_files = st.file_uploader("Selecciona uno o más archivos PDF", type="pdf", accept_multiple_files=True)

def procesar_todas_las_paginas(file, folio):
    dataframes = []
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            tabla = pagina.extract_table()
            if tabla:
                df = pd.DataFrame(tabla[1:], columns=tabla[0])
                df = df.drop(index=0).reset_index(drop=True)
                df.insert(0, "Folio", folio)

                columnas = [
                    "Folio", "Estado", "Recursos/Productos", "Código", "Fecha Elaboración",
                    "Lote", "Cantidad/Peso", "Estado Recurso", "% Glaseo", "Peso con Glaseo",
                    "Rut", "Tipo", "Nombre", "Dirección", "Tipo", "N°", "Fecha",
                    "Solicitud AOL", "Folio AOL"
                ]
                df.columns = columnas[:len(df.columns)]

                # Limpieza
                df["Cantidad/Peso"] = df["Cantidad/Peso"].str.strip().str.replace(',', '.', regex=False)
                df["Cantidad/Peso"] = pd.to_numeric(df["Cantidad/Peso"], errors="coerce")
                if "N°" in df.columns:
                    df["N°"] = pd.to_numeric(df["N°"], errors="coerce")
                if "Código" in df.columns:
                    df["Código"] = pd.to_numeric(df["Código"], errors="coerce")
                if "Peso con Glaseo" in df.columns:
                    df["Peso con Glaseo"] = pd.to_numeric(df["Peso con Glaseo"], errors="coerce")
                if "Lote" in df.columns:
                    df["Lote"] = df["Lote"].astype(str).str.replace(r'\s+', '', regex=True)

                dataframes.append(df)

    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

if uploaded_files:
    with st.spinner("Procesando archivos..."):
        df_final = pd.DataFrame()

        for file in uploaded_files:
            filename = file.name
            try:
                folio = pd.to_numeric(filename.split("_")[1], errors="coerce")
            except:
                folio = None

            df = procesar_todas_las_paginas(file, folio)
            df_final = pd.concat([df_final, df], ignore_index=True)

    if not df_final.empty:
        st.success("✅ ¡Tablas extraídas correctamente!")

        # Convertir todos los valores a texto seguro para prevenir errores de Arrow
        st.dataframe(df_final.astype(str).fillna(""))


        # Convertir a Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Tablas')
        output.seek(0)

        b64 = base64.b64encode(output.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="resultado_tablas.xlsx">📥 Descargar Excel</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.warning("⚠ No se extrajeron tablas de los archivos subidos.")
