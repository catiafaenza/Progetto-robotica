from core.mappa_parziale import Mappa, Posizione
from core.osservatore import Osservatore
from core.selettoreFrontiera import SelettoreFrontiera
from core.stato_robot import StatoRobot
from metriche.raccoglitore import RaccoglitoreMetriche
from metriche.reporter import stampa_riepilogo
from mms.interfaccia_mms import InterfacciaMMS
from navigazione.navigatore_micromouse import (
    NavigatoreMicromouse,
)
from planning.gestore_pianificazione import (
    GestorePianificazione,
)
from planning.pddl_planner import PDDLPlanner
from planning.plan_executor import PlanExecutor
from planning.proposizionale.problem_builder_factory import crea_problem_builder
from planning.strategia_aggiornamento import StrategiaAggiornamento


#metodo per trovare il centro del labirinto e quindi il goal    
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


def crea_navigatore() -> NavigatoreMicromouse:
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
    strategia_aggiornamento = StrategiaAggiornamento.INCREMENTALE
    builder = crea_problem_builder(strategia_aggiornamento)
    planner = PDDLPlanner()
    executor = PlanExecutor()
    metriche = RaccoglitoreMetriche(strategia_aggiornamento=strategia_aggiornamento)

    gestore_pianificazione = GestorePianificazione(
        selettore=selettore,
        builder=builder,
        planner=planner,
        executor=executor,
        metriche=metriche,
    )

    return NavigatoreMicromouse(
        interfaccia=interfaccia,
        robot=robot,
        mappa=mappa,
        osservatore=osservatore,
        gestore_pianificazione=gestore_pianificazione,
        executor=executor,
        metriche=metriche,
        centri=celle_centrali(larghezza, altezza),
    )


def main() -> None:
    navigatore = crea_navigatore()

    navigatore.esegui()

    stampa_riepilogo(
        metriche=navigatore.metriche.dati,
        mappa=navigatore.mappa,
        robot=navigatore.robot,
    )


if __name__ == "__main__":
    main()
