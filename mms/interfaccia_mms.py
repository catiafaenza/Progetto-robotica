import API

from core.azioni import Azioni
from core.lettura_sensori import LetturaSensori
from core.mappa_parziale import Mappa
from core.stato_passaggio import StatoPassaggio
from core.stato_robot import StatoRobot


class InterfacciaMMS:


    def colora_cella(
        self,
        posizione: tuple[int, int],
        colore: str = "G",
    ) -> None:
        x, y = posizione
        API.setColor(x, y, colore)
        
    def larghezza_labirinto(self) -> int:
        return API.mazeWidth()

    def altezza_labirinto(self) -> int:
        return API.mazeHeight()
    
    def leggi_sensori(self) -> LetturaSensori:
        return LetturaSensori(
            muro_davanti=API.wallFront(),
            muro_sinistra=API.wallLeft(),
            muro_destra=API.wallRight(),
        )

    def esegui_azione(
        self,
        azione: Azioni,
        robot: StatoRobot,
        mappa: Mappa,
    ) -> None:
        if azione == Azioni.GIRA_SINISTRA:
            API.turnLeft()
            robot.gira_sinistra()
            return

        if azione == Azioni.GIRA_DESTRA:
            API.turnRight()
            robot.gira_destra()
            return

        if azione == Azioni.AVANZA:
            self._avanza(robot, mappa)
            return

        raise ValueError(
            f"Azione non riconosciuta: {azione}"
        )

    def _avanza(
        self,
        robot: StatoRobot,
        mappa: Mappa,
    ) -> None:
        posizione_partenza = robot.posizione
        direzione_movimento = robot.direzione

        if API.wallFront():
            mappa.imposta_stato_passaggio(
                posizione_partenza,
                direzione_movimento,
                StatoPassaggio.MURO,
            )

            raise RuntimeError(
                "Impossibile avanzare: parete davanti."
            )

        posizione_arrivo = mappa.cella_vicina(
            posizione_partenza,
            direzione_movimento,
        )

        if not mappa.posizione_valida(posizione_arrivo):
            raise RuntimeError(
                f"Movimento fuori dalla mappa: "
                f"{posizione_arrivo}"
            )

        API.moveForward()
        robot.avanza()

        mappa.imposta_stato_passaggio(
            posizione_partenza,
            direzione_movimento,
            StatoPassaggio.LIBERO,
        )