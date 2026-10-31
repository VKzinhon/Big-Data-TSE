# Representatividade Política e Financiamento Eleitoral

Pipeline da disciplina de Big Data para as eleições de 2024. A pergunta do trabalho compara quem se candidata (gênero, raça, cargo, partido e UF) com o dinheiro declarado na prestação de contas.

Fonte: Portal de Dados Abertos do TSE. Recorte: candidaturas, receitas e despesas contratadas de 2024, por UF.

Nesta etapa os dados públicos passam pelo tratamento, ficam no grão de uma candidatura e estão prontos para carga no PostgreSQL da Aiven. A infraestrutura nasce por Terraform. Credenciais não entram no repositório.

```text
CSVs do TSE
    -> etl/02_transform.py
    -> parquet tratado (candidatura + financiamento)
    -> etl/03_load.py
    -> PostgreSQL na Aiven (terraform/)
```

## Estrutura do repositório

| Pasta | O que contém |
|---|---|
| `etl/` | Tratamento (`02_transform.py`), carga (`03_load.py`) e exploração |
| `terraform/` | Provisionamento do PostgreSQL |
| `docs/` | Decisões de LGPD e dicionário do tratamento |
| `requirements.txt` | Dependências Python |
| `.env.example` | Modelo da URI do banco, sem senha real |
| `terraform/terraform.tfvars.example` | Modelo do token da Aiven, sem token real |

Os CSVs brutos ficam em `etl/data_raw/` e o parquet tratado em `etl/data_processed/`. Os dois ficam fora do Git por tamanho. A base tratada se regenera com o script de tratamento.

## Dados utilizados

| Item | Descrição |
|---|---|
| Fonte | Portal de Dados Abertos do TSE |
| Base | Candidaturas (`consulta_cand_2024`) e prestação de contas eleitorais de candidatos 2024 |
| Período | Eleições de 2024 |
| Recorte | 26 estados. O Distrito Federal não entra: o pleito de 2024 é municipal e o DF não tem municípios |
| Formato | CSV com separador `;` e encoding `latin-1` |
| Chave | `SQ_CANDIDATO` em candidatos, receitas e despesas contratadas |

Arquivos usados:

- `consulta_cand_2024/consulta_cand_2024_{UF}.csv`
- `prestacao_de_contas_eleitorais_candidatos_2024/receitas_candidatos_2024_{UF}.csv`
- `prestacao_de_contas_eleitorais_candidatos_2024/despesas_contratadas_candidatos_2024_{UF}.csv`

Características que mudaram o desenho:

- A prestação de contas tem várias linhas por candidatura. O microdado bruto não cabe, e não precisa caber, no disco de 1 GB do plano gratuito.
- Prefeito de segundo turno aparece mais de uma vez em `consulta_cand`.
- `despesas_pagas` usa `SQ_PRESTADOR_CONTAS`. Não entra no cruzamento.
- Há CPF, CNPJ, e-mail, título de eleitor, data de nascimento e nome de doador ou fornecedor. Esses campos saem antes da gravação. Ver [docs/LGPD.md](docs/LGPD.md).

## Tratamento realizado

Código: `etl/02_transform.py` (a lógica está em `etl/transformar.py`).

| Problema encontrado | Decisão | Justificativa |
|---|---|---|
| `SQ_CANDIDATO` pode virar float na leitura | Ler a chave como texto e só então converter para inteiro | Float altera identificador grande e o join falha em silêncio |
| Várias linhas por candidato na prestação de contas | Somar `VR_RECEITA` e `VR_DESPESA_CONTRATADA` por `SQ_CANDIDATO` | A pergunta é quanto cada candidatura movimentou, não cada lançamento |
| Candidato sem receita ou sem despesa | Left join a partir da candidatura e preencher com 0 | Se quem não arrecadou sumir, a comparação entre perfil e dinheiro fica distorcida |
| Segundo turno repetido | Manter o maior `NR_TURNO` de cada `SQ_CANDIDATO` | O resultado final da campanha está no último turno |
| Marcadores `#NULO#`, `#NE#` e `-1` | Viram nulo. Idade negativa não vira zero | São ausências do TSE, não categorias |
| Vírgula decimal nos valores | Trocar vírgula por ponto e arredondar em centavos | O CSV oficial mistura os dois formatos |
| Mesmo rótulo em maiúsculas e minúsculas | Gênero, raça, cargo, partido, UF e situação em maiúsculas | Evita partir a mesma categoria em duas |
| Dados pessoais | Remover antes de gravar. Receitas e despesas são lidas só com chave e valor | O cruzamento não precisa de CPF. Nome de doador não entra na base analítica |
| Volume do arquivo de contas | Agregar em blocos de 200 mil linhas com Pandas | Uma linha por candidatura cabe no plano gratuito. PySpark não muda o resultado nesse grão |
| Situação da candidatura (apto, indeferido etc.) | Guardar a coluna, sem filtrar | O recorte "apenas aptos" é regra da análise seguinte |

A saída é uma linha por `SQ_CANDIDATO`:

- `etl/data_processed/candidatura.parquet`
- `etl/data_processed/financiamento.parquet`
- `etl/data_processed/manifest.json` com a contagem por UF

O nome de urna permanece. É o nome público da campanha. A data de nascimento sai. O arquivo de candidaturas de 2024 não traz `NR_IDADE_DATA_POSSE`, então a idade é calculada em 1º de janeiro do ano seguinte à eleição e só esse número é gravado.

Conferência da lógica, com CSV sintético no formato do TSE (não é a base oficial):

```powershell
.\venv\Scripts\python.exe etl\verificar_fixture.py
```

## Modelagem

Banco relacional. O grão é tabular, a chave é estável e a análise cruza atributos da candidatura com totais. Um banco documental não acrescenta nada a esse grão. Não há tabela de lançamento: cada doação estouraria o disco de 1 GB e guardaria dado pessoal de doador e fornecedor.

```text
candidatura                          financiamento
-----------------------------        ---------------------------------
sq_candidato  BIGINT  PK      1 -- 1 sq_candidato           BIGINT PK/FK
ano_eleicao   INTEGER                vr_receita             NUMERIC(16,2)
sg_uf         CHAR(2)                vr_despesa_contratada  NUMERIC(16,2)
nm_ue         TEXT                   qt_receitas            INTEGER
ds_cargo      TEXT                   qt_despesas            INTEGER
nm_urna       TEXT
sg_partido    TEXT
nm_partido    TEXT
ds_genero     TEXT
ds_cor_raca   TEXT
ds_situacao_candidatura TEXT
ds_sit_tot_turno        TEXT
nr_turno_resultado      SMALLINT
nr_idade_data_posse     SMALLINT
```

`financiamento.sq_candidato` referencia `candidatura.sq_candidato`. As duas tabelas têm a mesma quantidade de linhas. O dicionário com a coluna de origem de cada campo está em [docs/TRATAMENTO.md](docs/TRATAMENTO.md).

## Infraestrutura

| Item | Escolha |
|---|---|
| Nuvem | Aiven, plano gratuito |
| Serviço | PostgreSQL (`aiven_pg`) |
| Projeto Aiven | `cauamaia488-ead4` |
| Plano | `free-1-1gb`: 1 CPU, 1 GB de RAM, 1 GB de disco, até 20 conexões |
| Versão | PostgreSQL 18 |
| Região | `do-sfo` (DigitalOcean, São Francisco), atribuída pela Aiven no plano gratuito e registrada no Terraform |
| Ferramenta | Terraform `>= 1.5` e provider `aiven/aiven` `4.x` |
| Arquivos | `terraform/main.tf`, `variables.tf`, `outputs.tf` |

O recurso provisionado é um único serviço PostgreSQL, `pg-1f18e561` (`aiven_pg.tse`), com acesso público por SSL obrigatório. A carga (`etl/03_load.py`) apaga e recria as duas tabelas a cada execução, então rodar de novo substitui os dados sem duplicar.

## Segurança das informações

Nenhum token, senha ou URI real é versionado.

| Segredo | Onde fica | O que entra no Git |
|---|---|---|
| Token da Aiven | `terraform/terraform.tfvars`, só na máquina de quem aplica | `terraform.tfvars.example`, com texto de exemplo |
| URI do PostgreSQL | `.env`, variável `DATABASE_URL` | `.env.example`, com `SENHA` e `HOST` fictícios |
| Estado do Terraform | `.terraform/` e `*.tfstate` na máquina local | Nada. O state guarda a senha do banco |

No código, o token é `var.aiven_api_token` com `sensitive = true`. A URI de saída do Terraform também é `sensitive`, para o `plan` e o `apply` não imprimirem a senha. O `.gitignore` bloqueia `.env`, `terraform.tfvars`, `.terraform/` e os arquivos de state.

## Execução

Ferramentas: Python 3, o conteúdo de `requirements.txt` (Pandas, PyArrow, SQLAlchemy, psycopg e python-dotenv) e Terraform 1.5 ou superior. Conta na Aiven com um projeto e um token pessoal.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Coloque os CSVs oficiais em `etl/data_raw/`, nas pastas citadas em Dados utilizados.

```powershell
# Uma UF, para conferir
.\venv\Scripts\python.exe etl\02_transform.py --uf AC

# Todas as UFs encontradas em data_raw
.\venv\Scripts\python.exe etl\02_transform.py
```

Infraestrutura, com o token só no arquivo local:

```powershell
copy terraform\terraform.tfvars.example terraform\terraform.tfvars
# Edite terraform.tfvars com o token (projeto e servico ja vem preenchidos). Nao commite esse arquivo.

cd terraform
terraform init
terraform plan
terraform apply
terraform output -raw postgresql_service_uri
```

Copie a URI para `.env` na raiz do projeto:

```text
DATABASE_URL=postgres://avnadmin:...@....aivencloud.com:PORTA/defaultdb?sslmode=require
```

```powershell
.\venv\Scripts\python.exe etl\03_load.py
```

O script imprime a quantidade de linhas de cada tabela e o tamanho do banco. Esses números mostram que a base coube no plano de 1 GB.

## Painel

Com o serviço da Aiven em Running e o `.env` na raiz:

```powershell
.\venv\Scripts\python.exe -m streamlit run painel\app.py
```

Abre em http://localhost:8501. O painel lê as tabelas `candidatura` e `financiamento` e compara a fatia das candidaturas com a fatia do dinheiro, por gênero, raça e cargo.

Scripts anteriores de exploração, úteis para inspecionar o CSV cru: `etl/inspect_sample.py`, `etl/validar_merge.py` e `etl/01_explore.py`. Eles não gravam a base tratada.

## Fora desta etapa

O dashboard e as métricas de gênero e raça (percentual de candidaturas contra percentual do dinheiro) usam estas duas tabelas e ficam para a fase seguinte.
