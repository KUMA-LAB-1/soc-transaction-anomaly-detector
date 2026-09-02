from collections.abc import Iterable, Mapping
from dataclasses import fields
from typing import Any

import pandas as pd

from .contracts import GenerationTruth, SyntheticRecord

CAMPOS_GROUND_TRUTH = frozenset(campo.name for campo in fields(GenerationTruth))


def _validar_ausencia_ground_truth(
    dados: Mapping[str, Any],
    origem: str,
) -> None:
    """Impede que campos de ground truth atravessem a fronteira de modelagem."""
    campos_ground_truth_expostos = CAMPOS_GROUND_TRUTH.intersection(dados)

    if campos_ground_truth_expostos:
        campos = ", ".join(sorted(campos_ground_truth_expostos))
        raise ValueError(
            f"Dataset sintético inválido: ground truth exposto em {origem}: {campos}."
        )


def _validar_registro(registro: SyntheticRecord) -> None:
    """Valida a separação entre observáveis, labels e ground truth."""
    _validar_ausencia_ground_truth(
        registro.observables,
        "observáveis",
    )
    _validar_ausencia_ground_truth(
        registro.operational_labels,
        "labels operacionais",
    )

    colisoes = set(registro.observables).intersection(registro.operational_labels)

    if colisoes:
        campos = ", ".join(sorted(colisoes))
        raise ValueError(
            "Dataset sintético inválido: colisão entre observáveis e "
            f"labels operacionais: {campos}."
        )


def projetar_dataset_modelagem(
    registros: Iterable[SyntheticRecord],
) -> pd.DataFrame:
    """Projeta somente informações permitidas para o dataset de modelagem."""
    linhas = []

    for registro in registros:
        _validar_registro(registro)

        linhas.append(
            {
                **registro.observables,
                **registro.operational_labels,
            }
        )

    return pd.DataFrame(linhas)


def projetar_ground_truth(
    registros: Iterable[SyntheticRecord],
) -> pd.DataFrame:
    """Projeta a verdade de geração separadamente para avaliação."""
    linhas = []

    for registro in registros:
        linhas.append(
            {
                "id_transacao": registro.observables["id_transacao"],
                "scenario": registro.truth.scenario,
                "is_suspicious": registro.truth.is_suspicious,
                "attack_profile": registro.truth.attack_profile,
                "expected_mitre_techniques": (registro.truth.expected_mitre_techniques),
            }
        )

    return pd.DataFrame(linhas)
