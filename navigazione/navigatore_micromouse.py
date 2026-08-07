from core.mappa_parziale import Mappa, Posizione
from core.osservatore import Osservatore
from core.stato_robot import StatoRobot
from metriche.raccoglitore import RaccoglitoreMetriche
from mms.interfaccia_mms import InterfacciaMMS
from planning.gestore_pianificazione import GestorePianificazione
from planning.plan_executor import PlanExecutor
from utils.debug import debug


class NavigatoreMicromouse:
    """
    Coordina il ciclo Sense-Plan-Act senza conoscere
    i dettagli interni della costruzione PDDL.
    """

    def __init__(
        self,
        *,
        interfaccia: InterfacciaMMS,
        robot: StatoRobot,
        mappa: Mappa,
        osservatore: Osservatore,
        gestore_pianificazione: GestorePianificazione,
        executor: PlanExecutor,
        metriche: RaccoglitoreMetriche,
        centri: set[Posizione],
    ) -> None:
        self.interfaccia = interfaccia
        self.robot = robot
        self.mappa = mappa
        self.osservatore = osservatore
        self.gestore_pianificazione = (
            gestore_pianificazione
        )
        self.executor = executor
        self.metriche = metriche
        self.centri = set(centri)

    def esegui(
        self,
        massimo_cicli: int = 100_000,
    ) -> None:
        for numero_ciclo in range(massimo_cicli):
            self._osserva()
            self._stampa_stato(numero_ciclo)

            if self.robot.posizione in self.centri:
                self.metriche.termina(
                    "centro_raggiunto",
                    successo=True,
                )
                return

            if self.gestore_pianificazione.goal_raggiunto(
                self.robot.posizione
            ):
                debug(
                    "Goal raggiunto:",
                    sorted(
                        self.gestore_pianificazione.goal_correnti
                    ),
                )
                self.gestore_pianificazione.completa_goal_corrente()

            if not self.gestore_pianificazione.ha_piano():
                esito = self.gestore_pianificazione.pianifica(
                    mappa=self.mappa,
                    robot=self.robot,
                    centri=self.centri,
                )

                if not esito.successo:
                    self.metriche.termina(
                        esito.motivo_terminazione
                        or "errore_pianificazione"
                    )
                    return

            self._agisci()

        self.metriche.termina("limite_cicli_superato")

    def _osserva(self) -> None:
        lettura = self.interfaccia.leggi_sensori()

        self.osservatore.aggiorna_mappa(
            mappa=self.mappa,
            robot=self.robot,
            lettura=lettura,
        )

        self.interfaccia.colora_cella(
        self.robot.posizione,
        "G",
    )

    def _agisci(self) -> None:
        prossima_azione = (
            self.gestore_pianificazione.prossima_azione()
        )

        esecuzione = self.executor.esegui_azione_pddl(
            azione_pddl=prossima_azione,
            interfaccia=self.interfaccia,
            robot=self.robot,
            mappa=self.mappa,
        )

        if not esecuzione.successo:
            self.metriche.registra_piano_invalidato()

            debug(
                "Piano invalidato:",
                esecuzione.errore,
            )

            self.gestore_pianificazione.invalida_piano()
            return

        self.gestore_pianificazione.conferma_azione_eseguita()
        self.metriche.registra_esecuzione(esecuzione)

        debug(
            "Azione eseguita:",
            esecuzione.azione,
            f"nuova_pos={self.robot.posizione}",
            f"nuova_dir={self.robot.direzione.name}",
        )

    def _stampa_stato(self, numero_ciclo: int) -> None:
        debug(
            f"[ciclo {numero_ciclo}]",
            f"pos={self.robot.posizione}",
            f"dir={self.robot.direzione.name}",
            (
                "goal="
                f"{sorted(self.gestore_pianificazione.goal_correnti)}"
            ),
            (
                "tipo_goal="
                f"{self.gestore_pianificazione.tipo_goal}"
            ),
            (
                "azioni_rimanenti="
                f"{self.gestore_pianificazione.numero_azioni_rimanenti}"
            ),
        )
