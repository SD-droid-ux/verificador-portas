import streamlit as st
import pandas as pd
import os
from io import BytesIO

st.set_page_config(page_title="Buscar por CTO", layout="wide")
st.title("🔍 Buscar por CTO")

# Caminho fixo para a base
caminho_base = os.path.join("pages", "base_de_dados", "base.xlsx")

# Entrada do usuário
ctos_inputadas_raw = st.text_area("✏️ Lista de CTOs já indicadas (uma por linha):")
ctos_inputadas = [cto.strip().upper() for cto in ctos_inputadas_raw.split("\n") if cto.strip()]

if st.button("🔎 Iniciar Busca de CTOs"):
    try:
        df = pd.read_excel(caminho_base, engine="openpyxl")
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {caminho_base}")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao carregar base: {e}")
        st.stop()

    # Normalização
    df["cto"] = df["cto"].astype(str)
    df["CAMINHO_REDE"] = df["pop"].astype(str) + "/" + df["olt"].astype(str) + "/" + df["slot"].astype(str) + "/" + df["pon"].astype(str)
    df["cto_upper"] = df["cto"].str.upper()

    # Pré-calcular somas e criar lookup de SP8 disponíveis
    portas_por_caminho = df.groupby("CAMINHO_REDE")["portas"].sum().to_dict()
    sp8_por_caminho = {}

    for caminho, grupo in df[df["portas"] == 8].groupby("CAMINHO_REDE"):
        disponiveis = grupo[~grupo["cto_upper"].isin(ctos_inputadas)]["cto"].tolist()
        sp8_por_caminho[caminho] = disponiveis

    # Armazenar CTOs que forem trocadas
    ctos_trocadas = set()
    status_list = []
    trocavel_list = []

    for _, row in df.iterrows():
        caminho = row["CAMINHO_REDE"]
        cto = row["cto_upper"]
        portas_cto = row["portas"]
        total_portas = portas_por_caminho.get(caminho, 0)

        if portas_cto == 8 and total_portas < 128:
            if total_portas + 8 <= 128:
                ctos_trocadas.add(cto)
                status_list.append("✅ TROCA DE SP8 PARA SP16")
                trocavel_list.append("")
                portas_por_caminho[caminho] += 8  # atualiza soma futura
            else:
                status_list.append("⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE")
                trocavel_list.append("")
        elif portas_cto == 16:
            if total_portas >= 128:
                status_list.append("🔴 PON JÁ ESTÁ SATURADA")
                trocavel_list.append("")
            else:
                candidatos = [c for c in sp8_por_caminho.get(caminho, []) if c.upper() not in ctos_inputadas and c.upper() not in ctos_trocadas]
                encontrou = False
                for sp8 in candidatos:
                    nova_soma = total_portas - 8 + 16
                    if nova_soma <= 128:
                        status_list.append("✅ CTO JÁ É SP16 MAS PODE TROCAR SP8")
                        trocavel_list.append(sp8)
                        encontrou = True
                        break
                if not encontrou:
                    status_list.append("🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA")
                    trocavel_list.append("")
        else:
            status_list.append("⚪ STATUS INDEFINIDO")
            trocavel_list.append("")

    df["status"] = status_list
    df["cto_trocavel"] = trocavel_list
    df.drop(columns=["cto_upper"], inplace=True)

    st.success("✅ Análise concluída com sucesso!")
    st.dataframe(df)

    # Exportar Excel
    def to_excel_bytes(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Resultados")
        return output.getvalue()

    st.download_button(
        label="📥 Baixar resultados em Excel",
        data=to_excel_bytes(df),
        file_name="resultado_analise_otimizada.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
