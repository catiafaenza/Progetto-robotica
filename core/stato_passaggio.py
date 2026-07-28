from enum import Enum
class StatoPassaggio(Enum):
    SCONOSCIUTO = 0 #il robot non ha ancora osservato quel lato
    LIBERO = 1 #nella direzione del robot il passaggio è aperto
    MURO = 2 #nella direzione del robot c'è un muro
