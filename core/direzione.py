from enum import Enum

class Direzione(Enum):
    NORD = (0,1)
    EST = (1,0)
    SUD = (0,-1)
    OVEST = (-1,0)

    #come cambiano le direzioni quando il robot ruota a sinistra o a destra, o quando si considera la direzione opposta
    def sinistra(self) -> 'Direzione':
        if self == Direzione.NORD:
            return Direzione.OVEST
        elif self == Direzione.SUD:
            return Direzione.EST
        elif self == Direzione.EST:
            return Direzione.NORD
        elif self == Direzione.OVEST:
            return Direzione.SUD

    def destra(self) -> 'Direzione':
        if self == Direzione.NORD:
            return Direzione.EST
        elif self == Direzione.SUD:
            return Direzione.OVEST
        elif self == Direzione.EST:
            return Direzione.SUD
        elif self == Direzione.OVEST:
            return Direzione.NORD

    def opposta(self) -> 'Direzione':
        if self == Direzione.NORD:
            return Direzione.SUD
        elif self == Direzione.SUD:
            return Direzione.NORD
        elif self == Direzione.EST:
            return Direzione.OVEST
        elif self == Direzione.OVEST:
            return Direzione.EST
    