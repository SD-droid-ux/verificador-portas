import streamlit as st
import pandas as pd

st.set_page_config(page_title="Verificador de Caminhos de Rede", layout="wide")

st.title("🔍 Verificador de Caminhos de Rede por Portas")

uploaded_file = st.file_uploader("Envie o arquivo Excel com os dados", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("🔢 Dados Carregados")
    st.dataframe(df)

    # Combina os campos para formar o caminho de rede
    df["CAMINHO_REDE"] = df["POP"] + " / " + df["CHASSI"] + " / " + df["PLACA"] + " / " + df["OLT"]

    # Filtro por cidade
    cidades = df["CIDADE"].unique()
    cidade_selecionada = st.selectbox("Filtrar por cidade", ["Todas"] + list(cidades))
    if cidade_selecionada != "Todas":
        df = df[df["CIDADE"] == cidade_selecionada]

    # Soma de portas por caminho
    soma_portas = df.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()
    saturados = soma_portas[soma_portas["PORTAS"] > 128]

    st.subheader("🚨 Caminhos de Rede Saturados")
    if not saturados.empty:
        for _, row in saturados.iterrows():
            st.error(f"""
**{row['CAMINHO_REDE']}**
- Portas totais: {row['PORTAS']}
- Situação: Fora do padrão (máximo permitido: 128 portas)
            """)
    else:
        st.success("Todos os caminhos de rede estão dentro do padrão de 128 portas.")

