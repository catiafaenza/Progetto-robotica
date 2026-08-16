from planning.strategia_aggiornamento import (
    StrategiaAggiornamento,
    TipoProblema,
)

from test.utils import esegui_test


MAZES = [
    "japan1996ef",
    "japan2007ef",
    "16x16_example5",
]

STRATEGIE = [
    StrategiaAggiornamento.COMPLETA,
    StrategiaAggiornamento.INCREMENTALE,
]

CONFIGURAZIONI = [
    (
        TipoProblema.PROPOSIZIONALE,
        "fast-downward",
        "fast-downward-opt",
        "proposizionale",
    ),
    (
        TipoProblema.NUMERICO,
        "enhsp",
        "enhsp-opt",
        "numerico",
    ),
]


def main() -> None:

    for (
        tipo_problema,
        planner_esplorazione,
        planner_speed_run,
        nome_test,
    ) in CONFIGURAZIONI:

        for strategia in STRATEGIE:

            for maze in MAZES:

                esegui_test(
                    nome_test=nome_test,
                    configurazione=strategia.value,
                    maze=maze,
                    tipo_problema=tipo_problema,
                    strategia=strategia,
                    nome_planner=planner_esplorazione,
                    nome_planner_speed_run=planner_speed_run,
                    esegui_speed_run=True,
                )


if __name__ == "__main__":
    main()