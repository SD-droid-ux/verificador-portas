import streamlit as st
import pandas as pd

st.set_page_config(page_title="Verificador de Portas", layout="wide")
st.title("📊 Verificador de Caminhos de Rede Saturados")

uploaded_file = st.file_uploader("📎 Envie a planilha Excel com os dados", type=["xlsx"])

if uploaded_file:
    progress_bar = st.progress(0, text="🔍 Iniciando análise...")

    # Etapa 1 - Leitura da planilha (tenta pular linhas mal formatadas)
    progress_bar.progress(10, text="📄 Lendo a planilha...")
    found = False
    for skip in range(5):
        df = pd.read_excel(uploaded_file, skiprows=skip)
        df.columns = df.columns.astype(str).str.strip()
        colunas = df.columns.tolist()

        colunas_essenciais = ['POP', 'CHASSI', 'PLACA', 'OLT', 'PORTAS']
        if all(col in colunas for col in colunas_essenciais):
            found = True
            break

    progress_bar.progress(30, text="📑 Verificando colunas...")

    if not found:
        st.error("❌ Não foi possível localizar as colunas essenciais.")
        st.warning(f"⚠️ Colunas lidas: {colunas}")
        st.stop()

    # Etapa 2 - Criação da coluna Caminho de Rede
    progress_bar.progress(50, text="🔗 Gerando Caminhos de Rede...")
    df["CAMINHO_REDE"] = (
        df["POP"].astype(str) + " / " +
        df["CHASSI"].astype(str) + " / " +
        df["PLACA"].astype(str) + " / " +
        df["OLT"].astype(str)
    )

    # Etapa 3 - Conversão de PORTAS
    progress_bar.progress(60, text="🔢 Convertendo dados de portas...")
    df["PORTAS"] = pd.to_numeric(df["PORTAS"], errors="coerce")

    # Etapa 4 - Mostrar os dados
    progress_bar.progress(70, text="📋 Exibindo dados da planilha...")
    st.subheader("📄 Dados da Planilha")
    st.dataframe(df)

    # Etapa 5 - Filtro por cidade
    progress_bar.progress(80, text="🏙️ Aplicando filtro por cidade...")
    cidades = df["CIDADE"].dropna().unique()
    cidade = st.selectbox("Selecione a cidade:", ["Todas"] + list(cidades))

    if cidade != "Todas":
        df = df[df["CIDADE"] == cidade]

    # Etapa 6 - Agrupar e calcular
    progress_bar.progress(90, text="🧮 Agrupando e analisando caminhos de rede...")
    soma_portas = df.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()
    saturados = soma_portas[soma_portas["PORTAS"] > 128]

    # Etapa 7 - Resultado final
    progress_bar.progress(100, text="✅ Análise concluída!")

    if not saturados.empty:
        st.subheader("🚨 Caminhos de Rede Saturados")
        for _, row in saturados.iterrows():
            st.error(f"🔴 {row['CAMINHO_REDE']}\n➡️ Total de portas: {int(row['PORTAS'])} (Limite: 128)")
    else:
        st.success("✅ Todos os Caminhos de Rede estão dentro do limite de 128 portas.")
