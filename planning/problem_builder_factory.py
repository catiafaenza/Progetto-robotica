from planning.strategia_aggiornamento import StrategiaAggiornamento, TipoProblema
from planning.proposizionale.problem_builder_completo import ProblemBuilder
from planning.proposizionale.problem_builder_incrementale import ProblemBuilderIncrementale
from planning.numerico.problem_builder_numerico import ProblemBuilderNumerico

def crea_problem_builder(tipo: TipoProblema, strategia: StrategiaAggiornamento) -> ProblemBuilder:
    """
    Crea un'istanza di ProblemBuilder.
    """
    if tipo == TipoProblema.PROPOSIZIONALE:
        if strategia == StrategiaAggiornamento.COMPLETA:
            return ProblemBuilder()
        if strategia == StrategiaAggiornamento.INCREMENTALE:
            return ProblemBuilderIncrementale()
    if tipo == TipoProblema.NUMERICO:
        if strategia == StrategiaAggiornamento.COMPLETA:
            return ProblemBuilderNumerico()
        #if strategia == StrategiaAggiornamento.INCREMENTALE:
            # return ProblemBuilderNumericoIncrementale()
    raise ValueError(f"Combinazione di tipo e strategia non supportata: {tipo}, {strategia}")