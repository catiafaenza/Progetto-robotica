from dataclasses import dataclass
from time import perf_counter

from unified_planning.engines import (
    PlanGenerationResultStatus,
)
from unified_planning.model import Problem
from unified_planning.plans import Plan
from unified_planning.shortcuts import OneshotPlanner


@dataclass
class RisultatoPianificazione:
    piano: Plan
    tempo_pianificazione: float
    stato: PlanGenerationResultStatus
    nome_planner: str


class ErrorePianificazione(RuntimeError):
    pass


class PDDLPlanner:

    def __init__(self, nome_planner: str = "fast-downward-opt") -> None:
        self.nome_planner = nome_planner

    def solve(self, problem: Problem) -> RisultatoPianificazione:
        inizio = perf_counter()

        with OneshotPlanner(
            name=self.nome_planner,
        ) as planner:
            risultato = planner.solve(problem)

        fine = perf_counter()

        tempo_pianificazione = fine - inizio

        stati_risolti = {
            PlanGenerationResultStatus.SOLVED_SATISFICING,
            PlanGenerationResultStatus.SOLVED_OPTIMALLY,
        }

        if risultato.status not in stati_risolti:
            raise ErrorePianificazione(
                "Fast Downward non ha trovato un piano. "
                f"Stato: {risultato.status}"
            )

        if risultato.plan is None:
            raise ErrorePianificazione(
                "Il planner ha restituito uno stato risolto, "
                "ma il piano è assente."
            )

        return RisultatoPianificazione(
            piano=risultato.plan,
            tempo_pianificazione=tempo_pianificazione,
            stato=risultato.status,
            nome_planner=self.nome_planner,
        )