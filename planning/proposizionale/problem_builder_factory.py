from planning.strategia_aggiornamento import StrategiaAggiornamento
from planning.proposizionale.problem_builder_completo import ProblemBuilder
from planning.proposizionale.problem_builder_incrementale import ProblemBuilderIncrementale

def crea_problem_builder(strategia: StrategiaAggiornamento) -> ProblemBuilder:
    """
    Crea un'istanza di ProblemBuilder.
    """
    if strategia == StrategiaAggiornamento.COMPLETA:
        return ProblemBuilder()
    if strategia == StrategiaAggiornamento.INCREMENTALE:
        return ProblemBuilderIncrementale()
    raise ValueError(f"Strategia di aggiornamento non supportata: {strategia}")