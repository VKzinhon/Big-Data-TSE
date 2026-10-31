# -*- coding: utf-8 -*-
"""Carrega a base tratada no PostgreSQL (Aiven)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from modelo import COLUNAS_CANDIDATURA, COLUNAS_FINANCIAMENTO, DATA_PROCESSED
from transformar import limitar_idade

DDL_CANDIDATURA = """
CREATE TABLE candidatura (
    sq_candidato BIGINT PRIMARY KEY,
    ano_eleicao INTEGER,
    sg_uf CHAR(2),
    nm_ue TEXT,
    ds_cargo TEXT,
    nm_urna TEXT,
    sg_partido TEXT,
    nm_partido TEXT,
    ds_genero TEXT,
    ds_cor_raca TEXT,
    ds_sit_tot_turno TEXT,
    nr_turno_resultado SMALLINT,
    nr_idade_data_posse SMALLINT
)
"""

DDL_FINANCIAMENTO = """
CREATE TABLE financiamento (
    sq_candidato BIGINT PRIMARY KEY,
    vr_receita NUMERIC(16, 2) NOT NULL,
    vr_despesa_contratada NUMERIC(16, 2) NOT NULL,
    qt_receitas INTEGER NOT NULL,
    qt_despesas INTEGER NOT NULL,
    CONSTRAINT fk_financiamento_candidatura
        FOREIGN KEY (sq_candidato) REFERENCES candidatura (sq_candidato)
)
"""


def url_sqlalchemy(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def para_sql(df: pd.DataFrame) -> pd.DataFrame:
    saida = df.copy()
    for coluna in saida.columns:
        if str(saida[coluna].dtype) == "Int64":
            saida[coluna] = saida[coluna].astype(object).where(saida[coluna].notna(), None)
    return saida


def recriar_tabelas(engine: Engine) -> None:
    with engine.begin() as conexao:
        conexao.execute(text("DROP TABLE IF EXISTS financiamento"))
        conexao.execute(text("DROP TABLE IF EXISTS candidatura"))
        conexao.execute(text(DDL_CANDIDATURA))
        conexao.execute(text(DDL_FINANCIAMENTO))


def carregar(destino: Path, url: str) -> None:
    caminho_cand = destino / "candidatura.parquet"
    caminho_fin = destino / "financiamento.parquet"
    if not caminho_cand.exists() or not caminho_fin.exists():
        raise FileNotFoundError(
            f"Parquet tratado nao encontrado em {destino}. Rode etl/02_transform.py antes."
        )

    candidatura = pd.read_parquet(caminho_cand)
    financiamento = pd.read_parquet(caminho_fin)
    candidatura["nr_idade_data_posse"] = limitar_idade(candidatura["nr_idade_data_posse"])
    faltando_cand = [c for c in COLUNAS_CANDIDATURA if c not in candidatura.columns]
    faltando_fin = [c for c in COLUNAS_FINANCIAMENTO if c not in financiamento.columns]
    if faltando_cand or faltando_fin:
        raise ValueError(f"Parquet incompleto. Candidatura: {faltando_cand}. Financiamento: {faltando_fin}.")

    engine = create_engine(url_sqlalchemy(url), pool_pre_ping=True)
    recriar_tabelas(engine)
    para_sql(candidatura[COLUNAS_CANDIDATURA]).to_sql(
        "candidatura",
        engine,
        if_exists="append",
        index=False,
        chunksize=2000,
    )
    para_sql(financiamento[COLUNAS_FINANCIAMENTO]).to_sql(
        "financiamento",
        engine,
        if_exists="append",
        index=False,
        chunksize=2000,
    )

    with engine.connect() as conexao:
        n_cand = conexao.execute(text("SELECT COUNT(*) FROM candidatura")).scalar_one()
        n_fin = conexao.execute(text("SELECT COUNT(*) FROM financiamento")).scalar_one()
        tamanho = conexao.execute(
            text("SELECT pg_size_pretty(pg_database_size(current_database()))")
        ).scalar_one()
    print(f"candidatura: {n_cand} linhas")
    print(f"financiamento: {n_fin} linhas")
    print(f"tamanho do banco: {tamanho}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Carrega o parquet tratado no PostgreSQL.")
    parser.add_argument(
        "--destino",
        type=Path,
        default=DATA_PROCESSED,
        help="Pasta com candidatura.parquet e financiamento.parquet",
    )
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise SystemExit(
            "Defina DATABASE_URL no arquivo .env com a URI do Terraform "
            "(terraform output -raw postgresql_service_uri)."
        )
    carregar(args.destino, url)


if __name__ == "__main__":
    main()
