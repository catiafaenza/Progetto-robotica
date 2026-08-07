from planning.numerico.costi_azioni import CostiAzioni
from planning.numerico.supporto_numerico import SupportoNumerico
from planning.proposizionale.problem_builder_completo import (
    ProblemBuilder,
)


class ProblemBuilderNumericoCompleto(
    SupportoNumerico,
    ProblemBuilder,
):
    """
    Rigenera completamente il problema PDDL numerico.

    Riutilizza la costruzione completa del problema proposizionale
    e aggiunge il costo numerico delle azioni.
    """

    nome_problema = "mms_numerico_completo"

    def __init__(
        self,
        costi: CostiAzioni | None = None,
    ) -> None:
        self.costi = costi or CostiAzioni()