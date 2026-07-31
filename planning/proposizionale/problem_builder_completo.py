from unified_planning.model import Fluent, Object, Problem
from unified_planning.shortcuts import (
    BoolType,
    InstantaneousAction,
    Or,
    UserType,
)

from core.direzione import Direzione
from core.mappa_parziale import Mappa, Posizione
from core.stato_passaggio import StatoPassaggio
from core.stato_robot import StatoRobot


class ProblemBuilder:
    """Rigenera completamente il problema PDDL proposizionale."""

    def build(
        self,
        mappa: Mappa,
        robot: StatoRobot,
        celle_goal: set[Posizione],
    ) -> Problem:
        problema = Problem("mms_proposizionale")

        tipo_cella = UserType("Cella")
        tipo_direzione = UserType("Direzione")

        (
            robot_at,
            connesso,
            robot_facing,
            sinistra_di,
            destra_di,
        ) = self._crea_fluenti(
            problema,
            tipo_cella,
            tipo_direzione,
        )

        self._aggiungi_azione_avanza(
            problema,
            tipo_cella,
            tipo_direzione,
            robot_at,
            connesso,
            robot_facing,
        )
        self._aggiungi_azione_gira_sinistra(
            problema,
            tipo_direzione,
            robot_facing,
            sinistra_di,
        )
        self._aggiungi_azione_gira_destra(
            problema,
            tipo_direzione,
            robot_facing,
            destra_di,
        )

        celle = self._crea_oggetti_cella(mappa, problema, tipo_cella)
        direzioni = self._crea_oggetti_direzione(
            problema,
            tipo_direzione,
        )

        self._valida(robot, celle_goal, celle)
        self._imposta_stato_iniziale(
            robot,
            problema,
            robot_at,
            robot_facing,
            celle,
            direzioni,
        )
        self._imposta_relazioni_direzioni(
            problema,
            sinistra_di,
            destra_di,
            direzioni,
        )
        self._imposta_passaggi_liberi(
            mappa,
            problema,
            connesso,
            celle,
            direzioni,
        )
        self._imposta_goal(
            celle_goal,
            problema,
            robot_at,
            celle,
        )

        return problema

    def _crea_fluenti(self, problema, tipo_cella, tipo_direzione):
        robot_at = Fluent("robot_at", BoolType(), cella=tipo_cella)
        connesso = Fluent(
            "connesso",
            BoolType(),
            cella1=tipo_cella,
            cella2=tipo_cella,
            direzione=tipo_direzione,
        )
        robot_facing = Fluent(
            "robot_facing",
            BoolType(),
            direzione=tipo_direzione,
        )
        sinistra_di = Fluent(
            "sinistra_di",
            BoolType(),
            attuale=tipo_direzione,
            nuova=tipo_direzione,
        )
        destra_di = Fluent(
            "destra_di",
            BoolType(),
            attuale=tipo_direzione,
            nuova=tipo_direzione,
        )

        for fluente in (
            robot_at,
            connesso,
            robot_facing,
            sinistra_di,
            destra_di,
        ):
            problema.add_fluent(fluente, default_initial_value=False)

        return (
            robot_at,
            connesso,
            robot_facing,
            sinistra_di,
            destra_di,
        )

    def _aggiungi_azione_avanza(
        self,
        problema,
        tipo_cella,
        tipo_direzione,
        robot_at,
        connesso,
        robot_facing,
    ) -> None:
        avanza = InstantaneousAction(
            "avanza",
            partenza=tipo_cella,
            arrivo=tipo_cella,
            direzione=tipo_direzione,
        )

        partenza = avanza.parameter("partenza")
        arrivo = avanza.parameter("arrivo")
        direzione = avanza.parameter("direzione")

        avanza.add_precondition(robot_at(partenza))
        avanza.add_precondition(robot_facing(direzione))
        avanza.add_precondition(connesso(partenza, arrivo, direzione))

        avanza.add_effect(robot_at(partenza), False)
        avanza.add_effect(robot_at(arrivo), True)

        problema.add_action(avanza)

    def _aggiungi_azione_gira_sinistra(
        self,
        problema,
        tipo_direzione,
        robot_facing,
        sinistra_di,
    ) -> None:
        azione = InstantaneousAction(
            "gira_sinistra",
            attuale=tipo_direzione,
            nuova=tipo_direzione,
        )
        attuale = azione.parameter("attuale")
        nuova = azione.parameter("nuova")

        azione.add_precondition(robot_facing(attuale))
        azione.add_precondition(sinistra_di(attuale, nuova))
        azione.add_effect(robot_facing(attuale), False)
        azione.add_effect(robot_facing(nuova), True)

        problema.add_action(azione)

    def _aggiungi_azione_gira_destra(
        self,
        problema,
        tipo_direzione,
        robot_facing,
        destra_di,
    ) -> None:
        azione = InstantaneousAction(
            "gira_destra",
            attuale=tipo_direzione,
            nuova=tipo_direzione,
        )
        attuale = azione.parameter("attuale")
        nuova = azione.parameter("nuova")

        azione.add_precondition(robot_facing(attuale))
        azione.add_precondition(destra_di(attuale, nuova))
        azione.add_effect(robot_facing(attuale), False)
        azione.add_effect(robot_facing(nuova), True)

        problema.add_action(azione)

    def _crea_oggetti_cella(
        self,
        mappa: Mappa,
        problema: Problem,
        tipo_cella,
    ) -> dict[Posizione, Object]:
        celle: dict[Posizione, Object] = {}

        for x in range(mappa.larghezza):
            for y in range(mappa.altezza):
                posizione = (x, y)
                oggetto = Object(f"cell_{x}_{y}", tipo_cella)
                celle[posizione] = oggetto
                problema.add_object(oggetto)

        return celle

    def _crea_oggetti_direzione(
        self,
        problema: Problem,
        tipo_direzione,
    ) -> dict[Direzione, Object]:
        direzioni = {
            Direzione.NORD: Object("nord", tipo_direzione),
            Direzione.EST: Object("est", tipo_direzione),
            Direzione.SUD: Object("sud", tipo_direzione),
            Direzione.OVEST: Object("ovest", tipo_direzione),
        }
        problema.add_objects(direzioni.values())
        return direzioni

    def _valida(
        self,
        robot: StatoRobot,
        celle_goal: set[Posizione],
        celle: dict[Posizione, Object],
    ) -> None:
        if robot.posizione not in celle:
            raise ValueError(
                f"Posizione del robot fuori dalla mappa: {robot.posizione}"
            )
        if not celle_goal:
            raise ValueError("L'insieme delle celle goal è vuoto.")

        fuori_mappa = celle_goal.difference(celle)
        if fuori_mappa:
            raise ValueError(f"Celle goal fuori dalla mappa: {fuori_mappa}")

    def _imposta_stato_iniziale(
        self,
        robot,
        problema,
        robot_at,
        robot_facing,
        celle,
        direzioni,
    ) -> None:
        problema.set_initial_value(robot_at(celle[robot.posizione]), True)
        problema.set_initial_value(
            robot_facing(direzioni[robot.direzione]),
            True,
        )

    def _imposta_relazioni_direzioni(
        self,
        problema,
        sinistra_di,
        destra_di,
        direzioni,
    ) -> None:
        for attuale in Direzione:
            problema.set_initial_value(
                sinistra_di(
                    direzioni[attuale],
                    direzioni[attuale.sinistra()],
                ),
                True,
            )
            problema.set_initial_value(
                destra_di(
                    direzioni[attuale],
                    direzioni[attuale.destra()],
                ),
                True,
            )

    def _imposta_passaggi_liberi(
        self,
        mappa,
        problema,
        connesso,
        celle,
        direzioni,
    ) -> None:
        for posizione, oggetto_partenza in celle.items():
            for direzione in Direzione:
                if (
                    mappa.stato_passaggio(posizione, direzione)
                    != StatoPassaggio.LIBERO
                ):
                    continue

                destinazione = mappa.cella_vicina(posizione, direzione)
                if not mappa.posizione_valida(destinazione):
                    continue

                problema.set_initial_value(
                    connesso(
                        oggetto_partenza,
                        celle[destinazione],
                        direzioni[direzione],
                    ),
                    True,
                )

    def _imposta_goal(
        self,
        celle_goal,
        problema,
        robot_at,
        celle,
    ) -> None:
        goals = [robot_at(celle[posizione]) for posizione in celle_goal]
        problema.add_goal(goals[0] if len(goals) == 1 else Or(*goals))