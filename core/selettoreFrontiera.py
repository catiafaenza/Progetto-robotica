from dataclasses import dataclass

from core.direzione import Direzione
from core.mappa_parziale import Mappa, Posizione
from core.stato_robot import StatoRobot


@dataclass(frozen=True)
class ValutazioneFrontiera:
    posizione: Posizione
    distanza: int
    costo_rotazione_iniziale: int
    passaggi_sconosciuti: int
    numero_visite: int
    ordine_direzione: int


class SelettoreFrontiera:
    """Selezione deterministica del prossimo goal di esplorazione."""

    ORDINE_DIREZIONI = {
        Direzione.NORD: 0,
        Direzione.EST: 1,
        Direzione.SUD: 2,
        Direzione.OVEST: 3,
    }

    def scegli(self, mappa: Mappa, robot: StatoRobot) -> Posizione | None:
        valutazioni = [
            valutazione
            for frontiera in mappa.celle_frontiera()
            if (
                valutazione := self._valuta_frontiera(
                    mappa=mappa,
                    robot=robot,
                    frontiera=frontiera,
                )
            )
            is not None
        ]

        if not valutazioni:
            return None

        return min(valutazioni, key=self._chiave_ordinamento).posizione

    def _valuta_frontiera(
        self,
        mappa: Mappa,
        robot: StatoRobot,
        frontiera: Posizione,
    ) -> ValutazioneFrontiera | None:
        percorso = mappa.percorso_minimo(robot.posizione, frontiera)
        if percorso is None:
            return None

        direzione_iniziale = self._direzione_iniziale(
            mappa,
            percorso,
            robot.direzione,
        )

        return ValutazioneFrontiera(
            posizione=frontiera,
            distanza=len(percorso) - 1,
            costo_rotazione_iniziale=self._costo_rotazione(
                robot.direzione,
                direzione_iniziale,
            ),
            passaggi_sconosciuti=mappa.numero_passaggi_sconosciuti(frontiera),
            numero_visite=mappa.visite_cella(frontiera),
            ordine_direzione=self.ORDINE_DIREZIONI[direzione_iniziale],
        )

    def _direzione_iniziale(
        self,
        mappa: Mappa,
        percorso: list[Posizione],
        direzione_robot: Direzione,
    ) -> Direzione:
        if len(percorso) < 2:
            return direzione_robot
        return mappa.direzione_tra(percorso[0], percorso[1])

    def _costo_rotazione(
        self,
        direzione_attuale: Direzione,
        direzione_desiderata: Direzione,
    ) -> int:
        if direzione_attuale == direzione_desiderata:
            return 0
        if direzione_attuale.sinistra() == direzione_desiderata:
            return 1
        if direzione_attuale.destra() == direzione_desiderata:
            return 1
        return 2

    def _chiave_ordinamento(
        self,
        valutazione: ValutazioneFrontiera,
    ) -> tuple[int, int, int, int, int, int, int]:
        x, y = valutazione.posizione
        return (
            valutazione.distanza,
            valutazione.costo_rotazione_iniziale,
            -valutazione.passaggi_sconosciuti,
            valutazione.numero_visite,
            valutazione.ordine_direzione,
            x,
            y,
        )