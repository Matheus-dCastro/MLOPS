# Plano de Implementação: Reconstrução do Lab 3 e Execução do Lab 4

Este documento estabelece o roteiro completo, detalhado e passo a passo para:
1. **Configurar um repositório dedicado no GitHub** (`mlops-2026-2`) para isolar a API dos labs anteriores.
2. **Obter e configurar as credenciais necessárias** (Weights & Biases, Colab e MongoDB Atlas).
3. **Reconstruir todo o ambiente do Lab 3** (Docker, banco de dados e testes locais), reaproveitando o `controller.py` que já está pronto.
4. **Executar o Lab 4** (Continuous Deployment com GitHub Actions, GHCR e Azure Container Apps, incluindo tags de versão, gate de aprovação, teste de rollback e coleta de evidências para entrega).

---

## 1. Decisão de Arquitetura: Repositório Dedicado (`mlops-2026-2`)

Optamos por utilizar um repositório dedicado chamado `mlops-2026-2` no GitHub (em vez de reutilizar a raiz do repositório `MLOPS`), pelos seguintes motivos:
- **Separação de Contextos**: O repositório atual contém os códigos dos Labs 1 e 2 (Airflow, DAGs, etc.).
- **Compatibilidade com Docker e GitHub Actions**: O `Dockerfile` e os workflows (`.github/workflows/ci.yml` e `cd.yml`) operam obrigatoriamente na raiz do repositório.
- **Padrão dos Labs**: Todas as convenções do professor e referências no Azure, GHCR e W&B assumem o padrão `SEU-USUARIO/mlops-2026-2`.
- **Visibilidade**: O repositório deve ser **Público** para permitir revisores de ambiente gratuitos no GitHub Actions.

---

## 2. Preparação Prévia das Credenciais e Ambiente

Antes de subir a aplicação, você precisará coletar 3 credenciais e ativar o serviço Docker:

### 2.1. Iniciar o Docker Local
O serviço Docker do sistema precisa estar em execução:
```bash
sudo systemctl start docker
# Para testar:
docker ps
```

### 2.2. Chave de API do Weights & Biases (W&B)
1. Acesse: [https://wandb.ai/authorize](https://wandb.ai/authorize) (ou no perfil: *User Settings > API Keys*).
2. Copie a chave gerada (inicia com `wandb_v1_...`).

### 2.3. Treinar o Modelo no Google Colab
1. Abra o notebook `IntentClassifier` fornecido pelo professor e salve uma cópia no seu Google Drive.
2. Em **Secrets** (ícone de chave na barra lateral do Colab), crie `WANDB_KEY` com a chave do passo 2.2 e ative o acesso ao notebook.
3. Na aba **Arquivos** do Colab, faça upload do arquivo:
   `Unidade 2/API/confusion_examples.yml`
4. Execute as células em ordem: instalação, classe `IntentClassifier`, login no W&B e treinamento do modelo de confusão.
5. No W&B, abra o projeto `mlops-2026-2` > aba **Artifacts** > artefato `confusion-clf`.
   - Verifique se contém `model.keras` e `model_config.yml`.
   - Copie o identificador completo: `seu_usuario/mlops-2026-2/confusion-clf:v0`.

### 2.4. Banco no MongoDB Atlas
1. No [MongoDB Atlas](https://www.mongodb.com/cloud/atlas), crie um cluster gratuito M0.
2. Em **Database Access**, crie um usuário e senha (evite caracteres especiais).
3. Em **Network Access**, adicione o IP `0.0.0.0/0` (permite conexões do Docker local e do Azure).
4. Em **Connect > Drivers > Python**, copie a connection string e preencha a senha:
   ```text
   mongodb+srv://<usuario>:<senha>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

---

## 3. Visão Geral do Fluxo de Execução

```mermaid
flowchart TD
    Step1["1. Criar repo 'mlops-2026-2' no GitHub + subir código base com controller.py"] --> Step2
    Step2["2. Criar .env local e validar Lab 3 no Docker local (Swagger 200 OK)"] --> Step3
    Step3["3. Adicionar version em app.py e validar o CI verde no GitHub Actions"] --> Step4
    Step4["4. Gerar Token GHCR, fazer push manual e tornar pacote público"] --> Step5
    Step5["5. Criar Container App e Identidade Gerenciada com OIDC no Azure"] --> Step6
    Step6["6. Configurar Secrets, Variable APP_URL e Environment production no GitHub"] --> Step7
    Step7["7. Adicionar cd.yml, publicar tag v1.0.1 (com aprovação) e validar"] --> Step8
    Step8["8. Publicar tag v1.0.2, testar Rollback para v1.0.1 e coletar os prints para entrega"]
```

---

## 4. Roteiro Detalhado Passo a Passo

### FASE 1: Inicialização do Repositório e Reconstrução do Lab 3

#### Passo 1.1: Inicializar o Repositório Local e Conectar ao GitHub
- No GitHub, crie o repositório público vazio: `mlops-2026-2`.
- No ambiente de desenvolvimento, clonamos o repositório base da disciplina (`adaj/mlops-2026-2`), copiamos o [controller.py](file:///home/alomy/Projetos/UFRN_06/MLOPS/Unidade%202/API/controller.py) já pronto para `src/modules/intent_classifier/controller.py`, e apontamos a origem remota para o seu GitHub:
  ```bash
  git remote set-url origin https://github.com/Matheus-dCastro/mlops-2026-2.git
  git push -u origin main
  ```

#### Passo 1.2: Criar o arquivo `.env`
Na raiz da pasta da API, criar `.env` (ignorado pelo `.gitignore`):
```env
WANDB_API_KEY=wandb_v1_...
WANDB_PROJECT=mlops-2026-2
WANDB_MODELS=seu_usuario/mlops-2026-2/confusion-clf:v0
MONGO_URL=mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

#### Passo 1.3: Subir a API com Docker Compose
```bash
docker compose up --build
```
- Aguardar o log `Application startup complete.` (a API baixa o modelo do W&B na primeira inicialização).
- Abrir `http://localhost:8000/docs` no navegador.
- Executar `POST /predictions` com:
  ```json
  {
    "id": "lab-001",
    "nome": "Matheus Castro",
    "text": "eu não estou entendendo nada"
  }
  ```
- Validar o retorno com status **200 OK** contendo a predição.
- Confirmar nos logs do container (`docker logs -f mlops-container`) a linha `POST /predictions HTTP/1.1 200 OK`.

---

### FASE 2: Preparação da API para o Lab 4

#### Passo 2.1: Informar Versão no `src/app.py`
Adicionar `import os` e retornar `APP_VERSION`:
```python
import os

@app.get('/')
def root():
    return {'status': 'ok', 'version': os.getenv('APP_VERSION', 'dev')}
```

#### Passo 2.2: Garantir `workflow_call:` no `.github/workflows/ci.yml`
No bloco `on:` do `ci.yml`, certificar a linha:
```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
  workflow_call:
```
Fazer commit e push para a `main`. Conferir se o workflow de CI roda verde na aba **Actions** do GitHub.

---

### FASE 3: Configuração da Nuvem (GHCR & Azure Container Apps)

#### Passo 3.1: Publicar Imagem Inicial no GHCR
1. Gerar token clássico no GitHub (*Settings > Developer settings > Personal access tokens (classic)*) com o escopo `write:packages`.
2. Fazer build e push da imagem:
   ```bash
   echo SEU_TOKEN | docker login ghcr.io -u Matheus-dCastro --password-stdin
   docker build --platform linux/amd64 -t ghcr.io/matheus-dcastro/mlops-2026-2:latest .
   docker push ghcr.io/matheus-dcastro/mlops-2026-2:latest
   ```
3. No GitHub em **Packages**:
   - Abrir o pacote e alterar visibilidade para **Public**.
   - Em **Package settings > Manage Actions access**, adicionar o repositório `mlops-2026-2` com papel **Write**.
4. Criar a tag `v1.0.0`:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   docker tag ghcr.io/matheus-dcastro/mlops-2026-2:latest ghcr.io/matheus-dcastro/mlops-2026-2:v1.0.0
   docker push ghcr.io/matheus-dcastro/mlops-2026-2:v1.0.0
   ```

#### Passo 3.2: Criar o Container App no Azure
No Portal Azure:
- **Resource group**: `mlops-2026-2`
- **Container app name**: `intent-clf`
- **Container**:
  - Image source: *Docker Hub or other registries*
  - Image type: *Public*
  - Registry login server: `ghcr.io`
  - Image and tag: `matheus-dcastro/mlops-2026-2:v1.0.0`
- **CPU e Memória**: 2 vCPU, 4 GiB
- **Environment variables**:
  - `WANDB_PROJECT` = `mlops-2026-2` (Manual)
  - `WANDB_MODELS` = `seu_usuario/mlops-2026-2/confusion-clf:v0` (Manual)
  - `MONGO_DB` = `intent_classifier` (Manual)
  - `APP_VERSION` = `v1.0.0` (Manual)
  - `WANDB_API_KEY` (Secret)
  - `MONGO_URL` (Secret)
- **Ingress**: Enabled, Accepting traffic from anywhere, Target port: `8000`.
- **Startup probe**: TCP, porta 8000, Period: 10s, Failure threshold: 60.
- Obter a **Application Url** gerada (ex: `https://intent-clf.xxxxx.eastus.azurecontainerapps.io`).

#### Passo 3.3: Configurar Identidade Gerenciada e OIDC no Azure
1. Criar **Managed Identity**: `user-assigned-identity-1` no grupo `mlops-2026-2`.
2. Em **Azure role assignments**: Adicionar papel **Contributor** no escopo do Resource Group `mlops-2026-2`.
3. Em **Federated credentials > Add credential**:
   - Scenario: *GitHub Actions deploying Azure resources*
   - Organization: `Matheus-dCastro`
   - Repository: `mlops-2026-2`
   - Entity type: **Environment**
   - Name: `production`
4. Anotar: `Client ID`, `Tenant ID` e `Subscription ID`.

#### Passo 3.4: Configurar Secrets e Environment no GitHub
1. Em **Settings > Secrets and variables > Actions > Secrets**:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
   - `WANDB_API_KEY`, `WANDB_PROJECT`, `WANDB_MODELS`, `MONGO_URL` (para o CI smoke test)
2. Em **Variables**:
   - `APP_URL`: URL da aplicação no Azure com `https://` e sem barra no final.
3. Em **Environments**:
   - Criar `production`.
   - Habilitar **Required reviewers** e adicionar você mesmo.
   - Deployment branches and tags: *No restriction*.

---

### FASE 4: Pipeline de CD (`cd.yml`), Deploy e Rollback

#### Passo 4.1: Criar `.github/workflows/cd.yml`
Workflow com os 4 estágios:
- `ci`: valida testes unitários e smoke tests.
- `release`: constrói imagem e publica no GHCR com a tag da versão.
- `deploy`: atualiza o Azure Container App via OIDC (aguarda aprovação manual).
- `verify`: faz pooling HTTP via `curl` na URL pública até confirmar a versão e predição com sucesso.

#### Passo 4.2: Publicar Versão `v1.0.1`
```bash
git add .github/workflows/cd.yml
git commit -m "cd.yml"
git push
git tag v1.0.1
git push origin v1.0.1
```
- No GitHub Actions:
  - O job `deploy` ficará em estado amarelo (*Waiting*).
  - **Tirar print do deploy aguardando aprovação**.
  - Clicar em *Review deployments* > marcar *production* > *Approve and deploy*.
  - Aguardar o job `verify` terminar com `OK: v1.0.1 no ar`.
  - Acessar a URL no navegador e confirmar: `{"status":"ok","version":"v1.0.1"}`.

#### Passo 4.3: Publicar Versão `v1.0.2` e Testar Rollback para `v1.0.1`
1. Publicar `v1.0.2`:
   ```bash
   git tag v1.0.2
   git push origin v1.0.2
   ```
   Aprovar deploy e confirmar `"version":"v1.0.2"` no ar.
2. Executar Rollback:
   - Na aba **Actions** > selecionar workflow **CD** > clicar em **Run workflow**.
   - Branch: `main`, tag: `v1.0.1` > clicar em **Run workflow**.
   - Observar que `ci` e `release` ficam cinzas (pulados).
   - Aprovar o deploy em *production*.
   - Confirmar o log do `verify` com `OK: v1.0.1 no ar` e a URL respondendo `"version":"v1.0.1"`.

---

## 5. Checklist de Evidências para a Entrega do Lab 4

Para submissão final, é necessário gerar um documento PDF com os seguintes prints:
- [ ] Link do repositório público com `.github/workflows/cd.yml`.
- [ ] Print 1: Overview do Container App com Application Url e imagem com a tag.
- [ ] Print 2: Job `deploy` aguardando aprovação na versão `v1.0.1`.
- [ ] Print 3: Execução do run `v1.0.1` com `release`, `deploy` e `verify` verdes.
- [ ] Print 4: Log do job `verify` exibindo `OK: v1.0.1 no ar`.
- [ ] Print 5: Navegador exibindo `GET /` com `version: v1.0.2` e depois `version: v1.0.1` pós-rollback.
- [ ] Print 6: Execução do run de rollback com `ci` e `release` pulados.
- [ ] Print 7: Resource group `mlops-2026-2` apagado no portal Azure (para não consumir créditos).
