import streamlit as st
import time
import pandas as pd
import os
from collections import defaultdict

st.title("🔍 Buscar por CTO")

# Caminho da base de dados
caminho_base = os.path.join("pages", "base_de_dados", "base.xlsx")

# Tenta carregar os dados apenas uma vez
if "df" not in st.session_state or "portas_por_caminho" not in st.session_state:
    try:
        df = pd.read_excel(caminho_base)
        df["CAMINHO_REDE"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)
        portas_por_caminho = df.groupby("CAMINHO_REDE")["portas"].sum().to_dict()
        st.session_state["df"] = df
        st.session_state["portas_por_caminho"] = portas_por_caminho
    except FileNotFoundError:
        st.warning("⚠️ A base de dados não foi encontrada. Por favor, envie na página principal.")
        st.stop()

# Recupera os dados do session_state
df = st.session_state["df"]
portas_por_caminho = st.session_state["portas_por_caminho"]

input_ctos = list(dict.fromkeys(st.text_area("Insira os ID das CTOs (uma por linha)").upper().splitlines()))

if st.button("🔍 Buscar CTOs"):
    if not input_ctos or all(not cto.strip() for cto in input_ctos):
        st.warning("⚠️ Insira pelo menos um ID de CTO para buscar.")
    else:
        with st.spinner("🔄 Analisando CTOs..."):
            progress_bar = st.progress(0)
            for i in range(5):
                time.sleep(0.05)
                progress_bar.progress((i + 1) * 20)

            df_ctos = df[df["cto"].str.upper().isin(input_ctos)].copy()
            df_ctos["ordem"] = pd.Categorical(df_ctos["cto"].str.upper(), categories=input_ctos, ordered=True)
            df_ctos = df_ctos.sort_values("ordem").drop(columns=["ordem"])

            # Dicionário auxiliar com portas restantes por caminho
            portas_restantes = {k: 128 - v for k, v in portas_por_caminho.items()}

            def obter_status_aprimorado(df_inputado):
                status_dict = {}
                livres = portas_restantes.copy()

                for idx, row in df_inputado.iterrows():
                    caminho = row["CAMINHO_REDE"]
                    portas_cto = row["portas"]
                    total = portas_por_caminho.get(caminho, 0)

                    if total > 128:
                        status = "🔴 SATURADO"
                    elif total == 128 and portas_cto == 16:
                        status = "🔴 SATURADO"
                    elif total == 128 and portas_cto == 8:
                        status = "🔴 CTO É SP8 MAS PON JÁ ESTÁ SATURADA"
                    elif portas_cto == 16 and total < 128:
                        status = "✅ CTO JÁ É SP16 MAS A PON NÃO ESTÁ SATURADA"
                    elif portas_cto == 8 and total < 128:
                        if livres.get(caminho, 0) >= 8:
                            status = "✅ TROCA DE SP8 PARA SP16"
                            livres[caminho] -= 8
                        else:
                            status = "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE DE PORTAS NA PON"
                    else:
                        status = "⚪ STATUS INDEFINIDO"

                    status_dict[idx] = status

                return status_dict

            # Aplicar status
            df_ctos["STATUS"] = pd.Series(obter_status_aprimorado(df_ctos))

            if df_ctos.empty:
                st.info("Nenhuma CTO encontrada para os IDs informados.")
            else:
                st.dataframe(df_ctos, use_container_width=True)

        progress_bar.empty()
