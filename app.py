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

if st.button("🔎 Iniciar Busca de CTOs"):
    try:
        df = pd.read_excel(caminho_base, engine="openpyxl")
    except Exception as e:
        st.error(f"Erro ao carregar base: {e}")
        st.stop()

    # Tratamento inicial
    df["cto"] = df["cto"].astype(str)
    df["CAMINHO_REDE"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)
    df["cto_upper"] = df["cto"].str.upper()

    # Pré-calcular total de portas por caminho de rede
    total_portas = df.groupby("CAMINHO_REDE")["portas"].sum().rename("portas_totais").reset_index()
    df = df.merge(total_portas, on="CAMINHO_REDE", how="left")

    # Marcar CTOs inputadas
    df["inputada"] = df["cto_upper"].isin(ctos_inputadas)

    # Inicializar colunas de resultado
    df["status"] = "⚪ STATUS INDEFINIDO"
    df["cto_trocavel"] = ""

    # Análise vetorizada
    cond_sp8 = (df["portas"] == 8) & (df["portas_totais"] + 8 <= 128)
    df.loc[cond_sp8, "status"] = "✅ TROCA DE SP8 PARA SP16"

    cond_sp8_limite = (df["portas"] == 8) & (df["portas_totais"] + 8 > 128)
    df.loc[cond_sp8_limite, "status"] = "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE DE PORTAS NA PON"

    cond_sp16_saturada = (df["portas"] == 16) & (df["portas_totais"] >= 128)
    df.loc[cond_sp16_saturada, "status"] = "🔴 PON JÁ ESTÁ SATURADA"

    # Análise de SP16 que podem trocar SP8s
    df_sp16 = df[(df["portas"] == 16) & (df["portas_totais"] < 128)]
    df_sp8_disponiveis = df[(df["portas"] == 8) & (~df["cto_upper"].isin(ctos_inputadas))]

    for idx, row in df_sp16.iterrows():
        caminho = row["CAMINHO_REDE"]
        sp8_no_caminho = df_sp8_disponiveis[df_sp8_disponiveis["CAMINHO_REDE"] == caminho]
        if not sp8_no_caminho.empty:
            df.at[idx, "status"] = "✅ CTO JÁ É SP16 MAS PODE TROCAR SP8 NO CAMINHO"
            df.at[idx, "cto_trocavel"] = sp8_no_caminho.iloc[0]["cto"]

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
