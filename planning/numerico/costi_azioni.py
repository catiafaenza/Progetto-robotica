from dataclasses import dataclass


@dataclass(frozen=True)
class CostiAzioni:
    avanzamento: int = 1
    rotazione_destra: int = 2
    rotazione_sinistra: int = 2

    def __post_init__(self) -> None:
        if (
            self.avanzamento < 0
            or self.rotazione_destra < 0
            or self.rotazione_sinistra < 0
        ):
            raise ValueError(
                "I costi delle azioni devono essere non negativi."
            )