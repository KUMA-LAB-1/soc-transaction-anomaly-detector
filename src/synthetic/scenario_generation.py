from datetime import datetime

from .contracts import SyntheticRecord
from .generation_config import ScenarioGenerationConfig
from .scenarios import ScenarioDefinition
from .statistical import StatisticalGenerator


class ScenarioConfiguredGenerator:
    """Aplica configuracao V3 por cenario sobre um gerador estatistico."""

    def __init__(
        self,
        generator: StatisticalGenerator,
        scenario_configs: tuple[ScenarioGenerationConfig, ...],
    ) -> None:
        self._generator = generator
        self._scenario_configs = {
            config.scenario: config for config in scenario_configs
        }

    def gerar_registros(
        self,
        cenario: ScenarioDefinition,
        *,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
    ) -> list[SyntheticRecord]:
        config = self._scenario_configs.get(cenario.name)

        if config is None:
            return self._generator.gerar_registros(
                cenario,
                quantidade=quantidade,
                inicio=inicio,
                fim=fim,
            )

        return self._generator.gerar_registros(
            cenario,
            quantidade=quantidade,
            inicio=inicio,
            fim=fim,
            scenario_effect=config.scenario_effect,
            intensity_policy=config.intensity_policy,
        )
