import streamlit as st
import pandas as pd
import os
from collections import defaultdict

st.set_page_config(page_title="Buscar por CTO", layout="wide")
st.title("🔍 Buscar por CTO")

# Caminho fixo para a base
caminho_base = os.path.join("pages", "base_de_dados", "base.xlsx")

# Lista de CTOs já indicadas
ctos_inputadas_raw = st.text_area("✏️ Lista de CTOs já indicadas (uma por linha):")
ctos_inputadas = [cto.strip().upper() for cto in ctos_inputadas_raw.split("\n") if cto.strip()]

# Botão para iniciar a busca
if st.button("🔎 Iniciar Busca de CTOs"):
    try:
        df = pd.read_excel(caminho_base, engine="openpyxl")
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {caminho_base}")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao carregar base: {e}")
        st.stop()

    # Tratamento inicial
    df["cto"] = df["cto"].astype(str).str.upper()
    df["CAMINHO_REDE"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)

    # Filtrar apenas as CTOs indicadas
    df_filtrado = df[df["cto"].isin(ctos_inputadas)].copy()
    if df_filtrado.empty:
        st.warning("Nenhuma CTO indicada foi encontrada na base.")
        st.stop()

    # Cálculo de portas existentes por caminho de rede
    portas_existentes_dict = df.groupby("CAMINHO_REDE")["portas"].sum().to_dict()
    portas_acumuladas = defaultdict(int)

    resultados = []

    progress_bar = st.progress(0)
    total = len(df_filtrado)

    for i, (_, row) in enumerate(df_filtrado.iterrows(), start=1):
        cto = row["cto"]
        caminho = row["CAMINHO_REDE"]
        pop, olt, slot, pon = row["pop"], row["olt"], row["slot"], row["pon"]
        portas_novas = row["portas"]

        portas_existentes = portas_existentes_dict.get(caminho, 0)
        acumulado = portas_acumuladas[caminho]
        total_portas = portas_existentes + acumulado + portas_novas

        if total_portas <= 128:
            status = "✅ TROCA DE SP8 PARA SP16"
            portas_acumuladas[caminho] += portas_novas
        else:
            status = "🔴 EXCEDE LIMITE DE PORTAS"

        resultados.append({
            "cto": cto,
            "status": status,
            "pop": pop,
            "olt": olt,
            "slot": slot,
            "pon": pon,
            "portas_existentes": portas_existentes + acumulado,
            "portas_novas": portas_novas,
            "total_de_portas": total_portas
        })

        progress_bar.progress(i / total)

    resultado_df = pd.DataFrame(resultados)
    st.success("✅ Análise concluída com sucesso!")
    st.dataframe(resultado_df, use_container_width=True)
