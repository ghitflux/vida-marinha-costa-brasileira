"""Orquestra a análise. Cada função devolve uma tabela usada no notebook e no README."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from vida_marinha import dados, diversidade

N_REF = 1500  # registros da subamostra comum; cabe em todas as faixas
N_ALTO = 3000  # segunda régua, para conferir se o ranking depende da escolha de N_REF
PEIXES = {"Teleostei", "Actinopteri", "Actinopterygii", "Elasmobranchii", "Holocephali"}
N_PEIXES = 400


def _contagens(especies: pd.DataFrame) -> dict[int, np.ndarray]:
    return {lat: g["registros"].to_numpy() for lat, g in especies.groupby("lat_sul")}


def tabela_por_faixa(tabelas: dict[str, pd.DataFrame], n_ref: int = N_REF) -> pd.DataFrame:
    """Uma linha por faixa de latitude: esforço, riqueza bruta, riqueza rarefeita, completude e fonte dominante."""
    faixas, especies, conjuntos = tabelas["faixas"], tabelas["especies"], tabelas["conjuntos"]
    linhas = []
    for lat, contagens in _contagens(especies).items():
        total = int(contagens.sum())
        media, baixo, alto = diversidade.intervalo_por_sorteio(contagens, n_ref)
        fontes = conjuntos[conjuntos["lat_sul"] == lat].sort_values("registros", ascending=False)
        linhas.append(
            {
                "faixa": dados.rotulo(lat),
                "lat_sul": lat,
                "registros": int(faixas.loc[faixas["lat_sul"] == lat, "registros"].iloc[0]),
                "registros com espécie": total,
                "conjuntos de dados": int(len(fontes)),
                "riqueza bruta": int(len(contagens)),
                "riqueza rarefeita": float(diversidade.rarefacao(contagens, n_ref)[0]),
                "rarefeita (2,5%)": baixo,
                "rarefeita (97,5%)": alto,
                f"rarefeita em {N_ALTO}": (
                    float(diversidade.rarefacao(contagens, N_ALTO)[0]) if total >= N_ALTO else np.nan
                ),
                "Chao1": diversidade.chao1(contagens),
                "completude": diversidade.completude(contagens),
                "espécies novas a cada 100 registros": 100 * diversidade.chance_de_especie_nova(contagens),
                "fração do maior conjunto": float(fontes["registros"].iloc[0] / fontes["registros"].sum()),
                "maior conjunto": fontes["titulo"].iloc[0],
            }
        )
    tabela = pd.DataFrame(linhas).set_index("faixa").sort_values("lat_sul", ascending=False)
    tabela["posto pela riqueza bruta"] = tabela["riqueza bruta"].rank(ascending=False).astype(int)
    tabela["posto pela riqueza rarefeita"] = tabela["riqueza rarefeita"].rank(ascending=False).astype(int)
    tabela["mudança de posto"] = tabela["posto pela riqueza bruta"] - tabela["posto pela riqueza rarefeita"]
    return tabela


def resumo_geral(tabelas: dict[str, pd.DataFrame], tabela: pd.DataFrame) -> dict[str, float]:
    especies = tabelas["especies"]
    return {
        "faixas": int(len(tabela)),
        "registros": int(tabela["registros"].sum()),
        "registros_com_especie": int(tabela["registros com espécie"].sum()),
        "especies_distintas": int(especies["taxon_id"].nunique()),
        "registros_faixa_mais_amostrada": int(tabela["registros"].max()),
        "registros_faixa_menos_amostrada": int(tabela["registros"].min()),
        "razao_de_esforco": float(tabela["registros"].max() / tabela["registros"].min()),
        "n_ref": N_REF,
    }


def _spearman(a: pd.Series, b: pd.Series) -> dict[str, float]:
    juntos = pd.concat([a, b], axis=1).dropna()
    rho, p = stats.spearmanr(juntos.iloc[:, 0], juntos.iloc[:, 1])
    return {"rho": float(rho), "p": float(p), "faixas": int(len(juntos))}


def relacoes(tabela: pd.DataFrame) -> pd.DataFrame:
    """Correlações de postos (Spearman) que sustentam a história: o que acompanha o quê."""
    pares = {
        "riqueza bruta x registros": ("riqueza bruta", "registros com espécie"),
        "riqueza rarefeita x registros": ("riqueza rarefeita", "registros com espécie"),
        "riqueza bruta x riqueza rarefeita": ("riqueza bruta", "riqueza rarefeita"),
        "riqueza rarefeita x fração do maior conjunto": ("riqueza rarefeita", "fração do maior conjunto"),
        "completude x registros": ("completude", "registros com espécie"),
        "riqueza bruta x latitude": ("riqueza bruta", "lat_sul"),
        "riqueza rarefeita x latitude": ("riqueza rarefeita", "lat_sul"),
        f"rarefeita em {N_REF} x rarefeita em {N_ALTO}": ("riqueza rarefeita", f"rarefeita em {N_ALTO}"),
    }
    return pd.DataFrame({nome: _spearman(tabela[a], tabela[b]) for nome, (a, b) in pares.items()}).T


def lei_de_esforco(tabela: pd.DataFrame) -> dict[str, float]:
    """Reta em escala log-log: riqueza bruta em função do número de registros."""
    ajuste = stats.linregress(np.log10(tabela["registros com espécie"]), np.log10(tabela["riqueza bruta"]))
    return {
        "inclinacao": float(ajuste.slope),
        "intercepto": float(ajuste.intercept),
        "r2": float(ajuste.rvalue**2),
        # Com inclinação b, multiplicar os registros por 10 multiplica as espécies por 10^b.
        "fator_de_especies_ao_decuplicar_registros": float(10**ajuste.slope),
    }


def curvas_de_rarefacao(
    tabelas: dict[str, pd.DataFrame], latitudes: list[int], n_max: int = 12_000, pontos: int = 60
) -> pd.DataFrame:
    """Riqueza esperada em função do tamanho da subamostra, para as faixas escolhidas."""
    contagens = _contagens(tabelas["especies"])
    ns = np.unique(np.linspace(0, n_max, pontos).astype(int))
    curvas = {}
    for lat in latitudes:
        c = contagens[lat]
        validos = ns[ns <= c.sum()]
        curvas[dados.rotulo(lat)] = pd.Series(diversidade.rarefacao(c, validos), index=validos)
    return pd.DataFrame(curvas).rename_axis("registros na subamostra")


def so_peixes(tabelas: dict[str, pd.DataFrame], tabela: pd.DataFrame, n: int = N_PEIXES) -> tuple[pd.DataFrame, dict]:
    """O mesmo exercício só com peixes: o ranking rarefeito resiste a trocar o grupo biológico?"""
    especies = tabelas["especies"]
    peixes = especies[especies["classe"].isin(PEIXES)]
    linhas = []
    for lat, contagens in _contagens(peixes).items():
        if contagens.sum() < n:
            continue
        linhas.append(
            {
                "faixa": dados.rotulo(lat),
                "registros de peixes": int(contagens.sum()),
                "espécies de peixes": int(len(contagens)),
                "peixes, rarefeita": float(diversidade.rarefacao(contagens, n)[0]),
            }
        )
    resultado = pd.DataFrame(linhas).set_index("faixa")
    comparacao = _spearman(resultado["peixes, rarefeita"], tabela["riqueza rarefeita"].reindex(resultado.index))
    return resultado, comparacao


def prioridade(tabela: pd.DataFrame) -> pd.DataFrame:
    """Onde um novo levantamento rende mais: faixas ordenadas pela chance de registrar espécie nova."""
    colunas = [
        "registros",
        "riqueza bruta",
        "completude",
        "espécies novas a cada 100 registros",
        "fração do maior conjunto",
    ]
    return tabela[colunas].sort_values("espécies novas a cada 100 registros", ascending=False)


def tartarugas(tabelas: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """De onde vêm os registros de tartarugas-marinhas: por espécie, por tipo de fonte, por conjunto e por faixa."""
    t = tabelas["tartarugas"].copy()
    t["nome popular"] = t["especie"].map(dados.TARTARUGAS)
    total = t["registros"].sum()
    por_tipo = t.groupby("tipo_de_fonte")["registros"].sum().sort_values(ascending=False).to_frame()
    por_tipo["fração"] = por_tipo["registros"] / total
    por_conjunto = (
        t.groupby(["titulo", "tipo_de_fonte"])["registros"].sum().sort_values(ascending=False).reset_index()
    )
    por_conjunto["fração"] = por_conjunto["registros"] / total
    por_faixa = t.pivot_table(index="lat_sul", columns="tipo_de_fonte", values="registros", aggfunc="sum", fill_value=0)
    por_faixa = por_faixa.reindex(dados.faixas(), fill_value=0).sort_index(ascending=False)
    por_faixa.index = [dados.rotulo(lat) for lat in por_faixa.index]
    por_especie = t.pivot_table(
        index=["especie", "nome popular"], columns="tipo_de_fonte", values="registros", aggfunc="sum", fill_value=0
    )
    por_especie["total"] = por_especie.sum(axis=1)
    return {
        "por_tipo": por_tipo,
        "por_conjunto": por_conjunto,
        "por_faixa": por_faixa.rename_axis("faixa"),
        "por_especie": por_especie.sort_values("total", ascending=False),
    }
