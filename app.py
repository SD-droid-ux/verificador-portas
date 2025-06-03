import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Verificador de Portas", layout="wide")
st.title("📊 Verificador de Caminhos de Rede Saturados")

uploaded_file = st.file_uploader("📁 Envie a planilha Excel (.xlsx)", type="xlsx")

if uploaded_file:
    progress_text = "⏳ Analisando o arquivo..."
    progress_bar = st.progress(0, text=progress_text)

    df = pd.read_excel(uploaded_file, header=0)
    df.columns = df.columns.astype(str).str.strip()

    time.sleep(0.3)
    progress_bar.progress(10, text=progress_text)

    col_duplicadas = df.columns[df.columns.duplicated()].tolist()
    col_essenciais = ['POP', 'CHASSI', 'PLACA', 'OLT', 'PORTAS']

    if col_duplicadas:
        st.warning(f"⚠️ Colunas duplicadas encontradas: {col_duplicadas}")

    col_ausentes = [col for col in col_essenciais if col not in df.columns]
    if col_ausentes:
        st.error(f"❌ Colunas essenciais ausentes: {col_ausentes}")
    else:
        for col in col_essenciais:
            df[col] = df[col].astype(str)

        df["PORTAS"] = pd.to_numeric(df["PORTAS"], errors="coerce").fillna(0).astype(int)

        time.sleep(0.3)
        progress_bar.progress(30, text=progress_text)

        df["CAMINHO_REDE"] = df["POP"] + " / " + df["CHASSI"] + " / " + df["PLACA"] + " / " + df["OLT"]

        time.sleep(0.3)
        progress_bar.progress(50, text=progress_text)

        caminho_rede = df.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()
        caminho_rede.columns = ["CAMINHO_REDE", "TOTAL_PORTAS"]

        saturados = caminho_rede[caminho_rede["TOTAL_PORTAS"] > 128]

        time.sleep(0.3)
        progress_bar.progress(80, text=progress_text)

        df = df.merge(caminho_rede, on="CAMINHO_REDE", how="left")
        df['STATUS_CAMINHO'] = df['TOTAL_PORTAS'].apply(lambda x: "Saturado" if x > 128 else "OK")

        time.sleep(0.2)
        progress_bar.progress(100, text="✅ Análise concluída!")

        aba1, aba2, aba3 = st.tabs(["1. Análise Geral", "2. Filtro por Cidade", "3. Consulta por CTO"])

        with aba1:
            st.subheader("🔎 Caminhos de Rede com Excesso de Portas")
            if saturados.empty:
                st.success("Todos os caminhos de rede estão dentro do padrão (até 128 portas). ✅")
            else:
                for _, row in saturados.iterrows():
                    st.error(f"🚨 Caminho de Rede: {row['CAMINHO_REDE']} | Portas: {row['TOTAL_PORTAS']}")

        with aba2:
            cidades = sorted(df["CIDADE"].dropna().unique())
            cidade_selecionada = st.selectbox("Selecione a cidade:", cidades)
            df_filtrado = df[df["CIDADE"] == cidade_selecionada]
            st.dataframe(df_filtrado)

        with aba3:
            st.title("🔍 3. Consulta por CTO")
            st.markdown("Insira os ID das CTOs separados por vírgula (ex: `CTO001, CTO002, CTO003`)")
            input_ctos = st.text_area("Lista de CTOs", height=100)

            if input_ctos:
                lista_ctos = [cto.strip() for cto in input_ctos.split(",") if cto.strip()]
                df_ctos = df[df["ID CTO"].isin(lista_ctos)].copy()

                if df_ctos.empty:
                    st.warning("Nenhuma CTO encontrada na base.")
                else:
                    caminho_rede_portas = df.groupby("CAMINHO_REDE")["PORTAS"].sum().reset_index()
                    caminho_rede_portas.columns = ["CAMINHO_REDE", "PORTAS_TOTAL"]

                    df_ctos = df_ctos.merge(caminho_rede_portas, on="CAMINHO_REDE", how="left")
                    df_ctos["STATUS_CAMINHO"] = df_ctos["PORTAS_TOTAL"].apply(
                        lambda x: "Saturado" if x > 128 else "OK"
                    )

                    st.success(f"✅ {len(df_ctos)} CTO(s) encontradas.")
                    st.dataframe(df_ctos[[
                        "ID CTO", "CAMINHO_REDE", "PORTAS", "PORTAS_TOTAL", "STATUS_CAMINHO"
                    ]].sort_values("CAMINHO_REDE"))
else:
    st.info("📂 Aguardando envio da planilha Excel para iniciar a análise.")
