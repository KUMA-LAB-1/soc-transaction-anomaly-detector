from collections import Counter
from dataclasses import dataclass
from math import isclose
from typing import TYPE_CHECKING

from .label_policy import STATUS_NORMAL, STATUS_SUSPEITO

if TYPE_CHECKING:
    from .dataset import GeneratedSyntheticDataset


@dataclass(frozen=True, slots=True)
class ScenarioDiagnosticsEntry:
    scenario: str
    observed_count: int
    observed_proportion: float


@dataclass(frozen=True, slots=True)
class OperationalLabelDiagnostics:
    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int

    def __post_init__(self) -> None:
        contagens = (
            self.true_positive,
            self.true_negative,
            self.false_positive,
            self.false_negative,
        )

        for contagem in contagens:
            if isinstance(contagem, bool) or not isinstance(contagem, int):
                raise TypeError("contagens devem ser inteiros.")

            if contagem < 0:
                raise ValueError("contagens devem ser maiores ou iguais a zero.")

    @property
    def false_positive_rate(self) -> float | None:
        total_negativos_reais = self.false_positive + self.true_negative

        if total_negativos_reais == 0:
            return None

        return self.false_positive / total_negativos_reais

    @property
    def false_negative_rate(self) -> float | None:
        total_positivos_reais = self.false_negative + self.true_positive

        if total_positivos_reais == 0:
            return None

        return self.false_negative / total_positivos_reais


@dataclass(frozen=True, slots=True)
class DatasetDiagnostics:
    total_records: int
    scenarios: tuple[ScenarioDiagnosticsEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.scenarios, tuple):
            raise TypeError("scenarios deve ser uma tuple.")

        if sum(entry.observed_count for entry in self.scenarios) != self.total_records:
            raise ValueError("a soma de observed_count deve ser igual a total_records.")

        for entry in self.scenarios:
            expected_proportion = (
                entry.observed_count / self.total_records if self.total_records else 0.0
            )

            if not isclose(
                entry.observed_proportion,
                expected_proportion,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ValueError(
                    "observed_proportion deve corresponder a observed_count "
                    "sobre total_records."
                )


def analyze_synthetic_dataset(
    dataset: "GeneratedSyntheticDataset",
) -> DatasetDiagnostics:
    total_records = len(dataset.records)

    contagens = Counter(registro.truth.scenario for registro in dataset.records)

    cenarios_manifesto_ordenados = tuple(
        dict.fromkeys(entry.scenario for entry in dataset.manifest.scenarios)
    )
    cenarios_manifesto = set(cenarios_manifesto_ordenados)

    cenarios_desconhecidos = sorted(set(contagens) - cenarios_manifesto)

    if cenarios_desconhecidos:
        raise ValueError(
            "cenários observados ausentes do manifesto: "
            + ", ".join(cenarios_desconhecidos)
        )

    scenarios = tuple(
        ScenarioDiagnosticsEntry(
            scenario=scenario,
            observed_count=contagens[scenario],
            observed_proportion=contagens[scenario] / total_records,
        )
        for scenario in cenarios_manifesto_ordenados
    )

    return DatasetDiagnostics(
        total_records=total_records,
        scenarios=scenarios,
    )


def analyze_operational_label_confusion(
    dataset: "GeneratedSyntheticDataset",
) -> OperationalLabelDiagnostics:
    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0

    for registro in dataset.records:
        is_suspicious = registro.truth.is_suspicious
        if "status_transacao" not in registro.operational_labels:
            raise ValueError("operational_labels deve conter status_transacao.")

        status_transacao = registro.operational_labels["status_transacao"]

        if is_suspicious and status_transacao == STATUS_SUSPEITO:
            true_positive += 1
        elif is_suspicious and status_transacao == STATUS_NORMAL:
            false_negative += 1
        elif not is_suspicious and status_transacao == STATUS_SUSPEITO:
            false_positive += 1
        elif not is_suspicious and status_transacao == STATUS_NORMAL:
            true_negative += 1
        else:
            raise ValueError(
                f"status_transacao operacional desconhecido: {status_transacao}"
            )

    return OperationalLabelDiagnostics(
        true_positive=true_positive,
        true_negative=true_negative,
        false_positive=false_positive,
        false_negative=false_negative,
    )
