import sys
from collections import deque
from dataclasses import dataclass, field
from statistics import mean, median
from time import perf_counter

from unified_planning.plans import ActionInstance

from core.mappa_parziale import Mappa, Posizione
from core.osservatore import Osservatore
from core.selettoreFrontiera import SelettoreFrontiera
from core.stato_robot import StatoRobot
from mms.interfaccia_mms import InterfacciaMMS
from planning.pddl_planner import PDDLPlanner
from planning.plan_executor import PlanExecutor
from planning.problem_builder import ProblemBuilder


def debug(*valori: object) -> None:
    """
    Scrive i messaggi diagnostici su stderr.

    stdout deve rimanere riservato esclusivamente
    al protocollo di comunicazione con MMS.
    """
    print(*valori, file=sys.stderr, flush=True)


def celle_centrali(
    larghezza: int,
    altezza: int,
) -> set[Posizione]:
    """
    Restituisce la zona centrale del labirinto.

    Nei maze con dimensioni pari restituisce quattro celle.
    Nei maze con dimensioni dispari restituisce una cella.
    """
    xs = {
        (larghezza - 1) // 2,
        larghezza // 2,
    }

    ys = {
        (altezza - 1) // 2,
        altezza // 2,
    }

    return {
        (x, y)
        for x in xs
        for y in ys
    }


@dataclass
class MetricheChiamataPlanner:
    indice: int
    tipo_goal: str
    goal: set[Posizione]

    posizione_robot: Posizione
    direzione_robot: str

    tempo_generazione: float
    tempo_planning: float

    successo: bool

    lunghezza_piano: int | None = None
    stati_espansi: int | None = None
    stati_generati: int | None = None


@dataclass
class MetricheRun:
    successo: bool = False
    motivo_terminazione: str = "limite_cicli"

    chiamate_planner: int = 0
    chiamate_fallite: int = 0

    tempo_generazione_totale: float = 0.0
    tempo_planning_totale: float = 0.0

    stati_espansi_totali: int = 0
    stati_generati_totali: int = 0

    chiamate_con_stati_espansi: int = 0
    chiamate_con_stati_generati: int = 0

    azioni_totali: int = 0
    avanzamenti: int = 0
    rotazioni_sinistra: int = 0
    rotazioni_destra: int = 0

    piani_invalidati: int = 0
    terminazioni_senza_frontiere: int = 0

    chiamate: list[MetricheChiamataPlanner] = field(
        default_factory=list
    )


def registra_risultato_planning(
    metriche: MetricheRun,
    *,
    tipo_goal: str,
    goal: set[Posizione],
    robot: StatoRobot,
    tempo_generazione: float,
    risultato,
    lunghezza_piano: int | None,
) -> None:
    """
    Registra le metriche di una singola chiamata al planner.
    """

    if risultato.stati_espansi is not None:
        metriche.stati_espansi_totali += (
            risultato.stati_espansi
        )
        metriche.chiamate_con_stati_espansi += 1

    if risultato.stati_generati is not None:
        metriche.stati_generati_totali += (
            risultato.stati_generati
        )
        metriche.chiamate_con_stati_generati += 1

    metriche.chiamate.append(
        MetricheChiamataPlanner(
            indice=metriche.chiamate_planner,
            tipo_goal=tipo_goal,
            goal=set(goal),
            posizione_robot=robot.posizione,
            direzione_robot=robot.direzione.name,
            tempo_generazione=tempo_generazione,
            tempo_planning=(
                risultato.tempo_pianificazione
            ),
            successo=risultato.successo,
            lunghezza_piano=lunghezza_piano,
            stati_espansi=risultato.stati_espansi,
            stati_generati=risultato.stati_generati,
        )
    )


def stampa_riepilogo(
    metriche: MetricheRun,
    mappa: Mappa,
    robot: StatoRobot,
) -> None:
    visite_totali = sum(
        mappa.numero_visite.values()
    )

    visite_ripetute = max(
        0,
        visite_totali - len(mappa.celle_visitate),
    )

    tempi_planning = [
        chiamata.tempo_planning
        for chiamata in metriche.chiamate
    ]

    tempi_generazione = [
        chiamata.tempo_generazione
        for chiamata in metriche.chiamate
    ]

    debug("")
    debug("===== RIEPILOGO =====")
    debug("Successo:", metriche.successo)
    debug(
        "Motivo terminazione:",
        metriche.motivo_terminazione,
    )
    debug("Posizione finale:", robot.posizione)

    debug(
        "Celle visitate distinte:",
        len(mappa.celle_visitate),
    )
    debug("Visite ripetute:", visite_ripetute)

    debug(
        "Terminazioni senza frontiere:",
        metriche.terminazioni_senza_frontiere,
    )

    debug(
        "Chiamate planner:",
        metriche.chiamate_planner,
    )
    debug(
        "Chiamate fallite:",
        metriche.chiamate_fallite,
    )

    debug(
        "Tempo generazione totale:",
        f"{metriche.tempo_generazione_totale:.6f}s",
    )
    debug(
        "Tempo planning totale:",
        f"{metriche.tempo_planning_totale:.6f}s",
    )

    if tempi_generazione:
        debug(
            "Tempo generazione medio:",
            f"{mean(tempi_generazione):.6f}s",
        )
        debug(
            "Tempo generazione massimo:",
            f"{max(tempi_generazione):.6f}s",
        )

    if tempi_planning:
        debug(
            "Tempo planning medio:",
            f"{mean(tempi_planning):.6f}s",
        )
        debug(
            "Tempo planning mediano:",
            f"{median(tempi_planning):.6f}s",
        )
        debug(
            "Tempo planning massimo:",
            f"{max(tempi_planning):.6f}s",
        )

    if metriche.chiamate_con_stati_espansi > 0:
        debug(
            "Stati espansi totali:",
            metriche.stati_espansi_totali,
        )
        debug(
            "Stati espansi medi per chiamata disponibile:",
            (
                metriche.stati_espansi_totali
                / metriche.chiamate_con_stati_espansi
            ),
        )
        debug(
            "Chiamate con stati espansi disponibili:",
            (
                f"{metriche.chiamate_con_stati_espansi}"
                f"/{metriche.chiamate_planner}"
            ),
        )
    else:
        debug(
            "Stati espansi:",
            "non estratti dall'output del planner",
        )

    if metriche.chiamate_con_stati_generati > 0:
        debug(
            "Stati generati totali:",
            metriche.stati_generati_totali,
        )
        debug(
            "Stati generati medi per chiamata disponibile:",
            (
                metriche.stati_generati_totali
                / metriche.chiamate_con_stati_generati
            ),
        )
        debug(
            "Chiamate con stati generati disponibili:",
            (
                f"{metriche.chiamate_con_stati_generati}"
                f"/{metriche.chiamate_planner}"
            ),
        )
    else:
        debug(
            "Stati generati:",
            "non estratti dall'output del planner",
        )

    debug(
        "Piani invalidati:",
        metriche.piani_invalidati,
    )
    debug("Azioni totali:", metriche.azioni_totali)
    debug("Avanzamenti:", metriche.avanzamenti)
    debug(
        "Rotazioni sinistra:",
        metriche.rotazioni_sinistra,
    )
    debug(
        "Rotazioni destra:",
        metriche.rotazioni_destra,
    )

    if metriche.chiamate:
        debug("")
        debug("===== CHIAMATE AL PLANNER =====")

        for chiamata in metriche.chiamate:
            debug(
                f"Chiamata {chiamata.indice}:",
                f"tipo={chiamata.tipo_goal}",
                f"goal={sorted(chiamata.goal)}",
                f"pos={chiamata.posizione_robot}",
                f"dir={chiamata.direzione_robot}",
                f"generazione={chiamata.tempo_generazione:.6f}s",
                f"planning={chiamata.tempo_planning:.6f}s",
                f"piano={chiamata.lunghezza_piano}",
                f"espansi={chiamata.stati_espansi}",
                f"generati={chiamata.stati_generati}",
                f"successo={chiamata.successo}",
            )


def main() -> None:
    interfaccia = InterfacciaMMS()

    larghezza = interfaccia.larghezza_labirinto()
    altezza = interfaccia.altezza_labirinto()

    robot = StatoRobot()

    mappa = Mappa(
        larghezza=larghezza,
        altezza=altezza,
    )
    mappa.inizializza_pareti_esterne()

    osservatore = Osservatore()
    selettore = SelettoreFrontiera()
    builder = ProblemBuilder()
    planner = PDDLPlanner()
    executor = PlanExecutor()

    centri = celle_centrali(
        larghezza=larghezza,
        altezza=altezza,
    )

    piano_corrente: deque[ActionInstance] = deque()

    goal_correnti: set[Posizione] = set()
    tipo_goal: str | None = None

    metriche = MetricheRun()

    massimo_cicli = 100_000

    for numero_ciclo in range(massimo_cicli):
        # =====================================================
        # SENSE
        # =====================================================

        lettura = interfaccia.leggi_sensori()

        osservatore.aggiorna_mappa(
            mappa=mappa,
            robot=robot,
            lettura=lettura,
        )

        debug(
            f"[ciclo {numero_ciclo}]",
            f"pos={robot.posizione}",
            f"dir={robot.direzione.name}",
            f"goal={sorted(goal_correnti)}",
            f"tipo_goal={tipo_goal}",
            f"azioni_rimanenti={len(piano_corrente)}",
        )

        # =====================================================
        # CONDIZIONE DI SUCCESSO
        # =====================================================

        if robot.posizione in centri:
            metriche.successo = True
            metriche.motivo_terminazione = (
                "centro_raggiunto"
            )
            break

        # Se è stato raggiunto il goal corrente,
        # il piano precedente non serve più.
        if (
            goal_correnti
            and robot.posizione in goal_correnti
        ):
            debug(
                "Goal raggiunto:",
                sorted(goal_correnti),
            )

            piano_corrente.clear()
            goal_correnti.clear()
            tipo_goal = None

        # =====================================================
        # PLAN
        # =====================================================

        if not piano_corrente:
            distanze = mappa.distanze_da(
                robot.posizione
            )

            centri_raggiungibili = (
                centri.intersection(distanze.keys())
            )

            if centri_raggiungibili:
                goal_correnti = centri_raggiungibili
                tipo_goal = "centro"

            else:
                frontiera = selettore.scegli(
                    mappa=mappa,
                    robot=robot,
                )

                if frontiera is None:
                    metriche.terminazioni_senza_frontiere += 1
                    metriche.motivo_terminazione = (
                        "nessuna_frontiera_raggiungibile"
                    )
                    break

                goal_correnti = {frontiera}
                tipo_goal = "frontiera"

            debug(
                "Nuova pianificazione:",
                f"tipo={tipo_goal}",
                f"goal={sorted(goal_correnti)}",
            )

            tempo_generazione = 0.0
            risultato = None

            try:
                inizio_generazione = perf_counter()

                problema = builder.build(
                    mappa=mappa,
                    robot=robot,
                    celle_goal=goal_correnti,
                )

                tempo_generazione = (
                    perf_counter()
                    - inizio_generazione
                )

                metriche.tempo_generazione_totale += (
                    tempo_generazione
                )

                metriche.chiamate_planner += 1

                risultato = planner.solve(problema)

                metriche.tempo_planning_totale += (
                    risultato.tempo_pianificazione
                )

            except Exception as errore:
                metriche.chiamate_fallite += 1
                metriche.motivo_terminazione = (
                    "errore_pianificazione"
                )

                debug(
                    "Errore pianificazione:",
                    repr(errore),
                )
                break

            if risultato is None:
                metriche.chiamate_fallite += 1
                metriche.motivo_terminazione = (
                    "risultato_planner_assente"
                )
                break

            if (
                not risultato.successo
                or risultato.piano is None
            ):
                metriche.chiamate_fallite += 1
                metriche.motivo_terminazione = (
                    "planner_senza_piano"
                )

                registra_risultato_planning(
                    metriche,
                    tipo_goal=tipo_goal,
                    goal=goal_correnti,
                    robot=robot,
                    tempo_generazione=tempo_generazione,
                    risultato=risultato,
                    lunghezza_piano=None,
                )

                debug(
                    "Planner senza piano:",
                    risultato.stato,
                )

                debug(
                    "Output planner:",
                    risultato.output_planner,
                )
                break

            try:
                azioni_piano = executor.estrai_azioni(
                    risultato.piano
                )

                piano_corrente = deque(
                    azioni_piano
                )

            except (TypeError, ValueError) as errore:
                metriche.motivo_terminazione = (
                    "piano_non_sequenziale"
                )

                debug(
                    "Piano non eseguibile:",
                    errore,
                )
                break

            registra_risultato_planning(
                metriche,
                tipo_goal=tipo_goal,
                goal=goal_correnti,
                robot=robot,
                tempo_generazione=tempo_generazione,
                risultato=risultato,
                lunghezza_piano=len(piano_corrente),
            )

            debug(
                "Piano:",
                [
                    azione.action.name
                    for azione in piano_corrente
                ],
                (
                    "planning="
                    f"{risultato.tempo_pianificazione:.6f}s"
                ),
                f"espansi={risultato.stati_espansi}",
                f"generati={risultato.stati_generati}",
            )

            if not piano_corrente:
                metriche.motivo_terminazione = (
                    "piano_vuoto"
                )
                break

        # =====================================================
        # ACT
        # =====================================================

        prossima_azione = piano_corrente[0]

        esecuzione = executor.esegui_azione_pddl(
            azione_pddl=prossima_azione,
            interfaccia=interfaccia,
            robot=robot,
            mappa=mappa,
        )

        if not esecuzione.successo:
            metriche.piani_invalidati += 1

            debug(
                "Piano invalidato:",
                esecuzione.errore,
            )

            piano_corrente.clear()
            goal_correnti.clear()
            tipo_goal = None

            # Al ciclo successivo si leggono nuovamente
            # i sensori e si rigenera il problema.
            continue

        piano_corrente.popleft()

        metriche.azioni_totali += 1
        metriche.avanzamenti += (
            esecuzione.avanzamenti
        )
        metriche.rotazioni_sinistra += (
            esecuzione.rotazioni_sinistra
        )
        metriche.rotazioni_destra += (
            esecuzione.rotazioni_destra
        )

        debug(
            "Azione eseguita:",
            esecuzione.azione,
            f"nuova_pos={robot.posizione}",
            f"nuova_dir={robot.direzione.name}",
        )

    else:
        metriche.motivo_terminazione = (
            "limite_cicli_superato"
        )

    stampa_riepilogo(
        metriche=metriche,
        mappa=mappa,
        robot=robot,
    )


if __name__ == "__main__":
    main()