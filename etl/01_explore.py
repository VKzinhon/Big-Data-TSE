# -*- coding: utf-8 -*-
"""Exploracao inicial dos dados TSE (passo 7). Nao e o ETL final.

Carrega amostras, imprime .info(), .head() e contagens de DS_GENERO e DS_COR_RACA
para a equipe decidir quais colunas manter antes da limpeza.

Uso:
    python etl/01_explore.py
    python etl/01_explore.py --uf AC --nrows 1000
    python etl/01_explore.py --dataset candidatos
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

READ_OPTS = {"sep": ";", "encoding": "latin-1"}
COLUNAS_CATEGORICAS = ["DS_GENERO", "DS_COR_RACA", "DS_CARGO"]

BASE_DIR = Path(__file__).resolve().parent
DATA_RAW = BASE_DIR / "data_raw"

DATASETS = {
    "candidatos": DATA_RAW / "consulta_cand_2024" / "consulta_cand_2024_{uf}.csv",
    "receitas": (
        DATA_RAW
        / "prestacao_de_contas_eleitorais_candidatos_2024"
        / "receitas_candidatos_2024_{uf}.csv"
    ),
}


def explorar(nome: str, caminho: Path, nrows: int) -> None:
    print("\n" + "=" * 60)
    print(f"DATASET: {nome}")
    print(f"Arquivo: {caminho.name}")
    print("=" * 60)

    df = pd.read_csv(caminho, nrows=nrows, **READ_OPTS)
    print(f"\nShape: {df.shape[0]} linhas x {df.shape[1]} colunas")

    print("\n--- .info() ---")
    df.info()

    print("\n--- .head() ---")
    print(df.head())

    print("\n--- Valores unicos (DS_GENERO, DS_COR_RACA, DS_CARGO) ---")
    for col in COLUNAS_CATEGORICAS:
        if col not in df.columns:
            print(f"\n{col}: coluna ausente neste dataset")
            continue
        n_unicos = df[col].nunique()
        print(f"\n{col} ({n_unicos} valores unicos):")
        print(df[col].value_counts(dropna=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Exploracao inicial TSE passo 7")
    parser.add_argument("--uf", default="AC", help="Sigla da UF (default: AC)")
    parser.add_argument(
        "--nrows",
        type=int,
        default=1000,
        help="Linhas por arquivo (default: 1000)",
    )
    parser.add_argument(
        "--dataset",
        choices=["candidatos", "receitas", "todos"],
        default="todos",
        help="Qual base explorar (default: todos)",
    )
    args = parser.parse_args()

    uf = args.uf.upper()
    print(f"Exploracao | UF={uf} | nrows={args.nrows} | dataset={args.dataset}")

    nomes = list(DATASETS.keys()) if args.dataset == "todos" else [args.dataset]

    for nome in nomes:
        caminho = Path(str(DATASETS[nome]).format(uf=uf))
        if not caminho.exists():
            print(f"\nAVISO: {caminho} nao encontrado, pulando.")
            continue
        explorar(nome, caminho, args.nrows)

    print("\n" + "=" * 60)
    print("Este script NAO limpa nem grava dados.")
    print("Use o output para decidir colunas a manter no ETL.")
    print("Colunas LGPD a remover: etl/lgpd_columns.py | docs/LGPD.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
