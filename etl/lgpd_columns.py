# -*- coding: utf-8 -*-
"""Colunas a remover na fase Transform do ETL. Ver docs/LGPD.md."""

from __future__ import annotations

import pandas as pd

COLUNAS_REMOVER_LGPD = [
    "NR_CPF_CANDIDATO",
    "NR_CPF_VICE_CANDIDATO",
    "NR_CPF_CNPJ_DOADOR",
    "NR_CPF_CNPJ_FORNECEDOR",
    "NR_CNPJ_PRESTADOR_CONTA",
    "NM_DOADOR",
    "NM_DOADOR_RFB",
    "NM_FORNECEDOR",
    "NM_FORNECEDOR_RFB",
    "DS_EMAIL",
    "DT_NASCIMENTO",
    "NR_TITULO_ELEITORAL_CANDIDATO",
]


def remover_colunas_lgpd(df: pd.DataFrame) -> pd.DataFrame:
    """Devolve uma copia sem as colunas sensiveis que existirem no DataFrame."""
    cols = [c for c in COLUNAS_REMOVER_LGPD if c in df.columns]
    return df.drop(columns=cols)
