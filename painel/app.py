# -*- coding: utf-8 -*-
"""Painel local: abre no navegador e lê o PostgreSQL da Aiven.

Uso, na raiz do projeto:
    python -m streamlit run painel/app.py
"""

from __future__ import annotations

import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent

ORDEM_GENERO = ["FEMININO", "MASCULINO", "NÃO DIVULGÁVEL"]
ORDEM_RACA = [
    "BRANCA",
    "PARDA",
    "PRETA",
    "AMARELA",
    "INDÍGENA",
    "NÃO INFORMADO",
    "NÃO DIVULGÁVEL",
]
ORDEM_CARGO = ["VEREADOR", "PREFEITO", "VICE-PREFEITO"]

DINHEIRO = {
    "Receita": "vr_receita",
    "Despesa contratada": "vr_despesa_contratada",
}

CORES = alt.Scale(
    domain=["Candidaturas", "Dinheiro"],
    range=["#4C78A8", "#F58518"],
)


def url_sqlalchemy(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def inteiro(valor: float) -> str:
    return f"{int(valor):,}".replace(",", ".")


def reais(valor: float) -> str:
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


@st.cache_resource
def conectar():
    load_dotenv(ROOT / ".env")
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL ausente")
    return create_engine(url_sqlalchemy(url), pool_pre_ping=True)


@st.cache_data(ttl=300, show_spinner="Lendo o banco...")
def base(cargo: str, coluna_dinheiro: str) -> pd.DataFrame:
    if coluna_dinheiro not in DINHEIRO.values():
        raise ValueError(coluna_dinheiro)
    filtro = ""
    params: dict = {}
    if cargo != "Todos":
        filtro = "WHERE c.ds_cargo = :cargo"
        params["cargo"] = cargo
    sql = f"""
        SELECT c.sg_uf, c.ds_cargo, c.ds_genero, c.ds_cor_raca,
               COUNT(*) AS candidaturas,
               COALESCE(SUM(f.{coluna_dinheiro}), 0) AS dinheiro
        FROM candidatura c
        JOIN financiamento f ON f.sq_candidato = c.sq_candidato
        {filtro}
        GROUP BY c.sg_uf, c.ds_cargo, c.ds_genero, c.ds_cor_raca
    """
    with conectar().connect() as conexao:
        return pd.read_sql(text(sql), conexao, params=params)


def comparar(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    grupo = (
        df.groupby(coluna, dropna=False)
        .agg(candidaturas=("candidaturas", "sum"), dinheiro=("dinheiro", "sum"))
        .reset_index()
    )
    grupo[coluna] = grupo[coluna].astype("string").fillna("SEM INFORMACAO")
    total_candidaturas = float(grupo["candidaturas"].sum())
    total_dinheiro = float(grupo["dinheiro"].sum())
    grupo["pct_candidaturas"] = (
        grupo["candidaturas"] / total_candidaturas * 100 if total_candidaturas else 0
    )
    grupo["pct_dinheiro"] = grupo["dinheiro"] / total_dinheiro * 100 if total_dinheiro else 0
    grupo["diferenca"] = grupo["pct_dinheiro"] - grupo["pct_candidaturas"]
    return grupo


def ordenar(grupo: pd.DataFrame, coluna: str, ordem: list[str]) -> pd.DataFrame:
    rank = {nome: i for i, nome in enumerate(ordem)}
    saida = grupo.copy()
    saida["_ord"] = saida[coluna].map(lambda nome: rank.get(nome, len(ordem)))
    return saida.sort_values(["_ord", coluna]).drop(columns="_ord")


def grafico(grupo: pd.DataFrame, coluna: str, titulo: str) -> alt.Chart:
    longo = grupo.melt(
        id_vars=[coluna],
        value_vars=["pct_candidaturas", "pct_dinheiro"],
        var_name="serie",
        value_name="percentual",
    )
    longo["serie"] = longo["serie"].map(
        {"pct_candidaturas": "Candidaturas", "pct_dinheiro": "Dinheiro"}
    )
    return (
        alt.Chart(longo)
        .mark_bar()
        .encode(
            y=alt.Y(f"{coluna}:N", title=None, sort=list(grupo[coluna])),
            x=alt.X("percentual:Q", title="% do total"),
            color=alt.Color("serie:N", title=None, scale=CORES),
            yOffset="serie:N",
            tooltip=[
                alt.Tooltip(f"{coluna}:N", title="Grupo"),
                alt.Tooltip("serie:N", title="Série"),
                alt.Tooltip("percentual:Q", title="%", format=".1f"),
            ],
        )
        .properties(title=titulo, height=46 * max(len(grupo), 1) + 30)
    )


def ponto(valor: float, casas: int, sinal: bool = False) -> str:
    texto = f"{valor:+.{casas}f}" if sinal else f"{valor:.{casas}f}"
    return texto.replace(".", ",")


def tabela(grupo: pd.DataFrame, coluna: str, titulo: str, rotulo_dinheiro: str) -> None:
    view = pd.DataFrame(
        {
            titulo: grupo[coluna],
            "Candidaturas": grupo["candidaturas"].map(inteiro),
            rotulo_dinheiro: grupo["dinheiro"].map(reais),
            "% candidaturas": grupo["pct_candidaturas"].map(lambda valor: ponto(valor, 1)),
            "% dinheiro": grupo["pct_dinheiro"].map(lambda valor: ponto(valor, 1)),
            "Diferença (p.p.)": grupo["diferenca"].map(lambda valor: ponto(valor, 1, sinal=True)),
        }
    )
    st.dataframe(view, hide_index=True, width="stretch")


def main() -> None:
    st.set_page_config(
        page_title="Representatividade e financiamento 2024",
        layout="wide",
    )
    st.title("Representatividade política e financiamento eleitoral")
    st.caption(
        "Eleições municipais de 2024. Cada barra compara a fatia das candidaturas "
        "com a fatia do dinheiro declarado. Azul é gente. Laranja é recurso."
    )

    filtro_cargo, filtro_dinheiro = st.columns(2)
    with filtro_cargo:
        cargo = st.selectbox("Cargo", ["Todos", *ORDEM_CARGO])
    with filtro_dinheiro:
        rotulo_dinheiro = st.selectbox("Dinheiro", list(DINHEIRO))

    try:
        df = base(cargo, DINHEIRO[rotulo_dinheiro])
    except Exception:
        st.error(
            "O banco não respondeu. Na Aiven, o serviço precisa estar Running, "
            "e o arquivo .env precisa estar na raiz do projeto."
        )
        st.stop()

    if df.empty:
        st.warning("A consulta não voltou linhas para esse recorte.")
        st.stop()

    total_candidaturas = float(df["candidaturas"].sum())
    total_dinheiro = float(df["dinheiro"].sum())
    m1, m2, m3 = st.columns(3)
    m1.metric("Candidaturas", inteiro(total_candidaturas))
    m2.metric(rotulo_dinheiro, reais(total_dinheiro))
    m3.metric("UFs", inteiro(df["sg_uf"].nunique()))

    genero = ordenar(comparar(df, "ds_genero"), "ds_genero", ORDEM_GENERO)
    raca = ordenar(comparar(df, "ds_cor_raca"), "ds_cor_raca", ORDEM_RACA)

    st.altair_chart(grafico(genero, "ds_genero", "Gênero"), width="stretch")
    st.altair_chart(grafico(raca, "ds_cor_raca", "Raça"), width="stretch")

    if cargo == "Todos":
        por_cargo = ordenar(comparar(df, "ds_cargo"), "ds_cargo", ORDEM_CARGO)
        st.altair_chart(grafico(por_cargo, "ds_cargo", "Cargo"), width="stretch")
        st.info(
            "Vice-prefeito aparece com quase nenhum dinheiro. "
            "A prestação da chapa costuma ser lançada no candidato a prefeito."
        )

    st.subheader("Números do recorte")
    st.caption(
        "A diferença é a fatia do dinheiro menos a fatia das candidaturas, em pontos percentuais. "
        "Negativo: o grupo concorre mais do que recebe."
    )
    esquerda, direita = st.columns(2)
    with esquerda:
        tabela(genero, "ds_genero", "Gênero", rotulo_dinheiro)
    with direita:
        tabela(raca, "ds_cor_raca", "Raça", rotulo_dinheiro)

    st.caption("Fonte: Portal de Dados Abertos do TSE, eleições 2024. O painel lê o PostgreSQL na Aiven.")


if __name__ == "__main__":
    main()
else:
    main()
