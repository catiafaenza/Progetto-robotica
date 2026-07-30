from core.direzione import Direzione
from core.mappa_parziale import Mappa
from core.selettoreFrontiera import SelettoreFrontiera
from core.stato_passaggio import StatoPassaggio
from core.stato_robot import StatoRobot


def collega(
    mappa: Mappa,
    posizione: tuple[int, int],
    direzione: Direzione,
) -> None:
    mappa.imposta_stato_passaggio(
        posizione,
        direzione,
        StatoPassaggio.LIBERO,
    )


def test_sceglie_frontiera_piu_vicina() -> None:
    mappa = Mappa(4, 4)
    mappa.inizializza_pareti_esterne()

    collega(mappa, (0, 0), Direzione.NORD)
    collega(mappa, (0, 1), Direzione.NORD)
    collega(mappa, (0, 0), Direzione.EST)

    mappa.segna_cella_visitata((0, 0))

    robot = StatoRobot(
        posizione=(0, 0),
        direzione=Direzione.NORD,
    )

    selettore = SelettoreFrontiera()

    obiettivo = selettore.scegli(
        mappa=mappa,
        robot=robot,
    )

    assert obiettivo == (0, 1)

def test_restituisce_none_senza_frontiere() -> None:
    mappa = Mappa(4, 4)
    mappa.inizializza_pareti_esterne()
    mappa.segna_cella_visitata((0, 0))

    robot = StatoRobot(
        posizione=(0, 0),
        direzione=Direzione.NORD,
    )

    selettore = SelettoreFrontiera()

    assert selettore.scegli(mappa, robot) is None