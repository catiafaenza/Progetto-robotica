from core.direzione import Direzione
from core.mappa_parziale import Mappa
from core.stato_passaggio import StatoPassaggio


def crea_mappa_test() -> Mappa:
    mappa = Mappa(larghezza=4, altezza=4)
    mappa.inizializza_pareti_esterne()

    mappa.imposta_stato_passaggio(
        (0, 0),
        Direzione.NORD,
        StatoPassaggio.LIBERO,
    )

    mappa.imposta_stato_passaggio(
        (0, 1),
        Direzione.EST,
        StatoPassaggio.LIBERO,
    )

    return mappa


def test_conteggio_visite() -> None:
    mappa = crea_mappa_test()

    mappa.segna_cella_visitata((0, 0))
    mappa.segna_cella_visitata((0, 0))

    assert mappa.is_cella_visitata((0, 0))
    assert mappa.visite_cella((0, 0)) == 2


def test_frontiera() -> None:
    mappa = crea_mappa_test()
    mappa.segna_cella_visitata((0, 0))

    assert mappa.celle_frontiera() == {(0, 1)}


def test_distanza() -> None:
    mappa = crea_mappa_test()

    assert mappa.distanza((0, 0), (1, 1)) == 2
    assert mappa.distanza((0, 0), (3, 3)) is None


def test_percorso_minimo() -> None:
    mappa = crea_mappa_test()

    percorso = mappa.percorso_minimo(
        (0, 0),
        (1, 1),
    )

    assert percorso == [
        (0, 0),
        (0, 1),
        (1, 1),
    ]


def test_simmetria_passaggi() -> None:
    mappa = crea_mappa_test()

    assert (
        mappa.stato_passaggio(
            (0, 1),
            Direzione.SUD,
        )
        == StatoPassaggio.LIBERO
    )


def test_direzione_tra() -> None:
    mappa = crea_mappa_test()

    assert (
        mappa.direzione_tra((0, 0), (0, 1))
        == Direzione.NORD
    )