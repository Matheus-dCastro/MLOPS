from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
import requests

import pandas as pd
from sklearn.preprocessing import StandardScaler

from datetime import datetime
import os
    

# with DAG(
#     dag_id="tmdb_api",
#     start_date=datetime(2026, 9,12),
#     schedule= "@daily" ) as dag:

URL = "https://api.themoviedb.org/3/movie/top_rated" #  mudar para variaveis do airflow
URL_generos= "https://api.themoviedb.org/3/genre/movie/list" #  mudar para variaveis do airflow
API_KEY = "66f326ea45d4f51ff3ed4071d5f20ad0" #  mudar para variaveis do airflow


def api_request(URL="", api_key="", n_pages=None): # requisição
    parametros = {
        "api_key": api_key,
        "language": "pt-BR",
    }
    if n_pages is not None:
        parametros["page"] = n_pages

    result = requests.get(url=URL, params=parametros)
    if (result.status_code == 200):
        dados = result.json()
        return dados
    else:
        print(f"ERROR: {result.status_code}" )


def extract_task_moves(URL,API_KEY, pages=0 ): # extração
    all_moves = []
    
    for page in range(1, pages+1):
        requisicao = api_request(URL, API_KEY , str(page))
        if(requisicao and "results" in requisicao):
            all_moves.extend(requisicao["results"])
    return all_moves

def extract_task_gener(API_KEY, URL): # extraçao 
    id_generos= api_request(URL, API_KEY) # para o modelo saber oq é cada id_gener de cada filme
    genres = []
    if(id_generos and "genres" in id_generos):
        genres.extend(id_generos["genres"])
    return genres




def transform_task(moves, geners):
    df_all_moves =  pd.DataFrame(moves)
    
    os.makedirs("data", exist_ok=True)
    df_all_moves = df_all_moves.sort_values(by="vote_average", ascending=False) # ordena pela quanntidade de aprovação do filme pelo piblico

    df_all_moves["age"] =  datetime.now().year - pd.to_datetime(df_all_moves["release_date"]).dt.year # pega a idade do filme e a quantos anos ele foi lançado feature

    mapa_generos = {g["id"]: g["name"] for g in geners} # feature

    for id_g, nome_g in mapa_generos.items(): # feature
        coluna = f"genero_{nome_g.lower().replace(' ', '_')}"
        df_all_moves[coluna] = df_all_moves["genre_ids"].apply(lambda ids: 1 if id_g in ids else 0)
        
    df_all_moves["num_genres"] = df_all_moves["genre_ids"].apply(len) # feature
    
    df_all_moves =  df_all_moves.drop(["release_date","genre_ids","backdrop_path","poster_path","softcore","video","adult","original_title"],axis=1) # remove featores desnecessarias para analise

    scaler = StandardScaler()
    colunas_para_normalizar = ["vote_count","popularity"]
    df_all_moves[colunas_para_normalizar] = scaler.fit_transform(df_all_moves[colunas_para_normalizar])
    # fazer a .fillna("") para remover 
    
    return df_all_moves

def load_df(df:pd.DataFrame, name_df="features"):
    df.to_csv(f"data/{name_df}.csv", index=False)
    return df



filmes = extract_task_moves(URL, API_KEY,5) # pega os 100 filmes
generos = extract_task_gener(API_KEY,URL_generos) # pega os generos acossiados a cada id

df=transform_task(filmes, generos)
load_df(df)