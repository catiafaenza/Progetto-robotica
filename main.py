import API
import sys


from core.azioni import Azioni
from core.mappa_parziale import Mappa
from core.osservatore import Osservatore
from core.stato_robot import StatoRobot
from mms.interfaccia_mms import InterfacciaMMS

def debug(messaggio: str) -> None:
    print(messaggio, file=sys.stderr, flush=True)

'''
da capire dove va inserito

def trova_celle_centrali(larghezza: int, altezza: int) -> set[Posizione]:
        x_centrali = {
            (larghezza - 1) // 2,
            larghezza // 2,
        }

        y_centrali = {
            (altezza - 1) // 2,
            altezza // 2,
        }

        return {
            (x, y)
            for x in x_centrali
            for y in y_centrali
        }

'''
def main() -> None:
      
    interfaccia = InterfacciaMMS()
    larghezza = interfaccia.larghezza_labirinto()
    altezza = interfaccia.altezza_labirinto()

    mappa = Mappa(
        larghezza=larghezza,
        altezza=altezza,
    )

    robot = StatoRobot()
    osservatore = Osservatore()
    lettura = interfaccia.leggi_sensori()

    debug(f"Posizione: {robot.posizione}")
    debug(f"Direzione: {robot.direzione}")
    debug(f"Sensori: {lettura}")

    osservatore.aggiorna_mappa(mappa, robot, lettura)
    

    if not lettura.muro_davanti:
        azione = Azioni.AVANZA
    elif not lettura.muro_sinistra:
        azione = Azioni.GIRA_SINISTRA
    elif not lettura.muro_destra:
        azione = Azioni.GIRA_DESTRA
    else:
        debug("Robot bloccato sui tre lati osservabili.")
        return

    debug(f"Azione scelta: {azione}")

    interfaccia.esegui_azione(azione, robot, mappa)
    

    debug(f"Nuova posizione: {robot.posizione}")
    debug(f"Nuova direzione: {robot.direzione}")


if __name__ == "__main__":
    main()


'''def log(string):
    sys.stderr.write("{}\n".format(string))
    sys.stderr.flush()

def main():
    log("Running...")
    API.setColor(0, 0, "G")
    API.setText(0, 0, "abc")
    while True:
        if not API.wallLeft():
            API.turnLeft()
        while API.wallFront():
            API.turnRight()
        API.moveForward()

if __name__ == "__main__":
    main()
'''