from collections import deque
from dataclasses import dataclass
from time import perf_counter

from unified_planning.plans import ActionInstance

from core.mappa_parziale import Mappa, Posizione
from core.selettoreFrontiera import SelettoreFrontiera
from core.stato_robot import StatoRobot
from metriche.raccoglitore import RaccoglitoreMetriche
from planning.pddl_planner import PDDLPlanner
from planning.plan_executor import PlanExecutor
from planning.proposizionale.problem_builder_completo import ProblemBuilder
from utils.debug import debug


@dataclass(frozen=True)
class EsitoPianificazione:
    successo: bool
    motivo_terminazione: str | None = None


class GestorePianificazione:
    """
    Mantiene il goal e il piano correnti e coordina:
    selezione del goal, costruzione del problema e planner.
    """

    def __init__(
        self,
        *,
        selettore: SelettoreFrontiera,
        builder: ProblemBuilder,
        planner: PDDLPlanner,
        executor: PlanExecutor,
        metriche: RaccoglitoreMetriche,
    ) -> None:
        self.selettore = selettore
        self.builder = builder
        self.planner = planner
        self.executor = executor
        self.metriche = metriche

        self._piano_corrente: deque[ActionInstance] = deque()
        self._goal_correnti: set[Posizione] = set()
        self._tipo_goal: str | None = None

    @property
    def goal_correnti(self) -> set[Posizione]:
        return set(self._goal_correnti)

    @property
    def tipo_goal(self) -> str | None:
        return self._tipo_goal

    @property
    def numero_azioni_rimanenti(self) -> int:
        return len(self._piano_corrente)

    def ha_piano(self) -> bool:
        return bool(self._piano_corrente)

    def goal_raggiunto(self, posizione: Posizione) -> bool:
        return (
            bool(self._goal_correnti)
            and posizione in self._goal_correnti
        )

    def completa_goal_corrente(self) -> None:
        self.invalida_piano()

    def invalida_piano(self) -> None:
        self._piano_corrente.clear()
        self._goal_correnti.clear()
        self._tipo_goal = None

    def prossima_azione(self) -> ActionInstance:
        if not self._piano_corrente:
            raise RuntimeError("Non è disponibile alcuna azione.")
        return self._piano_corrente[0]

    def conferma_azione_eseguita(self) -> None:
        if not self._piano_corrente:
            raise RuntimeError(
                "Non è presente un'azione da confermare."
            )
        self._piano_corrente.popleft()

    def pianifica(
        self,
        *,
        mappa: Mappa,
        robot: StatoRobot,
        centri: set[Posizione],
    ) -> EsitoPianificazione:
        scelta = self._scegli_goal(
            mappa=mappa,
            robot=robot,
            centri=centri,
        )

        if scelta is None:
            
            return EsitoPianificazione(
                successo=False,
                motivo_terminazione=(
                    "nessuna_frontiera_raggiungibile"
                ),
            )

        self._goal_correnti, self._tipo_goal = scelta

        debug(
            "Nuova pianificazione:",
            f"tipo={self._tipo_goal}",
            f"goal={sorted(self._goal_correnti)}",
        )

        indice_chiamata = (
            self.metriche.inizia_chiamata_planner()
        )
        tempo_generazione = 0.0

        try:
            inizio_generazione = perf_counter()

            problema = self.builder.build(
                mappa=mappa,
                robot=robot,
                celle_goal=self._goal_correnti,
            )
            

            tempo_generazione = (
                perf_counter() - inizio_generazione
            )
            self.metriche.registra_generazione(
                tempo_generazione
            )

            risultato = self.planner.solve(problema)

        except Exception as errore:
            self.metriche.registra_fallimento_planner()
            debug("Errore pianificazione:", repr(errore))
            self.invalida_piano()
            return EsitoPianificazione(
                successo=False,
                motivo_terminazione="errore_pianificazione",
            )

        if not risultato.successo or risultato.piano is None:
            self.metriche.registra_fallimento_planner()
            self.metriche.registra_risultato_planning(
                indice=indice_chiamata,
                tipo_goal=self._tipo_goal,
                robot=robot,
                tempo_generazione=tempo_generazione,
                risultato=risultato,
                lunghezza_piano=None,
            )

            debug("Planner senza piano:", risultato.stato)
            debug("Output planner:", risultato.output_planner)

            self.invalida_piano()
            return EsitoPianificazione(
                successo=False,
                motivo_terminazione="planner_senza_piano",
            )

        try:
            azioni = self.executor.estrai_azioni(
                risultato.piano
            )
            self._piano_corrente = deque(azioni)
        except (TypeError, ValueError) as errore:
            self.metriche.registra_fallimento_planner()
            debug("Piano non eseguibile:", errore)
            self.invalida_piano()
            return EsitoPianificazione(
                successo=False,
                motivo_terminazione="piano_non_sequenziale",
            )

        self.metriche.registra_risultato_planning(
            indice=indice_chiamata,
            tipo_goal=self._tipo_goal,
            robot=robot,
            tempo_generazione=tempo_generazione,
            risultato=risultato,
            lunghezza_piano=len(self._piano_corrente),
        )

        debug(
            "Piano:",
            [
                azione.action.name
                for azione in self._piano_corrente
            ],
            (
                "planning="
                f"{risultato.tempo_pianificazione:.6f}s"
            ),
            f"espansi={risultato.stati_espansi}",
            f"generati={risultato.stati_generati}",
            f"dead_end={risultato.dead_end_planner}",
        )

        if not self._piano_corrente:
            self.invalida_piano()
            return EsitoPianificazione(
                successo=False,
                motivo_terminazione="piano_vuoto",
            )

        return EsitoPianificazione(successo=True)

    def _scegli_goal(
        self,
        *,
        mappa: Mappa,
        robot: StatoRobot,
        centri: set[Posizione],
    ) -> tuple[set[Posizione], str] | None:
        distanze = mappa.distanze_da(robot.posizione)

        centri_raggiungibili = centri.intersection(
            distanze.keys()
        )

        if centri_raggiungibili:
            return centri_raggiungibili, "centro"

        frontiera = self.selettore.scegli(
            mappa=mappa,
            robot=robot,
        )

        if frontiera is None:
            return None

        return {frontiera}, "frontiera"
