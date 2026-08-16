import random
from collections import deque
from pathlib import Path


DIMENSIONI = [8, 16, 32]
SEEDS = [42]

CARTELLA_OUTPUT = Path("mazes")


DIREZIONI = {
    "N": (0, 1, "S"),
    "E": (1, 0, "W"),
    "S": (0, -1, "N"),
    "W": (-1, 0, "E"),
}


def crea_griglia(dimensione: int):
    """
    Crea una griglia in cui inizialmente
    ogni cella ha quattro muri.
    """
    return {
        (x, y): {
            "N": True,
            "E": True,
            "S": True,
            "W": True,
        }
        for x in range(dimensione)
        for y in range(dimensione)
    }


def celle_centrali(dimensione: int) -> set[tuple[int, int]]:
    """
    Restituisce le quattro celle centrali.
    """

    basso = dimensione // 2 - 1
    alto = dimensione // 2

    return {
        (basso, basso),
        (basso, alto),
        (alto, basso),
        (alto, alto),
    }


def apri_passaggio(
    muri,
    cella1: tuple[int, int],
    cella2: tuple[int, int],
) -> None:
    """
    Rimuove il muro tra due celle adiacenti.
    """

    x1, y1 = cella1
    x2, y2 = cella2

    dx = x2 - x1
    dy = y2 - y1

    if dx == 1:
        muri[cella1]["E"] = False
        muri[cella2]["W"] = False

    elif dx == -1:
        muri[cella1]["W"] = False
        muri[cella2]["E"] = False

    elif dy == 1:
        muri[cella1]["N"] = False
        muri[cella2]["S"] = False

    elif dy == -1:
        muri[cella1]["S"] = False
        muri[cella2]["N"] = False

    else:
        raise ValueError(
            f"Celle non adiacenti: {cella1}, {cella2}"
        )


def genera_struttura_principale(
    muri,
    dimensione: int,
    rng: random.Random,
) -> None:
    """
    Genera un maze connesso tramite randomized DFS.

    Le quattro celle centrali vengono escluse:
    saranno collegate successivamente tramite
    un unico ingresso.

    La partenza (0, 0) viene forzata ad avere
    un'unica uscita verso nord.
    """

    centro = celle_centrali(dimensione)

    partenza = (0, 0)
    cella_sopra = (0, 1)

    # La partenza ha una sola uscita verso nord.
    apri_passaggio(
        muri,
        partenza,
        cella_sopra,
    )

    visitate = {
        partenza,
        cella_sopra,
    }

    stack = [cella_sopra]

    while stack:
        cella = stack[-1]

        x, y = cella

        vicini = []

        for dx, dy, _ in DIREZIONI.values():
            nx = x + dx
            ny = y + dy

            nuova = (nx, ny)

            if not (
                0 <= nx < dimensione
                and 0 <= ny < dimensione
            ):
                continue

            # Il centro viene costruito dopo.
            if nuova in centro:
                continue

            # Non creiamo altri accessi alla partenza.
            if nuova == partenza:
                continue

            if nuova not in visitate:
                vicini.append(nuova)

        if not vicini:
            stack.pop()
            continue

        prossima = rng.choice(vicini)

        apri_passaggio(
            muri,
            cella,
            prossima,
        )

        visitate.add(prossima)
        stack.append(prossima)

    numero_celle_esterne = (
        dimensione * dimensione
        - len(centro)
    )

    if len(visitate) != numero_celle_esterne:
        raise RuntimeError(
            "La struttura principale non è connessa."
        )


def aggiungi_loop(
    muri,
    dimensione: int,
    rng: random.Random,
) -> None:
    """
    Apre alcuni muri aggiuntivi per creare
    percorsi alternativi.

    Non modifica né la partenza né il centro.
    """

    centro = celle_centrali(dimensione)

    candidati = []

    for x in range(dimensione):
        for y in range(dimensione):

            cella = (x, y)

            if cella == (0, 0):
                continue

            if cella in centro:
                continue

            # Possibile collegamento verso est.
            if x + 1 < dimensione:
                altra = (x + 1, y)

                if (
                    altra != (0, 0)
                    and altra not in centro
                    and muri[cella]["E"]
                ):
                    candidati.append(
                        (cella, altra)
                    )

            # Possibile collegamento verso nord.
            if y + 1 < dimensione:
                altra = (x, y + 1)

                if (
                    altra != (0, 0)
                    and altra not in centro
                    and muri[cella]["N"]
                ):
                    candidati.append(
                        (cella, altra)
                    )

    rng.shuffle(candidati)

    # Circa il 4% delle celle genera
    # un collegamento aggiuntivo.
    numero_loop = max(
        1,
        dimensione * dimensione // 25,
    )

    for cella1, cella2 in candidati[:numero_loop]:
        apri_passaggio(
            muri,
            cella1,
            cella2,
        )


def configura_centro(
    muri,
    dimensione: int,
    rng: random.Random,
) -> None:
    """
    Configura le quattro celle centrali come goal.

    - Nessun muro interno.
    - Un solo ingresso dall'esterno.
    """

    basso = dimensione // 2 - 1
    alto = dimensione // 2

    sw = (basso, basso)
    nw = (basso, alto)
    se = (alto, basso)
    ne = (alto, alto)

    # Rimuoviamo tutti i muri interni al goal.
    apri_passaggio(muri, sw, nw)
    apri_passaggio(muri, sw, se)
    apri_passaggio(muri, nw, ne)
    apri_passaggio(muri, se, ne)

    possibili_ingressi = [
        # Sud
        (sw, (basso, basso - 1)),
        (se, (alto, basso - 1)),

        # Nord
        (nw, (basso, alto + 1)),
        (ne, (alto, alto + 1)),

        # Ovest
        (sw, (basso - 1, basso)),
        (nw, (basso - 1, alto)),

        # Est
        (se, (alto + 1, basso)),
        (ne, (alto + 1, alto)),
    ]

    cella_goal, cella_esterna = rng.choice(
        possibili_ingressi
    )

    apri_passaggio(
        muri,
        cella_goal,
        cella_esterna,
    )


def assicura_bordi(
    muri,
    dimensione: int,
) -> None:
    """
    Garantisce che tutti i bordi esterni
    siano completamente chiusi.
    """

    for x in range(dimensione):
        muri[(x, 0)]["S"] = True
        muri[(x, dimensione - 1)]["N"] = True

    for y in range(dimensione):
        muri[(0, y)]["W"] = True
        muri[(dimensione - 1, y)]["E"] = True


def celle_raggiungibili(
    muri,
    dimensione: int,
) -> set[tuple[int, int]]:
    """
    Restituisce tutte le celle raggiungibili
    dalla partenza tramite BFS.
    """

    partenza = (0, 0)

    visitate = {partenza}
    coda = deque([partenza])

    while coda:
        x, y = coda.popleft()

        for direzione, (dx, dy, _) in DIREZIONI.items():

            if muri[(x, y)][direzione]:
                continue

            nx = x + dx
            ny = y + dy

            if not (
                0 <= nx < dimensione
                and 0 <= ny < dimensione
            ):
                continue

            nuova = (nx, ny)

            if nuova not in visitate:
                visitate.add(nuova)
                coda.append(nuova)

    return visitate


def verifica_risolvibilita(
    muri,
    dimensione: int,
) -> None:
    """
    Verifica che:

    - tutte le celle siano raggiungibili;
    - tutte le celle goal siano raggiungibili.
    """

    raggiungibili = celle_raggiungibili(
        muri,
        dimensione,
    )

    tutte_le_celle = {
        (x, y)
        for x in range(dimensione)
        for y in range(dimensione)
    }

    if raggiungibili != tutte_le_celle:
        mancanti = tutte_le_celle - raggiungibili

        raise RuntimeError(
            f"Maze {dimensione}x{dimensione} non connesso. "
            f"Celle non raggiungibili: {len(mancanti)}"
        )

    centro = celle_centrali(dimensione)

    if not centro.issubset(raggiungibili):
        raise RuntimeError(
            "Il goal non è raggiungibile."
        )


def verifica_partenza(
    muri,
) -> None:
    """
    Verifica la configurazione richiesta
    dai test Micromouse:

        o   o
        | S |
        o---o

    quindi:
    - nord aperto
    - est chiuso
    - sud chiuso
    - ovest chiuso
    """

    partenza = muri[(0, 0)]

    assert partenza["N"] is False
    assert partenza["E"] is True
    assert partenza["S"] is True
    assert partenza["W"] is True


def genera_maze(
    dimensione: int,
    seed: int,
):
    rng = random.Random(seed)

    muri = crea_griglia(
        dimensione
    )

    genera_struttura_principale(
        muri,
        dimensione,
        rng,
    )

    aggiungi_loop(
        muri,
        dimensione,
        rng,
    )

    configura_centro(
        muri,
        dimensione,
        rng,
    )

    assicura_bordi(
        muri,
        dimensione,
    )

    verifica_partenza(
        muri
    )

    verifica_risolvibilita(
        muri,
        dimensione,
    )

    return muri


def contenuto_cella(
    x: int,
    y: int,
    dimensione: int,
) -> str:
    """
    Restituisce il contenuto ASCII della cella.
    """

    if (x, y) == (0, 0):
        return " S "

    if (x, y) in celle_centrali(dimensione):
        return " G "

    return "   "


def converti_in_ascii(
    muri,
    dimensione: int,
) -> str:
    """
    Converte il maze nel formato:

    o---o---o
    |   |   |
    o   o---o
    | S |   |
    o---o---o
    """

    righe = []

    # MMS visualizza la coordinata y più alta
    # nella parte superiore del file.
    for y in range(
        dimensione - 1,
        -1,
        -1,
    ):

        # ---------------------------------
        # Pareti nord
        # ---------------------------------

        riga_nord = ""

        for x in range(dimensione):

            riga_nord += "o"

            if muri[(x, y)]["N"]:
                riga_nord += "---"
            else:
                riga_nord += "   "

        riga_nord += "o"

        righe.append(riga_nord)

        # ---------------------------------
        # Pareti verticali + contenuto
        # ---------------------------------

        riga_cella = ""

        for x in range(dimensione):

            if muri[(x, y)]["W"]:
                riga_cella += "|"
            else:
                riga_cella += " "

            riga_cella += contenuto_cella(
                x,
                y,
                dimensione,
            )

        # Muro est dell'ultima cella.
        if muri[(dimensione - 1, y)]["E"]:
            riga_cella += "|"
        else:
            riga_cella += " "

        righe.append(riga_cella)

    # ---------------------------------
    # Parete sud
    # ---------------------------------

    ultima_riga = ""

    for x in range(dimensione):

        ultima_riga += "o"

        if muri[(x, 0)]["S"]:
            ultima_riga += "---"
        else:
            ultima_riga += "   "

    ultima_riga += "o"

    righe.append(ultima_riga)

    return "\n".join(righe) + "\n"


def salva_maze(
    muri,
    dimensione: int,
    seed: int,
) -> None:

    CARTELLA_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Il nome rispetta:
    # ^[A-Za-z0-9-]*$
    nome_file = (
        f"maze-{dimensione}x{dimensione}"
        f"-seed-{seed}.txt"
    )

    percorso = (
        CARTELLA_OUTPUT
        / nome_file
    )

    contenuto = converti_in_ascii(
        muri,
        dimensione,
    )

    percorso.write_text(
        contenuto,
        encoding="utf-8",
    )

    print(
        f"Creato: {percorso}"
    )


def main() -> None:

    for dimensione in DIMENSIONI:

        for seed in SEEDS:

            muri = genera_maze(
                dimensione,
                seed,
            )

            salva_maze(
                muri,
                dimensione,
                seed,
            )


if __name__ == "__main__":
    main()