# -*- coding: utf-8 -*-
"""Valida SQ_CANDIDATO entre candidatos e prestacao de contas (mesma UF).

Uso:
    python etl/validar_merge.py
    python etl/validar_merge.py --uf AC --nrows 5000
    python etl/validar_merge.py --base receitas
    python etl/validar_merge.py --base despesas_contratadas
    python etl/validar_merge.py --base ambas
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

CHAVE = "SQ_CANDIDATO"
READ_OPTS = {"sep": ";", "encoding": "latin-1"}

BASE_DIR = Path(__file__).resolve().parent
DATA_RAW = BASE_DIR / "data_raw"

CANDIDATOS_DIR = DATA_RAW / "consulta_cand_2024"
PRESTACAO_DIR = DATA_RAW / "prestacao_de_contas_eleitorais_candidatos_2024"

BASES_PRESTACAO = {
    "receitas": "receitas_candidatos_2024_{uf}.csv",
    "despesas_contratadas": "despesas_contratadas_candidatos_2024_{uf}.csv",
}


def carregar_csv(caminho: Path, nrows: int | None) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho}")
    return pd.read_csv(caminho, nrows=nrows, **READ_OPTS)


def normalizar_chave(df: pd.DataFrame, coluna: str) -> pd.Series:
    return pd.to_numeric(df[coluna], errors="coerce").astype("Int64")


def validar_coluna(nome_base: str, df: pd.DataFrame) -> None:
    print(f"\n--- {nome_base} ---")
    existe = CHAVE in df.columns
    print(f"  Coluna {CHAVE} existe? {'Sim' if existe else 'NAO'}")
    if not existe:
        print(f"  Colunas disponiveis (amostra): {list(df.columns[:8])} ...")
        return

    serie = normalizar_chave(df, CHAVE)
    nulos = int(serie.isna().sum())
    print(f"  dtype apos normalizacao: {serie.dtype}")
    print(f"  nulos/invalidos: {nulos} ({nulos / len(df) * 100:.1f}%)")
    print(f"  valores unicos: {serie.nunique()}")
    print(f"  amostra: {serie.dropna().head(3).tolist()}")


def validar_merge(
    cand: pd.DataFrame,
    contas: pd.DataFrame,
    nome_contas: str,
) -> pd.DataFrame:
    print(f"\n=== Merge: candidatos x {nome_contas} ===")

    if CHAVE not in cand.columns or CHAVE not in contas.columns:
        print("  ABORTADO: SQ_CANDIDATO ausente em uma das bases.")
        return pd.DataFrame()

    cand_ids = normalizar_chave(cand, CHAVE)
    contas_ids = normalizar_chave(contas, CHAVE)

    cand_tmp = cand.copy()
    contas_tmp = contas.copy()
    cand_tmp[CHAVE] = cand_ids
    contas_tmp[CHAVE] = contas_ids

    merged = cand_tmp.merge(contas_tmp, on=CHAVE, how="inner", suffixes=("_cand", "_contas"))

    cand_unicos = cand_ids.dropna().unique()
    contas_unicos = contas_ids.dropna().unique()
    em_ambos = len(set(cand_unicos) & set(contas_unicos))

    print(f"  Linhas candidatos (amostra): {len(cand)}")
    print(f"  Linhas prestacao (amostra):  {len(contas)}")
    print(f"  Linhas apos merge (inner):   {len(merged)}")
    print(f"  Candidatos unicos na amostra: {len(cand_unicos)}")
    print(f"  IDs em ambas as bases:        {em_ambos}")
    if len(cand_unicos):
        print(f"  % candidatos com match:       {em_ambos / len(cand_unicos) * 100:.1f}%")

    if merged.empty:
        print("  ATENCAO: merge retornou 0 linhas - verifique tipos ou arquivos da UF.")
        return merged

    colunas_demo = [
        CHAVE,
        "NM_CANDIDATO_cand",
        "NM_CANDIDATO",
        "DS_CARGO_cand",
        "DS_CARGO",
        "DS_GENERO",
        "DS_COR_RACA",
        "VR_RECEITA",
        "VR_DESPESA_CONTRATADA",
    ]
    colunas_demo = list(dict.fromkeys(c for c in colunas_demo if c in merged.columns))
    print("\n  Amostra do cruzamento:")
    print(merged[colunas_demo].head(5).to_string(index=False))

    return merged


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valida SQ_CANDIDATO entre candidatos e prestacao de contas."
    )
    parser.add_argument("--uf", default="AC", help="Sigla da UF (default: AC)")
    parser.add_argument(
        "--nrows",
        type=int,
        default=5000,
        help="Linhas por arquivo (default: 5000; use 0 para arquivo inteiro)",
    )
    parser.add_argument(
        "--base",
        choices=["receitas", "despesas_contratadas", "ambas"],
        default="ambas",
        help="Base de prestacao de contas para testar (default: ambas)",
    )
    args = parser.parse_args()

    nrows = None if args.nrows == 0 else args.nrows
    uf = args.uf.upper()

    arquivo_cand = CANDIDATOS_DIR / f"consulta_cand_2024_{uf}.csv"
    print(f"UF: {uf} | nrows: {nrows or 'todas'}")
    print(f"Candidatos: {arquivo_cand.name}")

    cand = carregar_csv(arquivo_cand, nrows)

    print("\n=== 1) Coluna e preenchimento ===")
    validar_coluna("candidatos", cand)

    bases = list(BASES_PRESTACAO.keys()) if args.base == "ambas" else [args.base]

    for nome_base in bases:
        padrao = BASES_PRESTACAO[nome_base]
        arquivo_contas = PRESTACAO_DIR / padrao.format(uf=uf)
        print(f"\nPrestacao: {arquivo_contas.name}")
        contas = carregar_csv(arquivo_contas, nrows)
        validar_coluna(nome_base, contas)
        validar_merge(cand, contas, nome_base)

    print("\n=== Observacao ===")
    print(
        "  despesas_pagas_*.csv NAO possui SQ_CANDIDATO "
        "(usa SQ_PRESTADOR_CONTAS). Join direto nao e possivel."
    )


if __name__ == "__main__":
    main()
