import streamlit as st
import pandas as pd

st.title("🔍 Diagnóstico da Planilha")

uploaded_file = st.file_uploader("📤 Envie a planilha Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0)
        df.columns = df.columns.str.strip()  # Remove espaços extras

        st.subheader("📑 Lista de colunas encontradas:")
        st.write(df.columns.tolist())

        if "POP" not in df.columns:
            st.error("❌ A coluna 'POP' não foi encontrada. Verifique o nome exato no Excel.")
        else:
            st.success("✅ Coluna 'POP' encontrada com sucesso!")

    except Exception as e:
        st.error("Erro ao carregar a planilha.")
        st.exception(e)
