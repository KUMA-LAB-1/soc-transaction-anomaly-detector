from datetime import datetime

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import (
    ScenarioObservableDiagnosticsEntry,
    analyze_scenario_observables,
)
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario


def test_analyze_scenario_observables_preserva_cenario_sem_registros():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 2, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=1,
        inicio=inicio,
        fim=fim,
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.99,
            ),
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=0.01,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
    )

    diagnostics = analyze_scenario_observables(dataset)

    assert diagnostics[1] == ScenarioObservableDiagnosticsEntry(
        scenario="credential_attack",
        record_count=0,
        transaction_value_median=None,
        recent_login_failures_mean=None,
    )
