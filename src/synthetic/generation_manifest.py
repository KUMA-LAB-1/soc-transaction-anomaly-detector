from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeedStrategyManifest:
    strategy_version: str
    statistical_seed: int
    population_seed: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.strategy_version, str)
            or not self.strategy_version.strip()
        ):
            raise ValueError("strategy_version deve ser uma string nao vazia.")

        if (
            isinstance(self.statistical_seed, bool)
            or not isinstance(self.statistical_seed, int)
            or self.statistical_seed < 0
        ):
            raise ValueError("statistical_seed deve ser um inteiro nao negativo.")

        if (
            isinstance(self.population_seed, bool)
            or not isinstance(self.population_seed, int)
            or self.population_seed < 0
        ):
            raise ValueError("population_seed deve ser um inteiro nao negativo.")
