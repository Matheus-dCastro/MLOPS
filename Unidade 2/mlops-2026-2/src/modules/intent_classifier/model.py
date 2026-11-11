from typing import Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def time_now():
    return datetime.now(timezone.utc)

class Mensagem(BaseModel):
    id: Optional[str] = None
    nome: Optional[str] = None
    text: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=time_now)

class ResultadoModelo(BaseModel):
    intent: str
    probs: Dict[str, float]

class PredicaoMensagem(BaseModel):
    mensagem: Mensagem
    predicao: ResultadoModelo


