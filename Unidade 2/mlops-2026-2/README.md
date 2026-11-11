# API do Intent Classifier (MLOps 2026-2)

API em **FastAPI** que classifica a intenção de uma mensagem de texto. Ao subir, ela baixa um ou mais modelos treinados do **Weights & Biases (W&B)**, gera a predição de cada modelo para cada mensagem recebida e **grava o resultado no MongoDB** (Atlas), para alimentar um painel no futuro.

O código segue a ideia de **monolito modular**: um único serviço, organizado em módulos por domínio, com a infraestrutura compartilhada (banco de dados) em `shared/`.

## Como as peças se encaixam

![Fluxo da API: o Colab treina e envia o modelo ao W&B; a API baixa o modelo ao subir e grava cada predição no MongoDB Atlas](docs/arquitetura.svg)

1. O modelo é **treinado no Colab** e enviado ao W&B como um *artefato* (o arquivo `.keras` e um `_config.yml`).
2. A API lê a variável `WANDB_MODELS`, baixa esses artefatos **uma vez, ao iniciar**, e os mantém na memória.
3. Cada `POST /predictions` roda **todos** os modelos carregados e salva a resposta no MongoDB.

## Estrutura do repositório

```
mlops-2026-2/
├── README.md
├── requirements.txt            # dependências com versões fixas
├── .env.example                # modelo do arquivo de segredos (este SIM vai para o git)
├── .gitignore                  # ignora .env, models/, wandb/ ...
└── src/
    ├── app.py                  # cria o FastAPI, carrega/descarrega os modelos (lifespan)
    ├── modules/
    │   └── intent_classifier/  # módulo de domínio
    │       ├── controller.py   # rotas HTTP (POST/GET /predictions)
    │       ├── service.py      # carrega os modelos do W&B e gera as predições
    │       ├── model.py        # esquemas Pydantic (entrada e saída da API)
    │       └── intent_classifier.py   # classe IntentClassifier (treino e predição)
    └── shared/
        └── database/
            └── engine.py       # conexão com o MongoDB (usada por qualquer módulo)
```

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Ponto de entrada. No *startup* chama `load_models()`; no *shutdown* chama `clear_models()`. |
| `controller.py` | Recebe a requisição, chama o `service`, grava no banco e devolve a resposta. |
| `service.py` | Lê `WANDB_MODELS`, instancia um `IntentClassifier` por modelo e expõe `predict_all(texto)`. |
| `model.py` | Define o formato da mensagem (`Mensagem`) e das predições. |
| `engine.py` | Cria o cliente do MongoDB a partir das variáveis `MONGO_*`. |

## Pré-requisitos

- **Git** e **Conda** (Miniconda ou Anaconda).
- Conta gratuita no **[Weights & Biases](https://wandb.ai)**.
- Conta gratuita no **[MongoDB Atlas](https://www.mongodb.com/cloud/atlas)**.
- Conta Google (para usar o Colab).
- Linux ou macOS. No **Windows**, use o **WSL2**: o pacote `tensorflow-text` não costuma ter versão para Windows nativo (confira a versão no PyPI).

## Passo a passo (siga nesta ordem)

### 1. Clonar o repositório

```bash
git clone https://github.com/adaj/mlops-2026-2.git
cd mlops-2026-2
```

Se você já clonou antes, apenas atualize:

```bash
git pull
```

### 2. Criar o ambiente conda e instalar as dependências

```bash
conda create -n mlops-2026-2 python=3.11 -y
conda activate mlops-2026-2
pip install -r requirements.txt
```

Use **Python 3.11**: é a versão compatível com o TensorFlow 2.19 fixado no `requirements.txt`.

### 3. Treinar um modelo no Colab e publicá-lo no W&B

Abra o notebook: **[IntentClassifier.ipynb](https://colab.research.google.com/drive/1YqTwhcoTdni6HBv_9W8Zw03452TV4ijC?usp=sharing)** e faça uma cópia (*Arquivo → Salvar uma cópia no Drive*).

1. **Segredo do W&B.** No painel lateral esquerdo do Colab, clique no ícone de **chave (Secrets)** → *Adicionar novo secret*.
   - Nome: `WANDB_KEY` (exatamente assim, é o nome que o notebook lê)
   - Valor: sua API key do W&B (veja a seção [Variáveis de ambiente](#variáveis-de-ambiente))
   - Ative **Acesso ao notebook**.
2. **Dados de treino.** No painel *Arquivos* do Colab, envie o arquivo `confusion_examples.yml` (fornecido pelo professor).
3. **Execute as células em ordem**: instalação dos pacotes, definição da classe `IntentClassifier`, login no W&B e treinamento.
4. Ao final do treino, abra o W&B e confira:
   - Projeto: `mlops-2026-2` (na sua conta)
   - Aba **Artifacts** → `confusion-clf` → aba **Files**: devem existir **dois** arquivos, `model.keras` e `model_config.yml`.
5. **Copie o nome completo do artefato**, no formato `entidade/projeto/artefato:versão`, por exemplo:

   ```
   seu_usuario_wandb/mlops-2026-2/confusion-clf:v0
   ```

   Você o encontra na página do artefato (campo de nome completo, ou aba *Usage*). Esse valor vai para `WANDB_MODELS`.

> **Atenção às versões.** Se, ao subir a API, aparecer o erro `Unrecognized keyword arguments passed to Dense: {'quantization_config': None}`, o Keras do Colab é diferente do instalado na sua máquina. Treine e carregue com as mesmas versões do `requirements.txt` (`tensorflow==2.19.1`, `keras==3.13.2`).

### 4. Criar o banco no MongoDB Atlas

1. Entre no Atlas e crie um **projeto**.
2. Crie um cluster gratuito (**M0 / Free**).
3. **Database Access** → *Add New Database User*: crie um usuário e uma senha (este usuário é só do banco). Prefira senhas **sem** caracteres especiais (`@ : / ? # %`).
4. **Network Access** → *Add IP Address*: adicione o seu IP (*Add Current IP Address*). Para uso em aula, `0.0.0.0/0` (qualquer IP) funciona, mas deixa o cluster aberto a toda a internet: use somente com dados fictícios e senha forte.
5. Em **Database → Connect → Drivers → Python**, copie a *connection string*:

   ```
   mongodb+srv://<usuario>:<db_password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

6. Troque `<db_password>` pela senha do passo 3 (sem os sinais `<` `>`). Se a senha tiver caracteres especiais, codifique-a: `python -c "from urllib.parse import quote_plus; print(quote_plus('SUA_SENHA'))"`.

O banco e a coleção são criados automaticamente na primeira gravação; não precisa criá-los à mão.

### 5. Criar o arquivo `.env`

Na **raiz do projeto**, copie o modelo e edite:

```bash
cp .env.example .env
```

Preencha com os seus valores (sem espaços ao redor do `=`):

```
WANDB_API_KEY=wandb_v1_...
WANDB_PROJECT=mlops-2026-2
WANDB_MODELS=seu_usuario_wandb/mlops-2026-2/confusion-clf:v0
MONGO_URL=mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

> **O `.env` é secreto e não pode ir para o git.** Ele já está no `.gitignore`. Confira com `git status` antes de qualquer `git add`: o `.env` não deve aparecer. Nunca publique prints, vídeos ou mensagens que mostrem esse arquivo.

### 6. (Opcional) Testar a conexão com o MongoDB

Com o ambiente ativo, na raiz do projeto:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os, pymongo; c = pymongo.MongoClient(os.environ['MONGO_URL'], serverSelectionTimeoutMS=5000); print(c.admin.command('ping'))"
```

A saída esperada é `{'ok': 1.0}`. Se der erro, veja [Solução de problemas](#solução-de-problemas) antes de subir a API.

### 7. Subir a API

Sempre a partir da **raiz do projeto**:

```bash
uvicorn src.app:app --port 8000
```

Para usar outra porta, mude o número (`--port 8001`). Não use `--reload`: ele reiniciaria o servidor a cada alteração e recarregaria os modelos todas as vezes.

Na primeira execução a subida demora: a API baixa o artefato do W&B e o modelo de *embeddings* de texto. Quando aparecer `Application startup complete.`, está pronto.

### 8. Testar no Swagger

1. Abra **http://localhost:8000/docs**.
2. Clique em `POST /predictions` → **Try it out**.
3. Preencha o corpo da requisição (só o `text` é obrigatório), por exemplo:

   ```json
   {
     "id": "msg-001",
     "nome": "Seu Nome",
     "text": "eu não estou entendendo nada"
   }
   ```

4. Clique em **Execute**. O esperado é o código **200** e uma resposta com a intenção e as probabilidades de cada modelo:

   ```json
   {
     "confusion-clf": {
       "intent": "confusion",
       "probs": { "confusion": 0.91, "neutral_statement": 0.06, "certainty": 0.03 }
     },
     "message": { "id": "msg-001", "nome": "Seu Nome", "text": "...", "timestamp": "..." }
   }
   ```

5. Para conferir a gravação, abra o Atlas → **Browse Collections** → banco `intent_classifier` → coleção `predictions`.

Pelo terminal, o equivalente é:

```bash
curl -X POST http://localhost:8000/predictions \
  -H "Content-Type: application/json" \
  -d '{"id": "msg-001", "nome": "Seu Nome", "text": "eu não estou entendendo nada"}'
```

## Variáveis de ambiente

Todas ficam no arquivo `.env` da raiz do projeto.

| Variável | Obrigatória | O que é | Como obter |
|---|---|---|---|
| `WANDB_API_KEY` | Sim | Chave de acesso à sua conta do W&B. A API usa para baixar os modelos. | Faça login no W&B e abra **https://wandb.ai/authorize**. Alternativa: foto do perfil (canto superior direito) → **User Settings** → seção **API Keys**. Chaves novas começam com `wandb_v1_`. |
| `WANDB_PROJECT` | Sim | Nome do projeto no W&B. | Use `mlops-2026-2`, o mesmo do notebook do Colab. |
| `WANDB_MODELS` | Sim | Lista de modelos a carregar, separados por **vírgula**, no formato `entidade/projeto/artefato:versão`. | Página do artefato no W&B (veja o passo 3). A *entidade* é o seu usuário (ou time) no W&B e aparece na URL `wandb.ai/<entidade>`. |
| `MONGO_URL` | Sim | *Connection string* do cluster MongoDB Atlas, já com usuário e senha. | Atlas → **Connect → Drivers → Python** (veja o passo 4). |
| `MONGO_DB` | Não | Nome do banco. Padrão: `intent_classifier`. | Escolha livre. |
| `MONGO_PRED_COLLECTION` | Não | Nome da coleção das predições. Padrão: `predictions`. | Escolha livre. |

Exemplo com **dois modelos** (note a vírgula e o nome de cada artefato):

```
WANDB_MODELS=seu_usuario/mlops-2026-2/confusion-clf:v0,seu_usuario/mlops-2026-2/clair_intents-clf:v0
```

Na resposta da API, cada modelo aparece pelo nome do artefato (`confusion-clf`, `clair_intents-clf`).

## Rotas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Verificação de saúde (`{"status": "ok"}`). |
| GET | `/docs` | Documentação interativa (Swagger). |
| POST | `/predictions` | Classifica uma mensagem com todos os modelos carregados e grava no MongoDB. |
| GET | `/predictions` | Lista as predições gravadas, das mais recentes para as mais antigas. O parâmetro `limit` define quantas (padrão: 20). |

Campos do corpo do `POST /predictions`: `text` (a mensagem, obrigatória e não pode ser vazia), `id` e `nome` (textos opcionais, úteis para identificar quem enviou) e `timestamp` (preenchido automaticamente). O que fica gravado no MongoDB é o mesmo conteúdo que a API devolve: o resultado de cada modelo mais a mensagem recebida.

## Solução de problemas

| Sintoma | Causa provável e solução |
|---|---|
| `KeyError: 'MONGO_URL'` | O `.env` não existe, está em outra pasta ou você rodou o `uvicorn` fora da raiz do projeto. |
| `ServerSelectionTimeoutError` | O seu IP não está liberado em **Network Access** no Atlas (a mudança leva cerca de um minuto), ou a rede bloqueia a porta 27017. |
| `Authentication failed` | Usuário ou senha errados na `MONGO_URL`, ou senha com caractere especial sem codificar. |
| `Could not fetch artifact ... from W&B` | Caminho do artefato errado em `WANDB_MODELS`, `WANDB_API_KEY` inválida, ou o artefato está em um projeto privado de outra conta. |
| `Config file (_config.yml) not found in W&B artifact` | O artefato foi gerado com uma versão antiga do código. Retreine no Colab e confira que a aba **Files** tem `model.keras` e `model_config.yml`. |
| `Unrecognized keyword arguments ... quantization_config` | Versões diferentes do Keras no treino e na API. Alinhe com o `requirements.txt`. |
| `422 Unprocessable Entity` no Swagger | O corpo está inválido: em geral falta o campo `text` ou ele está vazio. |
| `Address already in use` | A porta está ocupada. Use outra: `--port 8001`. |
| `ModuleNotFoundError: No module named 'src'` | Você não está na raiz do projeto. Rode o `uvicorn` de lá. |
| A subida é muito lenta | Normal na primeira vez: ela baixa os modelos. Nas próximas, o *cache* local acelera. |

## Segurança

- `.env` nunca é commitado. Se uma chave vazar (em um commit, print ou mensagem), **revogue-a imediatamente** no W&B (User Settings → API Keys) ou no Atlas (troque a senha do usuário).
- O arquivo `.env.example` guarda apenas **nomes** de variáveis e valores fictícios.

## Próximos passos

Empacotar a API em um container **Docker**, para rodar em qualquer máquina sem montar o ambiente conda à mão.
