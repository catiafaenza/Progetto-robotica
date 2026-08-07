
from core.azioni import Azioni
from core.direzione import Direzione
from core.mappa_parziale import Mappa, Posizione
from core.stato_robot import StatoRobot
from mms.interfaccia_mms import InterfacciaMMS
from planning.gestore_pianificazione import GestorePianificazione
from planning.plan_executor import PlanExecutor
from utils.debug import debug


class SpeedRun:

    def __init__(
        self,
        interfaccia: InterfacciaMMS,
        robot: StatoRobot,
        mappa: Mappa,
        gestore_pianificazione: GestorePianificazione,
        executor: PlanExecutor,
        centri: set[Posizione],
    ) -> None:
        self.interfaccia = interfaccia
        self.robot = robot
        self.mappa = mappa
        self.gestore = gestore_pianificazione
        self.executor = executor
        self.centri = centri

    def esegui(self) -> None:
        debug("\n===== SPEED RUN =====")

        # Riporta fisicamente il robot alla posizione iniziale.
        if not self._ritorna_all_inizio():
            debug("Impossibile tornare all'inizio.")
            return

        # La speed run parte sempre da (0, 0) verso NORD.
        self._orienta_nord()

        # Nuova pianificazione usando la mappa già conosciuta.
        problema = self.gestore.builder.build(
            mappa=self.mappa,
            robot=self.robot,
            celle_goal=self.centri,
        )

        risultato = self.gestore.planner.solve(problema)

        if risultato.piano is None:
            debug("Nessun piano trovato per la speed run.")
            return

        azioni = self.executor.estrai_azioni(
            risultato.piano
        )

        costo_piano = self.gestore.builder.calcola_costo_piano(
            risultato.piano
        )

        debug(
            "Piano speed run:",
            [azione.action.name for azione in azioni],
        )

        debug(
            f"Tempo planning: "
            f"{risultato.tempo_pianificazione:.6f}s",
            f"Lunghezza piano: {len(azioni)}",
            f"Costo piano: {costo_piano}",
        )

        # Esecuzione completa del piano senza nuova esplorazione.
        for azione in azioni:
            esecuzione = self.executor.esegui_azione_pddl(
                azione_pddl=azione,
                interfaccia=self.interfaccia,
                robot=self.robot,
                mappa=self.mappa,
            )

            if not esecuzione.successo:
                debug(
                    "Speed run interrotta:",
                    esecuzione.errore,
                )
                return

        successo = self.robot.posizione in self.centri

        debug(
            "Speed run terminata.",
            f"successo={successo}",
            f"posizione={self.robot.posizione}",
            f"tempo_planning="
            f"{risultato.tempo_pianificazione:.6f}s",
            f"lunghezza_piano={len(azioni)}",
            f"costo_piano={costo_piano}",
        )

    def _ritorna_all_inizio(self) -> bool:
        debug(
            "Ritorno all'inizio:",
            f"{self.robot.posizione} -> (0, 0)",
        )

        problema = self.gestore.builder.build(
            mappa=self.mappa,
            robot=self.robot,
            celle_goal={(0, 0)},
        )

        risultato = self.gestore.planner.solve(problema)

        if risultato.piano is None:
            return False

        azioni = self.executor.estrai_azioni(
            risultato.piano
        )

        debug(
            "Piano ritorno:",
            [azione.action.name for azione in azioni],
        )

        for azione in azioni:
            esecuzione = self.executor.esegui_azione_pddl(
                azione_pddl=azione,
                interfaccia=self.interfaccia,
                robot=self.robot,
                mappa=self.mappa,
            )

            if not esecuzione.successo:
                return False

        return self.robot.posizione == (0, 0)

    def _orienta_nord(self) -> None:
        while self.robot.direzione != Direzione.NORD:

            if self.robot.direzione.destra() == Direzione.NORD:
                azione = Azioni.GIRA_DESTRA
            else:
                azione = Azioni.GIRA_SINISTRA

            self.interfaccia.esegui_azione(
                azione=azione,
                robot=self.robot,
                mappa=self.mappa,
            )

