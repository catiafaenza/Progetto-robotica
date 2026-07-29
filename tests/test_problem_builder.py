from core.direzione import Direzione
from core.mappa_parziale import Mappa
from core.stato_passaggio import StatoPassaggio
from core.stato_robot import StatoRobot

from planning.pddl_planner import PDDLPlanner
from planning.problem_builder import ProblemBuilder


def crea_mappa_test() -> Mappa:
    """
    Costruisce questa mappa 2x2:

        (0, 1) -------- (1, 1) GOAL
          |
          |
        (0, 0) ROBOT

    Il robot parte da (0, 0), orientato verso nord.

    Il piano atteso è:
    1. avanza verso nord
    2. gira a destra
    3. avanza verso est
    """

    mappa = Mappa(
        larghezza=2,
        altezza=2,
    )

    # Imposta come muri i bordi esterni del labirinto.
    mappa.inizializza_pareti_esterne()

    # Passaggio libero:
    # (0, 0) -> NORD -> (0, 1)
    mappa.imposta_stato_passaggio(
        posizione=(0, 0),
        direzione=Direzione.NORD,
        stato=StatoPassaggio.LIBERO,
    )

    # Passaggio libero:
    # (0, 1) -> EST -> (1, 1)
    mappa.imposta_stato_passaggio(
        posizione=(0, 1),
        direzione=Direzione.EST,
        stato=StatoPassaggio.LIBERO,
    )

    return mappa


def main() -> None:
    # Creazione della mappa artificiale.
    mappa = crea_mappa_test()

    # Stato iniziale reale del robot.
    robot = StatoRobot(
        posizione=(0, 0),
        direzione=Direzione.NORD,
    )

    # Costruzione completa del problema UP.
    builder = ProblemBuilder()

    problem = builder.build(
        mappa=mappa,
        robot=robot,
        celle_goal={(1, 1)},
    )

    print("========== PROBLEMA UP ==========")
    print(problem)

    print("\n========== PROBLEM KIND ==========")
    print(problem.kind)

    # Invocazione di Fast Downward tramite PDDLPlanner.
    planner = PDDLPlanner(
        nome_planner="fast-downward-opt",
    )

    risultato = planner.solve(problem)

    print("\n========== RISULTATO ==========")
    print("Planner:", risultato.nome_planner)
    print("Stato:", risultato.stato)
    print(
        "Tempo di pianificazione:",
        f"{risultato.tempo_pianificazione:.6f} secondi",
    )

    print("\n========== PIANO ==========")

    for indice, azione in enumerate(
        risultato.piano.actions,
        start=1,
    ):
        print(f"{indice}. {azione}")

    # Controlli automatici sul piano.
    azioni = risultato.piano.actions

    assert len(azioni) == 3, (
        "Il piano dovrebbe contenere 3 azioni, "
        f"ma ne contiene {len(azioni)}."
    )

    nomi_azioni = [
        azione.action.name
        for azione in azioni
    ]

    assert nomi_azioni == [
        "avanza",
        "gira_destra",
        "avanza",
    ], (
        "Sequenza di azioni inattesa: "
        f"{nomi_azioni}"
    )

    print("\nTest completato con successo.")


if __name__ == "__main__":
    main()