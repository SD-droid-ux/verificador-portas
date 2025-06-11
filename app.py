def classificar(row, df, portas_por_caminho, input_ctos_upper, ctos_trocadas):
    caminho = row["CAMINHO_REDE"]
    total_portas = portas_por_caminho.get(caminho, 0)

    # Caso 1: CTO SP8 e pode ser trocada (sem ultrapassar 128)
    if row["portas"] == 8 and total_portas < 128:
        if total_portas + 8 <= 128:
            ctos_trocadas.add(row["cto"].upper())
            return "✅ TROCA DE SP8 PARA SP16", ""
        else:
            return "⚠️ TROCA DE SP8 PARA SP16 EXCEDE LIMITE DE PORTAS NA PON", ""

    # Caso 2: CTO SP16 já instalada
    if row["portas"] == 16:
        if total_portas >= 128:
            return "🔴 PON JÁ ESTÁ SATURADA", ""

        # Busca CTOs SP8 disponíveis no mesmo caminho de rede
        sp8_disponiveis = df[
            (df["CAMINHO_REDE"] == caminho) &
            (df["portas"] == 8) &
            (~df["cto"].str.upper().isin(input_ctos_upper)) &  # não foi indicada manualmente
            (~df["cto"].str.upper().isin(ctos_trocadas))       # ainda não foi trocada
        ]

        for _, sp8_cto in sp8_disponiveis.iterrows():
            nova_soma = total_portas - 8 + 16
            if nova_soma <= 128:
                # Encontrou uma CTO SP8 válida
                return "✅ CTO JÁ É SP16 MAS PODE TROCAR SP8 NO CAMINHO", sp8_cto["cto"]

        # Se nenhuma CTO SP8 puder ser trocada sem saturar
        return "🔴 CTO É SP16 MAS PON JÁ ESTÁ SATURADA", ""

    # Caso padrão (não se aplica)
    return "⚪ STATUS INDEFINIDO", ""
