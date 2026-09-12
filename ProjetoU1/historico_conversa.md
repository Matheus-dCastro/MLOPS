# 📚 Registro de Mentoria e Histórico de Desenvolvimento - MLOps (UFRN)

**Data:** 12 de Setembro de 2026  
**Disciplina:** MLOps (IMD3005 - UFRN)  
**Projeto:** Projeto 01 - Pipeline ETL & Feature Engineering (TMDB API & Apache Airflow)  
**Dinâmica:** Mentoria / Tutoria (o mentor orienta, desafia, revisa e analisa; o aluno implementa o código).

---

## 🎯 1. Prompts Iniciais Utilizados

### Prompt de Definição da Dinâmica de Mentoria (Início do Projeto):
> *"preciso q vc atue como meu mentor/tutor ou seja vc n deve implentar codigo, preciso q vc me ajude a fazrer o conusmo da TMDB api via json para um projeto da disciplica de mlops com isso quero q vc me ajude a montar o pepiline e passar a ela para ser usado no airflow..."*

### Prompt de Retomada Desta Sessão:
> *"relemebre de nossa ultima conversa haja da mesma maneira novamente, e me relembre quais features alem da idade eu falei q iriamos criar para o modelo analisar"*

---

## 🧭 2. Recapitulação das Features Planejadas

O objetivo do modelo é prever a avaliação (`vote_average`) de filmes futuros. As 4 técnicas de Feature Engineering planejadas foram:

1. **Extração Temporal:** Cálculo da idade do filme (`age`) baseada na data de lançamento (`release_date`).
2. **Codificação Categórica (Gêneros):** Mapeamento via dicionário dos `genre_ids` e expansão em colunas binárias (*Multi-Hot Encoding*) + contagem `num_genres`.
3. **Transformação Numérica:** Padronização / escalonamento de `vote_count` e `popularity` via `StandardScaler`.
4. **Processamento de Linguagem Natural / Texto:** Tratamento e extração de métricas da sinopse (`overview`) como contagem de palavras e caracteres.

---

## 🛠️ 3. Linha do Tempo e Evolução dos Desafios Técnicos

### 3.1. Resolução do Erro de Tipo na Idade (`age`)
* **Problema:** A linha `datetime.now() - df["release_date"]` gerava `TypeError`, pois a coluna vinha como `str`.
* **Solução Implementada pelo Aluno:** Conversão com `pd.to_datetime` e extração dos anos:
  ```python
  df_all_moves["age"] = datetime.now().year - pd.to_datetime(df_all_moves["release_date"]).dt.year
  ```

### 3.2. Mapeamento de Gêneros via API TMDB
* **Dúvida:** Como saber o que cada ID de gênero significa?
* **Solução:** Uso do endpoint oficial `https://api.themoviedb.org/3/genre/movie/list` com `language=pt-BR`.

### 3.3. Depuração do Erro 400 (Bad Request)
* **Problema:** Ao testar a requisição de gêneros, a API retornou erro 400 (`Invalid page: Pages start at 1...`).
* **Causa:** `n_pages="0"` foi enviado na query string; o endpoint de gêneros não é paginado e o TMDB não aceita página zero.
* **Solução:** Refatoração de `api_request` para tornar `n_pages=None` opcional e só adicionar o parâmetro quando informado.

### 3.4. Arquitetura de MLOps: Gêneros no DataFrame vs Variável Externa
* **Decisão Arquitetural:** Em vez de deixar uma variável solta para o modelo consultar, os gêneros foram incorporados diretamente no DataFrame dentro da `transform_task`.
* **Estrutura Airflow (Opção A):** Criação de duas tarefas de extração independentes que podem rodar em paralelo:
  * `extract_task_moves(URL, pages)`
  * `extract_task_gener()`
* **Multi-Hot Encoding:** Criação de colunas binárias (`0` ou `1`) para cada um dos 19 gêneros e criação da feature `num_genres`.

### 3.5. Padronização Numérica com `StandardScaler`
* **Problema Inicial:** Chamada de `.transform()` antes de `.fit()` gerava `NotFittedError`, e passar Series 1D causava erro de dimensionalidade.
* **Solução Implementada com Maestria:**
  * Uso de `scaler = StandardScaler()` dentro de `transform_task`.
  * Escalonamento conjunto de `vote_count` e `popularity` passando DataFrame 2D:
    ```python
    colunas_para_normalizar = ["vote_count", "popularity"]
    df_all_moves[colunas_para_normalizar] = scaler.fit_transform(df_all_moves[colunas_para_normalizar])
    ```
* **Limpeza:** Remoção de `release_date`, `genre_ids`, `backdrop_path`, `poster_path`, `softcore`, `video`, `adult` e `original_title`.

---

## 📊 4. Estado Atual do Dataset Gerado (`data/df_moves.csv`)

O pipeline executou com sucesso e gerou o arquivo com **28 colunas** limpas e estruturadas:
* Identificadores e Textos: `id`, `title`, `original_language`, `overview`
* Features Numéricas Contínuas Padronizadas: `popularity`, `vote_count`
* Variável Alvo (Target): `vote_average`
* Feature Temporal: `age`
* Features Categóricas (Multi-Hot 0/1): `genero_ação`, `genero_aventura`, `genero_animação`, `genero_comédia`, `genero_crime`, `genero_documentário`, `genero_drama`, `genero_família`, `genero_fantasia`, `genero_história`, `genero_terror`, `genero_música`, `genero_mistério`, `genero_romance`, `genero_ficção_científica`, `genero_cinema_tv`, `genero_thriller`, `genero_guerra`, `genero_faroeste`
* Feature de Complexidade: `num_genres`

---

## 🚀 5. Próximos Passos

1. **Processamento da Sinopse (`overview`):**
   * Preenchimento de valores nulos com `.fillna("")`.
   * Criação de `overview_word_count` e `overview_char_count`.
2. **Criação da Tarefa de Carga (`load_task`):**
   * Modularizar o salvamento do CSV em uma função dedicada (`load_task(df, caminho)`).
3. **Orquestração com Apache Airflow:**
   * Ativar a DAG conectando as tarefas: `extract_moves` + `extract_gener` ➔ `transform` ➔ `load`.
