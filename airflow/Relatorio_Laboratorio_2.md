# Laboratório 2: Rastreamento de Experimentos de ML com Weights & Biases
**Disciplina:** IMD3005 - MLOPS (UFRN)  
**Aluno:** Matheus Vinicius Silva Freire de Castro  
**Professor:** Prof. Adelson de Araújo  
**Repositório:** [https://github.com/Matheus-dCastro/MLOPS](https://github.com/Matheus-dCastro/MLOPS)  
**Link do W&B Report Oficial:** [https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/reports/Laboratório-2:-Rastreamento-de-Experimentos-com-W&B-(MLOps)--VmlldzoxODA0MDAzNg==](https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/reports/Laborat%C3%B3rio-2:-Rastreamento-de-Experimentos-com-W&B-(MLOps)--VmlldzoxODA0MDAzNg==)

---

## 1. Visão Geral da Atividade

Dando continuidade ao **Laboratório 1** (onde implementamos a extração e transformação de dados da API do The Movie Database - TMDB via Apache Airflow), este laboratório tem como objetivo treinar um modelo de Machine Learning (`RandomForestClassifier`) sobre as features construídas, aplicando o ecossistema completo do **Weights & Biases (W&B)**:
1. **Instrumentação de código**: Logging sistemático de hiperparâmetros, métricas (`train_score`, `test_score`, `cv_f1_macro_mean`, `cv_f1_macro_std`) e tabelas de interpretabilidade;
2. **W&B Sweeps**: Otimização sistemática de hiperparâmetros via **Busca Bayesiana (`method: bayes`)**;
3. **W&B Artifacts**: Versionamento seguro com hash deduplicado do dataset (`features-dataset`) e dos modelos treinados (`model-{run.id}`), identificando o melhor com a tag/alias `best`;
4. **Interpretabilidade**: Avaliação de relevância das variáveis preditoras via **Permutation Importance**;
5. **W&B Report**: Relatório dinâmico com painéis ao vivo (*Parallel Coordinates Plot* e *Feature Importance*), links dos artefatos e análise crítica do problema.

---

## 2. Dataset e Formulação do Problema de Machine Learning

- **Fonte dos Dados:** Pipeline do Airflow (`airflow/dag_feature_engineering.py`), gerando o arquivo `features.csv`.
- **Target Definido:** Problema de classificação binária (`target`), indicando se o filme possui avaliação de excelência dentro do catálogo top-rated (`1` para `vote_average >= 8.4` e `0` caso contrário).
- **Features Preditivas Utilizadas (24 variáveis):**
  - Métricas de engajamento: `popularity`, `vote_count`, `overview_count` (tamanho da sinopse);
  - Temporais e estruturais: `age` (idade do filme), `num_genres` (quantidade de gêneros);
  - Indicadores de gênero (One-Hot Encoded): `genero_ação`, `genero_aventura`, `genero_animação`, `genero_drama`, `genero_comédia`, `genero_crime`, etc.
  - Colunas de texto bruto e identificadores (`id`, `title`, `overview`, `original_language`) e a nota original (`vote_average`) foram removidas do conjunto de treino para evitar vazamento de dados (*data leakage*).

---

## 3. Espaço de Busca e Estratégia de Sweep

### 3.1 Hiperparâmetros Configurados no `sweep.yaml`:
- `n_estimators`: `[50, 100, 200, 400]`
- `max_depth`: `[3, 5, 10, 20, null]`
- `min_samples_split`: `[2, 5, 10]`
- `min_samples_leaf`: `[1, 2, 4]`
- `max_features`: `["sqrt", "log2", null]`

### 3.2 Justificativa da Escolha da Estratégia de Busca (Bayes)
- **Por que busca sistemática sobre ajuste manual por tentativa e erro?**  
  O ajuste manual consome tempo excessivo do engenheiro de ML, não garante convergência, é propenso a vieses cognitivos e não consegue navegar eficientemente em espaços combinatórios multidimensionais não-lineares.
- **Por que Otimização Bayesiana sobre Grid Search e Random Search?**  
  - O **Grid Search** avalia exaustivamente todas as combinações de uma grade fixa, desperdiçando tempo de computação em regiões pouco informativas e com custo exponencial.
  - O **Random Search** é melhor que o Grid para dimensões contínuas, mas é desprovido de memória, tratando cada tentativa de forma isolada.
  - A **Otimização Bayesiana (`method: bayes`)** cria um modelo probabilístico substituto (Surrogate Model) que mapeia hiperparâmetros à métrica objetivo (`cv_f1_macro_mean`). Ela equilibra inteligentemente a exploração de áreas incertas (*exploration*) com a intensificação nas áreas de melhor performance (*exploitation*), descobrindo os melhores hiperparâmetros com significativamente menos iterações e menor custo computacional.

---

## 4. Resultados do Sweep e Melhor Modelo Encontrado

Foram executados **27 runs** no sweep `h6ykq29c`.

### 🏆 Melhor Modelo (Campeão):
- **Nome do Run:** `giddy-sweep-3`
- **ID da Execução:** `ea7rojuz`
- **Métricas:**
  - **Validação Cruzada (5-fold CV F1 Macro):** **0.6446 ± 0.0673**
  - **Acurácia no Conjunto de Teste (Hold-out 20%):** **0.6000**
  - **Acurácia no Conjunto de Treino (80%):** **0.8500**
- **Hiperparâmetros Ótimos:**
  - `n_estimators`: **200**
  - `max_depth`: **10**
  - `min_samples_split`: **10**
  - `min_samples_leaf`: **2**
  - `max_features`: **sqrt**
- **Artifact Registrado:** `model-ea7rojuz` marcado com o alias **`best`**.

---

## 5. Investigação das Perguntas Exploratórias

### Pergunta 1: Há sinais de overfitting ao comparar métrica de treino vs. teste ao superotimizar hiperparâmetros?
**Sim.** Durante o sweep, configurações com alta capacidade e baixa regularização (`max_depth = None` ou `20`, `min_samples_leaf = 1`, `min_samples_split = 2`) obtiveram acurácia de treino perfeita de `1.000` (100% de acerto), enquanto seu desempenho em dados de teste despencou para `0.50` a `0.55`, com degradação do cross-validation.  
Em contraste, o modelo vencedor utilizou restrições regulatórias (`min_samples_leaf = 2`, `min_samples_split = 10`, `max_depth = 10`), alcançando `0.85` no treino e sustentando a maior média de generalização em validação cruzada (`0.6446`), demonstrando robustez contra overfitting.

### Pergunta 2: As features mais importantes (via Permutation Importance) fazem sentido no domínio do problema?
**Sim.** O ranqueamento das variáveis via Permutation Importance no conjunto de teste revelou que:
1. **`vote_count` e `popularity`:** São os maiores preditores. Filmes com grande volume de avaliações consolidam sua reputação pública no TMDB; notas extremas em amostras pequenas costumam regredir à média.
2. **`age` (Idade da Obra):** Filmes consagrados de décadas anteriores sustentam notas altas de forma resiliente, beneficiando-se do viés de sobrevivência (*apenas os verdadeiros clássicos continuam sendo ativamente revistos e bem avaliados*).
3. **Gêneros como `genero_drama` e `genero_animação`:** Produções dramáticas de prestígio e animações clássicas recebem notas sistematicamente mais altas da crítica e do público do que produções casuais de entretenimento.
4. **`overview_count`:** A extensão e riqueza da sinopse cadastrada refletem o esmero descritivo e a relevância atribuída à obra pela comunidade.

---

## 6. Links Oficiais para Avaliação

- 📑 **W&B Report Dinâmico:**  
  [https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/reports/Laboratório-2:-Rastreamento-de-Experimentos-com-W&B-(MLOps)--VmlldzoxODA0MDAzNg==](https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/reports/Laborat%C3%B3rio-2:-Rastreamento-de-Experimentos-com-W&B-(MLOps)--VmlldzoxODA0MDAzNg==)
- 🧹 **Página do Sweep (Parallel Coordinates e Runs):**  
  [https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/sweeps/h6ykq29c](https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/sweeps/h6ykq29c)
- 📦 **W&B Artifact do Dataset:**  
  [https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/artifacts/dataset/features-dataset](https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/artifacts/dataset/features-dataset)
- 🤖 **W&B Artifact do Melhor Modelo (`best`):**  
  [https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/artifacts/model/model-ea7rojuz](https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/artifacts/model/model-ea7rojuz)
- 🚀 **Página da Execução Campeã (`giddy-sweep-3`):**  
  [https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/runs/ea7rojuz](https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/runs/ea7rojuz)
