import streamlit as st
import pandas as pd
import os
import time

st.title("🔍 Buscar por CTO")

# Caminho da base de dados
caminho_base = os.path.join("pages", "base_de_dados", "base.xlsx")

# Carrega os dados da base
if "df" not in st.session_state or "portas_por_caminho" not in st.session_state:
    try:
        df = pd.read_excel(caminho_base)
        df.columns = df.columns.str.lower()  # padroniza colunas para minúsculas
        df["caminho_rede"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)
        st.session_state["df"] = df
        st.session_state["portas_por_caminho"] = df.groupby("caminho_rede")["portas"].sum().to_dict()
    except FileNotFoundError:
        st.warning("⚠️ A base de dados não foi encontrada. Por favor, envie na página principal.")
        st.stop()

# Dados em memória
df = st.session_state["df"]
portas_por_caminho = st.session_state["portas_por_caminho"]

# Entrada do usuário
input_ctos = list(dict.fromkeys(st.text_area("Insira os ID das CTOs (uma por linha)").upper().splitlines()))

# Botão de busca
if st.button("🔍 Buscar CTOs"):
    if not input_ctos or all(not cto.strip() for cto in input_ctos):
        st.warning("⚠️ Insira pelo menos um ID de CTO para buscar.")
        st.stop()

    with st.spinner("🔄 Analisando CTOs..."):
        progress_bar = st.progress(0)
        for i in range(5):
            time.sleep(0.1)
            progress_bar.progress((i + 1) * 20)

        # Filtrar CTOs da lista
        df_input = df[df["cto"].str.upper().isin(input_ctos)].copy()

        # Separar CTOs não ativadas
        df_nao_ativadas = df_input[df_input["status_cto"].str.upper() != "ATIVADO"]
        df_ativadas = df_input[df_input["status_cto"].str.upper() == "ATIVADO"]

        if df_ativadas.empty:
            st.warning("⚠️ Nenhuma das CTOs está ativada.")
        else:
            input_ctos_upper = set(input_ctos)
            ctos_trocadas = set()

            def classificar(row):
                caminho = row["caminho_rede"]
                total_portas = portas_por_caminho.get(caminho, 0)

                if total_portas > 128:
                    return "🔴 SATURADO", ""
                if total_portas == 128 and row["portas"] == 16:
                    return "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA", ""
                if total_portas == 128 and row["portas"] == 8:
                    return "🔴 CTO É SP8 MAS PON JÁ ESTÁ SATURADA", ""

                if row["portas"] == 8 and total_portas < 128:
                    if total_portas + 8 <= 128:
                        ctos_trocadas.add(row["cto"].upper())
                        return "✅ TROCA DE SP8 PARA SP16", ""
                    else:
                        return "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE DE PORTAS NA PON", ""

                if row["portas"] == 16 and total_portas < 128:
                    sp8_disponiveis = df[
                        (df["caminho_rede"] == caminho) &
                        (df["portas"] == 8) &
                        (~df["cto"].str.upper().isin(input_ctos_upper)) &
                        (~df["cto"].str.upper().isin(ctos_trocadas))
                    ]
                    if not sp8_disponiveis.empty:
                        cto_alvo = sp8_disponiveis.iloc[0]["cto"]
                        return "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA", cto_alvo
                    else:
                        return "✅ CTO JÁ É SP16 MAS A PON NÃO ESTÁ SATURADA", ""

                return "⚪ STATUS INDEFINIDO", ""

            df_ativadas["ordem"] = pd.Categorical(df_ativadas["cto"].str.upper(), categories=input_ctos, ordered=True)
            df_ativadas = df_ativadas.sort_values("ordem").drop(columns=["ordem"])
            df_ativadas[["STATUS", "CTO_SUGERIDA_TROCA"]] = df_ativadas.apply(lambda row: pd.Series(classificar(row)), axis=1)

            st.success(f"✅ {len(df_ativadas)} CTO(s) ATIVADAS analisadas.")
            st.dataframe(df_ativadas)

            st.download_button(
                label="📥 Baixar Resultado (.xlsx)",
                data=df_ativadas.to_excel(index=False),
                file_name="resultado_ctos_ativadas.xlsx"
            )

        # Exibir CTOs não ativadas
        if not df_nao_ativadas.empty:
            st.subheader("⚠️ CTOs NÃO ATIVADAS")
            st.dataframe(df_nao_ativadas)

        progress_bar.empty()
