# -*- coding: utf-8 -*-
"""Unifica candidatos, receitas e despesas contratadas do TSE 2024.

Grão da saída: uma linha por SQ_CANDIDATO. O dinheiro é somado.
Candidato sem lançamento permanece, com valor 0.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from lgpd_columns import COLUNAS_REMOVER_LGPD, remover_colunas_lgpd
from modelo import (
    ARQUIVO_CANDIDATOS,
    ARQUIVO_DESPESAS,
    ARQUIVO_RECEITAS,
    CANDIDATOS_DIR,
    CHAVE,
    COLUNAS_CANDIDATURA,
    COLUNAS_CATEGORIA_MAIUSCULA,
    COLUNAS_FINANCIAMENTO,
    COLUNAS_TEXTO,
    DATA_PROCESSED,
    DATA_RAW,
    IDADE_MAXIMA,
    PRESTACAO_DIR,
    READ_OPTS,
    RENOMEAR_CANDIDATURA,
    SENTINELAS_NUMERICAS,
    SENTINELAS_TEXTO,
)

CHUNK = 200_000


def normalizar_chave(serie: pd.Series) -> pd.Series:
    texto = serie.astype("string").str.strip()
    texto = texto.replace(SENTINELAS_TEXTO, pd.NA)
    return pd.to_numeric(texto, errors="coerce").astype("Int64")


def para_numero(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(serie) and not pd.api.types.is_object_dtype(serie):
        numero = pd.to_numeric(serie, errors="coerce")
    else:
        texto = serie.astype("string").str.strip()
        texto = texto.str.replace(",", ".", regex=False)
        texto = texto.replace(SENTINELAS_TEXTO, pd.NA)
        numero = pd.to_numeric(texto, errors="coerce")
    return numero.mask(numero.isin(SENTINELAS_NUMERICAS))


def limpar_texto(serie: pd.Series) -> pd.Series:
    texto = serie.astype("string").str.strip()
    return texto.replace(SENTINELAS_TEXTO, pd.NA)


def descobrir_ufs(pasta_candidatos: Path) -> list[str]:
    ufs = []
    for arquivo in sorted(pasta_candidatos.glob("consulta_cand_2024_*.csv")):
        uf = arquivo.stem.removeprefix("consulta_cand_2024_")
        if len(uf) == 2 and uf.isalpha():
            ufs.append(uf.upper())
    return ufs


def exigir_colunas(df: pd.DataFrame, colunas: list[str], arquivo: Path) -> None:
    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise ValueError(
            f"Colunas ausentes em {arquivo.name}: {faltando}. "
            f"Encontradas: {list(df.columns)}"
        )


def agregar_valor(caminho: Path, coluna_valor: str, nrows: int | None) -> tuple[pd.DataFrame, int]:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho}")

    leitor = pd.read_csv(
        caminho,
        nrows=nrows,
        chunksize=CHUNK,
        dtype={CHAVE: "string"},
        usecols=lambda nome: nome in {CHAVE, coluna_valor},
        **READ_OPTS,
    )
    partes: list[pd.DataFrame] = []
    linhas = 0
    for chunk in leitor:
        linhas += len(chunk)
        if chunk.empty:
            continue
        exigir_colunas(chunk, [CHAVE, coluna_valor], caminho)
        frame = pd.DataFrame(
            {
                "sq_candidato": normalizar_chave(chunk[CHAVE]),
                "valor": para_numero(chunk[coluna_valor]),
            }
        )
        frame = frame.dropna(subset=["sq_candidato"])
        if frame.empty:
            continue
        grupo = frame.groupby("sq_candidato", dropna=True).agg(
            soma=("valor", "sum"),
            qtd=("valor", "count"),
        )
        partes.append(grupo)

    if not partes:
        vazio = pd.DataFrame(
            {
                "sq_candidato": pd.Series(dtype="Int64"),
                "soma": pd.Series(dtype="float64"),
                "qtd": pd.Series(dtype="int64"),
            }
        )
        return vazio, linhas

    tudo = pd.concat(partes)
    tudo = tudo.groupby(level=0).agg(soma=("soma", "sum"), qtd=("qtd", "sum")).reset_index()
    tudo["sq_candidato"] = tudo["sq_candidato"].astype("Int64")
    tudo["soma"] = tudo["soma"].round(2)
    tudo["qtd"] = tudo["qtd"].astype("int64")
    return tudo, linhas


def limitar_idade(serie: pd.Series) -> pd.Series:
    """Idade negativa ou acima do limite vira nulo. O limite cobre data de nascimento invalida."""
    idade = para_numero(serie)
    return idade.where((idade >= 0) & (idade <= IDADE_MAXIMA)).round().astype("Int64")


def idade_na_posse(nascimento: pd.Series, ano_eleicao: pd.Series) -> pd.Series:
    """Idade em 1 de janeiro do ano seguinte à eleição. A data de nascimento não é gravada."""
    texto = nascimento.astype("string").str.strip().replace(SENTINELAS_TEXTO, pd.NA)
    datas = pd.to_datetime(texto, dayfirst=True, errors="coerce")
    ano = pd.to_numeric(ano_eleicao, errors="coerce")
    idade = (ano + 1) - datas.dt.year
    aniversario_depois = (datas.dt.month > 1) | ((datas.dt.month == 1) & (datas.dt.day > 1))
    idade = idade.where(~aniversario_depois, idade - 1)
    return idade.where(idade >= 0)


def preparar_candidatos(caminho: Path, nrows: int | None) -> tuple[pd.DataFrame, dict]:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho}")

    bruto = pd.read_csv(caminho, nrows=nrows, dtype={CHAVE: "string"}, **READ_OPTS)
    colunas_fonte = [c for c in RENOMEAR_CANDIDATURA if c != "NR_IDADE_DATA_POSSE"]
    exigir_colunas(bruto, colunas_fonte, caminho)
    if "NR_IDADE_DATA_POSSE" not in bruto.columns:
        if "DT_NASCIMENTO" not in bruto.columns:
            bruto["NR_IDADE_DATA_POSSE"] = pd.NA
        else:
            bruto["NR_IDADE_DATA_POSSE"] = idade_na_posse(
                bruto["DT_NASCIMENTO"], bruto["ANO_ELEICAO"]
            )
    linhas_brutas = len(bruto)

    sensiveis_presentes = [c for c in COLUNAS_REMOVER_LGPD if c in bruto.columns]
    limpo = remover_colunas_lgpd(bruto)
    ainda = [c for c in COLUNAS_REMOVER_LGPD if c in limpo.columns]
    if ainda:
        raise RuntimeError(f"Colunas LGPD permaneceram em {caminho.name}: {ainda}")

    frame = limpo[list(RENOMEAR_CANDIDATURA)].rename(columns=RENOMEAR_CANDIDATURA)
    frame["sq_candidato"] = normalizar_chave(frame["sq_candidato"])
    sem_chave = int(frame["sq_candidato"].isna().sum())
    frame = frame.dropna(subset=["sq_candidato"])

    for coluna in COLUNAS_TEXTO:
        frame[coluna] = limpar_texto(frame[coluna])
    for coluna in COLUNAS_CATEGORIA_MAIUSCULA:
        frame[coluna] = frame[coluna].str.upper()

    frame["ano_eleicao"] = para_numero(frame["ano_eleicao"]).astype("Int64")
    frame["nr_turno_resultado"] = para_numero(frame["nr_turno_resultado"]).astype("Int64")
    frame["nr_idade_data_posse"] = limitar_idade(frame["nr_idade_data_posse"])

    frame = frame.assign(_turno_ord=frame["nr_turno_resultado"].fillna(0))
    frame = frame.sort_values(["sq_candidato", "_turno_ord"], kind="mergesort")
    antes = len(frame)
    frame = frame.drop_duplicates("sq_candidato", keep="last").drop(columns="_turno_ord")
    duplicados_turno = antes - len(frame)

    return frame.reset_index(drop=True), {
        "linhas_brutas": linhas_brutas,
        "sem_chave": sem_chave,
        "duplicados_turno": duplicados_turno,
        "colunas_lgpd_encontradas": sensiveis_presentes,
    }


def _contar_orfaos(agregado: pd.DataFrame, ids_candidatos: set[int]) -> int:
    if agregado.empty:
        return 0
    chaves = agregado["sq_candidato"].astype("int64")
    return int((~chaves.isin(ids_candidatos)).sum())


def processar_uf(data_raw: Path, uf: str, nrows: int | None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    pasta_cand = data_raw / CANDIDATOS_DIR
    pasta_contas = data_raw / PRESTACAO_DIR
    arquivo_cand = pasta_cand / ARQUIVO_CANDIDATOS.format(uf=uf)
    arquivo_rec = pasta_contas / ARQUIVO_RECEITAS.format(uf=uf)
    arquivo_desp = pasta_contas / ARQUIVO_DESPESAS.format(uf=uf)

    print(f"\nUF {uf}")
    candidatos, stats_cand = preparar_candidatos(arquivo_cand, nrows)
    receitas, linhas_rec = agregar_valor(arquivo_rec, "VR_RECEITA", nrows)
    despesas, linhas_desp = agregar_valor(arquivo_desp, "VR_DESPESA_CONTRATADA", nrows)

    ids = set(candidatos["sq_candidato"].dropna().astype("int64"))
    orfaos_receita = _contar_orfaos(receitas, ids)
    orfaos_despesa = _contar_orfaos(despesas, ids)

    receitas = receitas.rename(columns={"soma": "vr_receita", "qtd": "qt_receitas"})
    despesas = despesas.rename(
        columns={"soma": "vr_despesa_contratada", "qtd": "qt_despesas"}
    )
    dinheiro = receitas.merge(despesas, on="sq_candidato", how="outer")
    unido = candidatos.merge(dinheiro, on="sq_candidato", how="left")

    for coluna in ("vr_receita", "vr_despesa_contratada"):
        unido[coluna] = unido[coluna].fillna(0).round(2)
    for coluna in ("qt_receitas", "qt_despesas"):
        unido[coluna] = unido[coluna].fillna(0).astype("int64")

    candidatura = unido[COLUNAS_CANDIDATURA].copy()
    financiamento = unido[COLUNAS_FINANCIAMENTO].copy()

    print(
        f"  candidaturas: {len(candidatura)} | "
        f"receitas lidas: {linhas_rec} | despesas lidas: {linhas_desp}"
    )
    return candidatura, financiamento, {
        "uf": uf,
        "linhas_candidatos_brutas": stats_cand["linhas_brutas"],
        "chaves_invalidas": stats_cand["sem_chave"],
        "linhas_turno_removidas": stats_cand["duplicados_turno"],
        "linhas_receita_brutas": linhas_rec,
        "linhas_despesa_brutas": linhas_desp,
        "receitas_sem_candidato": orfaos_receita,
        "despesas_sem_candidato": orfaos_despesa,
        "colunas_lgpd_encontradas": stats_cand["colunas_lgpd_encontradas"],
    }


def transformar(data_raw: Path, destino: Path, ufs: list[str], nrows: int | None) -> dict:
    if not data_raw.exists():
        raise FileNotFoundError(
            f"Pasta de dados brutos nao encontrada: {data_raw}. "
            "Coloque os CSVs do TSE em etl/data_raw/ (ver README)."
        )

    candidaturas: list[pd.DataFrame] = []
    financiamentos: list[pd.DataFrame] = []
    por_uf: list[dict] = []
    for uf in ufs:
        cand, fin, stats = processar_uf(data_raw, uf, nrows)
        candidaturas.append(cand)
        financiamentos.append(fin)
        por_uf.append(stats)

    candidatura = pd.concat(candidaturas, ignore_index=True)
    financiamento = pd.concat(financiamentos, ignore_index=True)

    repetidos = int(candidatura["sq_candidato"].duplicated().sum())
    if repetidos:
        candidatura = candidatura.drop_duplicates("sq_candidato", keep="first")
        financiamento = financiamento.drop_duplicates("sq_candidato", keep="first")

    candidatura = candidatura.sort_values(["sg_uf", "sq_candidato"], kind="mergesort")
    financiamento = financiamento.set_index("sq_candidato").loc[
        candidatura["sq_candidato"]
    ].reset_index()

    destino.mkdir(parents=True, exist_ok=True)
    caminho_cand = destino / "candidatura.parquet"
    caminho_fin = destino / "financiamento.parquet"
    candidatura.to_parquet(caminho_cand, index=False)
    financiamento.to_parquet(caminho_fin, index=False)

    lgpd = sorted({col for item in por_uf for col in item["colunas_lgpd_encontradas"]})
    manifesto = {
        "origem": "Portal de Dados Abertos do TSE, eleicoes 2024",
        "bases": [
            "consulta_cand_2024",
            "receitas_candidatos_2024",
            "despesas_contratadas_candidatos_2024",
        ],
        "fora_do_cruzamento": "despesas_pagas (chave SQ_PRESTADOR_CONTAS)",
        "grao": "uma linha por SQ_CANDIDATO",
        "ufs": ufs,
        "linhas_candidatura": int(len(candidatura)),
        "linhas_financiamento": int(len(financiamento)),
        "sq_candidato_repetido_entre_ufs": repetidos,
        "candidatos_sem_receita": int((financiamento["vr_receita"] == 0).sum()),
        "candidatos_sem_despesa": int((financiamento["vr_despesa_contratada"] == 0).sum()),
        "colunas_lgpd_removidas_quando_presentes": lgpd,
        "colunas_candidatura": COLUNAS_CANDIDATURA,
        "colunas_financiamento": COLUNAS_FINANCIAMENTO,
        "por_uf": por_uf,
        "arquivos": {
            "candidatura": caminho_cand.name,
            "financiamento": caminho_fin.name,
        },
    }
    (destino / "manifest.json").write_text(
        json.dumps(manifesto, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    print(f"\nCandidaturas: {len(candidatura)}")
    print(f"Financiamento: {len(financiamento)}")
    print(f"Saida: {destino}")
    return manifesto


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trata candidatos e prestacao de contas do TSE 2024."
    )
    parser.add_argument(
        "--data-raw",
        type=Path,
        default=DATA_RAW,
        help="Pasta com os CSVs brutos (default: etl/data_raw)",
    )
    parser.add_argument(
        "--destino",
        type=Path,
        default=DATA_PROCESSED,
        help="Pasta do parquet tratado (default: etl/data_processed)",
    )
    parser.add_argument(
        "--uf",
        nargs="*",
        help="Siglas de UF. Omita para processar todas as encontradas.",
    )
    parser.add_argument(
        "--nrows",
        type=int,
        default=0,
        help="Limite de linhas por arquivo (0 = arquivo inteiro)",
    )
    args = parser.parse_args()

    data_raw = args.data_raw
    pasta_cand = data_raw / CANDIDATOS_DIR
    if args.uf:
        ufs = [uf.upper() for uf in args.uf]
    else:
        ufs = descobrir_ufs(pasta_cand)
    if not ufs:
        raise SystemExit(f"Nenhum CSV de candidatos em {pasta_cand}")

    nrows = None if args.nrows == 0 else args.nrows
    print(f"UFs: {', '.join(ufs)} | nrows: {nrows or 'todas'}")
    transformar(data_raw, args.destino, ufs, nrows)


if __name__ == "__main__":
    main()
