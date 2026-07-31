from dataclasses import dataclass

from core.direzione import Direzione
from core.stato_passaggio import StatoPassaggio


Posizione = tuple[int, int]


@dataclass(frozen=True)
class ModificaPassaggio:
    posizione: Posizione
    direzione: Direzione
    stato: StatoPassaggio

    #dalla posizione (x,y) il passaggio verso direzione è stato modificato