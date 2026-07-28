from core.lettura_sensori import LetturaSensori
from core.mappa_parziale import Mappa
from core.stato_passaggio import StatoPassaggio
from core.stato_robot import StatoRobot

#sfrutta la lettura dei sensori per aggiornare la mappa parziale del robot
class Osservatore:
    def aggiorna_mappa(
        self,
        mappa: Mappa,
        robot: StatoRobot,
        lettura: LetturaSensori,
    ) -> None:
        
        #osservazioni dei muri in base alla direzione del robot (per ogni direzione true se c'è un muro, false altrimenti)
        osservazioni = {
            robot.direzione: lettura.muro_davanti,
            robot.direzione.sinistra(): lettura.muro_sinistra,
            robot.direzione.destra(): lettura.muro_destra,
        }

        for direzione, muro_presente in osservazioni.items():
            stato = (
                StatoPassaggio.MURO
                if muro_presente
                else StatoPassaggio.LIBERO
            )

            #aggiorna la mappa con le osservazioni dei muri
            mappa.imposta_stato_passaggio(
                posizione=robot.posizione,
                direzione=direzione,
                stato=stato,
            )
        #aggiorna le celle visitate
        mappa.segna_cella_visitata(robot.posizione)