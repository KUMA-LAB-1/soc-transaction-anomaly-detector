def selecionar_melhor_detector(
    resultados_validos: list[dict],
) -> dict:
    """Seleciona o melhor detector pelos critérios definidos pelo projeto.

    Critérios, nesta ordem:
    1. maior F1-score;
    2. maior recall;
    3. maior precision;
    4. menor tempo de execução.
    """
    if not resultados_validos:
        raise RuntimeError(
            "Nenhum detector de anomalia conseguiu concluir o treinamento."
        )

    return max(
        resultados_validos,
        key=lambda resultado: (
            resultado["f1_vs_status_real"],
            resultado["recall_vs_status_real"],
            resultado["precision_vs_status_real"],
            -resultado["tempo_segundos"],
        ),
    )
