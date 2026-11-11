# Guia de Execução Passo a Passo — Lab 4: CD com GitHub Actions e Azure Container Apps

**Disciplina:** IMD3005 - Engenharia de Machine Learning (MLOps) · 2026.2  
**Discente:** Matheus Vinicius Silva Freire de Castro  
**Repositório Base:** `Unidade 2/mlops-2026-2/`  

---

## 0. Estado do Ambiente (Já Preparado)

* [x] **Docker**: Instalado e operacional (`Docker version 29.9.0`).
* [x] **Azure CLI (`az`)**: Instalado e configurado no PATH (`azure-cli 2.92.0`).
* [x] **Código da API ajustado (Parte 1)**:
  * `src/app.py` expondo `APP_VERSION` no endpoint `GET /`.
  * `tests/integration/test_api.py` e `tests/e2e/test_smoke.py` atualizados para validar a versão.
  * `.github/workflows/ci.yml` pronto com o gatilho `workflow_call:`.

---

## Passo 1: Publicar o Repositório no GitHub

Entre na pasta do projeto:
```bash
cd "/home/alomyr/Projetos/UFRN-06/MLOPS/Unidade 2/mlops-2026-2"
```

1. Crie um repositório no seu GitHub chamado `intent-clf` (ou `mlops-2026-2`), configurado como **Public** (necessário para *Required reviewers* no plano gratuito).
2. Configure aponte a branch e envie o código:
```bash
git add src/app.py tests/ .github/workflows/ci.yml
git commit -m "GET / devolve version; ci.yml pode ser chamado"
git remote set-url origin https://github.com/Matheus-dCastro/intent-clf.git
git push -u origin main
```

---

## Passo 2: Cadastrar Segredos do W&B e Mongo no GitHub

No seu repositório no GitHub, acesse **Settings > Secrets and variables > Actions > New repository secret** e cadastre:
* `WANDB_API_KEY`: sua chave de API do W&B (`wandb_v1_...`).
* `WANDB_PROJECT`: `mlops-2026-2`
* `WANDB_MODELS`: `matheus-dcastro/mlops-2026-2/confusion-clf:v0`
* `MONGO_URL`: string de conexão do cluster MongoDB Atlas (`mongodb+srv://...`).

Após cadastrar, vá na aba **Actions** e acompanhe o workflow `CI - Build e Testes do Classificador` para garantir que fique **verde** em `test` e `smoke`.

---

## Passo 3: Enviar a Imagem Docker Inicial para o GHCR

1. No GitHub, gere um token em:
   **Foto de perfil > Settings > Developer settings > Personal access tokens > Tokens (classic)**
   * Marque o escopo: `write:packages`
2. No seu terminal, faça login e suba a imagem:
```bash
cd "/home/alomyr/Projetos/UFRN-06/MLOPS/Unidade 2/mlops-2026-2"

# Substitua SEU_TOKEN pelo token gerado
echo SEU_TOKEN | docker login ghcr.io -u matheus-dcastro --password-stdin

# Build e push da imagem:
docker build --platform linux/amd64 -t ghcr.io/matheus-dcastro/intent-clf:latest .
docker push ghcr.io/matheus-dcastro/intent-clf:latest
```
3. No seu GitHub:
   * Abra a aba **Packages** no seu perfil e clique no pacote `intent-clf`.
   * Em **Package settings**:
     * Altere a visibilidade para **Public**.
     * Em **Manage Actions access** > **Add repository**, selecione o repositório `intent-clf` com papel **Write**.

---

## Passo 4: Provisionamento no Azure

No terminal local (com o comando `az` já disponível):

1. **Autenticar na Azure**:
```bash
az login
```
*(Abra o link no navegador e autentique com o e-mail institucional da UFRN)*.

2. **Criar o Resource Group e o Ambiente**:
```bash
az group create --name mlops-2026-2 --location eastus
az containerapp env create --name mlops-env --resource-group mlops-2026-2 --location eastus
```

3. **Criar a Identidade Gerenciada e Atribuir Permissões**:
```bash
az identity create --name mlops-deployer --resource-group mlops-2026-2

# Recuperar IDs
CLIENT_ID=$(az identity show --name mlops-deployer --resource-group mlops-2026-2 --query clientId -o tsv)
PRINCIPAL_ID=$(az identity show --name mlops-deployer --resource-group mlops-2026-2 --query principalId -o tsv)
SUB_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

# Atribuir papel Contributor no resource group:
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role Contributor \
  --scope "/subscriptions/$SUB_ID/resourceGroups/mlops-2026-2"
```

4. **Criar a Credencial Federada (OIDC) para o GitHub Actions**:
```bash
# Substitua Matheus-dCastro/intent-clf pelo seu repositório exato
az identity federated-credential create \
  --name gh-actions-branch \
  --identity-name mlops-deployer \
  --resource-group mlops-2026-2 \
  --issuer https://token.actions.githubusercontent.com \
  --subject "repo:Matheus-dCastro/intent-clf:ref:refs/heads/main"

az identity federated-credential create \
  --name gh-actions-env \
  --identity-name mlops-deployer \
  --resource-group mlops-2026-2 \
  --issuer https://token.actions.githubusercontent.com \
  --subject "repo:Matheus-dCastro/intent-clf:environment:production"
```

5. **Subir a API no Azure Container Apps à mão**:
```bash
# Substitua pelas suas credenciais reais
az containerapp create \
  --name intent-clf \
  --resource-group mlops-2026-2 \
  --environment mlops-env \
  --image ghcr.io/matheus-dcastro/intent-clf:latest \
  --target-port 8000 \
  --ingress external \
  --secrets \
    wandb-api-key="SUA_CHAVE_WANDB" \
    mongo-url="SUA_MONGO_URL" \
  --env-vars \
    WANDB_API_KEY=secretref:wandb-api-key \
    WANDB_PROJECT=mlops-2026-2 \
    WANDB_MODELS=matheus-dcastro/mlops-2026-2/confusion-clf:v0 \
    MONGO_URL=secretref:mongo-url \
    APP_VERSION=latest
```

6. **Guardar a Application Url**:
```bash
APP_URL=$(az containerapp show --name intent-clf --resource-group mlops-2026-2 --query properties.configuration.ingress.fqdn -o tsv)
echo "URL da Aplicação: https://$APP_URL"
```

---

## Passo 5: Configurar GitHub Secrets, Variable e Environment

No repositório GitHub (`Settings > Secrets and variables > Actions`):

1. **Repository Secrets**:
   * `AZURE_CLIENT_ID`: `$CLIENT_ID` (Client ID da identidade gerenciada)
   * `AZURE_TENANT_ID`: `$TENANT_ID`
   * `AZURE_SUBSCRIPTION_ID`: `$SUB_ID`
2. **Repository Variables** (Aba *Variables*):
   * `APP_URL`: `https://$APP_URL` (com `https://` e sem barra no final).
3. **Environments** (`Settings > Environments > New environment`):
   * Nome: `production`
   * Marque: **Required reviewers** e adicione o seu usuário.
   * Em *Deployment branches and tags*: selecione **No restriction**.

---

## Passo 6: Criar o Workflow de CD (`cd.yml`)

O arquivo `.github/workflows/cd.yml` já pode ser criado na pasta `.github/workflows/` do projeto com os 4 jobs (`ci`, `release`, `deploy`, `verify`) e enviado via commit:
```bash
git add .github/workflows/cd.yml
git commit -m "cd.yml"
git push
```

---

## Passo 7: Testar Deploy e Rollback (Evidências do Relatório)

1. **Publicar a versão `v1.0.1`**:
```bash
git tag v1.0.1
git push origin v1.0.1
```
* Vá em Actions, abra o run `v1.0.1`.
* Tire o print da tela de deploy em *Waiting for review*.
* Aprove o deploy e aguarde o `verify` ficar verde (`OK: v1.0.1 no ar`).
* Acesse a `APP_URL` e confira `{"status":"ok","version":"v1.0.1"}`.

2. **Publicar a versão `v1.0.2`**:
```bash
git tag v1.0.2
git push origin v1.0.2
```
* Aprove o deploy e confira na URL: `{"status":"ok","version":"v1.0.2"}`.

3. **Executar o Rollback**:
* Em GitHub Actions > CD > **Run workflow**:
  * Branch: `main`
  * Tag: `v1.0.1`
  * Clique em **Run workflow**.
* Aprove o deploy e confira se a URL voltou para `{"status":"ok","version":"v1.0.1"}`.

4. **Coleta de Prints e Limpeza**:
* Reúna todos os prints exigidos pelo roteiro.
* Ao finalizar, exclua o Resource Group para evitar cobranças na conta da Azure:
```bash
az group delete --name mlops-2026-2 --yes --no-wait
```
