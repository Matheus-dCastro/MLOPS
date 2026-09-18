from airflow import DAG
from airflow.decorators import task
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.models import Variable
import requests

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

from datetime import datetime
import os
    

# este era o arquivo q eu estava usando para testar como o construia o projeto junto do uso da daq, 

URL = Variable.get("URL", "https://api.themoviedb.org/3/movie/top_rated")
URL_GEN= Variable.get("URL_GEN", "https://api.themoviedb.org/3/genre/movie/list")
API_KEY = Variable.get("KEY", "66f326ea45d4f51ff3ed4071d5f20ad0") 
pagues = int(Variable.get("pagues", 5))


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
        

@task   
def extract_task_moves(URL,API_KEY, pages=0 ): # extração
    all_moves = []
    
    for page in range(1, pages+1):
        requisicao = api_request(URL, API_KEY , str(page))
        if(requisicao and "results" in requisicao):
            all_moves.extend(requisicao["results"])
    return all_moves


@task   
def extract_task_gener(API_KEY, URL): # extraçao 
    id_generos= api_request(URL, API_KEY) # para o modelo saber oq é cada id_gener de cada filme
    genres = []
    if(id_generos and "genres" in id_generos):
        genres.extend(id_generos["genres"])
    return genres



@task   
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
    # Substitui strings vazias por NaN e depois aplica o fillna

    df_all_moves["overview_count"] = df_all_moves["overview"].fillna("").astype(str).str.strip().apply(len)
    
    df_all_moves["overview"] = df_all_moves["overview"].replace("", np.nan).fillna("")
    
    return df_all_moves

@task   
def load_df(df:pd.DataFrame, name_df="features"):
    df.to_csv(f"data/{name_df}.csv", index=False)
    return df


with DAG(
        dag_id="dag_feature_engineering",
        start_date=datetime(2026, 9, 17),
        schedule="@daily",
        catchup=False
    ) as dag:
    filmes = extract_task_moves(URL, API_KEY, pagues) 
    generos = extract_task_gener(API_KEY, URL_GEN)
    df = transform_task(filmes, generos)
    load_df(df)
