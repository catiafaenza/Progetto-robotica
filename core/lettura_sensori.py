from dataclasses import dataclass


#oggetto non modificabile
@dataclass(frozen=True)
class LetturaSensori:
    muro_davanti: bool
    muro_sinistra: bool
    muro_destra: bool

