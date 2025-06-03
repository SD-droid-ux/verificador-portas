import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Verificador de Portas", layout="wide")
st.title("🔍 Verificador de Caminhos de Rede Saturados")

uploaded_file = st.sidebar.file_uploader("📁 Envie a planilha Excel", type=[".xlsx"])

if uploaded_file:
    progress_bar = st.sidebar.progress(0, text="Lendo arquivo...")
    df = pd.read_excel(uploaded_file)

    # Verifica duplicatas
    duplicated_cols = df.columns[df.columns.duplicated()].tolist()
    colunas_esperadas = ['POP', 'CHASSI', 'PLACA', 'OLT', 'PORTAS']
    colunas_ausentes = [col for col in colunas_esperadas if col not in df.columns]

    if duplicated_cols or colunas_ausentes:
        st.error("⚠️ Problemas encontrados na base:")
        if duplicated_cols:
            st.error(f"🔁 Colunas duplicadas: {duplicated_cols}")
        if colunas_ausentes:
            st.error(f"❌ Colunas ausentes: {colunas_ausentes}")
        st.stop()

    # Normaliza tipos e cria identificador do caminho
    df['PORTAS'] = pd.to_numeric(df['PORTAS'], errors='coerce')
    df['CAMINHO_REDE'] = df['POP'].astype(str) + " / " + df['CHASSI'].astype(str) + " / " + df['PLACA'].astype(str) + " / " + df['OLT'].astype(str)

    aba = st.sidebar.radio("Escolha uma aba:", ["1️⃣ Visão Geral", "2️⃣ Filtrar por Cidade (Saturados)", "3️⃣ Buscar por CTO"])

    if aba == "1️⃣ Visão Geral":
        st.subheader("📊 Visão Geral dos Caminhos de Rede")
        caminho_group = df.groupby('CAMINHO_REDE')['PORTAS'].sum().reset_index()
        caminho_group['STATUS'] = caminho_group['PORTAS'].apply(lambda x: '🔴 Saturado' if x > 128 else '🟢 OK')
        st.dataframe(caminho_group)

    elif aba == "2️⃣ Filtrar por Cidade (Saturados)":
        st.subheader("🏙️ Caminhos Saturados por Cidade")
        cidades = df['CIDADE'].dropna().unique()
        cidade_escolhida = st.selectbox("Escolha a cidade:", cidades)

        if st.button("🔎 Buscar Caminhos Saturados"):
            progress = st.progress(0, text="Analisando dados...")
            df_cidade = df[df['CIDADE'] == cidade_escolhida].copy()

            df_cidade['CAMINHO_REDE'] = df_cidade['POP'].astype(str) + " / " + df_cidade['CHASSI'].astype(str) + " / " + df_cidade['PLACA'].astype(str) + " / " + df_cidade['OLT'].astype(str)
            total = len(df_cidade['CAMINHO_REDE'].unique())
            saturados = []
            for i, (caminho, grupo) in enumerate(df_cidade.groupby('CAMINHO_REDE')):
                soma = grupo['PORTAS'].sum()
                if soma > 128:
                    saturados.append({"CAMINHO": caminho, "PORTAS": soma})
                progress.progress(int((i + 1) / total * 100), text=f"Analisando {i + 1}/{total} caminhos...")

            resultado = pd.DataFrame(saturados)
            if not resultado.empty:
                st.success(f"✅ {len(resultado)} caminhos saturados encontrados!")
                st.dataframe(resultado)
            else:
                st.info("Nenhum caminho saturado encontrado.")

    elif aba == "3️⃣ Buscar por CTO":
        st.subheader("🔍 Análise por CTO")
        ctos_input = st.text_area("Insira os IDs das CTOs (um por linha):")

        if st.button("🔎 Buscar CTOs"):
            progress = st.progress(0, text="Analisando CTOs...")
            ctos = [cto.strip() for cto in ctos_input.strip().split("\n") if cto.strip()]
            df_filtrado = df[df['ID CTO'].isin(ctos)].copy()

            total = len(ctos)
            resultados = []
            for i, cto in enumerate(ctos):
                linha = df[df['ID CTO'] == cto]
                if not linha.empty:
                    portas = int(linha['PORTAS'].values[0])
                    caminho = linha['CAMINHO_REDE'].values[0]
                    soma = df[df['CAMINHO_REDE'] == caminho]['PORTAS'].sum()
                    status = []
                    if portas == 16:
                        status.append("🟡 16 portas (fora do padrão)")
                    elif portas == 8 and soma <= 128:
                        status.append("🟢 OK")
                    if soma > 128:
                        status.append("🔴 Caminho Saturado")
                    resultados.append({"CTO": cto, "PORTAS": portas, "CAMINHO": caminho, "STATUS": ", ".join(status)})
                else:
                    resultados.append({"CTO": cto, "PORTAS": "-", "CAMINHO": "Não encontrado", "STATUS": "❌ Não encontrada"})
                progress.progress(int((i + 1) / total * 100), text=f"Analisando {i + 1}/{total} CTOs...")

            st.dataframe(pd.DataFrame(resultados))
else:
    st.warning("⚠️ Envie um arquivo Excel para iniciar.")
