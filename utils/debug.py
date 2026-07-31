import sys


def debug(*valori: object) -> None:
    """
    Scrive i messaggi diagnostici su stderr.

    stdout deve rimanere riservato esclusivamente
    al protocollo di comunicazione con MMS.
    """
    print(*valori, file=sys.stderr, flush=True)
