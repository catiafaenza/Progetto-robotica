from statistics import mean, median

from core.mappa_parziale import Mappa
from core.stato_robot import StatoRobot
from metriche.modelli import MetricheRun
from utils.debug import debug


def stampa_riepilogo(
    metriche: MetricheRun,
    mappa: Mappa,
    robot: StatoRobot,
) -> None:
    visite_totali = sum(
        mappa.numero_visite.values()
    )

    visite_ripetute = max(
        0,
        visite_totali
        - len(mappa.celle_visitate),
    )

    tempi_generazione = [
        chiamata.tempo_generazione
        for chiamata in metriche.chiamate
    ]

    tempi_planning = [
        chiamata.tempo_planning
        for chiamata in metriche.chiamate
    ]

    debug("")
    debug("===== RIEPILOGO =====")

    debug(
        "Tipo di problema:",
        metriche.tipo_problema,
    )
    debug(
        "Strategia aggiornamento:",
        metriche.strategia_aggiornamento,
    )

    debug("Successo:", metriche.successo)
    debug(
        "Motivo terminazione:",
        metriche.motivo_terminazione,
    )
    debug("Posizione finale:", robot.posizione)

    debug(
        "Celle visitate distinte:",
        len(mappa.celle_visitate),
    )
    debug(
        "Visite ripetute:",
        visite_ripetute,
    )

    debug(
        "Chiamate planner:",
        metriche.chiamate_planner,
    )
    debug(
        "Chiamate fallite:",
        metriche.chiamate_fallite,
    )

    debug(
        "Tempo generazione totale:",
        f"{metriche.tempo_generazione_totale:.6f}s",
    )
    debug(
        "Tempo planning totale:",
        f"{metriche.tempo_planning_totale:.6f}s",
    )

    if tempi_generazione:
        debug(
            "Tempo generazione medio:",
            f"{mean(tempi_generazione):.6f}s",
        )
        debug(
            "Tempo generazione massimo:",
            f"{max(tempi_generazione):.6f}s",
        )

    if tempi_planning:
        debug(
            "Tempo planning medio:",
            f"{mean(tempi_planning):.6f}s",
        )
        debug(
            "Tempo planning mediano:",
            f"{median(tempi_planning):.6f}s",
        )
        debug(
            "Tempo planning massimo:",
            f"{max(tempi_planning):.6f}s",
        )

    if metriche.chiamate_con_stati_espansi > 0:
        debug(
            "Stati espansi totali:",
            metriche.stati_espansi_totali,
        )

        debug(
            "Stati espansi medi:",
            (
                metriche.stati_espansi_totali
                / metriche.chiamate_con_stati_espansi
            ),
        )

        debug(
            "Chiamate con stati espansi:",
            (
                f"{metriche.chiamate_con_stati_espansi}"
                f"/{metriche.chiamate_planner}"
            ),
        )
    else:
        debug(
            "Stati espansi:",
            "non disponibili",
        )

    debug(
        "Piani invalidati:",
        metriche.piani_invalidati,
    )

    debug(
        "Azioni totali:",
        metriche.azioni_totali,
    )
    debug(
        "Avanzamenti:",
        metriche.avanzamenti,
    )
    debug(
        "Rotazioni totali:",
        metriche.rotazioni_totali,
    )
    debug(
        "Costo eseguito totale:",
        metriche.costo_eseguito_totale,
    )

    if not metriche.chiamate:
        return

    debug("")
    debug("===== CHIAMATE AL PLANNER =====")

    for chiamata in metriche.chiamate:
        debug(
            f"Chiamata {chiamata.indice}: "
            f"tipo={chiamata.tipo_goal} "
            f"pos={chiamata.posizione_robot} "
            f"generazione={chiamata.tempo_generazione:.6f}s "
            f"planning={chiamata.tempo_planning:.6f}s "
            f"piano={chiamata.lunghezza_piano} "
            f"costo={chiamata.costo_piano} "
            f"ottimo={chiamata.piano_ottimo} "
            f"espansi={chiamata.stati_espansi} "
            f"successo={chiamata.successo}"
           
        )