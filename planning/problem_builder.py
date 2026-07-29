# Un oggetto Problem contiene:
# fluenti, azioni, stato iniziale e goal.

# PDDL proposizionale:
# i fluenti sono booleani.
# Fast Downward eseguirà il grounding.

# I passaggi LIBERI sono True, gli altri False.

# Tipi:
#   Cella
#   Direzione

# Fluenti:
#   robot_at(cella)
#   robot_facing(direzione)
#   connesso(cella1, cella2, direzione)
#   sinistra_di(direzione_attuale, nuova_direzione)
#   destra_di(direzione_attuale, nuova_direzione)

from unified_planning.shortcuts import *

from core.mappa_parziale import Mappa
from core.stato_robot import StatoRobot
from core.direzione import Direzione
from core.stato_passaggio import StatoPassaggio


Posizione = tuple[int, int]


class ProblemBuilder:

    def build(self, mappa: Mappa, robot: StatoRobot, celle_goal: set[Posizione]) -> Problem:
        problem = Problem("mms_proposizionale")

        # Tipi
        CellType = UserType("Cella")
        DirectionType = UserType("Direzione")

        # Fluenti
        robot_at, connesso, robot_facing, sinistra_di, destra_di = self.creaFluenti(problem, CellType, DirectionType)

        #Azioni
        self.azione_avanza(problem, CellType, DirectionType, robot_at, connesso, robot_facing)

        self.azione_gira_sinistra(problem, DirectionType, robot_facing, sinistra_di)

        self.azione_gira_a_destra(problem, DirectionType, robot_facing, destra_di)

        # Oggetti
        celle = self.crea_oggetti_cella(mappa, problem, CellType)

        direzioni = self.crea_oggetti_direzione(problem, DirectionType)

        self.validazione_stato_corrente(robot, celle_goal, celle)

        self.stato_iniziale(robot, problem, robot_at, robot_facing, celle, direzioni)

        self.relazioni_direzioni(problem, sinistra_di, destra_di, direzioni)

        self.passaggi_liberi(mappa, problem, connesso, celle, direzioni)

        self.goal(celle_goal, problem, robot_at, celle)

        return problem

    def goal(self, celle_goal, problem, robot_at, celle):
        espressioni_goal = [
            robot_at(celle[posizione_goal])
            for posizione_goal in celle_goal
        ]

        problem.add_goal(
            Or(espressioni_goal)
        )

    def passaggi_liberi(self, mappa, problem, connesso, celle, direzioni):
        for posizione, src_obj in celle.items():
            for direzione in Direzione:
                stato = mappa.stato_passaggio(
                    posizione,
                    direzione,
                )

                if stato != StatoPassaggio.LIBERO:
                    continue

                destinazione = mappa.cella_vicina(
                    posizione,
                    direzione,
                )

                if not mappa.posizione_valida(
                    destinazione
                ):
                    continue

                dest_obj = celle[destinazione]
                dir_obj = direzioni[direzione]

                problem.set_initial_value(
                    connesso(
                        src_obj,
                        dest_obj,
                        dir_obj,
                    ),
                    True,
                )

    def relazioni_direzioni(self, problem, sinistra_di, destra_di, direzioni):
        rotazioni_sinistra = {
            Direzione.NORD: Direzione.OVEST,
            Direzione.OVEST: Direzione.SUD,
            Direzione.SUD: Direzione.EST,
            Direzione.EST: Direzione.NORD,
        }

        rotazioni_destra = {
            Direzione.NORD: Direzione.EST,
            Direzione.EST: Direzione.SUD,
            Direzione.SUD: Direzione.OVEST,
            Direzione.OVEST: Direzione.NORD,
        }

        for attuale, nuova in rotazioni_sinistra.items():
            problem.set_initial_value(
                sinistra_di(
                    direzioni[attuale],
                    direzioni[nuova],
                ),
                True,
            )

        for attuale, nuova in rotazioni_destra.items():
            problem.set_initial_value(
                destra_di(
                    direzioni[attuale],
                    direzioni[nuova],
                ),
                True,
            )

    def stato_iniziale(self, robot, problem, robot_at, robot_facing, celle, direzioni):
        pos_iniziale = celle[robot.posizione]

        problem.set_initial_value(
            robot_at(pos_iniziale),
            True,
        )

        direzione_iniziale = direzioni[
            robot.direzione
        ]

        problem.set_initial_value(
            robot_facing(direzione_iniziale),
            True,
        )

    def validazione_stato_corrente(self, robot, celle_goal, celle):
        if robot.posizione not in celle:
            raise ValueError(
                "Posizione del robot fuori dalla mappa: "
                f"{robot.posizione}"
            )

        if not celle_goal:
            raise ValueError(
                "L'insieme delle celle goal è vuoto."
            )

        for posizione_goal in celle_goal:
            if posizione_goal not in celle:
                raise ValueError(
                    "Cella goal fuori dalla mappa: "
                    f"{posizione_goal}"
                )

    def crea_oggetti_direzione(self, problem, DirectionType):
        direzioni: dict[Direzione, Object] = {
            Direzione.NORD: Object(
                "nord",
                DirectionType,
            ),
            Direzione.SUD: Object(
                "sud",
                DirectionType,
            ),
            Direzione.OVEST: Object(
                "ovest",
                DirectionType,
            ),
            Direzione.EST: Object(
                "est",
                DirectionType,
            ),
        }

        problem.add_objects(direzioni.values())
        return direzioni

    def crea_oggetti_cella(self, mappa, problem, CellType):
        celle: dict[Posizione, Object] = {}

        for x in range(mappa.larghezza):
            for y in range(mappa.altezza):
                posizione = (x, y)

                cella = Object(
                    f"cell_{x}_{y}",
                    CellType,
                )

                celle[posizione] = cella
                problem.add_object(cella)
        return celle

    def azione_gira_a_destra(self, problem, DirectionType, robot_facing, destra_di):
        gira_destra = InstantaneousAction(
            "gira_destra",
            attuale=DirectionType,
            nuova=DirectionType,
        )

        attuale_destra = gira_destra.parameter(
            "attuale"
        )
        nuova_destra = gira_destra.parameter(
            "nuova"
        )

        gira_destra.add_precondition(
            robot_facing(attuale_destra)
        )
        gira_destra.add_precondition(
            destra_di(
                attuale_destra,
                nuova_destra,
            )
        )

        gira_destra.add_effect(
            robot_facing(attuale_destra),
            False,
        )
        gira_destra.add_effect(
            robot_facing(nuova_destra),
            True,
        )

        problem.add_action(gira_destra)

    def azione_gira_sinistra(self, problem, DirectionType, robot_facing, sinistra_di):
        gira_sinistra = InstantaneousAction(
            "gira_sinistra",
            attuale=DirectionType,
            nuova=DirectionType,
        )

        attuale_sinistra = gira_sinistra.parameter(
            "attuale"
        )
        nuova_sinistra = gira_sinistra.parameter(
            "nuova"
        )

        gira_sinistra.add_precondition(
            robot_facing(attuale_sinistra)
        )
        gira_sinistra.add_precondition(
            sinistra_di(
                attuale_sinistra,
                nuova_sinistra,
            )
        )

        gira_sinistra.add_effect(
            robot_facing(attuale_sinistra),
            False,
        )
        gira_sinistra.add_effect(
            robot_facing(nuova_sinistra),
            True,
        )

        problem.add_action(gira_sinistra)

    def azione_avanza(self, problem, CellType, DirectionType, robot_at, connesso, robot_facing):
        avanza = InstantaneousAction(
            "avanza",
            partenza=CellType,
            arrivo=CellType,
            direzione=DirectionType,
        )

        partenza = avanza.parameter("partenza")
        arrivo = avanza.parameter("arrivo")
        direzione_avanzamento = avanza.parameter(
            "direzione"
        )

        avanza.add_precondition(
            robot_at(partenza)
        )
        avanza.add_precondition(
            robot_facing(direzione_avanzamento)
        )
        avanza.add_precondition(
            connesso(
                partenza,
                arrivo,
                direzione_avanzamento,
            )
        )

        avanza.add_effect(
            robot_at(partenza),
            False,
        )
        avanza.add_effect(
            robot_at(arrivo),
            True,
        )

        problem.add_action(avanza)

    def creaFluenti(self, problem, CellType, DirectionType):
        robot_at = Fluent(
            "robot_at",
            BoolType(),
            cella=CellType,
        )

        connesso = Fluent(
            "connesso",
            BoolType(),
            cella1=CellType,
            cella2=CellType,
            direzione=DirectionType,
        )

        robot_facing = Fluent(
            "robot_facing",
            BoolType(),
            direzione=DirectionType,
        )

        sinistra_di = Fluent(
            "sinistra_di",
            BoolType(),
            attuale=DirectionType,
            nuova=DirectionType,
        )

        destra_di = Fluent(
            "destra_di",
            BoolType(),
            attuale=DirectionType,
            nuova=DirectionType,
        )

        # Assunzione di mondo chiuso:
        # tutto è falso se non impostato esplicitamente.
        problem.add_fluent(
            robot_at,
            default_initial_value=False,
        )
        problem.add_fluent(
            connesso,
            default_initial_value=False,
        )
        problem.add_fluent(
            robot_facing,
            default_initial_value=False,
        )
        problem.add_fluent(
            sinistra_di,
            default_initial_value=False,
        )
        problem.add_fluent(
            destra_di,
            default_initial_value=False,
        )
        return robot_at,connesso,robot_facing,sinistra_di,destra_di