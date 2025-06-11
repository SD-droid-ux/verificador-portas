import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🔍 Busca por CTOs Ativas")

# Upload da base
arquivo = st.file_uploader("Envie a base de dados", type=[".xlsx"])

if arquivo:
    df_base = pd.read_excel(arquivo)

    # Entrada da lista de CTOs a serem buscadas
    st.subheader("🔎 Insira as CTOs para análise (uma por linha):")
    input_ctos = st.text_area("Lista de CTOs").upper().splitlines()
    input_ctos = [cto.strip() for cto in input_ctos if cto.strip()]

    # Verifica se há CTOs não ativadas
    ctos_nao_ativadas = df_base[
        (df_base["cto"].str.upper().isin(input_ctos)) &
        (df_base["status_cto"].str.upper() != "ATIVADO")
    ]

    # Filtra CTOs ATIVADAS e solicitadas
    df_ctos = df_base[
        (df_base["cto"].str.upper().isin(input_ctos)) &
        (df_base["status_cto"].str.upper() == "ATIVADO")
    ].copy()

    if not df_ctos.empty:
        # Cria coluna de identificação da PON
        df_ctos["pon_id"] = df_ctos["pop"].astype(str) + "/" + df_ctos["slot"].astype(str) + "/" + df_ctos["olt"].astype(str) + "/" + df_ctos["pon"].astype(str)

        # Calcula portas por PON
        total_portas_pon = df_base[df_base["status_cto"].str.upper() == "ATIVADO"].copy()
        total_portas_pon["pon_id"] = total_portas_pon["pop"].astype(str) + "/" + total_portas_pon["slot"].astype(str) + "/" + total_portas_pon["olt"].astype(str) + "/" + total_portas_pon["pon"].astype(str)
        pon_portas = total_portas_pon.groupby("pon_id")["portas"].sum().to_dict()

        # CTOs já indicadas como troca
        ctos_indicadas = []

        def classificar(row):
            cto = row["cto"].upper()
            pon_id = row["pon_id"]
            portas = row["portas"]
            pon_total = pon_portas.get(pon_id, 0)

            if portas == 8:
                if pon_total >= 128:
                    return "🔴 CTO É SP8 MAS PON JÁ ESTÁ SATURADA", ""
                else:
                    novas_portas = 0
                    ctos_na_pon = total_portas_pon[(total_portas_pon["pon_id"] == pon_id) & (total_portas_pon["portas"] == 8)]
                    for _, sp8 in ctos_na_pon.iterrows():
                        if sp8["cto"].upper() in ctos_indicadas or sp8["cto"].upper() == cto:
                            novas_portas += 8
                    if pon_total + novas_portas > 128:
                        return "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE DE PORTAS NA PON", ""
                    else:
                        ctos_indicadas.append(cto)
                        return "✅ TROCA DE SP8 PARA SP16", ""

            elif portas == 16:
                if pon_total >= 128:
                    return "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA", ""
                else:
                    ctos_sp8_candidatas = total_portas_pon[
                        (total_portas_pon["pon_id"] == pon_id) &
                        (total_portas_pon["portas"] == 8) &
                        (~total_portas_pon["cto"].str.upper().isin(ctos_indicadas))
                    ]
                    if not ctos_sp8_candidatas.empty:
                        cto_sugerida = ctos_sp8_candidatas.iloc[0]["cto"]
                        return "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA", cto_sugerida
                    else:
                        return "✅ CTO JÁ É SP16 MAS A PON NÃO ESTÁ SATURADA", ""

            return "⚪ STATUS INDEFINIDO", ""

        df_ctos[["STATUS", "CTO_SUGERIDA_TROCA"]] = df_ctos.apply(lambda row: pd.Series(classificar(row)), axis=1)

        st.subheader("✅ Resultado da Análise para CTOs Ativas")
        st.dataframe(df_ctos)

    else:
        st.warning("Nenhuma CTO ATIVADA encontrada na lista fornecida.")

    if not ctos_nao_ativadas.empty:
        st.markdown("---")
        st.subheader("⚠️ CTOs Encontradas, mas NÃO ATIVADAS")
        st.dataframe(ctos_nao_ativadas)
