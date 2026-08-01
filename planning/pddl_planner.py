import re

from dataclasses import dataclass
from io import StringIO
from time import perf_counter

from unified_planning.engines import (
    PlanGenerationResultStatus,
)
from unified_planning.model import Problem
from unified_planning.plans import Plan
from unified_planning.shortcuts import (
    OneshotPlanner,
    get_environment,
)


# Evita che i crediti finiscano su stdout,
# che MMS usa per i propri comandi.
get_environment().credits_stream = None


@dataclass
class RisultatoPianificazione:
    piano: Plan | None
    tempo_pianificazione: float
    stato: PlanGenerationResultStatus
    nome_planner: str

    stati_espansi: int | None
    dead_end_planner: int | None

    output_planner: str

    @property
    def successo(self) -> bool:
        stati_risolti = {
            PlanGenerationResultStatus.SOLVED_SATISFICING,
            PlanGenerationResultStatus.SOLVED_OPTIMALLY,
        }

        return (
            self.stato in stati_risolti
            and self.piano is not None
        )


class PDDLPlanner:
    def __init__(
        self,
        nome_planner: str,
    ) -> None:
        self.nome_planner = nome_planner

    def solve(
        self,
        problema: Problem,
    ) -> RisultatoPianificazione:
        output_buffer = StringIO()
        inizio = perf_counter()

        with OneshotPlanner(
            name=self.nome_planner,
        ) as planner:
            risultato = planner.solve(
                problema,
                output_stream=output_buffer,
            )

        tempo_pianificazione = (
            perf_counter() - inizio
        )

        output_planner = output_buffer.getvalue()

        stati_espansi = self._estrai_intero(
            output=output_planner,
            patterns=[
                # Fast Downward
                r"Expanded\s+(\d+)\s+state",

                # ENHSP
                r"Expanded Nodes:\s*(\d+)",
            ],
        )

         

        dead_end_planner = self._estrai_intero(
            output=output_planner,
            patterns=[
                # Fast Downward
                r"Dead ends:\s*(\d+)\s+state",

                # ENHSP
                r"Number of Dead-Ends detected:\s*(\d+)",
            ],
        )

        return RisultatoPianificazione(
            piano=risultato.plan,
            tempo_pianificazione=tempo_pianificazione,
            stato=risultato.status,
            nome_planner=self.nome_planner,
            stati_espansi=stati_espansi,
            dead_end_planner=dead_end_planner,
            output_planner=output_planner,
        )

    def _estrai_intero(
        self,
        output: str,
        patterns: list[str],
    ) -> int | None:
        """
        Cerca una metrica usando più pattern, così da
        supportare formati prodotti da planner diversi.
        """
        for pattern in patterns:
            corrispondenze = re.findall(
                pattern,
                output,
                flags=re.IGNORECASE,
            )

            if corrispondenze:
                return int(
                    corrispondenze[-1]
                )

        return None