from core.direzione import Direzione

class StatoRobot:
    def __init__(
        self,
        posizione: tuple[int, int] = (0, 0),
        direzione: Direzione = Direzione.NORD,
    ):
        self.posizione = posizione
        self.direzione = direzione


   #rotazioni del robot
    def gira_sinistra(self) -> None:
        self.direzione = self.direzione.sinistra()

    def gira_destra(self) -> None:
        self.direzione = self.direzione.destra()

    #spostamento del robot
    def avanza(self) -> None:
        dx, dy = self.direzione.value
        x, y = self.posizione
        self.posizione = (x + dx, y + dy)

   
       


    

