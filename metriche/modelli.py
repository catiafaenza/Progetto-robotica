from dataclasses import dataclass, field

from core.mappa_parziale import Posizione


@dataclass(frozen=True)
class MetricheChiamataPlanner:
    indice: int
    tipo_goal: str

    posizione_robot: Posizione

    tempo_generazione: float
    tempo_planning: float
    successo: bool
    lunghezza_piano: int | None = None
    costo_piano: int | None = None
    piano_ottimo: bool = False
    stati_espansi: int | None = None

@dataclass
class MetricheRun:

    tipo_problema: str
    strategia_aggiornamento: str

    successo: bool = False
    motivo_terminazione: str = "limite_cicli"

    chiamate_planner: int = 0
    chiamate_fallite: int = 0

    tempo_generazione_totale: float = 0.0
    tempo_planning_totale: float = 0.0

    stati_espansi_totali: int = 0
    chiamate_con_stati_espansi: int = 0

    azioni_totali: int = 0
    avanzamenti: int = 0
    rotazioni_totali: int = 0

    costo_eseguito_totale: int = 0

    chiamate: list[MetricheChiamataPlanner] = field(
        default_factory=list
    )
