import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Verificador de Portas", layout="wide")

st.title("🔌 Verificador de Portas por Caminho de Rede")

uploaded_file = st.file_uploader("📂 Envie o arquivo Excel com os dados das CTOs", type=[".xlsx"])

if uploaded_file:
    progress_bar = st.progress(0, text="⏳ Analisando dados...")

    for i in range(100):
        time.sleep(0.01)  # Simula processamento real
        progress_bar.progress(i + 1, text=f"⏳ Analisando dados... {i + 1}%")

    df = pd.read_excel(uploaded_file, dtype=str)
    df.columns = [str(col).strip().upper() for col in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    colunas_essenciais = ["POP", "CHASSI", "PLACA", "OLT", "PORTAS", "ID CTO", "CIDADE"]
    if not all(col in df.columns for col in colunas_essenciais):
        st.error("❌ Algumas colunas essenciais estão ausentes na planilha. Verifique a estrutura do arquivo.")
    else:
        df["PORTAS"] = pd.to_numeric(df["PORTAS"], errors="coerce")
        df["CAMINHO_REDE"] = df["POP"] + " / " + df["CHASSI"] + " / " + df["PLACA"] + " / " + df["OLT"]

        grupo = df.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()
        grupo_saturado = grupo[grupo["PORTAS"] > 128]
        caminhos_saturados = grupo_saturado["CAMINHO_REDE"].tolist()

        st.subheader("1️⃣ Visão Geral")
        st.write("Todos os caminhos de rede (sem filtro de saturação):")
        st.dataframe(grupo)

        st.subheader("2️⃣ Caminhos de Rede Saturados por Cidade")
        cidades = df["CIDADE"].dropna().unique().tolist()
        cidade_selecionada = st.selectbox("Selecione a cidade", sorted(cidades))

        saturados_filtrados = df[df["CAMINHO_REDE"].isin(caminhos_saturados)]
        saturados_filtrados = saturados_filtrados[saturados_filtrados["CIDADE"] == cidade_selecionada]

        st.write(f"Caminhos de rede saturados em **{cidade_selecionada}**:")
        st.dataframe(saturados_filtrados)

        st.subheader("3️⃣ Consulta por CTO")
        st.write("Digite as CTOs separadas por linha. Exemplo:")
        st.code("CTO001\nCTO002\nCTO003")

        cto_input = st.text_area("Insira as CTOs", height=150)

        if st.button("🔍 Buscar CTOs"):
            lista_ctos = [cto.strip().upper() for cto in cto_input.splitlines() if cto.strip()]
            df_ctos = df[df["ID CTO"].isin(lista_ctos)]

            if df_ctos.empty:
                st.warning("Nenhuma CTO encontrada na base de dados.")
            else:
                def avaliar_cto(row):
                    caminho = row["CAMINHO_REDE"]
                    portas = row["PORTAS"]
                    if pd.isna(portas):
                        return "⚠️ Portas indefinidas"
                    if caminho in caminhos_saturados:
                        return f"🔴 {int(portas)} portas (Caminho Saturado)"
                    elif int(portas) == 16:
                        return "🟡 16 portas (fora do padrão)"
                    elif int(portas) == 8:
                        return "🟢 8 portas (ok)"
                    else:
                        return f"⚠️ {int(portas)} portas (verificar)"

                df_ctos["AVALIAÇÃO"] = df_ctos.apply(avaliar_cto, axis=1)
                st.dataframe(df_ctos[["ID CTO", "CAMINHO_REDE", "PORTAS", "AVALIAÇÃO"]])
