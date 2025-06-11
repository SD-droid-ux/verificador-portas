import streamlit as st
import pandas as pd
import os
from io import BytesIO

st.set_page_config(page_title="Buscar por CTO", layout="wide")
st.title("🔍 Buscar por CTO")

# Caminho fixo para a base
caminho_base = os.path.join("pages", "base_de_dados", "base.xlsx")

# Lista de CTOs já indicadas
ctos_inputadas_raw = st.text_area("✏️ Lista de CTOs já indicadas (uma por linha):")
ctos_inputadas = [cto.strip().upper() for cto in ctos_inputadas_raw.split("\n") if cto.strip()]

# Lê a base com openpyxl
try:
    df = pd.read_excel(caminho_base, engine="openpyxl")
except FileNotFoundError:
    st.error(f"Arquivo não encontrado: {caminho_base}")
    st.stop()
except Exception as e:
    st.error(f"Erro ao carregar base: {e}")
    st.stop()

# Tratamento inicial
df["cto"] = df["cto"].astype(str)
df["CAMINHO_REDE"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)

portas_por_caminho = df.groupby("CAMINHO_REDE")["portas"].sum().to_dict()
input_ctos_upper = set(ctos_inputadas)
ctos_trocadas = set()

# Lógica de análise
def classificar(row, df, portas_por_caminho, input_ctos_upper, ctos_trocadas):
    caminho = row["CAMINHO_REDE"]
    total_portas = portas_por_caminho.get(caminho, 0)

    if row["portas"] == 8 and total_portas < 128:
        if total_portas + 8 <= 128:
            ctos_trocadas.add(row["cto"].upper())
            return "✅ TROCA DE SP8 PARA SP16", ""
        else:
            return "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE DE PORTAS NA PON", ""

    if row["portas"] == 16:
        if total_portas >= 128:
            return "🔴 PON JÁ ESTÁ SATURADA", ""

        sp8_disponiveis = df[
            (df["CAMINHO_REDE"] == caminho) &
            (df["portas"] == 8) &
            (~df["cto"].str.upper().isin(input_ctos_upper)) &
            (~df["cto"].str.upper().isin(ctos_trocadas))
        ]

        for _, sp8_cto in sp8_disponiveis.iterrows():
            nova_soma = total_portas - 8 + 16
            if nova_soma <= 128:
                return "✅ CTO JÁ É SP16 MAS PODE TROCAR SP8 NO CAMINHO", sp8_cto["cto"]

        return "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA", ""

    return "⚪ STATUS INDEFINIDO", ""

df[["status", "cto_trocavel"]] = df.apply(lambda row: pd.Series(
    classificar(row, df, portas_por_caminho, input_ctos_upper, ctos_trocadas)
), axis=1)

st.success("✅ Análise concluída com sucesso!")
st.dataframe(df)

# Exportar para Excel
def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    return output.getvalue()

st.download_button(
    label="📥 Baixar resultados em Excel",
    data=to_excel_bytes(df),
    file_name="resultado_analise.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
