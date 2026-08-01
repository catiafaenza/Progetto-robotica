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

from unified_planning.plans import Plan

class ProblemBuilder:
    """
    Rigenera completamente un problema PDDL proposizionale.

    Questa classe contiene tutta la struttura comune alle modellazioni
    proposizionale e numerica.

    Le sottoclassi possono estendere il problema attraverso gli hook:

    - _crea_fluenti_specifici
    - _aggiungi_effetti_avanza
    - _aggiungi_effetti_gira_sinistra
    - _aggiungi_effetti_gira_destra
    - _imposta_stato_iniziale_specifico
    - _aggiungi_metriche
    """

    nome_problema = "mms_proposizionale"

    def build(
        self,
        mappa: Mappa,
        robot: StatoRobot,
        celle_goal: set[Posizione],
    ) -> Problem:
        problema = Problem(self.nome_problema)

        tipo_cella = UserType("Cella")
        tipo_direzione = UserType("Direzione")

        fluenti = self._crea_fluenti(
            problema=problema,
            tipo_cella=tipo_cella,
            tipo_direzione=tipo_direzione,
        )

        robot_at = fluenti["robot_at"]
        connesso = fluenti["connesso"]
        robot_facing = fluenti["robot_facing"]
        sinistra_di = fluenti["sinistra_di"]
        destra_di = fluenti["destra_di"]

        self._aggiungi_azione_avanza(
            problema=problema,
            tipo_cella=tipo_cella,
            tipo_direzione=tipo_direzione,
            robot_at=robot_at,
            connesso=connesso,
            robot_facing=robot_facing,
            fluenti=fluenti,
        )

        self._aggiungi_azione_gira_sinistra(
            problema=problema,
            tipo_direzione=tipo_direzione,
            robot_facing=robot_facing,
            sinistra_di=sinistra_di,
            fluenti=fluenti,
        )

        self._aggiungi_azione_gira_destra(
            problema=problema,
            tipo_direzione=tipo_direzione,
            robot_facing=robot_facing,
            destra_di=destra_di,
            fluenti=fluenti,
        )

        celle = self._crea_oggetti_cella(
            mappa=mappa,
            problema=problema,
            tipo_cella=tipo_cella,
        )

        direzioni = self._crea_oggetti_direzione(
            problema=problema,
            tipo_direzione=tipo_direzione,
        )

        self._valida(
            robot=robot,
            celle_goal=celle_goal,
            celle=celle,
        )

        self._imposta_stato_iniziale(
            robot=robot,
            problema=problema,
            robot_at=robot_at,
            robot_facing=robot_facing,
            celle=celle,
            direzioni=direzioni,
            fluenti=fluenti,
        )

        self._imposta_relazioni_direzioni(
            problema=problema,
            sinistra_di=sinistra_di,
            destra_di=destra_di,
            direzioni=direzioni,
        )

        self._imposta_passaggi_liberi(
            mappa=mappa,
            problema=problema,
            connesso=connesso,
            celle=celle,
            direzioni=direzioni,
        )

        self._imposta_goal(
            celle_goal=celle_goal,
            problema=problema,
            robot_at=robot_at,
            celle=celle,
        )

        self._aggiungi_metriche(
            problema=problema,
            fluenti=fluenti,
        )

        return problema

    def _crea_fluenti(
        self,
        problema: Problem,
        tipo_cella,
        tipo_direzione,
    ) -> dict[str, Fluent]:
        robot_at = Fluent(
            "robot_at",
            BoolType(),
            cella=tipo_cella,
        )

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

        fluenti: dict[str, Fluent] = {
            "robot_at": robot_at,
            "connesso": connesso,
            "robot_facing": robot_facing,
            "sinistra_di": sinistra_di,
            "destra_di": destra_di,
        }

        for fluente in fluenti.values():
            problema.add_fluent(
                fluente,
                default_initial_value=False,
            )

        self._crea_fluenti_specifici(
            problema=problema,
            fluenti=fluenti,
        )

        return fluenti

    def _crea_fluenti_specifici(
        self,
        problema: Problem,
        fluenti: dict[str, Fluent],
    ) -> None:
        """
        Hook per aggiungere fluenti specifici della modellazione.

        Nella versione proposizionale non aggiunge nulla.
        """
        return None

    def _aggiungi_azione_avanza(
        self,
        problema: Problem,
        tipo_cella,
        tipo_direzione,
        robot_at: Fluent,
        connesso: Fluent,
        robot_facing: Fluent,
        fluenti: dict[str, Fluent],
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

        avanza.add_precondition(
            robot_at(partenza)
        )

        avanza.add_precondition(
            robot_facing(direzione)
        )

        avanza.add_precondition(
            connesso(
                partenza,
                arrivo,
                direzione,
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

        self._aggiungi_effetti_avanza(
            azione=avanza,
            fluenti=fluenti,
        )

        problema.add_action(avanza)

    def _aggiungi_azione_gira_sinistra(
        self,
        problema: Problem,
        tipo_direzione,
        robot_facing: Fluent,
        sinistra_di: Fluent,
        fluenti: dict[str, Fluent],
    ) -> None:
        azione = InstantaneousAction(
            "gira_sinistra",
            attuale=tipo_direzione,
            nuova=tipo_direzione,
        )

        attuale = azione.parameter("attuale")
        nuova = azione.parameter("nuova")

        azione.add_precondition(
            robot_facing(attuale)
        )

        azione.add_precondition(
            sinistra_di(
                attuale,
                nuova,
            )
        )

        azione.add_effect(
            robot_facing(attuale),
            False,
        )

        azione.add_effect(
            robot_facing(nuova),
            True,
        )

        self._aggiungi_effetti_gira_sinistra(
            azione=azione,
            fluenti=fluenti,
        )

        problema.add_action(azione)

    def _aggiungi_azione_gira_destra(
        self,
        problema: Problem,
        tipo_direzione,
        robot_facing: Fluent,
        destra_di: Fluent,
        fluenti: dict[str, Fluent],
    ) -> None:
        azione = InstantaneousAction(
            "gira_destra",
            attuale=tipo_direzione,
            nuova=tipo_direzione,
        )

        attuale = azione.parameter("attuale")
        nuova = azione.parameter("nuova")

        azione.add_precondition(
            robot_facing(attuale)
        )

        azione.add_precondition(
            destra_di(
                attuale,
                nuova,
            )
        )

        azione.add_effect(
            robot_facing(attuale),
            False,
        )

        azione.add_effect(
            robot_facing(nuova),
            True,
        )

        self._aggiungi_effetti_gira_destra(
            azione=azione,
            fluenti=fluenti,
        )

        problema.add_action(azione)

    def _aggiungi_effetti_avanza(
        self,
        azione: InstantaneousAction,
        fluenti: dict[str, Fluent],
    ) -> None:
        """
        Hook per aggiungere effetti specifici all'avanzamento.

        Nella versione proposizionale non aggiunge nulla.
        """
        return None

    def _aggiungi_effetti_gira_sinistra(
        self,
        azione: InstantaneousAction,
        fluenti: dict[str, Fluent],
    ) -> None:
        """
        Hook per aggiungere effetti specifici alla rotazione sinistra.

        Nella versione proposizionale non aggiunge nulla.
        """
        return None

    def _aggiungi_effetti_gira_destra(
        self,
        azione: InstantaneousAction,
        fluenti: dict[str, Fluent],
    ) -> None:
        """
        Hook per aggiungere effetti specifici alla rotazione destra.

        Nella versione proposizionale non aggiunge nulla.
        """
        return None

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

                oggetto = Object(
                    f"cell_{x}_{y}",
                    tipo_cella,
                )

                celle[posizione] = oggetto
                problema.add_object(oggetto)

        return celle

    def _crea_oggetti_direzione(
        self,
        problema: Problem,
        tipo_direzione,
    ) -> dict[Direzione, Object]:
        direzioni = {
            Direzione.NORD: Object(
                "nord",
                tipo_direzione,
            ),
            Direzione.EST: Object(
                "est",
                tipo_direzione,
            ),
            Direzione.SUD: Object(
                "sud",
                tipo_direzione,
            ),
            Direzione.OVEST: Object(
                "ovest",
                tipo_direzione,
            ),
        }

        problema.add_objects(
            direzioni.values()
        )

        return direzioni

    def _valida(
        self,
        robot: StatoRobot,
        celle_goal: set[Posizione],
        celle: dict[Posizione, Object],
    ) -> None:
        if robot.posizione not in celle:
            raise ValueError(
                "Posizione del robot fuori dalla mappa: "
                f"{robot.posizione}"
            )

        if not celle_goal:
            raise ValueError(
                "L'insieme delle celle goal è vuoto."
            )

        fuori_mappa = celle_goal.difference(
            celle.keys()
        )

        if fuori_mappa:
            raise ValueError(
                f"Celle goal fuori dalla mappa: {fuori_mappa}"
            )

    def _imposta_stato_iniziale(
        self,
        robot: StatoRobot,
        problema: Problem,
        robot_at: Fluent,
        robot_facing: Fluent,
        celle: dict[Posizione, Object],
        direzioni: dict[Direzione, Object],
        fluenti: dict[str, Fluent],
    ) -> None:
        problema.set_initial_value(
            robot_at(
                celle[robot.posizione]
            ),
            True,
        )

        problema.set_initial_value(
            robot_facing(
                direzioni[robot.direzione]
            ),
            True,
        )

        self._imposta_stato_iniziale_specifico(
            problema=problema,
            fluenti=fluenti,
        )

    def _imposta_stato_iniziale_specifico(
        self,
        problema: Problem,
        fluenti: dict[str, Fluent],
    ) -> None:
        """
        Hook per impostare valori iniziali specifici.

        Nella versione proposizionale non aggiunge nulla.
        """
        return None

    def _imposta_relazioni_direzioni(
        self,
        problema: Problem,
        sinistra_di: Fluent,
        destra_di: Fluent,
        direzioni: dict[Direzione, Object],
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
        mappa: Mappa,
        problema: Problem,
        connesso: Fluent,
        celle: dict[Posizione, Object],
        direzioni: dict[Direzione, Object],
    ) -> None:
        for posizione, oggetto_partenza in celle.items():
            for direzione in Direzione:
                stato_passaggio = mappa.stato_passaggio(
                    posizione,
                    direzione,
                )

                if stato_passaggio != StatoPassaggio.LIBERO:
                    continue

                destinazione = mappa.cella_vicina(
                    posizione,
                    direzione,
                )

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
        celle_goal: set[Posizione],
        problema: Problem,
        robot_at: Fluent,
        celle: dict[Posizione, Object],
    ) -> None:
        goals = [
            robot_at(celle[posizione])
            for posizione in celle_goal
        ]

        if len(goals) == 1:
            problema.add_goal(goals[0])
        else:
            problema.add_goal(
                Or(*goals)
            )

    def _aggiungi_metriche(
        self,
        problema: Problem,
        fluenti: dict[str, Fluent],
    ) -> None:
        """
        Hook per aggiungere metriche di qualità.

        La versione proposizionale non aggiunge una metrica numerica.
        """
        return None

    def calcola_costo_piano(
        self,
        piano: Plan | None,
    ) -> int | None:
        """
        La modellazione proposizionale non utilizza
        un costo numerico esplicito.
        """
        return None