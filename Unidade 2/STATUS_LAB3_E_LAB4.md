# Relatório de Execução: Lab 3 (Concluído) e Preparação para o Lab 4

**Disciplina:** IMD3005 - Engenharia de Machine Learning (MLOps) · 2026.2  
**Docente:** Prof. Dr. Adelson de Araújo Silva Júnior  
**Discente:** Matheus Vinicius Silva Freire de Castro  
**Data:** 10/11/2026  

---

## 1. O que foi feito (Laboratório 3 — 100% Concluído)

O Laboratório 3 exigia a execução da API de classificação de intenções integrada com o Weights & Biases e MongoDB Atlas, validada localmente e via container Docker, entregando um único pacote compactado ou documento PDF com prints e código sem vazar variáveis de ambiente.

### 1.1 Consolidação dos Artefatos Obrigatórios
Todos os arquivos exigidos pelo roteiro foram organizados e validados no diretório [`Unidade 2/entrega_lab3/`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/entrega_lab3/):

1. **Print do Swagger UI (`POST /predictions` com 200 OK):**
   * Arquivo: [`print_swagger.png`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/entrega_lab3/print_swagger.png)
   * Evidência: Requisição interativa ao endpoint `/predictions` com o nome discente preenchido (*Matheus Vinicius Silva Freire de Castro*), status code HTTP `200` e payload de inferência gerado com sucesso.
2. **Código fonte de orquestração do endpoint:**
   * Arquivo: [`controller.py`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/entrega_lab3/controller.py)
   * Evidência: Implementação do endpoint FastAPI integrando `service.predict_all()`, Pydantic `Mensagem` e persistência na coleção `predictions` do MongoDB Atlas com remoção do `_id` BSON.
3. **Print dos Logs do Container Docker:**
   * Arquivo: [`print_logs.png`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/entrega_lab3/print_logs.png)
   * Evidência: Captura do terminal com `docker logs -f mlops-container` comprovando o método `POST /predictions` atendido com `200 OK`.

### 1.2 Relatórios Finais Gerados para Envio
Foram gerados e disponibilizados na pasta de entrega os formatos aceitos pela atividade:
* **Relatório Formal em PDF:**
  * [`lab_api_Matheus_Castro.pdf`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/entrega_lab3/lab_api_Matheus_Castro.pdf) (e versão com nome completo)
  * Documento de 4 páginas com capa institucional, arquitetura em camadas, prints integrados em alta resolução, transcrição integral do código em texto pesquisável (conforme exigência do roteiro), análise técnica e checklist de sigilo (ausência do `.env`).
* **Pacote Compactado ZIP:**
  * [`lab_api_Matheus_Castro.zip`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/entrega_lab3/lab_api_Matheus_Castro.zip)
  * Pacote limpo contendo unicamente os 3 arquivos essenciais (`controller.py`, `print_swagger.png`, `print_logs.png`), livre de segredos ou arquivos temporários.

---

## 2. Preparação Concluída para o Lab 4

Para deixar o projeto "no ponto" para o **Lab 4 (CD com GitHub Actions e Azure Container Apps)**, foram realizadas as etapas de preparação da Parte 1 no repositório da API em [`Unidade 2/mlops-2026-2/`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/mlops-2026-2/):

1. **Exposição de versão na rota raiz (`GET /`):**
   * Arquivo alterado: [`src/app.py`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/mlops-2026-2/src/app.py)
   * Modificação: Adicionado `import os` e retorno dinâmico:
     ```python
     @app.get('/')
     def root():
         return {'status': 'ok', 'version': os.getenv('APP_VERSION', 'dev')}
     ```
2. **Atualização da suíte de testes automatizados:**
   * [`tests/integration/test_api.py`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/mlops-2026-2/tests/integration/test_api.py): Ajustado teste unitário da rota `/` para verificar `{"status": "ok", "version": "dev"}`.
   * [`tests/e2e/test_smoke.py`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/mlops-2026-2/tests/e2e/test_smoke.py): Ajustado teste de fumaça e2e para ler `APP_VERSION` do ambiente.
3. **Validação do gatilho reutilizável de CI:**
   * Arquivo verificado: [`.github/workflows/ci.yml`](file:///home/alomyr/Projetos/UFRN-06/MLOPS/Unidade%202/mlops-2026-2/.github/workflows/ci.yml)
   * O gatilho `workflow_call:` já se encontra configurado no bloco `on:`, permitindo que o futuro `cd.yml` chame a suíte de testes antes do deploy.

---

## 3. O que precisa ser feito (Próximos Passos para o Lab 4)

O Lab 4 consiste em criar uma esteira de entrega contínua (CD) no GitHub Actions que compila a imagem Docker, envia ao GitHub Container Registry (GHCR) e faz deploy automatizado no Azure Container Apps com aprovação manual e suporte a rollback.

Abaixo estão os passos ordenados que iremos executar juntos:

### Passo 1: Definição e Publicação do Repositório da API no GitHub
- [ ] Definir o repositório remoto no GitHub do discente para a API:
  - Opção A (Recomendada): Criar um repositório dedicado na sua conta (ex: `https://github.com/Matheus-dCastro/intent-clf` ou `mlops-2026-2`).
  - Opção B: Utilizar uma branch ou a raiz do repositório `MLOPS`.
- [ ] Enviar o código da pasta `Unidade 2/mlops-2026-2` com as alterações da Parte 1 (`src/app.py`, testes e `ci.yml`) para o repositório remoto:
  ```bash
  git commit -m "GET / devolve version; ci.yml pode ser chamado"
  git push
  ```
- [ ] Garantir que o repositório seja **Público** (requisito para ativar o recurso de *Environments / Required Reviewers* no plano gratuito do GitHub).

### Passo 2: Configuração dos Segredos do CI no GitHub
Cadastrar em **Settings > Secrets and variables > Actions > New repository secret**:
- [ ] `WANDB_API_KEY`: Chave de API do Weights & Biases (`wandb_v1_...`).
- [ ] `WANDB_PROJECT`: Nome do projeto (geralmente `mlops-2026-2`).
- [ ] `WANDB_MODELS`: Identificador do modelo (`matheus-dcastro/mlops-2026-2/confusion-clf:v0`).
- [ ] `MONGO_URL`: String de conexão do cluster MongoDB Atlas.
- [ ] Acompanhar a aba **Actions** para certificar que o workflow `ci.yml` rode e fique **verde** nos jobs `test` e `smoke`.

### Passo 3: Publicação da Imagem Base no GHCR
- [ ] Gerar um Personal Access Token (Classic) no GitHub com o escopo `write:packages`.
- [ ] Fazer login no GHCR via Docker CLI e enviar a imagem inicial:
  ```bash
  echo SEU_TOKEN | docker login ghcr.io -u matheus-dcastro --password-stdin
  docker build --platform linux/amd64 -t ghcr.io/matheus-dcastro/intent-clf:latest .
  docker push ghcr.io/matheus-dcastro/intent-clf:latest
  ```
- [ ] Em **GitHub > Packages > Package settings**:
  - Alterar visibilidade para **Public**.
  - Em *Manage Actions access*, adicionar o repositório com permissão **Write**.

### Passo 4: Provisionamento da Infraestrutura na Nuvem (Azure)
- [ ] Instalar o Azure CLI (`az`) na máquina local ou utilizar o Cloud Shell.
- [ ] Autenticar com a conta institucional:
  ```bash
  az login
  ```
- [ ] Criar o Resource Group e o ambiente Container Apps:
  ```bash
  az group create --name mlops-2026-2 --location eastus
  az containerapp env create --name mlops-env --resource-group mlops-2026-2 --location eastus
  ```
- [ ] Criar a Identidade Gerenciada (`mlops-deployer`) e vincular a Role `Contributor` no Resource Group.
- [ ] Criar o Container App `intent-clf` com as credenciais do W&B e MongoDB injetadas via `--secrets` e variáveis de ambiente via `--env-vars`.
- [ ] Guardar a `Application Url` retornada pelo Azure.

### Passo 5: Configuração do OIDC e Ambiente de Produção no GitHub
- [ ] Configurar credencial federada no Azure para permitir que o GitHub Actions se autentique sem senhas estáticas (OIDC).
- [ ] Criar os Secrets no GitHub para o Azure:
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_SUBSCRIPTION_ID`
- [ ] Criar a Repository Variable:
  - `APP_URL`: URL da aplicação gerada pelo Azure Container Apps.
- [ ] Criar o Environment `production`:
  - Ativar **Required reviewers** e adicionar o seu usuário GitHub.

### Passo 6: Criação do Workflow de CD (`cd.yml`)
- [ ] Criar o arquivo `.github/workflows/cd.yml` contendo os 4 jobs:
  1. `ci`: Chama o `ci.yml` existente.
  2. `release`: Constrói e publica a imagem tagueada no GHCR.
  3. `deploy`: Realiza o deploy na revisão do Azure Container Apps (aguarda aprovação manual no environment `production`).
  4. `verify`: Executa validação ativa da URL conferindo se a versão esperada está no ar.

### Passo 7: Testes de Release e Rollback (Evidências para Entrega do Lab 4)
- [ ] Publicar a tag `v1.0.1`:
  ```bash
  git tag v1.0.1 && git push origin v1.0.1
  ```
  - Aprovar o deploy no GitHub Actions e tirar os prints necessários.
- [ ] Publicar a tag `v1.0.2`:
  ```bash
  git tag v1.0.2 && git push origin v1.0.2
  ```
  - Validar a atualização no ar.
- [ ] Testar o Rollback para `v1.0.1` via disparo manual (`Run workflow`) do `cd.yml`.
- [ ] Capturar todos os prints exigidos pelo roteiro do Lab 4 e compilar o PDF final.
- [ ] Apagar o Resource Group no Azure (`az group delete --name mlops-2026-2 --yes --no-wait`) para não consumir os créditos educacionais.
