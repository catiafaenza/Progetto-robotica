from unified_planning.model import Fluent, Problem
from unified_planning.model.metrics import MinimizeExpressionOnFinalState
from unified_planning.plans import Plan, SequentialPlan
from unified_planning.shortcuts import InstantaneousAction, IntType

from planning.numerico.costi_azioni import CostiAzioni


class SupportoNumerico:
    """
    Comportamento numerico condiviso dai builder completo e incrementale.

    La classe che utilizza questo supporto deve assegnare self.costi.
    """

    costi: CostiAzioni

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
        azione.add_increase_effect(
            fluenti["costo_totale"],
            self.costi.avanzamento,
        )

    def _aggiungi_effetti_gira_sinistra(
        self,
        azione: InstantaneousAction,
        fluenti: dict[str, Fluent],
    ) -> None:
        azione.add_increase_effect(
            fluenti["costo_totale"],
            self.costi.rotazione_sinistra,
        )

    def _aggiungi_effetti_gira_destra(
        self,
        azione: InstantaneousAction,
        fluenti: dict[str, Fluent],
    ) -> None:
        azione.add_increase_effect(
            fluenti["costo_totale"],
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