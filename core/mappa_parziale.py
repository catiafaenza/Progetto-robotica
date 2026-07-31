from collections import deque

from core.direzione import Direzione
from core.stato_passaggio import StatoPassaggio
from core.modifica_passaggio import ModificaPassaggio


Posizione = tuple[int, int]


class Mappa:
    """Mappa parziale costruita progressivamente tramite i sensori MMS."""

    ORDINE_DIREZIONI = (
        Direzione.NORD,
        Direzione.EST,
        Direzione.SUD,
        Direzione.OVEST,
    )

    def __init__(self, larghezza: int, altezza: int) -> None:
        if larghezza <= 0 or altezza <= 0:
            raise ValueError("Larghezza e altezza devono essere positive.")

        self.larghezza = larghezza
        self.altezza = altezza

        self.passaggi: dict[
            tuple[Posizione, Direzione],
            StatoPassaggio,
        ] = {}

        self.celle_visitate: set[Posizione] = set()
        self.numero_visite: dict[Posizione, int] = {}

        # Evita di contare come nuova visita ogni rilettura dei sensori
        # eseguita dopo una semplice rotazione nella stessa cella.
        self._ultima_cella_registrata: Posizione | None = None
        self._modifiche_passaggi: set[
            ModificaPassaggio
        ] = set()

    def cella_vicina(
        self,
        posizione: Posizione,
        direzione: Direzione,
    ) -> Posizione:
        x, y = posizione
        dx, dy = direzione.value
        return x + dx, y + dy

    def posizione_valida(self, posizione: Posizione) -> bool:
        x, y = posizione
        return 0 <= x < self.larghezza and 0 <= y < self.altezza

    def stato_passaggio(
        self,
        posizione: Posizione,
        direzione: Direzione,
    ) -> StatoPassaggio:
        if not self.posizione_valida(posizione):
            raise ValueError(f"Posizione fuori dalla mappa: {posizione}")

        return self.passaggi.get(
            (posizione, direzione),
            StatoPassaggio.SCONOSCIUTO,
        )

    def imposta_stato_passaggio(
            self,
            posizione: Posizione,
            direzione: Direzione,
            stato: StatoPassaggio,
        ) -> None:
            self._aggiorna_passaggio_orientato(
                posizione=posizione,
                direzione=direzione,
                stato=stato,
            )

            vicina = self.cella_vicina(
                posizione,
                direzione,
            )

            if self.posizione_valida(vicina):
                self._aggiorna_passaggio_orientato(
                    posizione=vicina,
                    direzione=direzione.opposta(),
                    stato=stato,
                )

    def segna_cella_visitata(self, posizione: Posizione) -> None:
        if not self.posizione_valida(posizione):
            raise ValueError(f"Posizione fuori dalla mappa: {posizione}")

        self.celle_visitate.add(posizione)

        if posizione != self._ultima_cella_registrata:
            self.numero_visite[posizione] = self.numero_visite.get(posizione, 0) + 1
            self._ultima_cella_registrata = posizione

    def is_cella_visitata(self, posizione: Posizione) -> bool:
        if not self.posizione_valida(posizione):
            raise ValueError(f"Posizione fuori dalla mappa: {posizione}")
        return posizione in self.celle_visitate

    def visite_cella(self, posizione: Posizione) -> int:
        if not self.posizione_valida(posizione):
            raise ValueError(f"Posizione fuori dalla mappa: {posizione}")
        return self.numero_visite.get(posizione, 0)

    def inizializza_pareti_esterne(self) -> None:
        for x in range(self.larghezza):
            self.imposta_stato_passaggio(
                (x, 0), Direzione.SUD, StatoPassaggio.MURO
            )
            self.imposta_stato_passaggio(
                (x, self.altezza - 1), Direzione.NORD, StatoPassaggio.MURO
            )

        for y in range(self.altezza):
            self.imposta_stato_passaggio(
                (0, y), Direzione.OVEST, StatoPassaggio.MURO
            )
            self.imposta_stato_passaggio(
                (self.larghezza - 1, y), Direzione.EST, StatoPassaggio.MURO
            )

    def vicini_raggiungibili(self, posizione: Posizione) -> list[Posizione]:
        if not self.posizione_valida(posizione):
            raise ValueError(f"Posizione fuori dalla mappa: {posizione}")

        vicini: list[Posizione] = []

        for direzione in self.ORDINE_DIREZIONI:
            if self.stato_passaggio(posizione, direzione) != StatoPassaggio.LIBERO:
                continue

            vicina = self.cella_vicina(posizione, direzione)
            if self.posizione_valida(vicina):
                vicini.append(vicina)

        return vicini

    def numero_passaggi_sconosciuti(self, posizione: Posizione) -> int:
        if not self.posizione_valida(posizione):
            raise ValueError(f"Posizione fuori dalla mappa: {posizione}")

        return sum(
            self.stato_passaggio(posizione, direzione)
            == StatoPassaggio.SCONOSCIUTO
            for direzione in self.ORDINE_DIREZIONI
        )

    def direzione_tra(
        self,
        partenza: Posizione,
        arrivo: Posizione,
    ) -> Direzione:
        if not self.posizione_valida(partenza):
            raise ValueError(f"Posizione di partenza non valida: {partenza}")
        if not self.posizione_valida(arrivo):
            raise ValueError(f"Posizione di arrivo non valida: {arrivo}")

        for direzione in self.ORDINE_DIREZIONI:
            if self.cella_vicina(partenza, direzione) == arrivo:
                return direzione

        raise ValueError(
            f"Le celle {partenza} e {arrivo} non sono adiacenti."
        )

    def celle_frontiera(self) -> set[Posizione]:
        """Celle non visitate raggiungibili da almeno una cella visitata."""
        frontiere: set[Posizione] = set()

        for visitata in self.celle_visitate:
            for vicina in self.vicini_raggiungibili(visitata):
                if vicina not in self.celle_visitate:
                    frontiere.add(vicina)

        return frontiere

    def is_frontiera(self, posizione: Posizione) -> bool:
        return posizione in self.celle_frontiera()




    # UTILITY BFS PER RISOLUZIONE DEI PAREGGI
    #1) verificare che una frontiera sia raggiungibile;
    #2) ordinare le frontiere per distanza;
    #3) risolvere deterministicamente i pareggi;
    #4) evitare chiamate al planner inutili.


    def distanze_da(self, partenza: Posizione) -> dict[Posizione, int]:
        if not self.posizione_valida(partenza):
            raise ValueError(f"Posizione di partenza non valida: {partenza}")

        distanze: dict[Posizione, int] = {partenza: 0}
        coda: deque[Posizione] = deque([partenza])

        while coda:
            corrente = coda.popleft()

            for vicina in self.vicini_raggiungibili(corrente):
                if vicina in distanze:
                    continue

                distanze[vicina] = distanze[corrente] + 1
                coda.append(vicina)

        return distanze

    def distanza(
        self,
        partenza: Posizione,
        arrivo: Posizione,
    ) -> int | None:
        return self.distanze_da(partenza).get(arrivo)

    def percorso_minimo(
        self,
        partenza: Posizione,
        arrivo: Posizione,
    ) -> list[Posizione] | None:
        """BFS sui soli passaggi già confermati come liberi."""
        if not self.posizione_valida(partenza):
            raise ValueError(f"Posizione di partenza non valida: {partenza}")
        if not self.posizione_valida(arrivo):
            raise ValueError(f"Posizione di arrivo non valida: {arrivo}")

        if partenza == arrivo:
            return [partenza]

        precedente: dict[Posizione, Posizione | None] = {partenza: None}
        coda: deque[Posizione] = deque([partenza])

        while coda:
            corrente = coda.popleft()

            for vicina in self.vicini_raggiungibili(corrente):
                if vicina in precedente:
                    continue

                precedente[vicina] = corrente

                if vicina == arrivo:
                    return self._ricostruisci_percorso(
                        partenza,
                        arrivo,
                        precedente,
                    )

                coda.append(vicina)

        return None

    def _ricostruisci_percorso(
        self,
        partenza: Posizione,
        arrivo: Posizione,
        precedente: dict[Posizione, Posizione | None],
    ) -> list[Posizione]:
        percorso: list[Posizione] = []
        corrente: Posizione | None = arrivo

        while corrente is not None:
            percorso.append(corrente)
            corrente = precedente[corrente]

        percorso.reverse()

        if not percorso or percorso[0] != partenza:
            raise RuntimeError("Errore durante la ricostruzione del percorso.")

        return percorso

    def estrai_modifiche_passaggi(
    self,
    ) -> set[ModificaPassaggio]:
        modifiche = set(self._modifiche_passaggi)
        self._modifiche_passaggi.clear()
        return modifiche

    def _aggiorna_passaggio_orientato(
        self,
        *,
        posizione: Posizione,
        direzione: Direzione,
        stato: StatoPassaggio,
    ) -> None:
        chiave = posizione, direzione

        stato_precedente = self.passaggi.get(
            chiave,
            StatoPassaggio.SCONOSCIUTO,
        )

        if stato_precedente == stato:
            return

        self.passaggi[chiave] = stato

        self._modifiche_passaggi.add(
            ModificaPassaggio(
                posizione=posizione,
                direzione=direzione,
                stato=stato,
            )
        )
            