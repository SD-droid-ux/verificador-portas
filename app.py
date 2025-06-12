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
    ctos_inputadas = [cto.strip().upper() for cto in input_ctos.split("\n") if cto.strip()]
    
    # Verifica duplicadas na entrada
    duplicadas_entrada = set([cto for cto in ctos_inputadas if ctos_inputadas.count(cto) > 1])
    if duplicadas_entrada:
        st.warning(f"⚠️ CTOs duplicadas na entrada: {', '.join(duplicadas_entrada)}")

    # Filtra CTOs existentes na base
    df_filtrada = base_df[base_df["cto"].str.upper().isin(set(ctos_inputadas))].copy()

    if df_filtrada.empty:
        st.warning("Nenhuma CTO encontrada na base com os nomes fornecidos.")
    else:
        # Verifica duplicadas na base
        contagem_base = df_filtrada["cto"].str.upper().value_counts()
        duplicadas_base = contagem_base[contagem_base > 1]
        if not duplicadas_base.empty:
            ctos_duplicadas_msg = "\n".join([f"- {cto}: {qtde} ocorrências" for cto, qtde in duplicadas_base.items()])
            st.warning("⚠️ CTOs duplicadas na base de dados:\n" + ctos_duplicadas_msg)

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
                "CTO": cto_nome,
                "STATUS": status,
                "POP": row.pop,
                "CHASSI": row.olt,
                "PLACA": row.slot,
                "OLT": row.pon,
                "ID_CTO": row.id_cto,
                "LATITUDE": row.latitude,
                "LONGITUDE": row.longitude,
                "CTO_ATIVA": "SIM",
                "PORTAS_EXISTENTES": portas_atual,
                "PORTAS_NOVAS": portas_novas,
                "_TOTAL_DE_PORTAS_": portas_acumuladas[caminho],
                "TIPO_CTO": f"SP{row.portas}",
            })

            if i % 5 == 0 or i == total - 1:
                progress.progress((i + 1) / total)

        # CTOs não encontradas
        ctos_nao_encontradas = set(ctos_inputadas) - set(df_filtrada["cto"].str.upper())
        for cto_nao in ctos_nao_encontradas:
            resultados.append({
                "CTO": cto_nao,
                "STATUS": "❌ NÃO ENCONTRADA",
                "POP": None
                "CHASSI": None,
                "PLACA": None,
                "OLT": None,
                "ID_CTO": None,
                "LATITUDE": None,
                "LONGITUDE": None
                "CTO_ATIVA": "NÃO",
                "PORTAS_EXISTENTES": None,
                "PORTAS_NOVAS": None,
                "TOTAL_DE_PORTAS": None,
                "TIPO_DE_CTO": None,
            })

        df_resultado = pd.DataFrame(resultados)

        st.success(f"✅ Análise concluída para {len(df_resultado)} CTO(s).")
        st.dataframe(df_resultado, use_container_width=True)

elif not input_ctos:
    st.info("Insira as CTOs desejadas para iniciar a análise.")
