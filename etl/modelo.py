# -*- coding: utf-8 -*-
"""Contrato da base tratada: nomes, tipos e caminhos."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_RAW = BASE_DIR / "data_raw"
DATA_PROCESSED = BASE_DIR / "data_processed"

CANDIDATOS_DIR = "consulta_cand_2024"
PRESTACAO_DIR = "prestacao_de_contas_eleitorais_candidatos_2024"

ARQUIVO_CANDIDATOS = "consulta_cand_2024_{uf}.csv"
ARQUIVO_RECEITAS = "receitas_candidatos_2024_{uf}.csv"
ARQUIVO_DESPESAS = "despesas_contratadas_candidatos_2024_{uf}.csv"

CHAVE = "SQ_CANDIDATO"
READ_OPTS = {"sep": ";", "encoding": "latin-1"}

SENTINELAS_TEXTO = ["#NULO#", "#NULO", "#NE#", "#NE", "-1", "-3", "-4"]
SENTINELAS_NUMERICAS = [-1, -3, -4]

# Idade acima disso vem de data de nascimento invalida na fonte e vira nulo.
IDADE_MAXIMA = 120

RENOMEAR_CANDIDATURA = {
    "SQ_CANDIDATO": "sq_candidato",
    "ANO_ELEICAO": "ano_eleicao",
    "SG_UF": "sg_uf",
    "NM_UE": "nm_ue",
    "DS_CARGO": "ds_cargo",
    "NM_URNA_CANDIDATO": "nm_urna",
    "SG_PARTIDO": "sg_partido",
    "NM_PARTIDO": "nm_partido",
    "DS_GENERO": "ds_genero",
    "DS_COR_RACA": "ds_cor_raca",
    "DS_SIT_TOT_TURNO": "ds_sit_tot_turno",
    "NR_TURNO": "nr_turno_resultado",
    "NR_IDADE_DATA_POSSE": "nr_idade_data_posse",
}

COLUNAS_CANDIDATURA = list(RENOMEAR_CANDIDATURA.values())

COLUNAS_FINANCIAMENTO = [
    "sq_candidato",
    "vr_receita",
    "vr_despesa_contratada",
    "qt_receitas",
    "qt_despesas",
]

COLUNAS_TEXTO = [
    "sg_uf",
    "nm_ue",
    "ds_cargo",
    "nm_urna",
    "sg_partido",
    "nm_partido",
    "ds_genero",
    "ds_cor_raca",
    "ds_sit_tot_turno",
]

COLUNAS_CATEGORIA_MAIUSCULA = [
    "sg_uf",
    "ds_cargo",
    "sg_partido",
    "ds_genero",
    "ds_cor_raca",
    "ds_sit_tot_turno",
]
