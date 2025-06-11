import streamlit as st
import pandas as pd
import os
import time
from io import BytesIO

st.title("🔍 Buscar por CTO")

# Função para exportar DataFrame para Excel em memória
def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# Caminho da base de dados
caminho_base = os.path.join("pages", "base_de_dados", "base.xlsx")

# Carrega os dados da base
if "df" not in st.session_state or "portas_por_caminho" not in st.session_state:
    try:
        df = pd.read_excel(caminho_base)
        df["CAMINHO_REDE"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)
        st.session_state["df"] = df
        st.session_state["portas_por_caminho"] = df.groupby("CAMINHO_REDE")["portas"].sum().to_dict()
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

        df_ctos = df[df["cto"].str.upper().isin(input_ctos)].copy()
        df_ctos["ordem"] = pd.Categorical(df_ctos["cto"].str.upper(), categories=input_ctos, ordered=True)
        df_ctos = df_ctos.sort_values("ordem").drop(columns=["ordem"])

        df_ctos["CAMINHO_REDE"] = df_ctos["pop"].astype(str) + "/" + df_ctos["olt"].astype(str) + "/" + df_ctos["slot"].astype(str) + "/" + df_ctos["pon"].astype(str)

        # Separa CTOs ativas e inativas
        df_ativadas = df_ctos[df_ctos["status_cto"].str.upper() == "ATIVADO"].copy()
        df_inativas = df_ctos[df_ctos["status_cto"].str.upper() != "ATIVADO"].copy()

        input_ctos_upper = set(input_ctos)
        ctos_trocadas = set()

        def classificar(row):
            caminho = row["CAMINHO_REDE"]
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
                    (df["CAMINHO_REDE"] == caminho) &
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

        df_ativadas[["STATUS", "CTO_SUGERIDA_TROCA"]] = df_ativadas.apply(lambda row: pd.Series(classificar(row)), axis=1)

        st.success(f"✅ {len(df_ativadas)} CTO(s) ativadas analisadas.")
        st.dataframe(df_ativadas)

        st.download_button(
            label="📥 Baixar Resultado (.xlsx)",
            data=to_excel_bytes(df_ativadas),
            file_name="resultado_ctos_ativadas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("📌 CTOs Não Ativadas Encontradas")
        if not df_inativas.empty:
            st.dataframe(df_inativas)
            st.download_button(
                label="📥 Baixar CTOs Inativas (.xlsx)",
                data=to_excel_bytes(df_inativas),
                file_name="ctos_nao_ativadas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("✅ Todas as CTOs informadas estão ativas.")

        progress_bar.empty()
