import streamlit as st
import pandas as pd

st.set_page_config(page_title="Verificador de Portas", layout="wide")

st.title("🔌 Verificador de Caminhos de Rede com Excesso de Portas")

# Upload do arquivo Excel
arquivo = st.file_uploader("Envie a planilha Excel (.xlsx)", type=["xlsx"])

if arquivo:
    df = pd.read_excel(arquivo)

    # Limpa espaços dos nomes das colunas
    df.columns = df.columns.str.strip()

    # Verifica colunas duplicadas
    if df.columns.duplicated().any():
        st.error("Erro: Há colunas com nomes duplicados no arquivo Excel. Verifique e corrija antes de continuar.")
        st.stop()

    # Mostra a tabela
    st.subheader("📄 Dados da Planilha")
    st.dataframe(df)

    # Filtro por cidade
    cidades = df["CIDADE"].dropna().unique()
    cidade_selecionada = st.selectbox("Filtrar por cidade", sorted(cidades))

    df_filtrado = df[df["CIDADE"] == cidade_selecionada]

    # Criar coluna 'CAMINHO_REDE'
    df_filtrado["CAMINHO_REDE"] = (
        df_filtrado["POP"].astype(str).str.strip() + " / " +
        df_filtrado["CHASSI"].astype(str).str.strip() + " / " +
        df_filtrado["PLACA"].astype(str).str.strip() + " / " +
        df_filtrado["OLT"].astype(str).str.strip()
    )

    # Agrupar e somar as portas por caminho de rede
    soma_portas = df_filtrado.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()

    # Filtrar caminhos de rede que ultrapassam 128 portas
    saturados = soma_portas[soma_portas["PORTAS"] > 128]

    st.subheader("🚨 Caminhos de Rede Saturados")
    if not saturados.empty:
        for _, row in saturados.iterrows():
            st.markdown(f"""
            - **Caminho de Rede**: `{row['CAMINHO_REDE']}`  
              ➤ Total de portas: `{row['PORTAS']}` (limite: 128) ⚠️
            """)
    else:
        st.success("Nenhum caminho de rede ultrapassou o limite de 128 portas.")
