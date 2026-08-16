from planning.strategia_aggiornamento import (
    StrategiaAggiornamento,
    TipoProblema,
)

from test.utils import esegui_test


MAZES = [
    "maze-8x8-seed-42",
    "maze-16x16-seed-42",
    "maze-32x32-seed-42",
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
    ),
    (
        TipoProblema.NUMERICO,
        "enhsp",
        "enhsp-opt",
    ),
]

MAX_CHIAMATE = 20


def main() -> None:

    for (
        tipo_problema,
        planner_esplorazione,
        planner_speed_run,
    ) in CONFIGURAZIONI:

        for strategia in STRATEGIE:

            for maze in MAZES:

                esegui_test(
                    nome_test="scalabilita",

                    configurazione=
                        strategia.value,

                    maze=maze,

                    tipo_problema=
                        tipo_problema,

                    strategia=
                        strategia,

                    nome_planner=
                        planner_esplorazione,

                    nome_planner_speed_run=
                        planner_speed_run,

                    esegui_speed_run=False,

                    max_chiamate_planner=
                        MAX_CHIAMATE,
                )


if __name__ == "__main__":
    main()