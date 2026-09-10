from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SyntheticSeedPlan:
    root_seed: int
    statistical_seed: int
    population_seed: int


def _derive_component_seed(
    root_seed: int,
    *,
    spawn_key: tuple[int, ...],
) -> int:
    seed_sequence = np.random.SeedSequence(
        root_seed,
        spawn_key=spawn_key,
    )

    return int(
        seed_sequence.generate_state(
            1,
            dtype=np.uint64,
        )[0]
    )


def build_synthetic_seed_plan(
    root_seed: int,
) -> SyntheticSeedPlan:
    if isinstance(root_seed, bool) or not isinstance(root_seed, int) or root_seed < 0:
        raise ValueError("root_seed deve ser um inteiro nao negativo.")

    return SyntheticSeedPlan(
        root_seed=root_seed,
        statistical_seed=_derive_component_seed(
            root_seed,
            spawn_key=(0,),
        ),
        population_seed=_derive_component_seed(
            root_seed,
            spawn_key=(1,),
        ),
    )
