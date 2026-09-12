# Big Data

Projeto de atividade acadêmica com pipeline ETL, infraestrutura Terraform e dashboard.

## Estrutura

```
.
├── docs/
│   ├── CONTEXTO_PARA_IA.md  # Handoff para Claude/IA — status e o que falta
│   └── LGPD.md              # Dados pessoais e decisão de tratamento (passo 6)
├── etl/
│   ├── 01_explore.py        # Exploracao inicial — info, head, categorias (passo 7)
│   ├── inspect_sample.py    # Inspeciona amostra de candidatos (passo 4)
│   ├── validar_merge.py     # Valida join SQ_CANDIDATO (passo 5)
│   ├── lgpd_columns.py      # Colunas a remover no ETL (LGPD)
│   └── data_raw/            # Dados brutos (não versionados — ver .gitignore)
│       ├── consulta_cand_2024/
│       └── prestacao_de_contas_eleitorais_candidatos_2024/
├── terraform/      # Infraestrutura como código
├── dashboard/    # Visualização e análise dos dados
└── README.md
```

### Dados brutos (`etl/data_raw/`)

Os CSVs do TSE ficam em `etl/data_raw/` e **não são versionados** no Git (arquivos grandes).

| Pasta | Conteúdo |
|-------|----------|
| `consulta_cand_2024/` | Candidatos por UF (`consulta_cand_2024_XX.csv`) |
| `prestacao_de_contas_eleitorais_candidatos_2024/` | Despesas contratadas e pagas por UF |

## Ambiente Python

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Leitura dos CSVs do TSE

Os arquivos usam **separador `;`** e **encoding `latin-1`** (ISO-8859-1), não UTF-8:

```python
import pandas as pd

df = pd.read_csv("arquivo.csv", sep=";", encoding="latin-1")
```

### Scripts de exploração

```powershell
# Passo 4 — inspecionar colunas em uma UF pequena
.\venv\Scripts\python.exe etl\inspect_sample.py --uf AC --nrows 1000

# Passo 5 — validar chave SQ_CANDIDATO e testar merge de amostra
.\venv\Scripts\python.exe etl\validar_merge.py --uf AC --nrows 5000
.\venv\Scripts\python.exe etl\validar_merge.py --base receitas
.\venv\Scripts\python.exe etl\validar_merge.py --base despesas_contratadas

# Passo 7 — exploracao para decidir colunas (nao e o ETL final)
.\venv\Scripts\python.exe etl\01_explore.py
.\venv\Scripts\python.exe etl\01_explore.py --uf AC --nrows 1000
.\venv\Scripts\python.exe etl\01_explore.py --dataset candidatos
```

#### Como testar o passo 7 (`01_explore.py`)

1. Abra o terminal na pasta do projeto (`Big data`).
2. Rode o comando padrao (UF pequena AC, 1000 linhas, candidatos + receitas):

   ```powershell
   .\venv\Scripts\python.exe etl\01_explore.py
   ```

3. **O que conferir no output:**
   - **`.info()`** — quantas colunas existem, tipos e se ha muitos nulos.
   - **`.head()`** — primeiras linhas; confirme acentos e separador corretos.
   - **`DS_GENERO` / `DS_COR_RACA`** — `value_counts` com categorias (ex.: MASCULINO, FEMININO, BRANCA, PARDA).
   - Compare **candidatos** vs **receitas**: genero/raca devem vir da base de candidatos no ETL final.

4. Variacoes uteis:

   ```powershell
   # So candidatos
   .\venv\Scripts\python.exe etl\01_explore.py --dataset candidatos

   # So receitas
   .\venv\Scripts\python.exe etl\01_explore.py --dataset receitas

   # Outra UF ou amostra maior
   .\venv\Scripts\python.exe etl\01_explore.py --uf SP --nrows 2000
   ```

5. **Nao esperar:** este script nao remove CPF, nao faz merge e nao salva arquivo — isso vem no ETL de limpeza.

**Chave de junção:** `SQ_CANDIDATO` existe em candidatos, receitas e despesas contratadas.
`despesas_pagas` usa `SQ_PRESTADOR_CONTAS` — join direto com candidatos não é possível.

## LGPD (passo 6)

Os CSVs do TSE contêm **dados pessoais**: CPF de candidatos, CPF/CNPJ de doadores e
fornecedores, e-mail, data de nascimento e título de eleitor.

**Decisão da equipe:** **remover** essas colunas na fase Transform do ETL, antes de
subir ao banco. O cruzamento entre bases usa `SQ_CANDIDATO`, sem necessidade de CPF.

Detalhes completos: [docs/LGPD.md](docs/LGPD.md)

Colunas afetadas (lista para o ETL): `etl/lgpd_columns.py`

### Documentação para assistentes de IA (Claude, etc.)

Se outra IA vai continuar o projeto, envie primeiro: **[docs/CONTEXTO_PARA_IA.md](docs/CONTEXTO_PARA_IA.md)**

Contém: passos concluídos (1–7), decisões técnicas, checklist do que falta (ETL, Terraform, dashboard) e comandos de verificação.

## Próximos passos

- [x] Configurar ambiente Python
- [x] Inspecionar amostra e validar merge (SQ_CANDIDATO)
- [x] Documentar achados LGPD e decisão de tratamento
- [x] Script de exploração inicial (`01_explore.py`)
- [ ] Configurar pipeline ETL (limpeza e transform)
- [ ] Provisionar infraestrutura com Terraform
- [ ] Desenvolver dashboard
