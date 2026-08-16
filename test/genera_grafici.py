
import csv
from pathlib import Path

import matplotlib.pyplot as plt


DATI = Path("test/dati")
GRAFICI = Path("test/grafici")

CONFRONTO = GRAFICI / "confronto"
SCALABILITA = GRAFICI / "scalabilita"


ETICHETTE = {
    ("proposizionale", "completa"):
        "Prop. completa",

    ("proposizionale", "incrementale"):
        "Prop. incrementale",

    ("numerico", "completa"):
        "Num. completa",

    ("numerico", "incrementale"):
        "Num. incrementale",
}


ORDINE = [
    ("proposizionale", "completa"),
    ("proposizionale", "incrementale"),
    ("numerico", "completa"),
    ("numerico", "incrementale"),
]


# =========================================================
# FUNZIONI GENERALI
# =========================================================

def leggi_csv(
    percorso: Path,
) -> list[dict[str, str]]:

    if not percorso.exists():
        return []

    with percorso.open(
        encoding="utf-8"
    ) as file:

        return list(
            csv.DictReader(file)
        )


def valore_float(
    riga: dict[str, str],
    metrica: str,
) -> float | None:

    valore = riga.get(
        metrica,
        "",
    )

    if valore == "":
        return None

    return float(valore)


def media(
    valori: list[float],
) -> float | None:

    if not valori:
        return None

    return sum(valori) / len(valori)


# =========================================================
# CONFRONTO PRINCIPALE
# 3 MAZE 16x16
# =========================================================

def ultime_run_per_maze_confronto():
    """
    Prende l'ultima run disponibile per ogni:

    modellazione
    + configurazione
    + maze

    In questo modo eventuali vecchie run duplicate
    non vengono contate più volte.
    """

    righe = (
        leggi_csv(
            DATI / "proposizionale.csv"
        )
        +
        leggi_csv(
            DATI / "numerico.csv"
        )
    )

    risultati = {}

    for riga in righe:

        chiave = (
            riga["modellazione"],
            riga["configurazione"],
            riga["maze"],
        )

        risultati[chiave] = riga

    return risultati


def medie_confronto():
    """
    Raggruppa i maze per configurazione
    e calcola le metriche medie.

    Il successo viene calcolato come
    percentuale di run riuscite.
    """

    run = (
        ultime_run_per_maze_confronto()
    )

    risultati = {}

    for chiave_configurazione in ORDINE:

        modellazione, configurazione = (
            chiave_configurazione
        )

        righe = [
            riga
            for (
                mod,
                conf,
                _,
            ), riga in run.items()
            if (
                mod == modellazione
                and conf == configurazione
            )
        ]

        if not righe:
            continue

        def valori(
            metrica: str,
        ) -> list[float]:

            risultato = []

            for riga in righe:

                valore = valore_float(
                    riga,
                    metrica,
                )

                if valore is not None:
                    risultato.append(
                        valore
                    )

            return risultato

        successi = valori(
            "successo"
        )

        risultato = {
            "numero_run":
                len(righe),

            "successo":
                media(successi),

            "tempo_planning_totale":
                media(
                    valori(
                        "tempo_planning_totale"
                    )
                ),

            "tempo_planning_medio":
                media(
                    valori(
                        "tempo_planning_medio"
                    )
                ),

            "stati_espansi":
                media(
                    valori(
                        "stati_espansi"
                    )
                ),

            "tempo_generazione":
                media(
                    valori(
                        "tempo_generazione"
                    )
                ),

            "tempo_generazione_medio":
                media(
                    valori(
                        "tempo_generazione_medio"
                    )
                ),

            "tempo_replanning_totale":
                media(
                    valori(
                        "tempo_replanning_totale"
                    )
                ),

            "tempo_replanning_medio":
                media(
                    valori(
                        "tempo_replanning_medio"
                    )
                ),

            "chiamate_planner":
                media(
                    valori(
                        "chiamate_planner"
                    )
                ),

            "azioni_totali":
                media(
                    valori(
                        "azioni_totali"
                    )
                ),

            "rotazioni":
                media(
                    valori(
                        "rotazioni"
                    )
                ),

            "speed_run_lunghezza":
                media(
                    valori(
                        "speed_run_lunghezza"
                    )
                ),

            "speed_run_tempo":
                media(
                    valori(
                        "speed_run_tempo"
                    )
                ),

            "speed_run_costo":
                media(
                    valori(
                        "speed_run_costo"
                    )
                ),
        }

        risultati[
            chiave_configurazione
        ] = risultato

    return risultati


def grafico_barre(
    metrica: str,
    titolo: str,
    xlabel: str,
    nome_file: str,
) -> None:

    risultati = medie_confronto()

    etichette = []
    valori = []

    for chiave in ORDINE:

        risultato = risultati.get(
            chiave
        )

        if risultato is None:
            continue

        valore = risultato.get(
            metrica
        )

        if valore is None:
            continue

        etichette.append(
            ETICHETTE[chiave]
        )

        valori.append(
            valore
        )

    if not valori:
        return

    CONFRONTO.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(8, 4.5)
    )

    barre = plt.barh(
        etichette,
        valori,
    )

    plt.xlabel(
        xlabel
    )

    plt.title(
        titolo
    )

    plt.grid(
        axis="x",
        alpha=0.25,
    )

    for barra, valore in zip(
        barre,
        valori,
    ):

        plt.text(
            barra.get_width(),
            barra.get_y()
            + barra.get_height() / 2,
            f" {valore:.3g}",
            va="center",
        )

    plt.tight_layout()

    plt.savefig(
        CONFRONTO
        / nome_file,
        dpi=200,
    )

    plt.close()


def salva_riepilogo() -> None:

    risultati = medie_confronto()

    if not risultati:
        return

    CONFRONTO.mkdir(
        parents=True,
        exist_ok=True,
    )

    percorso = (
        CONFRONTO
        / "riepilogo.csv"
    )

    campi = [
        "Configurazione",
        "Numero maze",
        "Tasso successo (%)",
        "Planning totale medio (s)",
        "Planning medio per chiamata (s)",
        "Stati espansi medi",
        "Generazione problema media (s)",
        "Generazione media per chiamata (s)",
        "Replanning totale medio (s)",
        "Replanning medio per chiamata (s)",
        "Chiamate planner medie",
        "Azioni totali medie",
        "Rotazioni medie",
        "Lunghezza speed run media",
        "Costo speed run medio",
        "Tempo planning speed run medio (s)",
    ]

    with percorso.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=campi,
        )

        writer.writeheader()

        for chiave in ORDINE:

            risultato = risultati.get(
                chiave
            )

            if risultato is None:
                continue

            output = {
                "Configurazione":
                    ETICHETTE[chiave],

                "Numero maze":
                    risultato[
                        "numero_run"
                    ],

                "Tasso successo (%)":
                    (
                        f"{risultato['successo']:.1f}"
                        if risultato[
                            "successo"
                        ] is not None
                        else ""
                    ),

                "Planning totale medio (s)":
                    (
                        f"{risultato['tempo_planning_totale']:.3f}"
                        if risultato[
                            "tempo_planning_totale"
                        ] is not None
                        else ""
                    ),

                "Planning medio per chiamata (s)":
                    (
                        f"{risultato['tempo_planning_medio']:.4f}"
                        if risultato[
                            "tempo_planning_medio"
                        ] is not None
                        else ""
                    ),

                "Stati espansi medi":
                    (
                        f"{risultato['stati_espansi']:.2f}"
                        if risultato[
                            "stati_espansi"
                        ] is not None
                        else ""
                    ),

                "Generazione problema media (s)":
                    (
                        f"{risultato['tempo_generazione']:.4f}"
                        if risultato[
                            "tempo_generazione"
                        ] is not None
                        else ""
                    ),

                "Generazione media per chiamata (s)":
                    (
                        f"{risultato['tempo_generazione_medio']:.5f}"
                        if risultato[
                            "tempo_generazione_medio"
                        ] is not None
                        else ""
                    ),

                "Replanning totale medio (s)":
                    (
                        f"{risultato['tempo_replanning_totale']:.3f}"
                        if risultato[
                            "tempo_replanning_totale"
                        ] is not None
                        else ""
                    ),

                "Replanning medio per chiamata (s)":
                    (
                        f"{risultato['tempo_replanning_medio']:.4f}"
                        if risultato[
                            "tempo_replanning_medio"
                        ] is not None
                        else ""
                    ),

                "Chiamate planner medie":
                    (
                        f"{risultato['chiamate_planner']:.2f}"
                        if risultato[
                            "chiamate_planner"
                        ] is not None
                        else ""
                    ),

                "Azioni totali medie":
                    (
                        f"{risultato['azioni_totali']:.2f}"
                        if risultato[
                            "azioni_totali"
                        ] is not None
                        else ""
                    ),

                "Rotazioni medie":
                    (
                        f"{risultato['rotazioni']:.2f}"
                        if risultato[
                            "rotazioni"
                        ] is not None
                        else ""
                    ),

                "Lunghezza speed run media":
                    (
                        f"{risultato['speed_run_lunghezza']:.2f}"
                        if risultato[
                            "speed_run_lunghezza"
                        ] is not None
                        else ""
                    ),

                "Costo speed run medio":
                    (
                        f"{risultato['speed_run_costo']:.2f}"
                        if risultato[
                            "speed_run_costo"
                        ] is not None
                        else ""
                    ),

                "Tempo planning speed run medio (s)":
                    (
                        f"{risultato['speed_run_tempo']:.4f}"
                        if risultato[
                            "speed_run_tempo"
                        ] is not None
                        else ""
                    ),
            }

            writer.writerow(
                output
            )


# =========================================================
# SCALABILITÀ
# =========================================================

def ultime_run_scalabilita():

    righe = leggi_csv(
        DATI / "scalabilita.csv"
    )

    risultati = {}

    for riga in righe:

        chiave = (
            riga["modellazione"],
            riga["configurazione"],
            int(
                riga["dimensione"]
            ),
        )

        risultati[chiave] = riga

    return risultati


def grafico_scalabilita(
    metrica: str,
    titolo: str,
    ylabel: str,
    nome_file: str,
) -> None:

    risultati = (
        ultime_run_scalabilita()
    )

    if not risultati:
        return

    dimensioni = sorted({
        dimensione
        for _, _, dimensione
        in risultati
    })

    SCALABILITA.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(8, 5)
    )

    disegnato = False

    for modellazione, configurazione in ORDINE:

        x = []
        y = []

        for dimensione in dimensioni:

            riga = risultati.get(
                (
                    modellazione,
                    configurazione,
                    dimensione,
                )
            )

            if riga is None:
                continue

            valore = valore_float(
                riga,
                metrica,
            )

            if valore is None:
                continue

            x.append(
                dimensione
            )

            y.append(
                valore
            )

        if not y:
            continue

        disegnato = True

        plt.plot(
            x,
            y,
            marker="o",
            label=ETICHETTE[
                (
                    modellazione,
                    configurazione,
                )
            ],
        )

    if not disegnato:
        plt.close()
        return

    plt.xticks(
        dimensioni,
        [
            f"{d}x{d}"
            for d in dimensioni
        ],
    )

    plt.xlabel(
        "Dimensione maze"
    )

    plt.ylabel(
        ylabel
    )

    plt.title(
        titolo
    )

    plt.grid(
        alpha=0.25,
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        SCALABILITA
        / nome_file,
        dpi=200,
    )

    plt.close()


def salva_riepilogo_scalabilita() -> None:

    risultati = (
        ultime_run_scalabilita()
    )

    if not risultati:
        return

    SCALABILITA.mkdir(
        parents=True,
        exist_ok=True,
    )

    percorso = (
        SCALABILITA
        / "riepilogo.csv"
    )

    campi = [
        "Configurazione",
        "Dimensione",
        "Chiamate planner",
        "Completato",
        "Interrotto per limite",
        "Planning medio (s)",
        "Stati espansi medi",
        "Generazione media (s)",
        "Replanning medio (s)",
    ]

    with percorso.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=campi,
        )

        writer.writeheader()

        for (
            modellazione,
            configurazione,
        ) in ORDINE:

            for dimensione in [
                8,
                16,
                32,
            ]:

                riga = risultati.get(
                    (
                        modellazione,
                        configurazione,
                        dimensione,
                    )
                )

                if riga is None:
                    continue

                output = {
                    "Configurazione":
                        ETICHETTE[
                            (
                                modellazione,
                                configurazione,
                            )
                        ],

                    "Dimensione":
                        f"{dimensione}x{dimensione}",

                    "Chiamate planner":
                        riga.get(
                            "chiamate_planner",
                            "",
                        ),

                    "Completato":
                        riga.get(
                            "completato",
                            "",
                        ),

                    "Interrotto per limite":
                        riga.get(
                            "interrotto_per_limite",
                            "",
                        ),

                    "Planning medio (s)":
                        (
                            f"{float(riga['tempo_planning_medio']):.4f}"
                            if riga.get(
                                "tempo_planning_medio"
                            )
                            else ""
                        ),

                    "Stati espansi medi":
                        (
                            f"{float(riga['stati_espansi_medi']):.2f}"
                            if riga.get(
                                "stati_espansi_medi"
                            )
                            else ""
                        ),

                    "Generazione media (s)":
                        (
                            f"{float(riga['tempo_generazione_medio']):.5f}"
                            if riga.get(
                                "tempo_generazione_medio"
                            )
                            else ""
                        ),

                    "Replanning medio (s)":
                        (
                            f"{float(riga['tempo_replanning_medio']):.4f}"
                            if riga.get(
                                "tempo_replanning_medio"
                            )
                            else ""
                        ),
                }

                writer.writerow(
                    output
                )


# =========================================================
# GENERAZIONE OUTPUT
# =========================================================

def genera_confronto() -> None:

    grafico_barre(
        metrica="successo",
        titolo="Tasso di successo",
        xlabel="Successo (%)",
        nome_file="successo.png",
    )

    grafico_barre(
        metrica="tempo_planning_totale",
        titolo="Tempo medio totale di pianificazione",
        xlabel="Tempo medio per run (s)",
        nome_file="tempo_planning.png",
    )

    grafico_barre(
        metrica="stati_espansi",
        titolo="Stati espansi medi",
        xlabel="Numero medio di stati",
        nome_file="stati_espansi.png",
    )

    grafico_barre(
        metrica="tempo_generazione",
        titolo="Tempo medio di generazione del problema",
        xlabel="Tempo medio per run (s)",
        nome_file="tempo_generazione.png",
    )

    grafico_barre(
        metrica="tempo_replanning_totale",
        titolo="Tempo medio complessivo di replanning",
        xlabel="Generazione + planning per run (s)",
        nome_file="tempo_replanning.png",
    )

    grafico_barre(
        metrica="rotazioni",
        titolo="Rotazioni medie durante l'esplorazione",
        xlabel="Numero medio di rotazioni",
        nome_file="rotazioni.png",
    )

    grafico_barre(
        metrica="speed_run_lunghezza",
        titolo="Lunghezza media del piano di speed run",
        xlabel="Numero medio di azioni",
        nome_file="speed_run_lunghezza.png",
    )

    grafico_barre(
        metrica="speed_run_costo",
        titolo="Costo medio del piano di speed run",
        xlabel="Costo medio del piano",
        nome_file="speed_run_costo.png",
    )

    salva_riepilogo()


def genera_scalabilita() -> None:

    grafico_scalabilita(
        metrica="tempo_planning_medio",
        titolo="Scalabilità del tempo medio di pianificazione",
        ylabel="Tempo medio per chiamata (s)",
        nome_file="tempo_planning_medio.png",
    )

    grafico_scalabilita(
        metrica="stati_espansi_medi",
        titolo="Scalabilità degli stati espansi",
        ylabel="Stati espansi medi per chiamata",
        nome_file="stati_espansi_medi.png",
    )

    grafico_scalabilita(
        metrica="tempo_generazione_medio",
        titolo="Scalabilità della generazione del problema",
        ylabel="Tempo medio per chiamata (s)",
        nome_file="tempo_generazione_medio.png",
    )

    grafico_scalabilita(
        metrica="tempo_replanning_medio",
        titolo="Scalabilità del tempo medio di replanning",
        ylabel="Generazione + planning per chiamata (s)",
        nome_file="tempo_replanning_medio.png",
    )

    salva_riepilogo_scalabilita()


def main() -> None:

    #genera_confronto()
    genera_scalabilita()

    print(
        "Grafici generati in test/grafici/"
    )


if __name__ == "__main__":
    main()
