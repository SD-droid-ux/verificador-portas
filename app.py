import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Buscar por CTO", layout="wide")
st.title("🔍 Buscar por CTO")

# Caminho fixo da base
caminho_base = os.path.join("pages", "base_de_dados", "base.xlsx")

# Entrada de CTOs indicadas
ctos_inputadas_raw = st.text_area("✏️ Lista de CTOs já indicadas (uma por linha):")
ctos_inputadas = [cto.strip().upper() for cto in ctos_inputadas_raw.split("\n") if cto.strip()]

if st.button("🔎 Iniciar Busca de CTOs"):
    try:
        df = pd.read_excel(caminho_base, engine="openpyxl")
    except Exception as e:
        st.error(f"Erro ao carregar a base: {e}")
        st.stop()

    # Pré-processamento
    df["cto"] = df["cto"].astype(str)
    df["CAMINHO_REDE"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)
    df["cto_upper"] = df["cto"].str.upper()

    # Total de portas por caminho
    total_portas = df.groupby("CAMINHO_REDE")["portas"].sum().rename("portas_totais")
    df = df.join(total_portas, on="CAMINHO_REDE")

    # Flags
    df["inputada"] = df["cto_upper"].isin(ctos_inputadas)
    df["status"] = "⚪ STATUS INDEFINIDO"
    df["cto_trocavel"] = ""

    # Classificações vetorizadas
    cond1 = (df["portas"] == 8) & (df["portas_totais"] + 8 <= 128)
    df.loc[cond1, "status"] = "✅ TROCA DE SP8 PARA SP16"

    cond2 = (df["portas"] == 8) & (df["portas_totais"] + 8 > 128)
    df.loc[cond2, "status"] = "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE DE PORTAS NA PON"

    cond3 = (df["portas"] == 16) & (df["portas_totais"] >= 128)
    df.loc[cond3, "status"] = "🔴 PON JÁ ESTÁ SATURADA"

    # Analisar SP16 que podem trocar com SP8 disponíveis no mesmo caminho
    df_sp8_disp = df[
        (df["portas"] == 8) &
        (~df["cto_upper"].isin(ctos_inputadas))
    ][["CAMINHO_REDE", "cto"]]

    # Para cada caminho, pegar primeiro SP8 disponível
    sp8_disponiveis_dict = df_sp8_disp.groupby("CAMINHO_REDE")["cto"].first().to_dict()

    cond4 = (df["portas"] == 16) & (df["portas_totais"] < 128)
    df_sp16_validas = df[cond4].copy()

    df.loc[cond4, "status"] = df_sp16_validas["CAMINHO_REDE"].map(
        lambda caminho: "✅ CTO JÁ É SP16 MAS PODE TROCAR SP8 NO CAMINHO" if caminho in sp8_disponiveis_dict else "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA"
    )

    df.loc[cond4, "cto_trocavel"] = df_sp16_validas["CAMINHO_REDE"].map(
        lambda caminho: sp8_disponiveis_dict.get(caminho, "")
    )

    st.success("✅ Análise concluída com sucesso!")
    st.dataframe(df)
