from dataclasses import replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.quality import (
    ScenarioDistributionSeparationEntry,
    analyze_scenario_distribution_separation,
)
from src.synthetic.scenarios import obter_cenario


def _build_controlled_dataset():
    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=8,
        inicio=datetime(2026, 1, 1, 0, 0),
        fim=datetime(2026, 1, 2, 0, 0),
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.5,
            ),
            ScenarioMix(
                cenario=obter_cenario("account_takeover"),
                proporcao=0.5,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
    )

    transaction_values = {
        "baseline": iter((1.0, 2.0, 3.0, 4.0)),
        "account_takeover": iter((3.0, 4.0, 5.0, 6.0)),
    }

    login_failures = {
        "baseline": iter((0, 0, 0, 0)),
        "account_takeover": iter((0, 1, 1, 1)),
    }

    records = tuple(
        replace(
            record,
            observables={
                **record.observables,
                "valor_transacao": next(transaction_values[record.truth.scenario]),
                "falhas_login_recentes": next(login_failures[record.truth.scenario]),
            },
        )
        for record in dataset.records
    )

    return replace(
        dataset,
        records=records,
    )


def test_analyze_scenario_distribution_separation_calcula_distancias_observadas():
    dataset = _build_controlled_dataset()

    result = analyze_scenario_distribution_separation(dataset)

    assert result == (
        ScenarioDistributionSeparationEntry(
            left_scenario="baseline",
            right_scenario="account_takeover",
            transaction_value_ecdf_distance=pytest.approx(0.50),
            recent_login_failures_ecdf_distance=pytest.approx(0.75),
        ),
    )


def test_analyze_scenario_distribution_separation_preserva_distancia_indisponivel():
    dataset = _build_controlled_dataset()

    baseline_records = tuple(
        record for record in dataset.records if record.truth.scenario == "baseline"
    )

    dataset_without_attack_records = replace(
        dataset,
        records=baseline_records,
        manifest=replace(
            dataset.manifest,
            quantidade=len(baseline_records),
            scenarios=tuple(
                replace(
                    entry,
                    allocated_quantity=(
                        len(baseline_records) if entry.scenario == "baseline" else 0
                    ),
                )
                for entry in dataset.manifest.scenarios
            ),
        ),
    )

    result = analyze_scenario_distribution_separation(dataset_without_attack_records)

    assert result == (
        ScenarioDistributionSeparationEntry(
            left_scenario="baseline",
            right_scenario="account_takeover",
            transaction_value_ecdf_distance=None,
            recent_login_failures_ecdf_distance=None,
        ),
    )


def test_analyze_scenario_distribution_separation_rejeita_cenario_fora_do_manifest():
    dataset = _build_controlled_dataset()

    corrupted_record = replace(
        dataset.records[0],
        truth=replace(
            dataset.records[0].truth,
            scenario="unknown_scenario",
        ),
    )

    corrupted_dataset = replace(
        dataset,
        records=(
            corrupted_record,
            *dataset.records[1:],
        ),
    )

    with pytest.raises(
        ValueError,
        match="cenário observado não está presente no manifest",
    ):
        analyze_scenario_distribution_separation(corrupted_dataset)
