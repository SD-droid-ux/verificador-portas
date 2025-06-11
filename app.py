import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Buscar por CTO", layout="wide")
st.title("🔍 Buscar por CTO")

caminho_base = os.path.join("pages", "base_de_dados", "base.xlsx")

# Cache para leitura da base (executa só uma vez e reutiliza)
@st.cache_data(show_spinner=False)
def carregar_base(caminho):
    df = pd.read_excel(caminho, engine="openpyxl")
    df["cto"] = df["cto"].astype(str)
    df["cto_upper"] = df["cto"].str.upper()
    df["CAMINHO_REDE"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)
    return df

# Entrada do usuário
ctos_inputadas_raw = st.text_area("✏️ Lista de CTOs já indicadas (uma por linha):")
ctos_inputadas = [cto.strip().upper() for cto in ctos_inputadas_raw.split("\n") if cto.strip()]

if st.button("🔎 Iniciar Busca de CTOs"):
    if not ctos_inputadas:
        st.warning("Por favor, insira ao menos uma CTO.")
        st.stop()

    try:
        df = carregar_base(caminho_base)
    except Exception as e:
        st.error(f"Erro ao carregar a base: {e}")
        st.stop()

    # Filtra df para conter só CTOs indicadas e seus caminhos de rede
    df_ctos_indicadas = df[df["cto_upper"].isin(ctos_inputadas)]
    caminhos_rede_dos_ctos = df_ctos_indicadas["CAMINHO_REDE"].unique()

    # Filtra df original para linhas que pertencem aos caminhos de rede relevantes
    df_filtrado = df[df["CAMINHO_REDE"].isin(caminhos_rede_dos_ctos)].copy()

    # Soma total portas por caminho no df filtrado
    total_portas = df_filtrado.groupby("CAMINHO_REDE")["portas"].sum().rename("portas_totais")
    df_filtrado = df_filtrado.join(total_portas, on="CAMINHO_REDE")

    df_filtrado["cto_upper"] = df_filtrado["cto_upper"].astype(str)
    df_filtrado["inputada"] = df_filtrado["cto_upper"].isin(ctos_inputadas)
    df_filtrado["status"] = "⚪ STATUS INDEFINIDO"
    df_filtrado["cto_trocavel"] = ""

    # Condições vetorizadas
    cond1 = (df_filtrado["portas"] == 8) & (df_filtrado["portas_totais"] + 8 <= 128)
    df_filtrado.loc[cond1, "status"] = "✅ TROCA DE SP8 PARA SP16"

    cond2 = (df_filtrado["portas"] == 8) & (df_filtrado["portas_totais"] + 8 > 128)
    df_filtrado.loc[cond2, "status"] = "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE DE PORTAS NA PON"

    cond3 = (df_filtrado["portas"] == 16) & (df_filtrado["portas_totais"] >= 128)
    df_filtrado.loc[cond3, "status"] = "🔴 PON JÁ ESTÁ SATURADA"

    # SP8 disponíveis no mesmo caminho, excluindo CTOs inputadas
    df_sp8_disp = df_filtrado[
        (df_filtrado["portas"] == 8) &
        (~df_filtrado["cto_upper"].isin(ctos_inputadas))
    ][["CAMINHO_REDE", "cto"]]

    sp8_disponiveis_dict = df_sp8_disp.groupby("CAMINHO_REDE")["cto"].first().to_dict()

    cond4 = (df_filtrado["portas"] == 16) & (df_filtrado["portas_totais"] < 128)
    df_sp16_validas = df_filtrado[cond4].copy()

    df_filtrado.loc[cond4, "status"] = df_sp16_validas["CAMINHO_REDE"].map(
        lambda c: "✅ CTO JÁ É SP16 MAS PODE TROCAR SP8 NO CAMINHO" if c in sp8_disponiveis_dict else "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA"
    )
    df_filtrado.loc[cond4, "cto_trocavel"] = df_sp16_validas["CAMINHO_REDE"].map(sp8_disponiveis_dict)

    st.success("✅ Análise concluída com sucesso!")
    st.dataframe(df_filtrado.reset_index(drop=True))
