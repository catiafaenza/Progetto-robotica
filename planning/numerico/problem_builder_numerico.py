from dataclasses import dataclass

from unified_planning.model import Fluent, Object, Problem
from unified_planning.model.metrics import MinimizeExpressionOnFinalState
from unified_planning.shortcuts import (
    BoolType,
    InstantaneousAction,
    IntType,
    Or,
    UserType,
)
from unified_planning.plans import Plan, SequentialPlan
from core.direzione import Direzione
from core.mappa_parziale import Mappa, Posizione
from core.stato_passaggio import StatoPassaggio
from core.stato_robot import StatoRobot
from planning.proposizionale.problem_builder_completo import ProblemBuilder

@dataclass(frozen=True)
class CostiAzioni:
    avanzamento: int = 1
    rotazione_destra: int = 2
    rotazione_sinistra: int= 2

    def __post_init__(self):
        if self.avanzamento < 0 or self.rotazione_destra < 0 or self.rotazione_sinistra < 0:
            raise ValueError("I costi delle azioni devono essere non negativi.")

class ProblemBuilderNumerico(ProblemBuilder):
    """
    Rigenera completamente il problema PDDL numerico.

    Estende il builder proposizionale aggiungendo:

    - il fluente numerico costo_totale;
    - l'incremento del costo per ogni azione;
    - la minimizzazione del costo totale finale.
    """

    nome_problema = "mms_numerico"

    def __init__(
        self,
        costi: CostiAzioni | None = None,
    ) -> None:
        self.costi = costi or CostiAzioni()

    def _crea_fluenti_specifici(
        self,
        problema: Problem,
        fluenti: dict[str, Fluent],
    ) -> None:
        costo_totale = Fluent(
            "costo_totale",
            IntType(0),
        )

        problema.add_fluent(
            costo_totale,
            default_initial_value=0,
        )

        fluenti["costo_totale"] = costo_totale

    def _aggiungi_effetti_avanza(
        self,
        azione: InstantaneousAction,
        fluenti: dict[str, Fluent],
    ) -> None:
        costo_totale = fluenti["costo_totale"]

        azione.add_increase_effect(
            costo_totale,
            self.costi.avanzamento,
        )

    def _aggiungi_effetti_gira_sinistra(
        self,
        azione: InstantaneousAction,
        fluenti: dict[str, Fluent],
    ) -> None:
        costo_totale = fluenti["costo_totale"]

        azione.add_increase_effect(
            costo_totale,
            self.costi.rotazione_sinistra,
        )

    def _aggiungi_effetti_gira_destra(
        self,
        azione: InstantaneousAction,
        fluenti: dict[str, Fluent],
    ) -> None:
        costo_totale = fluenti["costo_totale"]

        azione.add_increase_effect(
            costo_totale,
            self.costi.rotazione_destra,
        )

    def _imposta_stato_iniziale_specifico(
        self,
        problema: Problem,
        fluenti: dict[str, Fluent],
    ) -> None:
        problema.set_initial_value(
            fluenti["costo_totale"],
            0,
        )

    def _aggiungi_metriche(
        self,
        problema: Problem,
        fluenti: dict[str, Fluent],
    ) -> None:
        problema.add_quality_metric(
            MinimizeExpressionOnFinalState(
                fluenti["costo_totale"]
            )
        )

    def calcola_costo_piano(
        self,
        piano: Plan | None,
    ) -> int | None:
        if piano is None:
            return None

        if not isinstance(piano, SequentialPlan):
            raise TypeError(
                "Il costo può essere calcolato solo "
                "per un piano sequenziale."
            )

        costi_per_azione = {
            "avanza": self.costi.avanzamento,
            "gira_sinistra": self.costi.rotazione_sinistra,
            "gira_destra": self.costi.rotazione_destra,
        }

        costo_totale = 0

        for istanza_azione in piano.actions:
            nome_azione = istanza_azione.action.name

            try:
                costo_totale += costi_per_azione[nome_azione]
            except KeyError as errore:
                raise ValueError(
                    "Azione sconosciuta durante il calcolo "
                    f"del costo: {nome_azione}"
                ) from errore

        return costo_totale