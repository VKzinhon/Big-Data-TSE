# LGPD — dados pessoais nas bases do TSE

Os CSVs públicos de candidatura e prestação de contas de 2024 trazem identificadores que não são necessários para a pergunta do projeto (quem se candidata e como o dinheiro se distribui por gênero, raça e cargo).

## Decisão

Remover esses campos na transformação, antes de gravar o parquet e antes de subir ao PostgreSQL. O cruzamento usa `SQ_CANDIDATO`, identificador da candidatura publicado pelo TSE, sem CPF.

| Coluna | Onde aparece | Motivo |
|---|---|---|
| `NR_CPF_CANDIDATO` | Candidatos | CPF do candidato |
| `NR_CPF_VICE_CANDIDATO` | Candidatos | CPF do vice |
| `NR_TITULO_ELEITORAL_CANDIDATO` | Candidatos | Título de eleitor |
| `DS_EMAIL` | Candidatos | Contato pessoal |
| `DT_NASCIMENTO` | Candidatos | Data de nascimento |
| `NR_CPF_CNPJ_DOADOR` | Receitas | CPF ou CNPJ de quem doou |
| `NM_DOADOR`, `NM_DOADOR_RFB` | Receitas | Nome de quem doou |
| `NR_CPF_CNPJ_FORNECEDOR` | Despesas | CPF ou CNPJ do fornecedor |
| `NM_FORNECEDOR`, `NM_FORNECEDOR_RFB` | Despesas | Nome do fornecedor |
| `NR_CNPJ_PRESTADOR_CONTA` | Prestação de contas | CNPJ do prestador |

A lista usada pelo código está em `etl/lgpd_columns.py`.

## O que permanece

O nome de urna (`NM_URNA_CANDIDATO`) permanece. É o nome público da campanha e a métrica de representatividade não depende do nome civil. A idade na data da posse (`NR_IDADE_DATA_POSSE`) permanece no lugar da data de nascimento, para o recorte de faixa etária.

Receitas e despesas são lidas só com a chave e o valor. Nome e documento de doador ou fornecedor não entram no DataFrame. A saída soma os valores por candidatura, então o microdado do lançamento também não é armazenado.

## Base legal de trabalho

Fonte: Portal de Dados Abertos do TSE. Uso acadêmico, com minimização dos identificadores antes do armazenamento em nuvem.
