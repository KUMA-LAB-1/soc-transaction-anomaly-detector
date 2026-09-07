import pytest

from src.synthetic.scenario_effect_catalog import (
    CENARIO_EFFECTS_PADRAO,
    obter_efeito_cenario,
)
from src.synthetic.scenario_effects import ScenarioEffect
from src.synthetic.scenarios import CENARIOS_PADRAO


def test_catalogo_de_efeitos_cobre_todos_os_cenarios_padrao():
    assert set(CENARIO_EFFECTS_PADRAO) == set(CENARIOS_PADRAO)


def test_catalogo_contem_apenas_scenario_effect():
    assert all(
        isinstance(effect, ScenarioEffect) for effect in CENARIO_EFFECTS_PADRAO.values()
    )


def test_baseline_possui_efeito_neutro():
    effect = obter_efeito_cenario("baseline")

    assert effect.transaction_value_median_multiplier == 1.0
    assert effect.transaction_value_sigma_multiplier == 1.0
    assert effect.recent_login_failure_rate_increment == 0.0


def test_credential_attack_prioriza_perturbacao_de_login():
    effect = obter_efeito_cenario("credential_attack")

    assert effect.transaction_value_median_multiplier == 1.0
    assert effect.recent_login_failure_rate_increment > 0.0


def test_account_takeover_combina_efeito_transacional_e_login():
    effect = obter_efeito_cenario("account_takeover")

    assert effect.transaction_value_median_multiplier > 1.0
    assert effect.transaction_value_sigma_multiplier >= 1.0
    assert effect.recent_login_failure_rate_increment > 0.0


def test_location_anomaly_nao_forca_efeito_transacional_ou_login():
    effect = obter_efeito_cenario("location_anomaly")

    assert effect.transaction_value_median_multiplier == 1.0
    assert effect.transaction_value_sigma_multiplier == 1.0
    assert effect.recent_login_failure_rate_increment == 0.0


def test_transaction_anomaly_prioriza_perturbacao_transacional():
    effect = obter_efeito_cenario("transaction_anomaly")

    assert effect.transaction_value_median_multiplier > 1.0
    assert effect.transaction_value_sigma_multiplier > 1.0
    assert effect.recent_login_failure_rate_increment == 0.0


def test_obter_efeito_cenario_retorna_objeto_do_catalogo():
    effect = obter_efeito_cenario("account_takeover")

    assert effect is CENARIO_EFFECTS_PADRAO["account_takeover"]


def test_obter_efeito_cenario_rejeita_cenario_desconhecido():
    with pytest.raises(
        ValueError,
        match="Cenário sintético desconhecido",
    ):
        obter_efeito_cenario("kraken_attack")


def test_catalogo_de_efeitos_e_somente_leitura():
    with pytest.raises(TypeError):
        CENARIO_EFFECTS_PADRAO["baseline"] = ScenarioEffect(
            transaction_value_median_multiplier=9.0,
            transaction_value_sigma_multiplier=9.0,
            recent_login_failure_rate_increment=9.0,
        )
