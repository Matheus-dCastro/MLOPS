### 🔗 Links Oficiais Gerados no Weights & Biases

  • 📑 W&B Report Oficial do Laboratório 2 https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/reports/Laborat%C3%B3rio-2:-
  Rastreamento-de-Experimentos-com-W&B-(MLOps)--VmlldzoxODA0MDAzNg== (Entregável principal da atividade)
  • 🧹 Página do Sweep (Parallel Coordinates e Runs) https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/sweeps/h6ykq29c
  • 🏆 Página da Execução Campeã (giddy-sweep-3 / ea7rojuz) https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/runs/ea7rojuz
  • 📦 W&B Artifact do Dataset (features-dataset) https://wandb.ai/matheus-dcastro/mlops-lab2-
  sweep/artifacts/dataset/features-dataset
  • 🤖 W&B Artifact do Melhor Modelo com alias best https://wandb.ai/matheus-dcastro/mlops-lab2-sweep/artifacts/model/model-
  ea7rojuz
  ──────
  ## 📖 Passo a Passo: Como Reproduzir e Visualizar Tudo "na Mão"
  Aqui está o guia prático para você entender o fluxo de trabalho e ver tudo acontecendo ao vivo na interface do Weights &
  Biases:

  ### Passo 1: Como rodar um treinamento e acompanhar ao vivo no Dashboard
  1. No seu terminal, ative o ambiente virtual:
    source airflow/.venv/bin/activate
  2. Se quiser disparar um run avulso de teste:
    python train.py

  3. Se quiser disparar novos agentes no seu Sweep ativo para vê-los treinando ao vivo:
    wandb agent matheus-dcastro/mlops-lab2-sweep/h6ykq29c --count 2
  4. Onde ver na tela:
      • Abra o projeto no navegador: https://wandb.ai/matheus-dcastro/mlops-lab2-sweep.
      • Você verá o run com status verde piscando (Running).
      • Conforme o modelo treina, as métricas cv_f1_macro_mean, test_score, train_score e a tabela feature_importance aparecem
      em tempo real na tela.

  ──────
  ### Passo 2: Como visualizar e configurar o Parallel Coordinates Plot
  1. No menu lateral esquerdo do projeto no W&B, clique no ícone Sweeps (ícone de vassoura 🧹).
  2. Clique no sweep ativo: h6ykq29c.
  3. Na tela principal você verá o gráfico Parallel Coordinates Plot.
  4. Como editar para atender à regra do professor (apenas hiperparâmetros + métrica no final):
      • Passe o mouse sobre o canto superior direito do gráfico de coordenadas paralelas e clique no ícone de lápis (Edit).
      • Remova colunas automáticas desnecessárias (como epoch, _runtime, etc.).
      • Deixe estritamente as colunas dos hiperparâmetros na ordem:
          1. n_estimators
          2. max_depth
          3. min_samples_split
          4. min_samples_leaf
          5. max_features
          6. Última coluna: cv_f1_macro_mean (a métrica de performance).
      • Dica de análise: Você pode clicar e arrastar o cursor do mouse verticalmente sobre a coluna cv_f1_macro_mean para
      selecionar apenas as linhas com notas altas. As linhas coloridas destacarão exatamente quais faixas de hiperparâmetros
      geraram esses melhores resultados!
  ──────
  ### Passo 3: Como inspecionar e gerenciar os Artifacts (Dataset e Modelo)

  1. No menu lateral esquerdo do W&B, clique em Artifacts (ícone de caixas 📦).
  2. Dataset:
      • Clique em features-dataset.
      • Na aba Overview e Files, você verá o features.csv com hash de verificação de integridade (o W&B deduplica se o
      conteúdo for idêntico).
  3. Modelos:
      • Clique em model-ea7rojuz (ou no modelo com maior F1).
      • Observe que ele já possui a tag/badge best que adicionamos automaticamente via script.
      • Se precisar adicionar ou alterar um alias manualmente em qualquer run:
          1. Clique no artifact desejado;
          2. No painel direito de metadados, localize a seção Aliases;
          3. Clique no botão +, digite best e pressione Enter.
  ──────
  ### Passo 4: Como abrir e editar o W&B Report
  1. No menu lateral esquerdo, clique em Reports (ícone de documento 📑).
  2. Abra o relatório: Laboratório 2: Rastreamento de Experimentos com W&B (MLOps).
  3. O relatório já contém:
      • Justificativa da estratégia bayesiana contra busca manual, grid e random search;
      • O Parallel Coordinates Plot incorporado como painel vivo (não estático);
      • As métricas do modelo campeão (giddy-sweep-3: CV F1 Macro de 0.6446, Acurácia no Teste de 0.60, Acurácia no Treino de
      0.85);
      • A tabela de Permutation Importance;
      • Links diretos para os artefatos;
      • Respostas completas para as duas perguntas exploratórias requeridas pelo professor.
  4. Caso queira editar o texto ou a diagramação, basta clicar no botão Edit no canto superior direito do relatório, fazer os
  ajustes e clicar em Save.
  ──────
  ### Passo 5: Arquivos Prontos no seu Repositório

  • train.py: Script de treino instrumentado com wandb.init, wandb.log, cross-validation 5 folds, permutation_importance e log
  de artefatos.
  • sweep.yaml: Arquivo de configuração do sweep bayesiano e limites dos 5 hiperparâmetros.
  • dag_feature_engineering.py: DAG atualizada que gera a feature de target binário para o modelo de ML.
  • generate_report.py: Script que consulta a API do W&B e constrói o relatório com painéis vivos.
  • process_sweep_results.py: Script que analisa os runs e adiciona o alias best ao artifact campeão.
  • Relatorio_Laboratorio_2.md: Cópia local em Markdown com todo o conteúdo textual e respostas do relatório.
  • .gitignore: Atualizado para manter o repositório limpo, ignorando artefatos pesados, pastas do wandb e caches.
