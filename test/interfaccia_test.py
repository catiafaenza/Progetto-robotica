from pathlib import Path

from core.azioni import Azioni
from core.direzione import Direzione
from core.lettura_sensori import LetturaSensori
from core.mappa_parziale import Mappa
from core.stato_passaggio import StatoPassaggio
from core.stato_robot import StatoRobot


class InterfacciaMazeTest:

    def __init__(
        self,
        percorso_maze: str | Path,
        robot: StatoRobot,
    ) -> None:

        self.robot = robot

        self.muri = {}

        self.larghezza = 0
        self.altezza = 0

        self._carica_maze(
            Path(percorso_maze)
        )

    def _carica_maze(
        self,
        percorso: Path,
    ) -> None:

        if not percorso.exists():
            raise FileNotFoundError(
                f"Maze non trovato: {percorso}"
            )

        with percorso.open(
            encoding="utf-8"
        ) as file:

            righe = [
                riga.rstrip("\n")
                for riga in file
                if riga.strip()
            ]

        if not righe:
            raise ValueError(
                "Maze vuoto."
            )

        # Maze ASCII:
        # o---o---o...
        if righe[0].startswith("o"):
            self._carica_maze_ascii(
                righe
            )

        # Maze numerico:
        # x y N E S W
        else:
            self._carica_maze_numerico(
                righe
            )

    def _carica_maze_numerico(
        self,
        righe: list[str],
    ) -> None:

        max_x = -1
        max_y = -1

        for riga in righe:

            valori = riga.split()

            if len(valori) != 6:
                raise ValueError(
                    f"Riga maze non valida: {riga}"
                )

            (
                x,
                y,
                nord,
                est,
                sud,
                ovest,
            ) = map(
                int,
                valori,
            )

            posizione = (
                x,
                y,
            )

            self.muri[
                (
                    posizione,
                    Direzione.NORD,
                )
            ] = bool(nord)

            self.muri[
                (
                    posizione,
                    Direzione.EST,
                )
            ] = bool(est)

            self.muri[
                (
                    posizione,
                    Direzione.SUD,
                )
            ] = bool(sud)

            self.muri[
                (
                    posizione,
                    Direzione.OVEST,
                )
            ] = bool(ovest)

            max_x = max(
                max_x,
                x,
            )

            max_y = max(
                max_y,
                y,
            )

        self.larghezza = (
            max_x + 1
        )

        self.altezza = (
            max_y + 1
        )

    def _carica_maze_ascii(
        self,
        righe: list[str],
    ) -> None:

        self.altezza = (
            len(righe) - 1
        ) // 2

        self.larghezza = (
            len(righe[0]) - 1
        ) // 4

        for y_ascii in range(
            self.altezza
        ):

            # Nel file ASCII la prima
            # riga rappresenta la parte alta.
            # Nel progetto y=0 è in basso.
            y = (
                self.altezza
                - 1
                - y_ascii
            )

            riga_nord = (
                righe[
                    2 * y_ascii
                ]
            )

            riga_celle = (
                righe[
                    2 * y_ascii + 1
                ]
            )

            riga_sud = (
                righe[
                    2 * y_ascii + 2
                ]
            )

            for x in range(
                self.larghezza
            ):

                posizione = (
                    x,
                    y,
                )

                centro = (
                    2 + 4 * x
                )

                muro_nord = (
                    riga_nord[
                        centro - 1:
                        centro + 2
                    ]
                    == "---"
                )

                muro_sud = (
                    riga_sud[
                        centro - 1:
                        centro + 2
                    ]
                    == "---"
                )

                muro_ovest = (
                    riga_celle[
                        4 * x
                    ]
                    == "|"
                )

                muro_est = (
                    riga_celle[
                        4 * (x + 1)
                    ]
                    == "|"
                )

                self.muri[
                    (
                        posizione,
                        Direzione.NORD,
                    )
                ] = muro_nord

                self.muri[
                    (
                        posizione,
                        Direzione.EST,
                    )
                ] = muro_est

                self.muri[
                    (
                        posizione,
                        Direzione.SUD,
                    )
                ] = muro_sud

                self.muri[
                    (
                        posizione,
                        Direzione.OVEST,
                    )
                ] = muro_ovest

    def colora_cella(
        self,
        posizione: tuple[int, int],
        colore: str = "G",
    ) -> None:

        # Nei test non serve
        # visualizzare nulla.
        pass

    def larghezza_labirinto(
        self,
    ) -> int:

        return self.larghezza

    def altezza_labirinto(
        self,
    ) -> int:

        return self.altezza

    def leggi_sensori(
        self,
    ) -> LetturaSensori:

        posizione = (
            self.robot.posizione
        )

        direzione = (
            self.robot.direzione
        )

        return LetturaSensori(
            muro_davanti=self._muro(
                posizione,
                direzione,
            ),

            muro_sinistra=self._muro(
                posizione,
                direzione.sinistra(),
            ),

            muro_destra=self._muro(
                posizione,
                direzione.destra(),
            ),
        )

    def _muro(
        self,
        posizione: tuple[int, int],
        direzione: Direzione,
    ) -> bool:

        return self.muri[
            (
                posizione,
                direzione,
            )
        ]

    def esegui_azione(
        self,
        azione: Azioni,
        robot: StatoRobot,
        mappa: Mappa,
    ) -> None:

        if azione == Azioni.GIRA_SINISTRA:
            robot.gira_sinistra()
            return

        if azione == Azioni.GIRA_DESTRA:
            robot.gira_destra()
            return

        if azione == Azioni.AVANZA:
            self._avanza(
                robot,
                mappa,
            )
            return

        raise ValueError(
            f"Azione non riconosciuta: {azione}"
        )

    def _avanza(
        self,
        robot: StatoRobot,
        mappa: Mappa,
    ) -> None:

        posizione_partenza = (
            robot.posizione
        )

        direzione_movimento = (
            robot.direzione
        )

        if self._muro(
            posizione_partenza,
            direzione_movimento,
        ):

            mappa.imposta_stato_passaggio(
                posizione_partenza,
                direzione_movimento,
                StatoPassaggio.MURO,
            )

            raise RuntimeError(
                "Impossibile avanzare: "
                "parete davanti."
            )

        posizione_arrivo = (
            mappa.cella_vicina(
                posizione_partenza,
                direzione_movimento,
            )
        )

        if not mappa.posizione_valida(
            posizione_arrivo
        ):

            raise RuntimeError(
                f"Movimento fuori dalla mappa: "
                f"{posizione_arrivo}"
            )

        robot.avanza()

        mappa.imposta_stato_passaggio(
            posizione_partenza,
            direzione_movimento,
            StatoPassaggio.LIBERO,
        )