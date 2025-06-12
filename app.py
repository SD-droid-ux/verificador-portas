import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="🔎 Verificar CTOs - Otimizado", layout="wide")
st.title("🔎 Verificador de CTOs - Otimizado")

@st.cache_data
def carregar_base():
    caminho_base_rede = os.path.join("pages", "base_de_dados", "base.xlsx")
    return pd.read_excel(caminho_base_rede, engine="openpyxl")

# Carrega a base
base_df = carregar_base()

# Verifica colunas obrigatórias
colunas_necessarias = ["pop", "olt", "slot", "pon", "cto", "portas", "latitude", "longitude", "id_cto"]
colunas_faltando = [col for col in colunas_necessarias if col not in base_df.columns]
if colunas_faltando:
    st.error(f"❌ A base de dados está faltando as colunas: {', '.join(colunas_faltando)}")
    st.stop()

# Cria a coluna CAMINHO_REDE
base_df["CAMINHO_REDE"] = (
    base_df["pop"].astype(str) + "/" +
    base_df["olt"].astype(str) + "/" +
    base_df["slot"].astype(str) + "/" +
    base_df["pon"].astype(str)
)

st.markdown("Insira a lista de CTOs que deseja analisar (uma por linha):")
input_ctos = st.text_area("Lista de CTOs")

iniciar = st.button("🚀 Iniciar Análise")

if input_ctos and iniciar:
    # Lista das CTOs digitadas
    ctos_inputadas = [cto.strip().upper() for cto in input_ctos.split("\n") if cto.strip()]
    # Verifica duplicatas na lista
    duplicadas = set([cto for cto in ctos_inputadas if ctos_inputadas.count(cto) > 1])
    if duplicadas:
        st.warning(f"⚠️ CTOs duplicadas na entrada: {', '.join(duplicadas)}")

    df_filtrada = base_df[base_df["cto"].str.upper().isin(set(ctos_inputadas))].copy()

    if df_filtrada.empty:
        st.warning("Nenhuma CTO encontrada na base com os nomes fornecidos.")
    else:
        portas_existentes_dict = base_df.groupby("CAMINHO_REDE")["portas"].sum().to_dict()
        portas_acumuladas = {}
        resultados = []

        total = len(df_filtrada)
        progress = st.progress(0)

        for i, row in enumerate(df_filtrada.itertuples(index=False)):
            caminho = row.CAMINHO_REDE
            cto_nome = row.cto.upper()
            portas_atual = portas_acumuladas.get(caminho, portas_existentes_dict.get(caminho, 0))

            if row.portas == 8 and portas_atual + 8 <= 128:
                status = "✅ TROCA DE SP8 PARA SP16"
                portas_novas = 8
            elif row.portas == 8:
                status = "🔴 EXCEDE LIMITE"
                portas_novas = 0
            else:
                status = "⚪ SEM TROCA"
                portas_novas = 0

            portas_acumuladas[caminho] = portas_atual + portas_novas

            resultados.append({
                "cto": cto_nome,
                "id_cto": row.id_cto,
                "status": status,
                "pop": row.pop,
                "olt": row.olt,
                "slot": row.slot,
                "pon": row.pon,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "portas_existentes": portas_atual,
                "portas_novas": portas_novas,
                "total_de_portas": portas_acumuladas[caminho],
            })

            if i % 5 == 0 or i == total - 1:
                progress.progress((i + 1) / total)

        df_resultado = pd.DataFrame(resultados)

        st.success(f"✅ Análise concluída para {len(df_resultado)} CTO(s).")
        st.dataframe(df_resultado, use_container_width=True)

elif not input_ctos:
    st.info("Insira as CTOs desejadas para iniciar a análise.")
