# -*- coding: utf-8 -*-
"""Confere o tratamento com CSVs sinteticos no formato do TSE."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from lgpd_columns import COLUNAS_REMOVER_LGPD
from transformar import transformar

BASE = Path(__file__).resolve().parent
DESTINO = BASE / "data_processed_fixture"


def main() -> None:
    if DESTINO.exists():
        shutil.rmtree(DESTINO)

    manifesto = transformar(BASE / "fixtures", DESTINO, ["AC"], None)
    candidatura = pd.read_parquet(DESTINO / "candidatura.parquet")
    financiamento = pd.read_parquet(DESTINO / "financiamento.parquet")

    assert list(candidatura["sq_candidato"]) == [1001, 1002, 1003]
    assert len(financiamento) == 3
    assert not any(coluna in candidatura.columns for coluna in COLUNAS_REMOVER_LGPD)

    linha_1001 = candidatura.set_index("sq_candidato").loc[1001]
    dinheiro_1001 = financiamento.set_index("sq_candidato").loc[1001]
    assert linha_1001["ds_sit_tot_turno"] == "ELEITO"
    assert int(linha_1001["nr_turno_resultado"]) == 2
    assert linha_1001["nm_urna"] == "URNA UM"
    assert float(dinheiro_1001["vr_receita"]) == 30.5
    assert float(dinheiro_1001["vr_despesa_contratada"]) == 3.0
    assert int(dinheiro_1001["qt_receitas"]) == 2

    linha_1002 = candidatura.set_index("sq_candidato").loc[1002]
    dinheiro_1002 = financiamento.set_index("sq_candidato").loc[1002]
    assert pd.isna(linha_1002["nr_idade_data_posse"])
    assert linha_1002["ds_genero"] == "FEMININO"
    assert linha_1002["ds_cor_raca"] == "PARDA"
    assert float(dinheiro_1002["vr_receita"]) == 0.0
    assert int(dinheiro_1002["qt_receitas"]) == 0

    dinheiro_1003 = financiamento.set_index("sq_candidato").loc[1003]
    assert float(dinheiro_1003["vr_receita"]) == 5.0
    assert float(dinheiro_1003["vr_despesa_contratada"]) == 7.5

    assert manifesto["por_uf"][0]["receitas_sem_candidato"] == 1
    assert manifesto["linhas_candidatura"] == 3
    print("Fixture OK: 3 candidaturas, turno 2 preservado, zeros e LGPD conferidos.")


if __name__ == "__main__":
    main()
