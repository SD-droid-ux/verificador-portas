import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Verificador de Portas", layout="wide")

st.title("🔍 Verificador de Portas - CTOs Saturadas")

# Upload do arquivo base
uploaded_file = st.file_uploader("📤 Envie a base de dados (.xlsx):", type=["xlsx"])

# Campo para inserir as CTOs a verificar
ctos_input = st.text_area("✏️ Insira as CTOs a verificar (uma por linha):")

# Botão para iniciar a busca
iniciar_busca = st.button("🚀 Iniciar Análise")

if uploaded_file and ctos_input and iniciar_busca:
    # Leitura da base
    base_df = pd.read_excel(uploaded_file)

    # Verifica se as colunas obrigatórias existem
    colunas_necessarias = ["pop", "olt", "slot", "pon", "portas", "cto"]
    colunas_faltando = [col for col in colunas_necessarias if col not in base_df.columns]

    if colunas_faltando:
        st.error(f"❌ As seguintes colunas estão faltando na base: {', '.join(colunas_faltando)}")
        st.stop()

    # Criação segura do CAMINHO_REDE
    for col in ["pop", "olt", "slot", "pon", "cto"]:
        base_df[col] = base_df[col].astype(str)

    base_df["CAMINHO_REDE"] = (
        base_df["pop"] + "/" + base_df["olt"] + "/" + base_df["slot"] + "/" + base_df["pon"]
    )

    # Processamento inicial
    ctos_lista = [cto.strip() for cto in ctos_input.splitlines() if cto.strip()]
    base_filtrada = base_df[base_df["cto"].isin(ctos_lista)].copy()

    if base_filtrada.empty:
        st.warning("⚠️ Nenhuma CTO da lista foi encontrada na base.")
        st.stop()

    # Agrupamento por caminho de rede
    caminhos_ctos = base_filtrada.groupby("CAMINHO_REDE")

    resultados = []
    progresso = st.progress(0)
    total = len(base_filtrada)
    contador = 0

    uso_caminhos = {}  # Guardará portas usadas progressivamente

    for _, row in base_filtrada.iterrows():
        caminho = row["CAMINHO_REDE"]
        portas_existentes = uso_caminhos.get(caminho, base_df[base_df["CAMINHO_REDE"] == caminho]["portas"].sum())
        portas_novas = row["portas"]
        total_portas = portas_existentes + portas_novas

        if total_portas <= 128:
            resultado = {
                "cto": row["cto"],
                "situação": "✅ TROCA DE SP8 PARA SP16",
                "pop": row["pop"],
                "olt": row["olt"],
                "slot": row["slot"],
                "pon": row["pon"],
                "portas_existentes": portas_existentes,
                "portas_novas": portas_novas,
                "total_de_portas": total_portas
            }
            resultados.append(resultado)
            uso_caminhos[caminho] = total_portas  # Atualiza o uso acumulado
        contador += 1
        progresso.progress(contador / total)

    # Exibir os resultados
    if resultados:
        df_resultado = pd.DataFrame(resultados)
        st.success(f"✅ {len(df_resultado)} CTO(s) aptas encontradas.")
        st.dataframe(df_resultado, use_container_width=True)
    else:
        st.warning("⚠️ Nenhuma CTO está apta para a troca SP8 para SP16.")
