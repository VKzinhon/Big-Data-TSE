# -*- coding: utf-8 -*-
"""Colunas a remover na fase Transform do ETL. Ver docs/LGPD.md."""

COLUNAS_REMOVER_LGPD = [
    "NR_CPF_CANDIDATO",
    "NR_CPF_VICE_CANDIDATO",
    "NR_CPF_CNPJ_DOADOR",
    "NR_CPF_CNPJ_FORNECEDOR",
    "NR_CNPJ_PRESTADOR_CONTA",
    "DS_EMAIL",
    "DT_NASCIMENTO",
    "NR_TITULO_ELEITORAL_CANDIDATO",
]


def remover_colunas_lgpd(df, inplace: bool = False):
    """Remove colunas sensiveis presentes no DataFrame."""
    cols = [c for c in COLUNAS_REMOVER_LGPD if c in df.columns]
    return df.drop(columns=cols, inplace=inplace)
