from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv

load_dotenv()

from src.modules.intent_classifier.model import Mensagem, ResultadoModelo, PredicaoMensagem
from src.modules.intent_classifier import service

from src.shared.database.engine import prediction_collection

router = APIRouter()

@router.post('/predictions')
def post_predictions(msg: Mensagem):
    outputs = service.predict_all(msg.text)
    outputs['message'] = msg.model_dump()          # a mensagem entra ANTES de gravar
    prediction_collection.insert_one(outputs)      # grava predicoes + mensagem
    outputs.pop('_id', None)                       # o insert_one adiciona _id (ObjectId)
    return outputs

@router.get('/predictions')
def get_predictions(limit: int = 20):
    cursor = (prediction_collection
              .find({}, {'_id': 0})                # _id fora, ObjectId nao vira JSON
              .sort('message.timestamp', -1)       # mais recentes primeiro
              .limit(limit))
    return list(cursor)                            # cursor -> lista
