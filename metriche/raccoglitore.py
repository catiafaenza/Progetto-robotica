from core.mappa_parziale import Posizione
from core.stato_robot import StatoRobot
from metriche.modelli import (
    MetricheChiamataPlanner,
    MetricheRun,
)
from planning.pddl_planner import (
    RisultatoPianificazione,
)
from planning.plan_executor import RisultatoEsecuzione
from unified_planning.engines import (
    PlanGenerationResultStatus,
)
from planning.numerico.problem_builder_completo import CostiAzioni

class RaccoglitoreMetriche:
    """
    Centralizza l'aggiornamento delle metriche
    relative a una singola run.
    """

    def __init__(
        self,
        tipo_problema: str,
        strategia_aggiornamento: str,
        costi_azioni: CostiAzioni | None = None,
    ) -> None:
        self.dati = MetricheRun(
            tipo_problema=tipo_problema,
            strategia_aggiornamento=strategia_aggiornamento
        )
        self.costi_azioni = costi_azioni or CostiAzioni()

    def inizia_chiamata_planner(self) -> int:
        self.dati.chiamate_planner += 1
        return self.dati.chiamate_planner

    def registra_generazione(
        self,
        tempo: float,
    ) -> None:
        self.dati.tempo_generazione_totale += tempo

    def registra_risultato_planning(
        self,
        *,
        indice: int,
        tipo_goal: str,
        robot: StatoRobot,
        tempo_generazione: float,
        risultato: RisultatoPianificazione,
        lunghezza_piano: int | None,
        costo_piano: int | None,
    ) -> None:
        """
        Registra le metriche relative a una chiamata
        conclusa al planner.
        """
        self.dati.tempo_planning_totale += (
            risultato.tempo_pianificazione
        )

        if risultato.stati_espansi is not None:
            self.dati.stati_espansi_totali += (
                risultato.stati_espansi
            )
            self.dati.chiamate_con_stati_espansi += 1

        self.dati.chiamate.append(
            MetricheChiamataPlanner(
                indice=indice,
                tipo_goal=tipo_goal,
                posizione_robot=robot.posizione,
                tempo_generazione=tempo_generazione,
                tempo_planning=(
                    risultato.tempo_pianificazione
                ),
                successo=risultato.successo,
                lunghezza_piano=lunghezza_piano,
                costo_piano=costo_piano,
                piano_ottimo=(
                    risultato.stato
                    == PlanGenerationResultStatus.SOLVED_OPTIMALLY
                ),
                stati_espansi=risultato.stati_espansi,
            )
        )

    def registra_fallimento_planner(self) -> None:
        self.dati.chiamate_fallite += 1

    def registra_esecuzione(
        self,
        esecuzione: RisultatoEsecuzione,
    ) -> None:
        self.dati.azioni_totali += 1
        self.dati.avanzamenti += (
            esecuzione.avanzamenti
        )

        self.dati.rotazioni_totali += (
            esecuzione.rotazioni_sinistra
            + esecuzione.rotazioni_destra
        )

        
        self.dati.costo_eseguito_totale += (
            esecuzione.avanzamenti
            * self.costi_azioni.avanzamento
            + esecuzione.rotazioni_sinistra
            * self.costi_azioni.rotazione_sinistra
            + esecuzione.rotazioni_destra
            * self.costi_azioni.rotazione_destra
    )

    def registra_piano_invalidato(self) -> None:
        self.dati.piani_invalidati += 1

    def termina(
        self,
        motivo: str,
        *,
        successo: bool = False,
    ) -> None:
        self.dati.successo = successo
        self.dati.motivo_terminazione = motivo