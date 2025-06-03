import streamlit as st
import pandas as pd

st.set_page_config(page_title="Verificador de Portas", layout="wide")
st.title("🔌 Verificador de Portas por Caminho de Rede")

uploaded_file = st.file_uploader("📤 Envie a planilha Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Verificar colunas duplicadas
        duplicated_columns = df.columns[df.columns.duplicated()].tolist()
        if duplicated_columns:
            st.error("❌ Há colunas duplicadas na planilha! Corrija antes de continuar.")
            st.warning(f"Colunas duplicadas encontradas: {duplicated_columns}")
        else:
            # Criar coluna de caminho de rede
            df["CAMINHO_REDE"] = (
                df["POP"].astype(str)
                + " / "
                + df["CHASSI"].astype(str)
                + " / "
                + df["PLACA"].astype(str)
                + " / "
                + df["OLT"].astype(str)
            )

            # Filtro por cidade
            cidades = df["CIDADE"].dropna().unique().tolist()
            cidade_selecionada = st.selectbox("🏙️ Selecione uma cidade", ["Todas"] + cidades)

            if cidade_selecionada != "Todas":
                df = df[df["CIDADE"] == cidade_selecionada]

            st.subheader("📋 Dados da Planilha")
            st.dataframe(df, use_container_width=True)

            # Agrupar e somar portas por caminho de rede
            st.subheader("🚨 Caminhos de Rede Saturados (>128 portas)")
            portas_por_caminho = df.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()
            saturados = portas_por_caminho[portas_por_caminho["PORTAS"] > 128]

            if not saturados.empty:
                for _, row in saturados.iterrows():
                    st.error(
                        f'Caminho de Rede: **{row["CAMINHO_REDE"]}** — '
                        f'🔴 Total de portas: **{row["PORTAS"]}** (limite: 128)'
                    )
            else:
                st.success("✅ Nenhum caminho de rede ultrapassou 128 portas.")

    except Exception as e:
        st.error("❌ Ocorreu um erro ao processar a planilha.")
        st.exception(e)
