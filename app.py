import streamlit as st
import pandas as pd
import os
import time

st.set_page_config(page_title="Buscar por CTO", layout="wide")
st.title("🔍 Buscar por CTO")

caminho_base = os.path.join("pages", "base_de_dados", "base.xlsx")

@st.cache_data(show_spinner=False)
def carregar_base(caminho):
    df = pd.read_excel(caminho, engine="openpyxl")
    df["cto"] = df["cto"].astype(str)
    df["cto_upper"] = df["cto"].str.upper()
    df["CAMINHO_REDE"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)
    return df

# Entrada do usuário
ctos_inputadas_raw = st.text_area("✏️ Lista de CTOs para analisar (uma por linha):")
ctos_inputadas = [cto.strip().upper() for cto in ctos_inputadas_raw.split("\n") if cto.strip()]

if st.button("🔎 Iniciar análise individual"):
    if not ctos_inputadas:
        st.warning("Insira ao menos uma CTO.")
        st.stop()

    try:
        df = carregar_base(caminho_base)
    except Exception as e:
        st.error(f"Erro ao carregar base: {e}")
        st.stop()

    resultados = []
    progresso = st.progress(0, text="⏳ Iniciando análise...")

    total = len(ctos_inputadas)
    for i, cto_input in enumerate(ctos_inputadas):
        progresso.progress((i + 1) / total, text=f"🔎 Analisando CTO {i+1} de {total}: {cto_input}")

        cto_linha = df[df["cto_upper"] == cto_input]

        if cto_linha.empty:
            resultados.append({
                "cto": cto_input,
                "status": "❌ CTO não encontrada na base",
                "pop": "-", "olt": "-", "slot": "-", "pon": "-",
                "portas_existentes": "-", "portas_novas": "-", "total_de_portas": "-",
                "cto_trocavel": "-"
            })
            continue

        cto_linha = cto_linha.iloc[0]
        caminho_rede = cto_linha["CAMINHO_REDE"]
        portas_cto = cto_linha["portas"]
        pop = cto_linha["pop"]
        olt = cto_linha["olt"]
        slot = cto_linha["slot"]
        pon = cto_linha["pon"]

        df_caminho = df[df["CAMINHO_REDE"] == caminho_rede]
        portas_existentes = df_caminho["portas"].sum()

        portas_novas = 8 if portas_cto == 8 else 0
        total_de_portas = portas_existentes + portas_novas

        status = "⚪ STATUS INDEFINIDO"
        cto_trocavel = ""

        if portas_cto == 8 and total_de_portas <= 128:
            status = "✅ TROCA DE SP8 PARA SP16"
        elif portas_cto == 8 and total_de_portas > 128:
            status = "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE"
        elif portas_cto == 16 and portas_existentes >= 128:
            status = "🔴 CTO É SP16 E CAMINHO SATURADO"
        elif portas_cto == 16 and portas_existentes < 128:
            df_sp8_disp = df_caminho[(df_caminho["portas"] == 8) & (df_caminho["cto_upper"] != cto_input)]
            if not df_sp8_disp.empty:
                cto_trocavel = df_sp8_disp.iloc[0]["cto"]
                status = "✅ CTO É SP16 E PODE TROCAR OUTRA SP8"
            else:
                status = "🔴 CTO É SP16, SEM SP8 DISPONÍVEL"

        resultados.append({
            "cto": cto_input,
            "status": status,
            "pop": pop,
            "olt": olt,
            "slot": slot,
            "pon": pon,
            "portas_existentes": portas_existentes,
            "portas_novas": portas_novas,
            "total_de_portas": total_de_portas,
            "cto_trocavel": cto_trocavel
        })

    progresso.empty()
    df_resultado = pd.DataFrame(resultados)
    st.success("✅ Análise concluída com sucesso!")
    st.dataframe(df_resultado, use_container_width=True)
