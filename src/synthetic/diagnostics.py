from collections import Counter
from dataclasses import dataclass
from math import isclose
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dataset import GeneratedSyntheticDataset


@dataclass(frozen=True, slots=True)
class ScenarioDiagnosticsEntry:
    scenario: str
    observed_count: int
    observed_proportion: float


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
