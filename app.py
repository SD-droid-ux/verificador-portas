import streamlit as st
import pandas as pd

st.set_page_config(page_title="Busca por CTOs", layout="wide")

st.title("🔍 Busca por CTOs Específicas")

# Upload do arquivo Excel com a base de dados
uploaded_file = st.file_uploader("📁 Envie o arquivo Excel da base de rede:", type=["xlsx"])

if uploaded_file:
    # Leitura do arquivo Excel
    try:
        df_ctos = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()

    # Verifica se as colunas essenciais existem
    colunas_necessarias = ["cto", "status_cto"]
    for col in colunas_necessarias:
        if col not in df_ctos.columns.str.lower():
            st.error(f"A coluna '{col}' não foi encontrada na base.")
            st.stop()

    # Normaliza colunas para minúsculas
    df_ctos.columns = df_ctos.columns.str.lower()

    # Entrada manual das CTOs a buscar
    input_ctos = st.text_area("✍️ Insira a lista de CTOs que deseja buscar (uma por linha):").upper().splitlines()

    if input_ctos:
        # Filtrar CTOs na base
        df_filtrado = df_ctos[df_ctos["cto"].str.upper().isin([cto.strip() for cto in input_ctos])]

        # Dividir entre ativadas e não ativadas
        ativadas = df_filtrado[df_filtrado["status_cto"].str.upper() == "ATIVADO"]
        nao_ativadas = df_filtrado[df_filtrado["status_cto"].str.upper() != "ATIVADO"]

        # Exibir CTOs ATIVADAS
        st.subheader("✅ CTOs ATIVADAS")
        if not ativadas.empty:
            st.dataframe(ativadas)
        else:
            st.info("Nenhuma CTO ativada encontrada.")

        # Exibir CTOs NÃO ATIVADAS
        st.subheader("⚠️ CTOs NÃO ATIVADAS")
        if not nao_ativadas.empty:
            st.dataframe(nao_ativadas)
        else:
            st.success("Todas as CTOs estão ativadas.")
    else:
        st.warning("Digite ou cole uma lista de CTOs no campo acima.")
