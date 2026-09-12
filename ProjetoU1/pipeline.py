from airflow import DAG
from datetime import datetime
from airflow.providers.standard.operators.empty import EmptyOperator
import requests, json
import pandas as pd
import os
    

# with DAG(
#     dag_id="tmdb_api",
#     start_date=datetime(2026, 9,12),
#     schedule= "@daily" ) as dag:

URL = "https://api.themoviedb.org/3/movie/top_rated"
API_KEY = "66f326ea45d4f51ff3ed4071d5f20ad0"


def api_request(URL="", api_key="", n_pages=""):
    parametros = {
        "api_key": api_key,
        "language": "pt-BR",
        "page": n_pages,
    }
    
    result = requests.get(url=URL, params=parametros)
    if (result.status_code == 200):
        dados = result.json()
        return dados
    else:
        print(f"ERROR: {result.status_code}" )


def extract_task(pages):
    all_moves = []
    for page in range(1, pages+1):
        requisicao = api_request(URL, API_KEY , str(page))
        if(requisicao and "results" in requisicao):
            all_moves.extend(requisicao["results"])
    return all_moves

def transform_task(moves,):
    df_all_moves =  pd.DataFrame(moves)
    
    os.makedirs("data", exist_ok=True)
    df_all_moves =  df_all_moves.drop(["backdrop_path","poster_path","softcore","video","adult","original_title"],axis=1)
    df_all_moves = df_all_moves.sort_values(by="vote_average", ascending=False)
    df_all_moves.to_csv("data/raw_movies.csv", index=False)
    return df_all_moves

transform_task(extract_task(5))