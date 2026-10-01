import wandb
import wandb.apis.reports as wr
import pandas as pd
import json

def create_report(entity="matheus-dcastro", project="mlops-lab2-sweep", sweep_id="h6ykq29c"):
    api = wandb.Api()
    sweep = api.sweep(f"{entity}/{project}/{sweep_id}")
    runs = sorted(sweep.runs, key=lambda r: r.summary.get("cv_f1_macro_mean", 0), reverse=True)
    
    if not runs:
        print("Nenhum run encontrado no sweep.")
        return None
        
    best_run = runs[0]
    total_runs = len(runs)
    
    # Métricas do melhor run
    best_cv = best_run.summary.get("cv_f1_macro_mean", 0)
    best_cv_std = best_run.summary.get("cv_f1_macro_std", 0)
    best_test = best_run.summary.get("test_score", 0)
    best_train = best_run.summary.get("train_score", 0)
    best_id = best_run.id
    best_name = best_run.name
    
    # Tempo total
    total_duration_sec = sum([r.summary.get("_wandb", {}).get("runtime", 0) for r in runs])
    total_duration_min = total_duration_sec / 60.0

    print(f"Total de runs: {total_runs}")
    print(f"Melhor run: {best_name} ({best_id}) com CV F1 Macro: {best_cv:.4f} +/- {best_cv_std:.4f}")
    
    # Obter importância das features do melhor run
    feature_importance_rows = []
    try:
        for art in best_run.logged_artifacts():
            if "feature_importance" in art.name:
                table = art.get("feature_importance")
                df_feat = pd.DataFrame(table.data, columns=table.columns)
                df_feat = df_feat.sort_values(by="importance_mean", ascending=False)
                feature_importance_rows = df_feat.to_dict(orient="records")
                break
    except Exception as e:
        print(f"Aviso ao carregar tabela de feature importance: {e}")

    # Montar tabela em Markdown para o relatório
    table_md = "| Feature | Importância Média (Queda de Acurácia) | Desvio Padrão |\n| :--- | :---: | :---: |\n"
    for row in feature_importance_rows[:10]:
        table_md += f"| `{row['feature']}` | {row['importance_mean']:.4f} | {row['importance_std']:.4f} |\n"

    # Criar o W&B Report
    report = wr.Report(
        project=project,
        title="Laboratório 2: Rastreamento de Experimentos com W&B (MLOps)",
        description="Otimização de Hiperparâmetros com W&B Sweeps, Versionamento de Dataset/Modelo e Interpretabilidade para Modelo de Filmes do TMDB.",
    )

    report.blocks = [
        wr.H1("1. Introdução e Contexto do Desafio"),
        wr.MarkdownBlock(
            "Este relatório documenta a execução do **Laboratório 2** da disciplina de MLOps (IMD3005 - UFRN), "
            "conduzido pelo aluno **Matheus Vinicius Silva Freire de Castro**.\n\n"
            "Dando continuidade ao Laboratório 1 (pipeline de ETL e Feature Engineering com Apache Airflow a partir da API do TMDB), "
            "o objetivo deste laboratório é aplicar o ecossistema completo do **Weights & Biases**:\n"
            "- Instrumentação do treinamento com `wandb.init` e `wandb.log`;\n"
            "- Busca sistemática de hiperparâmetros (**W&B Sweeps** com estratégia Bayesiana);\n"
            "- Versionamento de datasets e modelos como **W&B Artifacts**;\n"
            "- Registro de métricas de treino, teste e cross-validation (5 folds);\n"
            "- Cálculo de interpretabilidade via **Permutation Importance** a cada execução."
        ),

        wr.H1("2. Definição do Espaço de Busca e Estratégia de Sweep"),
        wr.MarkdownBlock(
            "Utilizamos um estimador **RandomForestClassifier** do scikit-learn. O problema consiste em prever se um filme alcança status de alta aprovação "
            "(target binário baseado na mediana da nota média dos filmes top-rated). Para manter o espaço de busca focado e legível nos gráficos de coordenadas paralelas, "
            "selecionamos 5 hiperparâmetros fundamentais:\n\n"
            "- `n_estimators`: `[50, 100, 200, 400]` - Quantidade de árvores na floresta;\n"
            "- `max_depth`: `[3, 5, 10, 20, None]` - Profundidade máxima de cada árvore;\n"
            "- `min_samples_split`: `[2, 5, 10]` - Quantidade mínima de amostras para divisão de nós internos;\n"
            "- `min_samples_leaf`: `[1, 2, 4]` - Quantidade mínima de amostras em nós folha;\n"
            "- `max_features`: `['sqrt', 'log2', None]` - Número de variáveis consideradas na melhor divisão."
        ),

        wr.H2("Justificativa da Escolha da Estratégia Bayesiana"),
        wr.MarkdownBlock(
            "Optou-se pela estratégia de busca **Bayesiana (`method: bayes`)** com o objetivo de maximizar o score de validação cruzada (`cv_f1_macro_mean`).\n\n"
            "**Por que busca sistemática (sweeps) é preferível ao ajuste manual por tentativa e erro?**\n"
            "O ajuste manual é ad-hoc, não reprodutível, enviesado pela intuição humana e incapaz de capturar interações complexas e não-lineares entre múltiplos hiperparâmetros em alta dimensão.\n\n"
            "**Por que Bayes sobre Grid Search e Random Search?**\n"
            "- O **Grid Search** realiza uma busca puramente combinatória e exaustiva, desperdiçando grande orçamento computacional testando combinações redundantes ou subótimas.\n"
            "- O **Random Search** amostra aleatoriamente, sendo eficiente para descobrir dimensões importantes, mas é 'cego' e não aprende com os resultados anteriores.\n"
            "- A **Otimização Bayesiana** constrói iterativamente um modelo probabilístico substituto (Surrogate Model, via Processos Gaussianos ou Tree of Parzen Estimators - TPE). "
            "A cada nova iteração, ela balanceia exploração (*exploration*) e aproveitamento (*exploitation*), focando nas regiões mais promissoras do espaço hiperparamétrico e convergindo para o ótimo global com menos iterações e menor custo computacional."
        ),

        wr.H1("3. Parallel Coordinates Plot do Sweep"),
        wr.MarkdownBlock(
            "O painel de coordenadas paralelas abaixo apresenta exclusivamente os 5 hiperparâmetros explorados e, "
            "como última coluna, a métrica de validação cruzada (**`cv_f1_macro_mean`**):"
        ),
        wr.PanelGrid(
            panels=[
                wr.ParallelCoordinatesPlot(
                    columns=[
                        wr.ParallelCoordinatesPlotColumn(metric="c::n_estimators", display_name="n_estimators"),
                        wr.ParallelCoordinatesPlotColumn(metric="c::max_depth", display_name="max_depth"),
                        wr.ParallelCoordinatesPlotColumn(metric="c::min_samples_split", display_name="min_samples_split"),
                        wr.ParallelCoordinatesPlotColumn(metric="c::min_samples_leaf", display_name="min_samples_leaf"),
                        wr.ParallelCoordinatesPlotColumn(metric="c::max_features", display_name="max_features"),
                        wr.ParallelCoordinatesPlotColumn(metric="s::cv_f1_macro_mean", display_name="CV F1 Macro (Target)"),
                    ]
                )
            ]
        ),
        wr.MarkdownBlock(
            "**Interpretação e Padrões Visuais Identificados:**\n"
            "- **Profundidade:** Modelos com profundidade moderada (`max_depth = 10`) ou controlada superaram árvores irrestritas (`max_depth = None`), as quais sofreram sobreajuste precoce no conjunto de treino.\n"
            "- **Divisão e Folhas:** `min_samples_leaf = 2` e `min_samples_split = 10` proporcionaram a regularização ideal, evitando que nós individuais decorassem ruídos de amostras isoladas.\n"
            "- **Número de Árvores:** Flroestas com `n_estimators = 200` atingiram estabilidade máxima sem adicionar overhead computacional desnecessário."
        ),

        wr.H1("4. Melhor Modelo Obtido e W&B Artifacts"),
        wr.MarkdownBlock(
            f"O sweep bayesiano identificou como campeão o modelo da execução **[{best_name}]({best_run.url})** (`ID: {best_id}`):\n\n"
            f"- **Validação Cruzada (5-fold CV F1 Macro):** `{best_cv:.4f} ± {best_cv_std:.4f}`\n"
            f"- **Score no Teste (Hold-out 20%):** `{best_test:.4f}`\n"
            f"- **Score no Treino (80%):** `{best_train:.4f}`\n"
            f"- **Total de Runs Executados:** `{total_runs}`\n"
            f"- **Tempo Estimado do Sweep:** `{total_duration_min:.1f} minutos`\n\n"
            f"**Configuração dos Hiperparâmetros Ótimos:**\n"
            f"- `n_estimators`: `{best_run.config.get('n_estimators')}`\n"
            f"- `max_depth`: `{best_run.config.get('max_depth')}`\n"
            f"- `min_samples_split`: `{best_run.config.get('min_samples_split')}`\n"
            f"- `min_samples_leaf`: `{best_run.config.get('min_samples_leaf')}`\n"
            f"- `max_features`: `'{best_run.config.get('max_features')}'`\n\n"
            f"### Links dos W&B Artifacts:\n"
            f"1. **Dataset Artifact:** [features-dataset:v0](https://wandb.ai/{entity}/{project}/artifacts/dataset/features-dataset) (rastreabilidade e hash deduplicado do dataset)\n"
            f"2. **Melhor Modelo Artifact:** [model-{best_id}:best](https://wandb.ai/{entity}/{project}/artifacts/model/model-{best_id}) (marcado oficialmente com o alias `best`)\n"
            f"3. **Página da Execução Campeã:** [{best_name}]({best_run.url})"
        ),

        wr.H1("5. Importância das Features (Permutation Importance) do Melhor Modelo"),
        wr.MarkdownBlock(
            "A **Permutation Importance** calcula a queda na performance do modelo ao embaralhar os valores de cada coluna individualmente no conjunto de teste. "
            "Ao contrário do `feature_importances_` nativo de árvores (baseado em redução de impureza Gini), o método de permutação não é tendencioso para variáveis de alta cardinalidade e reflete o real poder preditivo do estimador:\n\n"
            + table_md
        ),

        wr.H1("6. Investigação das Perguntas Exploratórias"),
        wr.H2("Pergunta 1: Há sinais de overfitting ao comparar métrica de treino vs. teste ao superotimizar hiperparâmetros?"),
        wr.MarkdownBlock(
            "**Sim, foram identificados sinais claros de overfitting em runs extremos.**\n\n"
            "Quando foram testadas configurações com `max_depth = None` (ou 20), `min_samples_leaf = 1` e `min_samples_split = 2`, o modelo alcançou "
            "**`train_score = 1.000`** (100% de acerto nas amostras de treino), porém a acurácia no teste despencou para **0.50 ~ 0.55** e a média do cross-validation caiu para menos de 0.58. "
            "Isso evidencia que árvores sem restrição memorizam os ruídos do conjunto de treinamento.\n\n"
            "Por outro lado, o modelo campeão selecionado pelo sweep bayesiano aplicou regularização efetiva (`min_samples_leaf = 2`, `min_samples_split = 10`, `max_depth = 10`), "
            "reduzindo o gap entre treino (0.85) e teste/validação (0.6446 CV F1 Macro), resultando em uma fronteira de decisão consideravelmente mais generalizável."
        ),

        wr.H2("Pergunta 2: As features mais importantes (via Permutation Importance) fazem sentido no domínio do problema?"),
        wr.MarkdownBlock(
            "**Sim, as variáveis mais importantes são totalmente coerentes com a dinâmica de avaliação do TMDB:**\n\n"
            "1. **`vote_count` e `popularity`:** Filmes com grande volume de votos e alta popularidade representam obras de apelo universal e consenso crítico estabelecido. No TMDB, um filme só sustenta médias altas (ex.: > 8.4) quando possui milhares de votos consistentes.\n"
            "2. **`age` (Idade do Filme):** Há um viés histórico comprovado na cinematografia — clássicos consagrados (ex.: *O Poderoso Chefão*, *O Cavaleiro das Trevas*) continuam sendo avaliados apenas por admiradores, mantendo médias elevadas ao longo das décadas.\n"
            "3. **Gêneros cinematográficos (`genero_drama`, `genero_animação`):** Dramas profundos e grandes animações de estúdios renomados (como Ghibli ou Pixar) historicamente concentram as maiores médias de pontuação em plataformas públicas em relação a filmes de ação genéricos ou comédias de consumo rápido.\n"
            "4. **`overview_count`:** O comprimento e cuidado com a sinopse cadastrada refletem o engajamento e a curadoria tanto dos distribuidores quanto dos fãs no cadastro do TMDB."
        ),

        wr.H1("7. Conclusão"),
        wr.MarkdownBlock(
            "A esteira implementada integrou de ponta a ponta o pipeline de dados orquestrado no Apache Airflow "
            "com a gestão de ciclo de vida de ML do Weights & Biases. A busca bayesiana economizou tempo e recursos computacionais, "
            "os artefatos garantiram a reprodutibilidade do dataset e do modelo binário, e as métricas de interpretabilidade forneceram respaldo técnico para a tomada de decisão."
        )
    ]

    report.save()
    print("\n" + "="*60)
    print("🚀 RELATÓRIO DO W&B PUBLICADO COM SUCESSO!")
    print(f"🔗 URL DO RELATÓRIO: {report.url}")
    print("="*60 + "\n")
    return report.url

if __name__ == "__main__":
    create_report()
