import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ScenarioManifestEntry:
    scenario: str
    configured_proportion: float
    allocated_quantity: int

    def __post_init__(self) -> None:
        if not isinstance(self.scenario, str) or not self.scenario.strip():
            raise ValueError("scenario deve ser uma string não vazia.")

        if isinstance(self.configured_proportion, bool) or not isinstance(
            self.configured_proportion,
            (int, float),
        ):
            raise ValueError("configured_proportion deve ser numérica.")

        if not math.isfinite(self.configured_proportion):
            raise ValueError("configured_proportion deve ser finita.")

        if self.configured_proportion <= 0.0 or self.configured_proportion > 1.0:
            raise ValueError("configured_proportion deve estar no intervalo (0, 1].")

        if isinstance(self.allocated_quantity, bool) or not isinstance(
            self.allocated_quantity,
            int,
        ):
            raise ValueError("allocated_quantity deve ser um inteiro não negativo.")

        if self.allocated_quantity < 0:
            raise ValueError("allocated_quantity deve ser um inteiro não negativo.")


@dataclass(frozen=True, slots=True)
class LabelPolicyManifest:
    false_positive_probability: float
    false_negative_probability: float

    def __post_init__(self) -> None:
        if isinstance(self.false_positive_probability, bool) or not isinstance(
            self.false_positive_probability,
            (int, float),
        ):
            raise ValueError("false_positive_probability deve ser numérica.")

        if not math.isfinite(self.false_positive_probability):
            raise ValueError("false_positive_probability deve ser finita.")

        if not 0.0 <= self.false_positive_probability <= 1.0:
            raise ValueError(
                "false_positive_probability deve estar no intervalo [0, 1]."
            )

        if isinstance(self.false_negative_probability, bool) or not isinstance(
            self.false_negative_probability,
            (int, float),
        ):
            raise ValueError("false_negative_probability deve ser numérica.")

        if not math.isfinite(self.false_negative_probability):
            raise ValueError("false_negative_probability deve ser finita.")

        if not 0.0 <= self.false_negative_probability <= 1.0:
            raise ValueError(
                "false_negative_probability deve estar no intervalo [0, 1]."
            )


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    schema_version: str
    seed: int
    quantidade: int
    inicio: datetime
    fim: datetime
    scenarios: tuple[ScenarioManifestEntry, ...]
    label_policy: LabelPolicyManifest

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ValueError("schema_version deve ser uma string não vazia.")

        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ValueError("seed deve ser um inteiro não negativo.")

        if self.seed < 0:
            raise ValueError("seed deve ser um inteiro não negativo.")

        if isinstance(self.quantidade, bool) or not isinstance(
            self.quantidade,
            int,
        ):
            raise ValueError("quantidade deve ser um inteiro positivo.")

        if self.quantidade <= 0:
            raise ValueError("quantidade deve ser um inteiro positivo.")

        if not isinstance(self.inicio, datetime):
            raise ValueError("inicio deve ser datetime.")

        if not isinstance(self.fim, datetime):
            raise ValueError("fim deve ser datetime.")

        if self.fim <= self.inicio:
            raise ValueError("fim deve ser posterior a inicio.")

        if not isinstance(self.scenarios, tuple):
            raise ValueError("scenarios deve ser uma tuple.")

        if not self.scenarios:
            raise ValueError("scenarios não pode ser vazio.")

        if not all(
            isinstance(entry, ScenarioManifestEntry) for entry in self.scenarios
        ):
            raise ValueError("scenarios deve conter apenas ScenarioManifestEntry.")

        if not isinstance(self.label_policy, LabelPolicyManifest):
            raise ValueError("label_policy deve ser LabelPolicyManifest.")

        soma_proporcoes = sum(entry.configured_proportion for entry in self.scenarios)

        if not math.isclose(
            soma_proporcoes,
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("a soma de configured_proportion deve ser igual a 1.")

        quantidade_alocada = sum(entry.allocated_quantity for entry in self.scenarios)

        if quantidade_alocada != self.quantidade:
            raise ValueError(
                "a soma de allocated_quantity deve ser igual a quantidade."
            )
