from dataclasses import dataclass
from typing import Protocol

from unified_planning.plans import ActionInstance, Plan, SequentialPlan

from core.azioni import Azioni
from core.mappa_parziale import Mappa
from core.stato_robot import StatoRobot


class InterfacciaEsecuzione(Protocol):
    def esegui_azione(
        self,
        azione: Azioni,
        robot: StatoRobot,
        mappa: Mappa,
    ) -> None:
        ...


@dataclass(frozen=True)
class RisultatoEsecuzione:
    successo: bool
    azione: Azioni | None
    avanzamenti: int
    rotazioni_sinistra: int
    rotazioni_destra: int
    errore: str | None = None


class PlanExecutor:
    def estrai_azioni(self, piano: Plan) -> list[ActionInstance]:
        if not isinstance(piano, SequentialPlan):
            raise TypeError("Il planner non ha restituito un piano sequenziale.")
        return list(piano.actions)

    def converti_azione(self, azione_pddl: ActionInstance) -> Azioni:
        conversione: dict[str, Azioni] = {
            "avanza": Azioni.AVANZA,
            "gira_sinistra": Azioni.GIRA_SINISTRA,
            "gira_destra": Azioni.GIRA_DESTRA,
        }

        nome = azione_pddl.action.name
        try:
            return conversione[nome]
        except KeyError as errore:
            raise ValueError(f"Azione PDDL non riconosciuta: {nome}") from errore

    def esegui_azione_pddl(
        self,
        azione_pddl: ActionInstance,
        interfaccia: InterfacciaEsecuzione,
        robot: StatoRobot,
        mappa: Mappa,
    ) -> RisultatoEsecuzione:
        try:
            azione = self.converti_azione(azione_pddl)
            interfaccia.esegui_azione(
                azione=azione,
                robot=robot,
                mappa=mappa,
            )
        except (RuntimeError, ValueError) as errore:
            return RisultatoEsecuzione(
                successo=False,
                azione=None,
                avanzamenti=0,
                rotazioni_sinistra=0,
                rotazioni_destra=0,
                errore=str(errore),
            )

        return RisultatoEsecuzione(
            successo=True,
            azione=azione,
            avanzamenti=int(azione == Azioni.AVANZA),
            rotazioni_sinistra=int(azione == Azioni.GIRA_SINISTRA),
            rotazioni_destra=int(azione == Azioni.GIRA_DESTRA),
        )