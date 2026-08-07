from planning.numerico.problem_builder_completo import ProblemBuilderNumericoCompleto
from planning.numerico.costi_azioni import CostiAzioni

from planning.proposizionale.problem_builder_incrementale import (
    ProblemBuilderIncrementale,
)


class ProblemBuilderNumericoIncrementale(
    ProblemBuilderIncrementale,
    ProblemBuilderNumericoCompleto,
):
    """
    Costruisce una sola volta il problema PDDL numerico
    e aggiorna solamente le informazioni modificate.
    """

    nome_problema = "mms_numerico_incrementale"

    def __init__(
        self,
        costi: CostiAzioni | None = None,
    ) -> None:
        ProblemBuilderIncrementale.__init__(self)
        self.costi = costi or CostiAzioni()