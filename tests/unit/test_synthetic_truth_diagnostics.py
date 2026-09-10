from datetime import datetime
from types import SimpleNamespace

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset_v3
from src.synthetic.generation_config import (
    ScenarioGenerationConfig,
    SyntheticGenerationConfig,
)
from src.synthetic.intensity import EventIntensityPolicy
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario
from src.synthetic.severity import SeverityPolicy
from src.synthetic.truth_diagnostics import (
    ScenarioTruthCoverageEntry,
    analyze_scenario_truth_coverage,
)


def test_analyze_scenario_truth_coverage_distingue_sinais_por_cenario():
    dataset = generate_synthetic_dataset_v3(
        seed=4242,
        quantidade=40,
        inicio=datetime(2026, 1, 1, 0, 0),
        fim=datetime(2026, 1, 8, 0, 0),
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.50,
            ),
            ScenarioMix(
                cenario=obter_cenario("account_takeover"),
                proporcao=0.50,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
        generation_config=SyntheticGenerationConfig(
            severity_policy=SeverityPolicy(
                normal_min=0.0,
                normal_max=40.0,
                suspicious_min=20.0,
                suspicious_max=100.0,
            ),
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="account_takeover",
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=0.50,
                        intensity_max=0.50,
                    ),
                ),
            ),
        ),
    )

    result = analyze_scenario_truth_coverage(dataset)

    assert result == (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=20,
            severity_score_count=20,
            severity_score_proportion=1.0,
            event_intensity_count=0,
            event_intensity_proportion=0.0,
        ),
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=20,
            severity_score_count=20,
            severity_score_proportion=1.0,
            event_intensity_count=20,
            event_intensity_proportion=1.0,
        ),
    )


def test_analyze_scenario_truth_coverage_preserva_proporcao_indisponivel_sem_registros():
    dataset = generate_synthetic_dataset_v3(
        seed=42,
        quantidade=1,
        inicio=datetime(2026, 1, 1, 0, 0),
        fim=datetime(2026, 1, 2, 0, 0),
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.99,
            ),
            ScenarioMix(
                cenario=obter_cenario("account_takeover"),
                proporcao=0.01,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
        generation_config=SyntheticGenerationConfig(
            severity_policy=SeverityPolicy(
                normal_min=0.0,
                normal_max=40.0,
                suspicious_min=20.0,
                suspicious_max=100.0,
            ),
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="account_takeover",
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=0.50,
                        intensity_max=0.50,
                    ),
                ),
            ),
        ),
    )

    result = analyze_scenario_truth_coverage(dataset)

    assert result[1] == ScenarioTruthCoverageEntry(
        scenario="account_takeover",
        record_count=0,
        severity_score_count=0,
        severity_score_proportion=None,
        event_intensity_count=0,
        event_intensity_proportion=None,
    )


def test_analyze_scenario_truth_coverage_rejeita_scenario_dos_records_ausente_do_manifest():
    dataset = SimpleNamespace(
        manifest=SimpleNamespace(
            scenarios=(
                SimpleNamespace(
                    scenario="baseline",
                ),
            ),
        ),
        records=(
            SimpleNamespace(
                truth=SimpleNamespace(
                    scenario="baseline",
                    severity_score=10.0,
                    event_intensity=None,
                ),
            ),
            SimpleNamespace(
                truth=SimpleNamespace(
                    scenario="undeclared_scenario",
                    severity_score=80.0,
                    event_intensity=0.75,
                ),
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=("records contem scenario ausente do manifest: undeclared_scenario"),
    ):
        analyze_scenario_truth_coverage(dataset)
