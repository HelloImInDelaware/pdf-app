# app.py

import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
import os
import tempfile
import tabula

# Procesamiento de PDF similar al que ya tienes
def procesar_pagina_1(filename, folio):
    tables = tabula.read_pdf(filename, pages=1, multiple_tables=True, lattice=True)
    dfs = [t for t in tables if t.shape[1] > 1]
    df = pd.concat(dfs, ignore_index=True).iloc[1:].reset_index(drop=True)

    columnas = [
        "Estado", "Recursos/Producto", "Código", "Fecha Elaboración", "Lote", "Cantidad / Peso",
        "Peso con Glaseo", "% Glaseo", "por eliminar", "Rut", "Tipo", "Nombre", "Dirección",
        "Tipo Documento", "por eliminar", "Guía", "Fecha Guía", "por eliminar", "por eliminar"
    ]
    df.columns = columnas
    df = df.drop(columns=["por eliminar"])
    df.insert(0, "Folio", folio)

    df["Archivo"] = os.path.basename(filename)
    df["Cantidad / Peso"] = df["Cantidad / Peso"].str.strip().str.replace(',', '.', regex=False)
    df["Cantidad / Peso"] = pd.to_numeric(df["Cantidad / Peso"], errors="coerce")
    df["Guía"] = pd.to_numeric(df["Guía"], errors="coerce")
    df["Código"] = pd.to_numeric(df["Código"], errors="coerce")
    df["Peso con Glaseo"] = pd.to_numeric(df["Peso con Glaseo"], errors="coerce")
    df['Lote'] = df['Lote'].astype(str).str.replace(r'\s+', '', regex=True)

    return df

def procesar_pagina_otras(filename, page_num, folio):
    tables = tabula.read_pdf(filename, pages=page_num, multiple_tables=True, lattice=True)
    dfs = [t for t in tables if t.shape[1] > 1]
    df = pd.concat(dfs, ignore_index=True).iloc[1:].reset_index(drop=True)

    columnas = [
        "Estado", "Recursos/Producto", "Código", "Fecha Elaboración", "Lote", "Cantidad / Peso",
        "Peso con Glaseo", "% Glaseo", "por eliminar", "Rut", "Tipo", "Nombre", "Dirección",
        "Tipo Documento", "Guía", "Fecha Guía", "por eliminar", "por eliminar"
    ]
    df.columns = columnas
    df = df.drop(columns=["por eliminar"])
    df.insert(0, "Folio", folio)
    df.insert(1, "Archivo", os.path.basename(filename))

    df["Cantidad / Peso"] = df["Cantidad / Peso"].str.replace('.', ',', regex=False)
    df["Cantidad / Peso"] = df["Cantidad / Peso"].str.replace(',', '.', regex=False)
    df["Cantidad / Peso"] = pd.to_numeric(df["Cantidad / Peso"], errors="coerce")
    df["Guía"] = pd.to_numeric(df["Guía"], errors="coerce")
    df["Código"] = pd.to_numeric(df["Código"], errors="coerce")
    df["Peso con Glaseo"] = pd.to_numeric(df["Peso con Glaseo"], errors="coerce")
    df['Lote'] = df['Lote'].astype(str).str.replace(r'\s+', '', regex=True)

    return df

# App principal
st.title("Procesador de PDFs de Trazabilidad")
st.write("Sube uno o más archivos PDF para procesarlos y exportarlos a Excel.")

uploaded_files = st.file_uploader("Selecciona archivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    if st.button("Procesar archivos"):
        df_final = pd.DataFrame()

        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name

            try:
                folio = pd.to_numeric(uploaded_file.name.split("_")[1], errors="coerce")
            except:
                folio = None

            reader = PdfReader(tmp_file_path)
            total_paginas = len(reader.pages)

            df_pdf = procesar_pagina_1(tmp_file_path, folio)

            if total_paginas > 1:
                for p in range(2, total_paginas + 1):
                    df_otras = procesar_pagina_otras(tmp_file_path, p, folio)
                    df_pdf = pd.concat([df_pdf, df_otras], ignore_index=True)

            df_final = pd.concat([df_final, df_pdf], ignore_index=True)

        # Descargar como Excel
        st.success("Procesamiento completado.")
        st.dataframe(df_final.head())

        output = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        df_final.to_excel(output.name, index=False)

        with open(output.name, "rb") as f:
            st.download_button("Descargar Excel", f, file_name="resultado.xlsx")

