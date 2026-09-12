# -*- coding: utf-8 -*-
"""Inspeciona amostra de um CSV do TSE (passo 4).

Uso:
    python etl/inspect_sample.py
    python etl/inspect_sample.py --uf AC --nrows 1000
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

COLUNAS_ESPERADAS = ["DS_GENERO", "DS_COR_RACA", "DS_CARGO", "SQ_CANDIDATO"]
READ_OPTS = {"sep": ";", "encoding": "latin-1"}

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_PADRAO = (
    BASE_DIR / "data_raw" / "consulta_cand_2024" / "consulta_cand_2024_{uf}.csv"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspeciona amostra de candidatos TSE.")
    parser.add_argument("--uf", default="AC", help="Sigla da UF (default: AC)")
    parser.add_argument("--nrows", type=int, default=1000, help="Linhas a ler (default: 1000)")
    args = parser.parse_args()

    arquivo = Path(str(ARQUIVO_PADRAO).format(uf=args.uf.upper()))
    df = pd.read_csv(arquivo, nrows=args.nrows, **READ_OPTS)

    print(f"Arquivo: {arquivo.name}")
    print(f"Shape: {df.shape}")

    print("\nColunas esperadas:")
    for col in COLUNAS_ESPERADAS:
        status = "OK" if col in df.columns else "FALTANDO"
        print(f"  {col}: {status}")

    print(f"\nTodas as colunas ({len(df.columns)}):")
    print(df.columns.tolist())

    presentes = [c for c in COLUNAS_ESPERADAS if c in df.columns]
    print("\nAmostra das colunas-chave:")
    print(df[presentes].head(10))

    print("\nValores distintos (amostra):")
    for col in ["DS_GENERO", "DS_COR_RACA", "DS_CARGO"]:
        if col in df.columns:
            print(f"\n{col}:")
            print(df[col].value_counts().head(10))


if __name__ == "__main__":
    main()
