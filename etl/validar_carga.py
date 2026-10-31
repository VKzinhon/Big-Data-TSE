# -*- coding: utf-8 -*-
"""Confere a carga no PostgreSQL: volume, chave, idade e a tabela perfil.

Uso, na raiz do projeto, com o servico da Aiven em Running:
    python etl/validar_carga.py
"""

from __future__ import annotations

import sys

from sqlalchemy import text

from carregar import engine_do_env


def main() -> None:
    engine = engine_do_env()
    with engine.connect() as conexao:
        tabelas = conexao.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY 1
                """
            )
        ).scalars().all()
        print("tabelas:", ", ".join(tabelas))
        for nome in ("candidatura", "financiamento", "perfil"):
            if nome not in tabelas:
                print(f"FALTA a tabela {nome}")
                sys.exit(1)

        n_cand = conexao.execute(text("SELECT COUNT(*) FROM candidatura")).scalar_one()
        n_fin = conexao.execute(text("SELECT COUNT(*) FROM financiamento")).scalar_one()
        n_perfil = conexao.execute(text("SELECT COUNT(*) FROM perfil")).scalar_one()
        orfaos = conexao.execute(
            text(
                """
                SELECT COUNT(*)
                FROM financiamento f
                LEFT JOIN candidatura c ON c.sq_candidato = f.sq_candidato
                WHERE c.sq_candidato IS NULL
                """
            )
        ).scalar_one()
        idade = conexao.execute(
            text(
                """
                SELECT
                    COUNT(*) FILTER (WHERE nr_idade_data_posse IS NULL),
                    COUNT(*) FILTER (WHERE nr_idade_data_posse > 120),
                    COUNT(*) FILTER (WHERE nr_idade_data_posse < 0),
                    MIN(nr_idade_data_posse),
                    MAX(nr_idade_data_posse)
                FROM candidatura
                """
            )
        ).one()
        totais = conexao.execute(
            text(
                """
                SELECT
                    (SELECT ROUND(SUM(vr_receita), 2) FROM financiamento),
                    (SELECT ROUND(SUM(vr_receita), 2) FROM perfil),
                    (SELECT ROUND(SUM(vr_despesa_contratada), 2) FROM financiamento),
                    (SELECT ROUND(SUM(vr_despesa_contratada), 2) FROM perfil),
                    (SELECT SUM(qt_candidaturas) FROM perfil)
                """
            )
        ).one()
        tamanho = conexao.execute(
            text("SELECT pg_size_pretty(pg_database_size(current_database()))")
        ).scalar_one()

    print(f"candidatura: {n_cand}")
    print(f"financiamento: {n_fin}")
    print(f"perfil: {n_perfil}")
    print(f"financiamento sem candidatura: {orfaos}")
    print(
        "idade nulos/acima de 120/negativas/min/max: "
        f"{idade[0]}/{idade[1]}/{idade[2]}/{idade[3]}/{idade[4]}"
    )
    print(f"receita candidatura=perfil: {totais[0]} = {totais[1]}")
    print(f"despesa candidatura=perfil: {totais[2]} = {totais[3]}")
    print(f"candidaturas somadas no perfil: {totais[4]}")
    print(f"tamanho: {tamanho}")

    erros = []
    if n_cand != n_fin:
        erros.append("candidatura e financiamento tem quantidades diferentes")
    if orfaos:
        erros.append("ha financiamento sem candidatura")
    if idade[1] or idade[2]:
        erros.append("ha idade impossivel")
    if totais[0] != totais[1] or totais[2] != totais[3]:
        erros.append("a soma do perfil nao fecha com o financiamento")
    if totais[4] != n_cand:
        erros.append("o perfil nao cobre todas as candidaturas")
    if erros:
        for erro in erros:
            print("FALHA:", erro)
        sys.exit(1)
    print("Carga conferida.")


if __name__ == "__main__":
    main()
