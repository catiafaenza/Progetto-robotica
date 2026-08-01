from enum import Enum

class StrategiaAggiornamento(Enum):
    COMPLETA = "completa"
    INCREMENTALE = "incrementale"

class TipoProblema(Enum):
    PROPOSIZIONALE = "proposizionale"
    NUMERICO = "numerico"