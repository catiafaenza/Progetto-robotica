
import csv
from pathlib import Path

from core.mappa_parziale import Mappa, Posizione
from core.osservatore import Osservatore
from core.selettoreFrontiera import SelettoreFrontiera
from core.stato_robot import StatoRobot

from metriche.raccoglitore import RaccoglitoreMetriche

from navigazione.navigatore_micromouse import NavigatoreMicromouse
from navigazione.speed_run import SpeedRun

from planning.gestore_pianificazione import GestorePianificazione
from planning.pddl_planner import PDDLPlanner
from planning.plan_executor import PlanExecutor
from planning.problem_builder_factory import crea_problem_builder
from planning.strategia_aggiornamento import (
    StrategiaAggiornamento,
    TipoProblema,
)

from test.interfaccia_test import InterfacciaMazeTest
from test.planner_limitato import (
    LimiteChiamatePlanner,
    PlannerLimitato,
)


MAZES = Path("mazes")
DATI = Path("test/dati")


def celle_centrali(
    larghezza: int,
    altezza: int,
) -> set[Posizione]:

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


def trova_maze(
    maze: str,
) -> Path:

    percorsi = [
        MAZES / f"{maze}.num",
        MAZES / f"{maze}.txt",
        MAZES / "scalabilita" / f"{maze}.num",
        MAZES / "scalabilita" / f"{maze}.txt",
    ]

    for percorso in percorsi:

        if percorso.exists():
            return percorso

    raise FileNotFoundError(
        f"Maze non trovato: {maze}"
    )


def esegui_test(
    nome_test: str,
    configurazione: str,
    maze: str,
    tipo_problema: TipoProblema,
    strategia: StrategiaAggiornamento,
    nome_planner: str,
    nome_planner_speed_run: str,
    esegui_speed_run: bool = True,
    max_chiamate_planner: int | None = None,
) -> None:

    robot = StatoRobot()

    percorso_maze = trova_maze(
        maze
    )

    interfaccia = InterfacciaMazeTest(
        percorso_maze=percorso_maze,
        robot=robot,
    )

    larghezza = (
        interfaccia.larghezza_labirinto()
    )

    altezza = (
        interfaccia.altezza_labirinto()
    )

    mappa = Mappa(
        larghezza,
        altezza,
    )

    mappa.inizializza_pareti_esterne()

    osservatore = Osservatore()
    selettore = SelettoreFrontiera()

    builder = crea_problem_builder(
        tipo_problema,
        strategia,
    )

    # Planner usato durante l'esplorazione.
    planner_base = PDDLPlanner(
        nome_planner
    )

    if max_chiamate_planner is not None:

        planner = PlannerLimitato(
            planner=planner_base,
            max_chiamate=max_chiamate_planner,
        )

    else:

        planner = planner_base

    executor = PlanExecutor()

    metriche = RaccoglitoreMetriche(
        tipo_problema=tipo_problema.value,
        strategia_aggiornamento=strategia.value,
    )

    gestore = GestorePianificazione(
        selettore=selettore,
        builder=builder,
        planner=planner,
        executor=executor,
        metriche=metriche,
    )

    centri = celle_centrali(
        larghezza,
        altezza,
    )

    navigatore = NavigatoreMicromouse(
        interfaccia=interfaccia,
        robot=robot,
        mappa=mappa,
        osservatore=osservatore,
        gestore_pianificazione=gestore,
        executor=executor,
        metriche=metriche,
        centri=centri,
    )

    print(
        f"\n=== {tipo_problema.value} | "
        f"{configurazione} | "
        f"{maze} "
        f"({larghezza}x{altezza}) ==="
    )

    interrotto_per_limite = False

    try:

        navigatore.esegui()

    except LimiteChiamatePlanner:

        interrotto_per_limite = True

        print(
            f"\nLimite di "
            f"{max_chiamate_planner} "
            f"chiamate al planner raggiunto."
        )

    completato = (
        robot.posizione
        in centri
    )

    risultato_speed_run = None

    if (
        esegui_speed_run
        and completato
        and not interrotto_per_limite
    ):

        # Planner separato e ottimale
        # usato esclusivamente per la speed run.
        planner_speed_run = PDDLPlanner(
            nome_planner_speed_run
        )

        speed_run = SpeedRun(
            interfaccia=interfaccia,
            robot=robot,
            mappa=mappa,
            gestore_pianificazione=gestore,
            planner_speed_run=planner_speed_run,
            executor=executor,
            centri=centri,
        )

        risultato_speed_run = (
            speed_run.esegui()
        )

    salva_run(
        nome_test=nome_test,
        configurazione=configurazione,
        maze=maze,
        tipo_problema=tipo_problema.value,
        mappa=mappa,
        metriche=metriche.dati,
        speed_run=risultato_speed_run,
        completato=completato,
        interrotto_per_limite=(
            interrotto_per_limite
        ),
        limite_chiamate=(
            max_chiamate_planner
        ),
    )

    salva_chiamate(
        nome_test=nome_test,
        configurazione=configurazione,
        maze=maze,
        tipo_problema=tipo_problema.value,
        dimensione=larghezza,
        metriche=metriche.dati,
    )


def salva_run(
    nome_test,
    configurazione,
    maze,
    tipo_problema,
    mappa,
    metriche,
    speed_run,
    completato,
    interrotto_per_limite,
    limite_chiamate,
):

    DATI.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_csv = (
        DATI
        / f"{nome_test}.csv"
    )

    chiamate = (
        metriche.chiamate_planner
    )

    riga = {
        "modellazione":
            tipo_problema,

        "configurazione":
            configurazione,

        "maze":
            maze,

        "dimensione":
            mappa.larghezza,

        # Stato della run

        "completato":
            int(completato),

        "interrotto_per_limite":
            int(
                interrotto_per_limite
            ),

        "limite_chiamate":
            (
                limite_chiamate
                if limite_chiamate
                is not None
                else ""
            ),

        # Successo

        "successo":
            (
                int(metriche.successo) * 100
                if not interrotto_per_limite
                else ""
            ),

        # Planning

        "tempo_planning_totale":
            metriche.tempo_planning_totale,

        "tempo_planning_medio":
            (
                metriche.tempo_planning_totale
                / chiamate
                if chiamate
                else 0
            ),

        "stati_espansi":
            metriche.stati_espansi_totali,

        "stati_espansi_medi":
            (
                metriche.stati_espansi_totali
                / chiamate
                if chiamate
                else 0
            ),

        "chiamate_planner":
            chiamate,

        # Generazione problema

        "tempo_generazione":
            metriche.tempo_generazione_totale,

        "tempo_generazione_medio":
            (
                metriche.tempo_generazione_totale
                / chiamate
                if chiamate
                else 0
            ),

        # Replanning complessivo

        "tempo_replanning_totale":
            (
                metriche.tempo_generazione_totale
                + metriche.tempo_planning_totale
            ),

        "tempo_replanning_medio":
            (
                (
                    metriche.tempo_generazione_totale
                    + metriche.tempo_planning_totale
                )
                / chiamate
                if chiamate
                else 0
            ),

        # Esplorazione

        "azioni_totali":
            metriche.azioni_totali,

        "avanzamenti":
            metriche.avanzamenti,

        "rotazioni":
            metriche.rotazioni_totali,

        "costo_esplorazione":
            metriche.costo_eseguito_totale,

        # Speed run

        "speed_run_successo":
            (
                int(
                    speed_run["successo"]
                ) * 100
                if speed_run
                else ""
            ),

        "speed_run_tempo":
            (
                speed_run[
                    "tempo_planning"
                ]
                if speed_run
                else ""
            ),

        "speed_run_lunghezza":
            (
                speed_run[
                    "lunghezza_piano"
                ]
                if speed_run
                else ""
            ),

        "speed_run_costo":
            (
                speed_run[
                    "costo_piano"
                ]
                if speed_run
                else ""
            ),
    }

    nuovo_file = (
        not file_csv.exists()
    )

    with file_csv.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=riga.keys(),
        )

        if nuovo_file:
            writer.writeheader()

        writer.writerow(
            riga
        )


def salva_chiamate(
    nome_test,
    configurazione,
    maze,
    tipo_problema,
    dimensione,
    metriche,
):

    DATI.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_csv = (
        DATI
        / f"{nome_test}_chiamate.csv"
    )

    for chiamata in metriche.chiamate:

        riga = {
            "modellazione":
                tipo_problema,

            "configurazione":
                configurazione,

            "maze":
                maze,

            "dimensione":
                dimensione,

            "chiamata":
                chiamata.indice,

            "tempo_planning":
                chiamata.tempo_planning,

            "stati_espansi":
                (
                    chiamata.stati_espansi
                    if chiamata.stati_espansi
                    is not None
                    else ""
                ),
        }

        nuovo_file = (
            not file_csv.exists()
        )

        with file_csv.open(
            "a",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=riga.keys(),
            )

            if nuovo_file:
                writer.writeheader()

            writer.writerow(
                riga
            )
