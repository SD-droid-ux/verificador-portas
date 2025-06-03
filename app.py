import streamlit as st
import pandas as pd
import time

st.set_page_config(layout="wide")
st.title("📊 Verificador de Portas por Caminho de Rede")

uploaded_file = st.file_uploader("📂 Envie a planilha Excel", type=[".xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = df.loc[:, ~df.columns.duplicated()]

    colunas_essenciais = ["POP", "CHASSI", "PLACA", "OLT", "PORTAS", "ID CTO", "CIDADE"]
    if not all(col in df.columns for col in colunas_essenciais):
        st.error("❌ Colunas essenciais ausentes na planilha. Verifique se possui: " + ", ".join(colunas_essenciais))
    else:
        df["CAMINHO_REDE"] = df["POP"].astype(str) + " / " + df["CHASSI"].astype(str) + " / " + df["PLACA"].astype(str) + " / " + df["OLT"].astype(str)

        aba = st.sidebar.radio("Selecione a aba", ["1. Visão Geral", "2. Filtro por Cidade", "3. Buscar por CTO"])

        if aba == "1. Visão Geral":
            with st.spinner("🔄 Carregando visão geral..."):
                progress_bar = st.progress(0)
                for i in range(5):
                    time.sleep(0.2)
                    progress_bar.progress((i + 1) * 20)

                total_ctos = len(df)
                total_portas = df["PORTAS"].sum()
                caminho_rede_grupo = df.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()
                saturados = caminho_rede_grupo[caminho_rede_grupo["PORTAS"] > 128]

            progress_bar.empty()

            st.metric("🔢 Total de CTOs", total_ctos)
            st.metric("🔌 Total de Portas", total_portas)
            st.metric("🔴 Caminhos Saturados", len(saturados))

        elif aba == "2. Filtro por Cidade":
            cidade = st.selectbox("Selecione a Cidade", df["CIDADE"].unique())

            if st.button("🔍 Filtrar Caminhos Saturados"):
                with st.spinner("🔄 Analisando cidade selecionada..."):
                    progress_bar = st.progress(0)
                    for i in range(5):
                        time.sleep(0.2)
                        progress_bar.progress((i + 1) * 20)

                    df_cidade = df[df["CIDADE"] == cidade]
                    grupo = df_cidade.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()
                    saturados = grupo[grupo["PORTAS"] > 128]

                    st.subheader(f"Caminhos Saturados em {cidade}")
                    st.dataframe(saturados)

                progress_bar.empty()

               elif aba == "3. Buscar por CTO":
            input_ctos = st.text_area("Insira os ID das CTOs (uma por linha)").splitlines()

            if st.button("🔍 Buscar CTOs"):
                with st.spinner("🔄 Analisando CTOs..."):
                    progress_bar = st.progress(0)
                    for i in range(5):
                        time.sleep(0.2)
                        progress_bar.progress((i + 1) * 20)

                    df_ctos = df[df["ID CTO"].isin(input_ctos)]

                    def verificar_status(linha):
                        total = df[df["CAMINHO_REDE"] == linha["CAMINHO_REDE"]]["PORTAS"].sum()
                        if total > 128:
                            return "🔴 Saturado"
                        elif linha["PORTAS"] == 16:
                            return "⚠️ 16 portas (fora padrão)"
                        else:
                            return "✅ OK"

                    df_ctos["STATUS"] = df_ctos.apply(verificar_status, axis=1)

                    # Ordenar na mesma ordem da entrada
                    df_ctos["ID CTO"] = pd.Categorical(df_ctos["ID CTO"], categories=input_ctos, ordered=True)
                    df_ctos = df_ctos.sort_values("ID CTO")

                    # Remover coluna 'Unnamed: 0' se existir
                    df_ctos = df_ctos.loc[:, ~df_ctos.columns.str.contains("^Unnamed")]

                    st.dataframe(df_ctos)

                progress_bar.empty()

else:
    st.info("📥 Aguarde o envio de um arquivo para iniciar a análise.")
