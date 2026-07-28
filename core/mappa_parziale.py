from core.direzione import Direzione
from core.stato_passaggio import StatoPassaggio
from core.stato_robot import StatoRobot
from core.lettura_sensori import LetturaSensori

class Mappa:
    #non ho ostacoli ma solo pareti divisorie

    #ASSUNZIONE: Il robot conosce a priori la dimensione della griglia, 
    # la propria configurazione iniziale e la definizione della zona obiettivo. 
    # Non conosce invece la disposizione delle pareti interne, 
    # che viene acquisita progressivamente attraverso i sensori del simulatore MMS.

    def __init__(self, larghezza: int, altezza: int):
        if larghezza <= 0 or altezza <= 0:
            raise ValueError(
                "Larghezza e altezza devono essere positive."
            )

        self.larghezza = larghezza
        self.altezza = altezza
        self.passaggi: dict[
            tuple[tuple[int, int], Direzione], #chiave: posizione e direzione
            StatoPassaggio ] = {}
        self.celle_visitate: set[tuple[int, int]] = set()
        

    def cella_vicina(
        self,
        posizione: tuple[int, int],
        direzione: Direzione) -> tuple[int, int]:
   
        x, y = posizione
        dx, dy = direzione.value

        return x + dx, y + dy

    def posizione_valida(
        self, posizione: tuple[int, int]) -> bool:

        x, y = posizione

        return (
            0 <= x < self.larghezza
            and 0 <= y < self.altezza
        )

    #partendo da una cella (x,y) in direzione d, il passaggio è libero, c'è un muro o non lo so ancora?
    def stato_passaggio(
        self,
        posizione: tuple[int, int],
        direzione: Direzione) -> StatoPassaggio:

        if not self.posizione_valida(posizione):
            raise ValueError(
                f"Posizione fuori dalla mappa: {posizione}"
            )
         
        return self.passaggi.get((posizione, direzione), StatoPassaggio.SCONOSCIUTO) #se la chiave non esiste, ritorna SCONOSCIUTO

    def imposta_stato_passaggio(self,
        posizione: tuple[int, int],
        direzione: Direzione,
        stato: StatoPassaggio) -> None:

        if not self.posizione_valida(posizione):
            raise ValueError(
                f"Posizione fuori dalla mappa: {posizione}"
            )

        cella_vicina = self.cella_vicina(posizione, direzione)

        #aggiorno il passaggio alla posizione corrente
        self.passaggi[(posizione, direzione)] = stato

        #aggiorno il lato apposto della cella vicina per simmetria
        if self.posizione_valida(cella_vicina):
            self.passaggi[
                (cella_vicina, direzione.opposta())
            ] = stato

    def segna_cella_visitata(
        self,
        posizione: tuple[int, int],
    ) -> None:
        if not self.posizione_valida(posizione):
            raise ValueError(
                f"Posizione fuori dalla mappa: {posizione}"
            )

        self.celle_visitate.add(posizione)

    def is_cella_visitata( self, posizione: tuple[int, int]) -> bool:
        if not self.posizione_valida(posizione):
            raise ValueError(
                f"Posizione fuori dalla mappa: {posizione}"
            )

        return posizione in self.celle_visitate

    def inizializza_pareti_esterne(self) -> None:
        for x in range(self.larghezza):
                self.imposta_stato_passaggio(
                    (x, 0),
                    Direzione.SUD,
                    StatoPassaggio.MURO,
                )

                self.imposta_stato_passaggio(
                    (x, self.altezza - 1),
                    Direzione.NORD,
                    StatoPassaggio.MURO,
                )

        for y in range(self.altezza):
                self.imposta_stato_passaggio(
                    (0, y),
                    Direzione.OVEST,
                    StatoPassaggio.MURO,
                )

                self.imposta_stato_passaggio(
                    (self.larghezza - 1, y),
                    Direzione.EST,
                    StatoPassaggio.MURO,
                )
    def vicini_raggiungibili(self, posizione: tuple[int, int]) -> list[tuple[int, int]]:
        vicini = []
        for direzione in Direzione:
            if(self.stato_passaggio(posizione, direzione) == StatoPassaggio.LIBERO):
                cella_vicina = self.cella_vicina(posizione, direzione)
                if self.posizione_valida(cella_vicina):
                    vicini.append(cella_vicina)
        return vicini

   