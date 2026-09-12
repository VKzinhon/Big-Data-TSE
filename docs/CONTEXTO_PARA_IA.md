# Contexto do projeto — documentacao para assistentes de IA

> **Para Claude / Cursor / outras IAs:** leia este arquivo primeiro antes de sugerir
> implementacoes. Ele resume o que ja foi feito, decisoes tecnicas, o que falta e como
> verificar gaps no repositorio.

---

## 1. Visao geral

| Item | Detalhe |
|------|---------|
| **Projeto** | Atividade academica de Big Data |
| **Pasta raiz** | `Big data` (Windows: `C:\Users\Force\Downloads\Big data`) |
| **Objetivo final** | Pipeline ETL + infraestrutura Terraform + dashboard sobre eleicoes municipais 2024 (TSE) |
| **Dados** | Candidatos + prestacao de contas eleitoral 2024 |
| **Stack atual** | Python 3.14, pandas, Git (sem commits ainda) |
| **Idioma** | Portugues (documentacao e comunicacao com o aluno) |

### Entregaveis esperados pelo guia da faculdade

```
/
??? etl/           # Pipeline de dados
??? terraform/     # Infraestrutura como codigo
??? dashboard/     # Visualizacao
??? README.md
```

---

## 2. O que JA foi feito (passos 1 a 7)

### Passo 1 — Estrutura e Git

- [x] Pastas `/etl`, `/terraform`, `/dashboard`
- [x] `README.md` na raiz
- [x] `git init` executado
- [ ] **Primeiro commit ainda NAO feito** (todos os arquivos estao untracked)

### Passo 2 — Dados brutos

- [x] `etl/data_raw/` criado
- [x] Datasets movidos para dentro de `data_raw/`:
  - `consulta_cand_2024/` (27 CSVs por UF + BRASIL + leiame.pdf)
  - `prestacao_de_contas_eleitorais_candidatos_2024/` (108 CSVs + PDFs)
- [x] `.gitignore` ignora `etl/data_raw/` (arquivos grandes)

### Passo 3 — Ambiente Python

- [x] `venv/` criado
- [x] `pandas==3.0.5` instalado
- [x] `requirements.txt`
- [x] Convencao de leitura TSE documentada: `sep=";"`, `encoding="latin-1"`

**Windows/PowerShell:** ativacao do venv pode exigir:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\Activate.ps1
```
Alternativa: `.\venv\Scripts\python.exe` direto nos comandos.

### Passo 4 — Inspecao de amostra

- [x] Colunas confirmadas em `consulta_cand_2024_AC.csv`:
  - `DS_GENERO`, `DS_COR_RACA`, `DS_CARGO`, `SQ_CANDIDATO`
- [x] Script: `etl/inspect_sample.py`
- [x] Testado manualmente pelo aluno (output OK)

### Passo 5 — Validacao da chave de juncao

- [x] `SQ_CANDIDATO` funciona entre candidatos e:
  - `receitas_candidatos_2024_*.csv`
  - `despesas_contratadas_candidatos_2024_*.csv`
- [x] Script: `etl/validar_merge.py`
- [x] Resultados validados em AC (amostra):
  - Receitas: ~80,1% candidatos com match
  - Despesas contratadas: ~56,8% candidatos com match
- [x] **Limitacao documentada:** `despesas_pagas_*.csv` NAO tem `SQ_CANDIDATO` (usa `SQ_PRESTADOR_CONTAS`)

### Passo 6 — LGPD

- [x] `docs/LGPD.md` — colunas sensiveis e decisao da equipe
- [x] `etl/lgpd_columns.py` — lista + funcao `remover_colunas_lgpd()`
- [x] **Decisao:** REMOVER CPF/CNPJ/e-mail/nascimento/titulo antes do banco
- [x] Manter `SQ_CANDIDATO` para cruzamento (sem CPF)

### Passo 7 — Exploracao inicial

- [x] `etl/01_explore.py` — `.info()`, `.head()`, `value_counts` de genero/raca/cargo
- [x] Explora candidatos + receitas (amostra por UF)
- [x] **Nao e ETL final** — so para decidir colunas antes da limpeza

---

## 3. O que AINDA FALTA (prioridade sugerida)

### Alta prioridade — ETL

| Item | Status | Notas |
|------|--------|-------|
| Script de limpeza/transform (`02_clean.py` ou similar) | Pendente | Usar `lgpd_columns.py`, normalizar tipos, tratar `#NULO` |
| Script de carga/agregacao (`03_load.py` ou similar) | Pendente | Saida parquet/csv limpo ou carga em banco |
| Processar todas as UFs sem estourar memoria | Pendente | Ler UF a UF ou chunks; nunca carregar tudo de uma vez |
| Join candidatos + receitas/despesas (escala nacional) | Pendente | `left join` em `SQ_CANDIDATO` |
| Tratar `despesas_pagas` | Pendente | Join indireto via `SQ_DESPESA` ou outra estrategia |
| Pasta `etl/data_processed/` ou similar | Pendente | Dados limpos (provavelmente no `.gitignore`) |
| Decisao formal de colunas a manter | Parcial | Exploracao feita; falta documentar escolha final da equipe |

### Media prioridade — Infraestrutura

| Item | Status | Notas |
|------|--------|-------|
| Arquivos Terraform em `/terraform` | Vazio (so `.gitkeep`) | Banco, bucket, etc. conforme guia |
| Variaveis, outputs, backend | Pendente | |
| Integracao ETL -> destino provisionado | Pendente | |

### Media prioridade — Dashboard

| Item | Status | Notas |
|------|--------|-------|
| App em `/dashboard` | Vazio (so `.gitkeep`) | Streamlit, Power BI, Grafana, etc. — confirmar com guia |
| Visualizacoes por genero, raca, cargo, financas | Pendente | |
| Conexao com dados processados ou banco | Pendente | |

### Baixa prioridade — Repo e entrega

| Item | Status |
|------|--------|
| Primeiro commit Git | Pendente |
| Commits incrementais por etapa | Pendente |
| Atualizar README com arquitetura final | Parcial |

---

## 4. Arquitetura de dados

### Fontes (raw)

```
etl/data_raw/
??? consulta_cand_2024/
?   ??? consulta_cand_2024_{UF}.csv      # 50 colunas, ~candidatos por UF
??? prestacao_de_contas_eleitorais_candidatos_2024/
    ??? receitas_candidatos_2024_{UF}.csv
    ??? despesas_contratadas_candidatos_2024_{UF}.csv
    ??? despesas_pagas_candidatos_2024_{UF}.csv
    ??? receitas_candidatos_doador_originario_2024_{UF}.csv
    ??? leiame_*.pdf
```

### Leitura obrigatoria dos CSVs

```python
pd.read_csv(arquivo, sep=";", encoding="latin-1")
```

### Chave de juncao

| Relacao | Chave | Funciona? |
|---------|-------|-----------|
| candidatos <-> receitas | `SQ_CANDIDATO` | Sim |
| candidatos <-> despesas contratadas | `SQ_CANDIDATO` | Sim |
| candidatos <-> despesas pagas | `SQ_CANDIDATO` | **Nao** (usar estrategia alternativa) |

### Colunas analiticas principais

- `SQ_CANDIDATO` — ID tecnico do candidato
- `DS_GENERO`, `DS_COR_RACA`, `DS_CARGO`
- `SG_UF`, `NM_UE` (municipio)
- `VR_RECEITA`, `VR_DESPESA_CONTRATADA`, `VR_PAGTO_DESPESA` (valores em formato BR: `"1.234,56"` — precisara conversao no ETL)

### Valores especiais TSE

- `#NULO`, `#NE`, `-4` — tratar na limpeza
- CPF candidato frequentemente `-4` (nao divulgado), mas doadores/fornecedores podem ter CPF/CNPJ real

---

## 5. Scripts existentes em `/etl`

| Arquivo | Proposito | ETL final? |
|---------|-----------|------------|
| `inspect_sample.py` | Passo 4 — checar 4 colunas-chave | Nao |
| `validar_merge.py` | Passo 5 — testar merge `SQ_CANDIDATO` | Nao |
| `lgpd_columns.py` | Lista colunas LGPD + helper de remocao | Usado pelo ETL futuro |
| `01_explore.py` | Passo 7 — info/head/categorias | Nao |

### Comandos de verificacao rapida

```powershell
cd "C:\Users\Force\Downloads\Big data"

.\venv\Scripts\python.exe etl\inspect_sample.py --uf AC --nrows 1000
.\venv\Scripts\python.exe etl\validar_merge.py --uf AC --nrows 5000
.\venv\Scripts\python.exe etl\01_explore.py --uf AC --nrows 1000
```

---

## 6. Decisoes tecnicas ja tomadas (nao reverter sem motivo)

1. **Dados raw fora do Git** — `etl/data_raw/` no `.gitignore`
2. **Encoding latin-1 e separador `;`** — padrao TSE
3. **Chave de merge: `SQ_CANDIDATO`** — nao usar CPF
4. **LGPD: remover** colunas de documento antes do banco (ver `lgpd_columns.py`)
5. **UF pequena (AC) para testes** — antes de escalar para Brasil inteiro
6. **Genero/raca no ETL final** — preferir base de **candidatos** (mais completa que receitas)

---

## 7. Armadilhas conhecidas

| Problema | Solucao |
|----------|---------|
| PowerShell bloqueia `Activate.ps1` | `Set-ExecutionPolicy -Scope Process` ou usar `python.exe` do venv direto |
| CSV com encoding errado | Sempre `encoding="latin-1"` |
| Colunas coladas | Sempre `sep=";"` |
| Memoria estoura | `nrows` em testes; processar por UF no ETL final |
| Merge 0 linhas | Normalizar `SQ_CANDIDATO` para mesmo tipo numerico |
| Arquivos `.py` com acentos no Windows | Usar `# -*- coding: utf-8 -*-` ou evitar caracteres especiais em strings |
| `despesas_pagas` sem `SQ_CANDIDATO` | Nao tentar join direto com candidatos |

---

## 8. Checklist para IA verificar gaps

Use este checklist ao revisar o repositorio:

```
ESTRUTURA
[ ] etl/ existe com scripts
[ ] terraform/ tem arquivos .tf (atualmente VAZIO)
[ ] dashboard/ tem codigo do dashboard (atualmente VAZIO)
[ ] README.md atualizado

DADOS
[ ] etl/data_raw/ existe localmente (pode nao estar no Git)
[ ] consulta_cand_2024 e prestacao_de_contas presentes

ETL
[ ] Existe script de LIMPEZA/TRANSFORM (02_*.py) — FALTA
[ ] Existe script de CARGA nacional — FALTA
[ ] lgpd_columns.py aplicado no transform — FALTA
[ ] Valores monetarios convertidos de "1.234,56" para float — FALTA
[ ] Tratamento de #NULO e -4 — FALTA

INFRA
[ ] Terraform provisiona recurso (RDS, S3, etc.) — FALTA

DASHBOARD
[ ] Visualizacoes implementadas — FALTA

LGPD
[x] docs/LGPD.md
[x] Decisao documentada (remover CPF)

GIT
[ ] Pelo menos um commit — FALTA
```

---

## 9. Proximo passo logico (passo 8+)

Com base no progresso atual, o proximo passo esperado pelo fluxo do guia e:

1. **Definir colunas finais** a manter (apos discussao com base no output de `01_explore.py`)
2. **Criar `etl/02_clean.py`** (ou notebook) com:
   - Leitura por UF
   - Remocao LGPD (`remover_colunas_lgpd`)
   - Selecao de colunas
   - Limpeza de categorias (`#NULO`, etc.)
   - Conversao de valores monetarios
3. **Criar `etl/03_transform.py`** com merge e agregacoes
4. **Terraform** conforme especificacao do professor
5. **Dashboard** consumindo dados processados

---

## 10. Arquivos de referencia

| Arquivo | Conteudo |
|---------|----------|
| `README.md` | Visao geral, comandos, status parcial |
| `docs/LGPD.md` | Detalhamento LGPD |
| `docs/CONTEXTO_PARA_IA.md` | Este arquivo |
| `etl/lgpd_columns.py` | Colunas a remover |
| `.gitignore` | `etl/data_raw/`, `venv/`, `__pycache__` |
| `requirements.txt` | `pandas==3.0.5` |

---

## 11. Como usar este doc com Claude

**Prompt sugerido para o aluno colar no Claude:**

> Leia `docs/CONTEXTO_PARA_IA.md` e `README.md`. Compare com o repositorio atual,
> liste o que falta para completar a atividade (ETL, Terraform, dashboard, LGPD, Git)
> e sugira o proximo passo concreto com arquivos a criar.

**O que a IA deve fazer:**

1. Ler este documento + listar arquivos reais no repo
2. Marcar itens do checklist da secao 8
3. Nao sugerir reprocessar passos 1-7 ja concluidos
4. Respeitar decisoes da secao 6
5. Propor implementacao incremental (uma UF antes do Brasil inteiro)

---

*Ultima atualizacao: passos 1-7 concluidos. ETL final, Terraform e dashboard pendentes.*
