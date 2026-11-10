"""Coleta no OBIS e carga do extrato agregado.

Fonte: OBIS, Ocean Biodiversity Information System (https://obis.org), API v3.
A coleta usa só pontos de acesso agregados (contagens por área), então nenhum registro individual
de ocorrência é redistribuído aqui.

Recorte: a área "Brazil: all" do OBIS (a Zona Econômica Exclusiva do Brasil, com as ilhas
oceânicas), cortada em faixas de 2 graus de latitude.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

API = "https://api.obis.org/v3"
AREA_BRASIL = 26  # "Brazil: all" na lista de áreas do OBIS
LAT_SUL, LAT_NORTE, PASSO = -36, 6, 2
LON_OESTE, LON_LESTE = -60, -20  # mais largo que a ZEE; quem recorta de fato é a área do OBIS
PAUSA_S = 0.4
PASTA = Path("data")

TARTARUGAS = {
    "Chelonia mydas": "tartaruga-verde",
    "Caretta caretta": "tartaruga-cabeçuda",
    "Eretmochelys imbricata": "tartaruga-de-pente",
    "Lepidochelys olivacea": "tartaruga-oliva",
    "Dermochelys coriacea": "tartaruga-de-couro",
}


def faixas() -> list[int]:
    """Latitude sul de cada faixa, do sul para o norte."""
    return list(range(LAT_SUL, LAT_NORTE, PASSO))


def rotulo(lat_sul: int) -> str:
    """Rótulo legível de uma faixa: '24°S a 22°S', '2°S a 0°', '0° a 2°N'."""

    def grau(lat: int) -> str:
        return "0°" if lat == 0 else f"{abs(lat)}°{'S' if lat < 0 else 'N'}"

    return f"{grau(lat_sul)} a {grau(lat_sul + PASSO)}"


def poligono(lat_sul: int) -> str:
    lat_norte = lat_sul + PASSO
    return (
        f"POLYGON(({LON_OESTE} {lat_sul}, {LON_LESTE} {lat_sul}, {LON_LESTE} {lat_norte}, "
        f"{LON_OESTE} {lat_norte}, {LON_OESTE} {lat_sul}))"
    )


def obter(caminho: str, tentativas: int = 4, **parametros) -> dict:
    """Uma chamada à API, com pausa entre chamadas e repetição com espera crescente."""
    url = f"{API}/{caminho}?{urllib.parse.urlencode(parametros)}"
    requisicao = urllib.request.Request(url, headers={"User-Agent": "estudo-portfolio-dados/0.1"})
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(requisicao, timeout=180) as resposta:
                dados = json.loads(resposta.read())
            time.sleep(PAUSA_S)
            return dados
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if tentativa == tentativas:
                raise
            time.sleep(5 * tentativa)
    raise RuntimeError("inalcançável")


def _paginado(caminho: str, tamanho: int = 5000, **parametros) -> list[dict]:
    resultados: list[dict] = []
    while True:
        pagina = obter(caminho, size=tamanho, skip=len(resultados), **parametros)
        lote = pagina.get("results", [])
        resultados.extend(lote)
        if len(lote) < tamanho:
            return resultados


def tipo_de_fonte(titulo: str) -> str:
    """Classifica um conjunto de dados pelo título: ciência cidadã, telemetria ou levantamento/coleção.

    A regra é por palavras do título, então é aproximada. "aggregated per 1-degree cell" é a marca
    dos conjuntos de rastreamento por satélite que o OBIS-SEAMAP entrega resumidos por célula.
    """
    t = str(titulo).lower()
    if any(p in t for p in ("inaturalist", "observation.org", "ebird", "citizen", "happywhale")):
        return "ciência cidadã"
    marcas = ("track", "telemetr", "satellite", "migration", "tagg", "movebank", "aggregated per 1-degree cell")
    if any(p in t for p in marcas):
        return "telemetria"
    return "levantamento ou coleção"


def baixar(destino: Path = PASTA) -> dict:
    """Coleta tudo e grava os quatro CSVs agregados e o registro da coleta."""
    destino.mkdir(parents=True, exist_ok=True)
    linhas_faixa, linhas_especie, linhas_conjunto = [], [], []
    for lat_sul in faixas():
        filtro = {"areaid": AREA_BRASIL, "geometry": poligono(lat_sul)}
        est = obter("statistics", **filtro)
        linhas_faixa.append(
            {
                "lat_sul": lat_sul,
                "registros": est["records"],
                "especies": est["species"],
                "taxons": est["taxa"],
                "registros_nivel_especie": est["specieslevel"],
                "conjuntos": est["datasets"],
                "ano_min": est["yearrange"][0],
                "ano_max": est["yearrange"][1],
            }
        )
        for taxon in _paginado("checklist", **filtro):
            if taxon.get("taxonRank") != "Species":
                continue
            linhas_especie.append(
                {
                    "lat_sul": lat_sul,
                    "taxon_id": taxon["taxonID"],
                    "especie": taxon["scientificName"],
                    "reino": taxon.get("kingdom"),
                    "filo": taxon.get("phylum"),
                    "classe": taxon.get("class"),
                    "registros": taxon["records"],
                }
            )
        for conjunto in _paginado("dataset", tamanho=500, **filtro):
            linhas_conjunto.append(
                {
                    "lat_sul": lat_sul,
                    "conjunto_id": conjunto["id"],
                    "titulo": " ".join(str(conjunto.get("title") or "").split())[:160],
                    "registros": conjunto["records"],
                }
            )

    linhas_tartaruga = []
    for especie in TARTARUGAS:
        for lat_sul in faixas():
            filtro = {"areaid": AREA_BRASIL, "geometry": poligono(lat_sul), "scientificname": especie}
            for conjunto in _paginado("dataset", tamanho=500, **filtro):
                titulo = " ".join(str(conjunto.get("title") or "").split())[:160]
                linhas_tartaruga.append(
                    {
                        "especie": especie,
                        "lat_sul": lat_sul,
                        "conjunto_id": conjunto["id"],
                        "titulo": titulo,
                        "registros": conjunto["records"],
                    }
                )

    pd.DataFrame(linhas_faixa).to_csv(destino / "faixas.csv", index=False)
    pd.DataFrame(linhas_especie).to_csv(destino / "especies_por_faixa.csv", index=False)
    pd.DataFrame(linhas_conjunto).to_csv(destino / "conjuntos_por_faixa.csv", index=False)
    pd.DataFrame(linhas_tartaruga).to_csv(destino / "tartarugas_por_conjunto.csv", index=False)

    coleta = {
        "coletado_em": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "api": API,
        "area_obis": {"id": AREA_BRASIL, "nome": "Brazil: all"},
        "faixas": {"lat_sul": LAT_SUL, "lat_norte": LAT_NORTE, "passo_graus": PASSO},
        "linhas": {
            "faixas": len(linhas_faixa),
            "especies_por_faixa": len(linhas_especie),
            "conjuntos_por_faixa": len(linhas_conjunto),
            "tartarugas_por_conjunto": len(linhas_tartaruga),
        },
    }
    (destino / "coleta.json").write_text(json.dumps(coleta, indent=2, ensure_ascii=False), encoding="utf-8")
    return coleta


def carregar(pasta: Path = PASTA) -> dict[str, pd.DataFrame]:
    """Lê o extrato agregado versionado em `data/` e classifica cada conjunto de dados pelo tipo de fonte."""
    tabelas = {
        "faixas": pd.read_csv(pasta / "faixas.csv"),
        "especies": pd.read_csv(pasta / "especies_por_faixa.csv"),
        "conjuntos": pd.read_csv(pasta / "conjuntos_por_faixa.csv"),
        "tartarugas": pd.read_csv(pasta / "tartarugas_por_conjunto.csv"),
    }
    for nome in ("conjuntos", "tartarugas"):
        tabelas[nome]["tipo_de_fonte"] = tabelas[nome]["titulo"].map(tipo_de_fonte)
    return tabelas


def data_da_coleta(pasta: Path = PASTA) -> str:
    return json.loads((pasta / "coleta.json").read_text(encoding="utf-8"))["coletado_em"][:10]
