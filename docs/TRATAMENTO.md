# Tratamento, modelagem e armazenamento

Entrega da fase 2: base tratada, processo que a produz e modelo pronto para o PostgreSQL na Aiven.

Tema: representatividade política e financiamento eleitoral nas eleições de 2024. A pergunta compara o perfil de quem concorre (gênero, raça, cargo, partido, UF) com o dinheiro declarado na prestação de contas.

## Origem e versão original

| Item | Valor |
|---|---|
| Fonte | Portal de Dados Abertos do TSE |
| Pleito | Eleições 2024 |
| Candidatos | `consulta_cand_2024/consulta_cand_2024_{UF}.csv` |
| Receitas | `prestacao_de_contas_eleitorais_candidatos_2024/receitas_candidatos_2024_{UF}.csv` |
| Despesas contratadas | `prestacao_de_contas_eleitorais_candidatos_2024/despesas_contratadas_candidatos_2024_{UF}.csv` |
| Formato | CSV, separador `;`, encoding `latin-1` |
| Versão no Git | Os CSVs brutos ficam em `etl/data_raw/` e não são versionados, pelo tamanho |

`despesas_pagas` fica de fora. Nessa base a chave é `SQ_PRESTADOR_CONTAS`, e o join direto com a candidatura não fecha.

## Versão resultante

O script `etl/02_transform.py` grava:

- `etl/data_processed/candidatura.parquet`
- `etl/data_processed/financiamento.parquet`
- `etl/data_processed/manifest.json` com contagens por UF

O grão é **uma linha por `SQ_CANDIDATO`**. As duas tabelas têm a mesma quantidade de linhas. O parquet também fica fora do Git. Quem clona o repositório regenera a base rodando o script sobre os CSVs.

## Decisões de tratamento

1. **Chave em texto na leitura, inteiro na saída.** `SQ_CANDIDATO` entra com `dtype=str` e só depois vira número. Isso evita o pandas promover a coluna a float e alterar o identificador.
2. **Uma linha por candidatura.** Prefeito de segundo turno aparece duas vezes em `consulta_cand`. O script ordena por `NR_TURNO` e mantém o maior turno, que é o resultado final.
3. **Dinheiro somado, não linha a linha.** `VR_RECEITA` e `VR_DESPESA_CONTRATADA` são convertidos para número (vírgula decimal aceita), somados por candidato e arredondados em centavos. A quantidade de lançamentos fica em `qt_receitas` e `qt_despesas`.
4. **Quem não movimentou dinheiro permanece.** O join parte da candidatura (left join) e preenche ausência com 0. Tirar esses registros distorceria a comparação entre percentual de candidaturas e percentual do recurso.
5. **Lançamento sem candidatura na UF não entra na base.** A contagem vai para o `manifest.json` (`receitas_sem_candidato`, `despesas_sem_candidato`).
6. **Marcadores do TSE viram nulo.** `#NULO#`, `#NULO`, `#NE#`, `#NE` e `-1` nas colunas de texto. Idade negativa ou nula não vira zero.
7. **Categorias em maiúsculas.** Gênero, raça, cargo, partido, UF, situação e resultado, para o mesmo rótulo não se partir em dois.
8. **Situação da candidatura não é filtro desta fase.** `ds_situacao_candidatura` fica na tabela. O recorte "apenas aptos" é regra de análise da fase seguinte, e apagar o registro agora impediria essa escolha.
9. **LGPD antes de gravar.** Colunas de CPF, CNPJ, e-mail, título, nascimento e nome de doador ou fornecedor são removidas. Detalhe em [LGPD.md](LGPD.md).
10. **Leitura em blocos na prestação de contas.** Receitas e despesas são agregadas em chunks de 200 mil linhas. A base analítica cabe no disco de 1 GB do plano gratuito. O microdado bruto, não.

Pandas, e não PySpark: depois da agregação por UF o volume é uma linha por candidatura. A leitura em chunks cobre o requisito de processamento em lote sem um cluster.

## Modelo relacional

PostgreSQL na Aiven, plano `free-1` (1 GB). Relacional porque o grão é tabular, a chave é estável e a análise cruza dimensões com totais. Banco documental não acrescenta nada a esse grão.

```text
candidatura 1 --- 1 financiamento
   sq_candidato        sq_candidato (PK e FK)
```

Não há tabela de lançamento. Cada doação deixaria de caber no plano gratuito e responderia outra pergunta (quem doou), que exigiria guardar dado pessoal.

### candidatura

| Coluna | Tipo | Origem |
|---|---|---|
| `sq_candidato` | `BIGINT` PK | `SQ_CANDIDATO` |
| `ano_eleicao` | `INTEGER` | `ANO_ELEICAO` |
| `sg_uf` | `CHAR(2)` | `SG_UF` |
| `nm_ue` | `TEXT` | `NM_UE` (município) |
| `ds_cargo` | `TEXT` | `DS_CARGO` |
| `nm_urna` | `TEXT` | `NM_URNA_CANDIDATO` |
| `sg_partido` | `TEXT` | `SG_PARTIDO` |
| `nm_partido` | `TEXT` | `NM_PARTIDO` |
| `ds_genero` | `TEXT` | `DS_GENERO` |
| `ds_cor_raca` | `TEXT` | `DS_COR_RACA` |
| `ds_situacao_candidatura` | `TEXT` | `DS_SITUACAO_CANDIDATURA` |
| `ds_sit_tot_turno` | `TEXT` | `DS_SIT_TOT_TURNO` |
| `nr_turno_resultado` | `SMALLINT` | maior `NR_TURNO` mantido |
| `nr_idade_data_posse` | `SMALLINT` | `NR_IDADE_DATA_POSSE` quando o arquivo traz a coluna. No layout de 2024 ela não vem em `consulta_cand`; a idade é calculada em 1º de janeiro do ano seguinte à eleição a partir de `DT_NASCIMENTO`, e a data é descartada em seguida |

### financiamento

| Coluna | Tipo | Origem |
|---|---|---|
| `sq_candidato` | `BIGINT` PK/FK | candidatura |
| `vr_receita` | `NUMERIC(16,2)` | soma de `VR_RECEITA` |
| `vr_despesa_contratada` | `NUMERIC(16,2)` | soma de `VR_DESPESA_CONTRATADA` |
| `qt_receitas` | `INTEGER` | lançamentos de receita |
| `qt_despesas` | `INTEGER` | lançamentos de despesa |

## Como reproduzir

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Conferencia com dados sinteticos (nao sao os microdados oficiais)
.\venv\Scripts\python.exe etl\verificar_fixture.py

# Base oficial: CSVs em etl/data_raw/
.\venv\Scripts\python.exe etl\02_transform.py --uf AC
.\venv\Scripts\python.exe etl\02_transform.py
```

Infraestrutura, só depois da conta Aiven e de um token pessoal:

```powershell
copy terraform\terraform.tfvars.example terraform\terraform.tfvars
# edite o token e o nome do projeto; esse arquivo nao entra no Git

cd terraform
terraform init
terraform plan
terraform apply
terraform output -raw postgresql_service_uri
```

Cole a URI em `.env` na raiz do projeto (`DATABASE_URL=...`). O arquivo `.env` não entra no Git.

```powershell
.\venv\Scripts\python.exe etl\03_load.py
```

A carga apaga e recria `candidatura` e `financiamento`, então rodar de novo substitui os dados. O script imprime a contagem de linhas e o tamanho do banco. Esses dois números fecham o item de volume da entrega. O plano gratuito limita o disco a 1 GB e as conexões a 20.

## O que esta fase não faz

Não calcula o percentual de candidaturas contra o percentual do dinheiro, nem publica o dashboard. As colunas de gênero, raça, cargo, UF e os totais ficam prontos para essa regra na fase seguinte.
