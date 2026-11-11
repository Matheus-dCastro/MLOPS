from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from src.modules.intent_classifier.model import Mensagem

pytestmark = pytest.mark.unit


def test_mensagem_aceita_apenas_texto():
    msg = Mensagem(text="oi")
    assert msg.text == "oi"
    assert msg.id is None
    assert msg.nome is None


def test_mensagem_rejeita_texto_vazio():
    with pytest.raises(ValidationError):
        Mensagem(text="")


def test_mensagem_rejeita_sem_texto():
    with pytest.raises(ValidationError):
        Mensagem(nome="Ana")


def test_mensagem_timestamp_padrao_tem_fuso_utc():
    msg = Mensagem(text="oi")
    assert isinstance(msg.timestamp, datetime)
    assert msg.timestamp.utcoffset() == timedelta(0)
