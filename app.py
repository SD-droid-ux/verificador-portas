import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🔍 Verificador de Portas - CTOs Ativas")

# Upload da base
arquivo = st.file_uploader("Envie a base de dados", type=[".xlsx"])

if arquivo:
    df_base = pd.read_excel(arquivo)

    # Exibir CTOs NÃO ATIVADAS separadamente
    ctos_nao_ativadas = df_base[df_base["status_cto"].str.upper() != "ATIVADO"]

    # Filtrar apenas CTOs ATIVADAS
    df_ctos = df_base[df_base["status_cto"].str.upper() == "ATIVADO"].copy()

    # Criar coluna de identificação da PON
    df_ctos["pon_id"] = df_ctos["pop"].astype(str) + "/" + df_ctos["slot"].astype(str) + "/" + df_ctos["olt"].astype(str) + "/" + df_ctos["pon"].astype(str)

    # Total de portas por PON
    total_portas_pon = df_ctos.groupby("pon_id")["portas"].sum().to_dict()

    # CTOs já indicadas como TROCA
    if "STATUS" in df_ctos.columns:
        ctos_indicadas = df_ctos[df_ctos["STATUS"].str.contains("TROCA", na=False)]["cto"].str.upper().tolist()
    else:
        ctos_indicadas = []

    def classificar(row):
        cto = row["cto"].upper()
        pon_id = row["pon_id"]
        portas = row["portas"]
        pon_total = total_portas_pon.get(pon_id, 0)

        if portas == 8:
            if pon_total >= 128:
                return "🔴 CTO É SP8 MAS PON JÁ ESTÁ SATURADA", ""
            else:
                novas_portas = 0
                ctos_na_pon = df_ctos[(df_ctos["pon_id"] == pon_id) & (df_ctos["portas"] == 8)]
                for _, sp8 in ctos_na_pon.iterrows():
                    if sp8["cto"].upper() in ctos_indicadas or sp8["cto"].upper() == cto:
                        novas_portas += 8
                if pon_total + novas_portas > 128:
                    return "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE DE PORTAS NA PON", ""
                else:
                    return "✅ TROCA DE SP8 PARA SP16", ""

        elif portas == 16:
            if pon_total >= 128:
                return "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA", ""
            else:
                ctos_sp8_candidatas = df_ctos[
                    (df_ctos["pon_id"] == pon_id) &
                    (df_ctos["portas"] == 8) &
                    (~df_ctos["cto"].str.upper().isin(ctos_indicadas))
                ]
                if not ctos_sp8_candidatas.empty:
                    cto_sugerida = ctos_sp8_candidatas.iloc[0]["cto"]
                    return "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA", cto_sugerida
                else:
                    return "✅ CTO JÁ É SP16 MAS A PON NÃO ESTÁ SATURADA", ""

        return "⚪ STATUS INDEFINIDO", ""

    df_ctos[["STATUS", "CTO_SUGERIDA_TROCA"]] = df_ctos.apply(lambda row: pd.Series(classificar(row)), axis=1)

    st.subheader("✅ Resultado da Análise para CTOs Ativadas")
    st.dataframe(df_ctos)

    if not ctos_nao_ativadas.empty:
        st.markdown("---")
        st.subheader("⚠️ CTOs Não Ativadas Encontradas na Base")
        st.dataframe(ctos_nao_ativadas)
