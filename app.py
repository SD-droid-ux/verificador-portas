import streamlit as st
import pandas as pd

st.set_page_config(page_title="Verificador de Portas CTO", layout="wide")
st.title("🔎 Verificador de Caminhos de Rede com Excesso de Portas")

# Upload da planilha
uploaded_file = st.file_uploader("📤 Envie a planilha Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Leitura e limpeza inicial
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()

        st.subheader("📋 Colunas encontradas:")
        colunas = df.columns.tolist()
        st.write(colunas)

        # Verifica colunas duplicadas
        colunas_duplicadas = df.columns[df.columns.duplicated()].tolist()
        if colunas_duplicadas:
            st.warning(f"⚠️ Colunas duplicadas encontradas: {colunas_duplicadas}")
        else:
            st.success("✅ Não há colunas duplicadas.")

        # Colunas essenciais
        col_essenciais = ["POP", "CHASSI", "PLACA", "OLT", "PORTAS"]
        ausentes = [col for col in col_essenciais if col not in df.columns]
        if ausentes:
            st.error(f"❌ Colunas essenciais ausentes: {ausentes}")
            st.stop()
        else:
            st.success("✅ Todas as colunas essenciais estão presentes.")

        # Filtro por cidade
        cidades = df["CIDADE"].dropna().unique().tolist()
        cidade_selecionada = st.selectbox("🌆 Filtrar por cidade:", ["Todas"] + sorted(cidades))

        if cidade_selecionada != "Todas":
            df = df[df["CIDADE"] == cidade_selecionada]

        # Criar coluna de identificação do Caminho de Rede
        df["CAMINHO_REDE"] = (
            df["POP"].astype(str) + " / " +
            df["CHASSI"].astype(str) + " / " +
            df["PLACA"].astype(str) + " / " +
            df["OLT"].astype(str)
        )

        # Calcular total de portas por caminho
        soma_portas = df.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()
        soma_portas.columns = ["CAMINHO_REDE", "TOTAL_PORTAS"]
        saturados = soma_portas[soma_portas["TOTAL_PORTAS"] > 128]

        st.subheader("📊 Caminhos de Rede fora do padrão (mais de 128 portas):")

        if not saturados.empty:
            for _, row in saturados.iterrows():
                st.error(f"🚨 {row['CAMINHO_REDE']}\nTotal de portas: {row['TOTAL_PORTAS']}")
        else:
            st.success("✅ Nenhum Caminho de Rede ultrapassa 128 portas.")

        # Exibir tabela completa se desejar
        with st.expander("🔍 Ver tabela original"):
            st.dataframe(df)

    except Exception as e:
        st.error("❌ Erro ao processar a planilha.")
        st.exception(e)
else:
    st.info("👈 Envie um arquivo Excel para iniciar a análise.")
