from unified_planning.model import (
    Fluent,
    Object,
    Problem,
)
from unified_planning.shortcuts import UserType

from core.direzione import Direzione
from core.mappa_parziale import Mappa, Posizione
from core.stato_passaggio import StatoPassaggio
from core.stato_robot import StatoRobot
from planning.proposizionale.problem_builder_completo import ProblemBuilder


class ProblemBuilderIncrementale(
    ProblemBuilder
):
    """
    Costruisce una sola volta la struttura del problema.

    Alle chiamate successive aggiorna solamente:

    - posizione del robot;
    - orientamento del robot;
    - passaggi modificati;
    - goal.
    """

    def __init__(self) -> None:
        self._problema: Problem | None = None

        self._robot_at: Fluent | None = None
        self._connesso: Fluent | None = None
        self._robot_facing: Fluent | None = None
        self._sinistra_di: Fluent | None = None
        self._destra_di: Fluent | None = None

        self._celle: dict[
            Posizione,
            Object,
        ] = {}

        self._direzioni: dict[
            Direzione,
            Object,
        ] = {}

        self._larghezza: int | None = None
        self._altezza: int | None = None

        self._posizione_precedente: (
            Posizione | None
        ) = None

        self._direzione_precedente: (
            Direzione | None
        ) = None

        # Utili successivamente per le metriche.
        self.ultima_costruzione_iniziale = False
        self.ultimo_numero_fatti_aggiornati = 0

    def build(
            self,
            mappa: Mappa,
            robot: StatoRobot,
            celle_goal: set[Posizione],
        ) -> Problem:
            costruzione_iniziale = self._problema is None

            if costruzione_iniziale:
                self._inizializza_problema(mappa)
            else:
                self._verifica_dimensioni(mappa)

            self._valida(
                robot=robot,
                celle_goal=celle_goal,
                celle=self._celle,
            )

            if costruzione_iniziale:
                self._inizializza_passaggi(mappa)
                mappa.estrai_modifiche_passaggi()
            else:
                self._aggiorna_passaggi(mappa)

            self._aggiorna_stato_robot(robot)
            self._aggiorna_goal(celle_goal)

            return self._richiedi_problema()

    def _inizializza_problema(
        self,
        mappa: Mappa,
    ) -> None:
        self._larghezza = mappa.larghezza
        self._altezza = mappa.altezza

        problema = Problem(
            "mms_proposizionale_incrementale"
        )

        tipo_cella = UserType("Cella")
        tipo_direzione = UserType("Direzione")

        (
            self._robot_at,
            self._connesso,
            self._robot_facing,
            self._sinistra_di,
            self._destra_di,
        ) = self._crea_fluenti(
            problema=problema,
            tipo_cella=tipo_cella,
            tipo_direzione=tipo_direzione,
        )

        self._aggiungi_azione_avanza(
            problema=problema,
            tipo_cella=tipo_cella,
            tipo_direzione=tipo_direzione,
            robot_at=self._robot_at,
            connesso=self._connesso,
            robot_facing=self._robot_facing,
        )

        self._aggiungi_azione_gira_sinistra(
            problema=problema,
            tipo_direzione=tipo_direzione,
            robot_facing=self._robot_facing,
            sinistra_di=self._sinistra_di,
        )

        self._aggiungi_azione_gira_destra(
            problema=problema,
            tipo_direzione=tipo_direzione,
            robot_facing=self._robot_facing,
            destra_di=self._destra_di,
        )

        self._celle = self._crea_oggetti_cella(
            mappa=mappa,
            problema=problema,
            tipo_cella=tipo_cella,
        )

        self._direzioni = (
            self._crea_oggetti_direzione(
                problema=problema,
                tipo_direzione=tipo_direzione,
            )
        )

        self._imposta_relazioni_direzioni(
            problema=problema,
            sinistra_di=self._sinistra_di,
            destra_di=self._destra_di,
            direzioni=self._direzioni,
        )

        self._problema = problema

    def _inizializza_passaggi(
        self,
        mappa: Mappa,
    ) -> int:
        """
        Alla prima costruzione legge tutti i passaggi
        attualmente conosciuti.
        """
        problema = self._richiedi_problema()
        connesso = self._richiedi_connesso()

        aggiornamenti = 0

        for (
            posizione,
            partenza,
        ) in self._celle.items():
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

                problema.set_initial_value(
                    connesso(
                        partenza,
                        self._celle[destinazione],
                        self._direzioni[direzione],
                    ),
                    True,
                )

                aggiornamenti += 1

        return aggiornamenti

    def _aggiorna_passaggi(
            self,
            mappa: Mappa,
        ) -> int:
            problema = self._richiedi_problema()
            connesso = self._richiedi_connesso()

            aggiornamenti = 0

            modifiche = mappa.estrai_modifiche_passaggi()

            for modifica in modifiche:
                destinazione = mappa.cella_vicina(
                    modifica.posizione,
                    modifica.direzione,
                )

                if not mappa.posizione_valida(destinazione):
                    continue

                valore = (
                    modifica.stato
                    == StatoPassaggio.LIBERO
                )

                problema.set_initial_value(
                    connesso(
                        self._celle[modifica.posizione],
                        self._celle[destinazione],
                        self._direzioni[modifica.direzione],
                    ),
                    valore,
                )

                aggiornamenti += 1

            return aggiornamenti

    def _aggiorna_stato_robot(
        self,
        robot: StatoRobot,
    ) -> int:
        problema = self._richiedi_problema()
        robot_at = self._richiedi_robot_at()
        robot_facing = (
            self._richiedi_robot_facing()
        )

        aggiornamenti = 0

        # Rimuove la vecchia posizione solo quando cambia.
        if (
            self._posizione_precedente is not None
            and self._posizione_precedente
            != robot.posizione
        ):
            problema.set_initial_value(
                robot_at(
                    self._celle[
                        self._posizione_precedente
                    ]
                ),
                False,
            )

            aggiornamenti += 1

        # Imposta la nuova posizione alla prima chiamata
        # oppure quando è cambiata.
        if (
            self._posizione_precedente
            != robot.posizione
        ):
            problema.set_initial_value(
                robot_at(
                    self._celle[robot.posizione]
                ),
                True,
            )

            aggiornamenti += 1

        # Rimuove il vecchio orientamento.
        if (
            self._direzione_precedente is not None
            and self._direzione_precedente
            != robot.direzione
        ):
            problema.set_initial_value(
                robot_facing(
                    self._direzioni[
                        self._direzione_precedente
                    ]
                ),
                False,
            )

            aggiornamenti += 1

        # Imposta il nuovo orientamento.
        if (
            self._direzione_precedente
            != robot.direzione
        ):
            problema.set_initial_value(
                robot_facing(
                    self._direzioni[
                        robot.direzione
                    ]
                ),
                True,
            )

            aggiornamenti += 1

        self._posizione_precedente = (
            robot.posizione
        )
        self._direzione_precedente = (
            robot.direzione
        )

        return aggiornamenti

    def _aggiorna_goal(
        self,
        celle_goal: set[Posizione],
    ) -> None:
        problema = self._richiedi_problema()
        robot_at = self._richiedi_robot_at()

        problema.clear_goals()

        self._imposta_goal(
            celle_goal=celle_goal,
            problema=problema,
            robot_at=robot_at,
            celle=self._celle,
        )

    def _verifica_dimensioni(
        self,
        mappa: Mappa,
    ) -> None:
        if (
            mappa.larghezza != self._larghezza
            or mappa.altezza != self._altezza
        ):
            raise ValueError(
                "Il ProblemBuilderIncrementale è "
                "già associato a una mappa con "
                "dimensioni diverse."
            )

    def _richiedi_problema(self) -> Problem:
        if self._problema is None:
            raise RuntimeError(
                "Problema incrementale non "
                "inizializzato."
            )

        return self._problema

    def _richiedi_robot_at(self) -> Fluent:
        if self._robot_at is None:
            raise RuntimeError(
                "Fluent robot_at non inizializzato."
            )

        return self._robot_at

    def _richiedi_connesso(self) -> Fluent:
        if self._connesso is None:
            raise RuntimeError(
                "Fluent connesso non inizializzato."
            )

        return self._connesso

    def _richiedi_robot_facing(self) -> Fluent:
        if self._robot_facing is None:
            raise RuntimeError(
                "Fluent robot_facing non "
                "inizializzato."
            )

        return self._robot_facing

        