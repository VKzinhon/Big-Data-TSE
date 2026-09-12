# LGPD — Dados pessoais nos arquivos do TSE

Documentacao do passo 6: identificacao de dados sensiveis e decisao de tratamento
antes da carga no banco de dados.

## Fonte dos dados

- **Origem:** dados abertos do TSE (Eleicoes Municipais 2024)
- **Uso:** atividade academica (pipeline ETL + dashboard)
- **Local no projeto:** `etl/data_raw/` (nao versionado no Git)

## Colunas sensiveis identificadas

### CPF e documentos de identificacao

| Coluna | Arquivo(s) | Descricao |
|--------|------------|-----------|
| `NR_CPF_CANDIDATO` | candidatos, receitas, despesas contratadas | CPF do candidato |
| `NR_CPF_VICE_CANDIDATO` | receitas, despesas contratadas | CPF do vice na chapa |
| `NR_CPF_CNPJ_DOADOR` | receitas | CPF ou CNPJ de quem doou |
| `NR_CPF_CNPJ_FORNECEDOR` | despesas contratadas | CPF ou CNPJ do fornecedor |
| `NR_CNPJ_PRESTADOR_CONTA` | receitas, despesas contratadas | CNPJ do prestador de contas |

### Outros dados pessoais

| Coluna | Arquivo(s) | Descricao |
|--------|------------|-----------|
| `DS_EMAIL` | candidatos | E-mail do candidato |
| `DT_NASCIMENTO` | candidatos | Data de nascimento |
| `NR_TITULO_ELEITORAL_CANDIDATO` | candidatos | Titulo de eleitor |
| `NM_CANDIDATO` | varios | Nome civil (dado publico eleitoral, manter com criterio) |
| `NM_DOADOR`, `NM_FORNECEDOR` | prestacao de contas | Nomes de terceiros |

### Arquivos sem CPF direto de candidato

- `despesas_pagas_candidatos_2024_*.csv` — nao possui `SQ_CANDIDATO` nem CPF de candidato;
  usa `SQ_PRESTADOR_CONTAS` para identificar o prestador.

## Mascaramento ja feito pelo TSE

Em amostras dos dados de AC, observamos:

- `NR_CPF_CANDIDATO` = `-4` (codigo TSE para **nao divulgado**)
- `DS_EMAIL` = `NAO DIVULGAVEL`

**Atencao:** isso **nao** vale para todos os registros. Em receitas e despesas,
`NR_CPF_CNPJ_DOADOR` e `NR_CPF_CNPJ_FORNECEDOR` podem conter CPF/CNPJ legiveis
(ex.: CNPJ de diretorio partidario).

## Decisao da equipe

| Tratamento | Colunas | Justificativa |
|------------|---------|---------------|
| **Remover** | CPF, CNPJ de terceiros, e-mail, data de nascimento, titulo de eleitor | Minimizacao de dados (LGPD art. 6). A analise usa `SQ_CANDIDATO`, genero, raca, cargo e valores — nao exige documento de identificacao. |
| **Manter** | `SQ_CANDIDATO`, `DS_GENERO`, `DS_COR_RACA`, `DS_CARGO`, `SG_UF`, valores financeiros | Necessarios para o objetivo do dashboard e do ETL. |
| **Manter com criterio** | `NM_CANDIDATO`, `NM_URNA_CANDIDATO` | Nomes publicos no contexto eleitoral; sem vinculo a CPF apos remocao das colunas de documento. |

### Alternativas consideradas e descartadas

- **Mascarar** (`***.***.***-12`): ainda expoe parcialmente o documento; desnecessario para nossa analise.
- **Hashear** (SHA-256 + salt): util se fosse preciso rastrear a mesma pessoa entre bases sem expor CPF; nosso cruzamento ja usa `SQ_CANDIDATO`.

## Implementacao no ETL

Na fase **Transform**, antes de gravar no banco:

1. Remover colunas listadas em `etl/lgpd_columns.py`
2. Nao incluir dados brutos com CPF em artefatos versionados ou no dashboard
3. Manter `data_raw/` apenas local e fora do Git (`.gitignore`)

## Base legal (contexto academico)

Dados publicos divulgados pelo TSE para transparencia eleitoral, utilizados em
ambiente de ensino/pesquisa, com **minimizacao** dos dados pessoais conforme
principios da LGPD (necessidade, adequacao e transparencia).
