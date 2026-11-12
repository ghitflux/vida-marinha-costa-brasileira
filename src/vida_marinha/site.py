"""Gráficos adicionais para o site, como dados, para ele desenhar nativamente (`para_o_site.graficos_extras`).

O texto e o gráfico principal deste estudo (o perfil por latitude) vêm de outro arquivo do site; aqui saem só os
extras, cada um equivalente a uma figura ou achado do README. Todo valor sai do dicionário de resultados gravado
por `scripts/rodar_analise.py`; nada é digitado à mão.
"""

from __future__ import annotations

import math

IDIOMAS = ("pt", "en", "es")
TIPOS_DE_FONTE = {
    "ciência cidadã": ("Ciência cidadã", "Citizen science", "Ciencia ciudadana"),
    "telemetria": ("Telemetria", "Satellite telemetry", "Telemetría"),
    "levantamento ou coleção": ("Levantamento ou coleção", "Survey or collection", "Muestreo o colección"),
}


def _n(valor: float, casas: int) -> dict[str, str]:
    """O mesmo número nos três idiomas (pt e es com vírgula decimal; sinal de menos tipográfico)."""
    texto = f"{valor:.{casas}f}".replace("-", "−")
    return {"pt": texto.replace(".", ","), "en": texto, "es": texto.replace(".", ",")}


def _p(valor: float) -> dict[str, str]:
    return {i: f"{t}%" for i, t in _n(valor * 100, 0).items()}


def _milhar(valor: float) -> dict[str, str]:
    us = f"{valor:,.0f}"
    return {"pt": us.replace(",", "."), "en": us, "es": us.replace(",", ".")}


def _faixa(rotulo: str) -> dict[str, str]:
    """'24°S a 22°S' nos três idiomas."""
    return {"pt": rotulo, "en": rotulo.replace(" a ", " to "), "es": rotulo}


def _rotulos(faixas: list[str]) -> dict[str, list[str]]:
    return {i: [_faixa(f)[i] for f in faixas] for i in IDIOMAS}


def _ordinal(posto: int) -> dict[str, str]:
    sufixo = {1: "st", 2: "nd", 3: "rd"}.get(posto if posto < 20 else posto % 10, "th")
    if 11 <= posto % 100 <= 13:
        sufixo = "th"
    return {"pt": f"{posto}º", "en": f"{posto}{sufixo}", "es": f"{posto}.º"}


def riqueza_x_esforco(r: dict) -> dict:
    """Dispersão: riqueza bruta e rarefeita contra o número de registros (eixo em log10, como na figura)."""
    faixas = r["por_faixa"]
    rel = r["relacoes"]
    bruta, rarefeita = _n(rel["riqueza bruta x registros"]["rho"], 2), _n(rel["riqueza rarefeita x registros"]["rho"], 2)
    fator = _n(r["lei_de_esforco"]["fator_de_especies_ao_decuplicar_registros"], 1)
    n_ref = _milhar(r["resumo"]["n_ref"])

    def serie(coluna: str) -> list[list[float]]:
        return [[round(math.log10(f["registros com espécie"]), 3), round(f[coluna], 1)] for f in faixas]

    return {
        "tipo": "pontos",
        "titulo": {
            "pt": f"Mais registros, mais espécies (correlação de {bruta['pt']}); com a mesma régua, {rarefeita['pt']}",
            "en": f"More records, more species (correlation {bruta['en']}); on a common yardstick, {rarefeita['en']}",
            "es": f"Más registros, más especies (correlación de {bruta['es']}); con la misma vara, {rarefeita['es']}",
        },
        "leitura": {
            "pt": f"Cada ponto é uma faixa de 2° de latitude. Dez vezes mais registros dão {fator['pt']} vezes mais espécies registradas; contadas em {n_ref['pt']} registros sorteados, a relação some.",
            "en": f"Each point is a 2° latitude band. Ten times the records give {fator['en']} times the recorded species; counted in {n_ref['en']} randomly drawn records, the link disappears.",
            "es": f"Cada punto es una franja de 2° de latitud. Diez veces más registros dan {fator['es']} veces más especies registradas; contadas en {n_ref['es']} registros sorteados, la relación desaparece.",
        },
        "eixo_x": {
            "pt": "Registros identificados até espécie (log10: 3 = mil, 5 = 100 mil)",
            "en": "Records identified to species (log10: 3 = 1,000, 5 = 100,000)",
            "es": "Registros identificados hasta especie (log10: 3 = mil, 5 = 100.000)",
        },
        "eixo_y": {"pt": "Espécies", "en": "Species", "es": "Especies"},
        "formato_x": "numero",
        "formato_y": "numero",
        "series": [
            {"nome": {"pt": "Riqueza bruta", "en": "Raw richness", "es": "Riqueza bruta"}, "papel": "base", "pontos": serie("riqueza bruta")},
            {
                "nome": {"pt": f"Riqueza em {n_ref['pt']} registros", "en": f"Richness in {n_ref['en']} records", "es": f"Riqueza en {n_ref['es']} registros"},
                "papel": "principal",
                "pontos": serie("riqueza rarefeita"),
            },
        ],
    }


def troca_de_ranking(r: dict) -> dict:
    """Barras: quantas posições cada faixa sobe ou desce quando passa da riqueza bruta para a rarefeita."""
    faixas = r["por_faixa"]
    lider = min(faixas, key=lambda f: f["posto pela riqueza bruta"])
    queda = min(faixas, key=lambda f: f["mudança de posto"])
    nomes = [f["faixa"] for f in faixas]
    rotulos = _rotulos(nomes)
    a, b = _ordinal(lider["posto pela riqueza bruta"]), _ordinal(lider["posto pela riqueza rarefeita"])
    qa, qb = _ordinal(queda["posto pela riqueza bruta"]), _ordinal(queda["posto pela riqueza rarefeita"])
    fl, fq = _faixa(lider["faixa"]), _faixa(queda["faixa"])
    n_ref = _milhar(r["resumo"]["n_ref"])
    return {
        "tipo": "barras",
        "titulo": {
            "pt": f"Com a mesma régua, a faixa líder cai do {a['pt']} para o {b['pt']} lugar no ranking",
            "en": f"On a common yardstick, the top band drops from {a['en']} to {b['en']} place",
            "es": f"Con la misma vara, la franja líder cae del {a['es']} al {b['es']} puesto",
        },
        "leitura": {
            "pt": f"Posições ganhas (positivo) ou perdidas ao trocar as espécies registradas pelas espécies em {n_ref['pt']} registros, do norte ao sul. A líder é {fl['pt']}; a maior queda é a de {fq['pt']}, do {qa['pt']} para o {qb['pt']}.",
            "en": f"Places gained (positive) or lost when recorded species are replaced by species in {n_ref['en']} records, north to south. The leader is {fl['en']}; the biggest fall is {fq['en']}, from {qa['en']} to {qb['en']}.",
            "es": f"Puestos ganados (positivo) o perdidos al cambiar las especies registradas por las especies en {n_ref['es']} registros, de norte a sur. La líder es {fl['es']}; la mayor caída es la de {fq['es']}, del {qa['es']} al {qb['es']}.",
        },
        "eixo_x": {"pt": "Faixa de latitude, do norte ao sul", "en": "Latitude band, north to south", "es": "Franja de latitud, de norte a sur"},
        "eixo_y": {"pt": "Mudança de posto", "en": "Change in rank", "es": "Cambio de puesto"},
        "formato_x": "numero",
        "formato_y": "numero",
        "series": [
            {
                "nome": {"pt": "Posições ganhas ou perdidas", "en": "Places gained or lost", "es": "Puestos ganados o perdidos"},
                "papel": "principal",
                "pontos": [[rotulos["pt"][k], int(f["mudança de posto"])] for k, f in enumerate(faixas)],
                "rotulos": rotulos,
            }
        ],
    }


def curvas_de_rarefacao(r: dict) -> dict:
    """Linhas: as curvas de rarefação das faixas da figura, cada uma até onde acabam os registros dela."""
    curvas = r["curvas_de_rarefacao"]
    eixo = "registros na subamostra"
    faixas = [c for c in curvas[0] if c != eixo]
    n_ref = r["resumo"]["n_ref"]
    rarefeita = {f["faixa"]: f["riqueza rarefeita"] for f in r["por_faixa"]}
    bruta = {f["faixa"]: f["riqueza bruta"] for f in r["por_faixa"]}
    topo_regua = max(faixas, key=lambda f: rarefeita[f])
    topo_bruta = max(faixas, key=lambda f: bruta[f])
    papeis = ["principal", "alternativa", "base", "neutro"]
    series = []
    for k, faixa in enumerate(faixas[:4]):
        pontos = [[int(c[eixo]), round(c[faixa], 1)] for c in curvas if c[faixa] is not None]
        passo = math.ceil(len(pontos) / 80)
        series.append({"nome": _faixa(faixa), "papel": papeis[k], "pontos": pontos[::passo]})
    t, b, n = _faixa(topo_regua), _faixa(topo_bruta), _milhar(n_ref)
    if topo_regua != topo_bruta:
        titulo = {
            "pt": f"Na régua de {n['pt']} registros, {t['pt']} supera {b['pt']}, a líder bruta",
            "en": f"At {n['en']} records, {t['en']} beats {b['en']}, the raw leader",
            "es": f"Con {n['es']} registros, {t['es']} supera a {b['es']}, la líder bruta",
        }
    else:
        titulo = {
            "pt": f"Na régua de {n['pt']} registros, {t['pt']} continua à frente",
            "en": f"At {n['en']} records, {t['en']} stays ahead",
            "es": f"Con {n['es']} registros, {t['es']} sigue al frente",
        }
    return {
        "tipo": "linhas",
        "titulo": titulo,
        "leitura": {
            "pt": f"Espécies esperadas numa subamostra aleatória dos registros de cada faixa (rarefação de Hurlbert). Cada curva termina onde acabam os registros da faixa; {n['pt']} é o maior número que cabe em todas as 21.",
            "en": f"Expected species in a random subsample of each band's records (Hurlbert rarefaction). Each curve stops where the band runs out of records; {n['en']} is the largest size that fits all 21 bands.",
            "es": f"Especies esperadas en una submuestra aleatoria de los registros de cada franja (rarefacción de Hurlbert). Cada curva termina donde se acaban los registros de la franja; {n['es']} es el mayor número que cabe en las 21.",
        },
        "eixo_x": {"pt": "Registros na subamostra", "en": "Records in the subsample", "es": "Registros en la submuestra"},
        "eixo_y": {"pt": "Espécies esperadas", "en": "Expected species", "es": "Especies esperadas"},
        "formato_x": "numero",
        "formato_y": "numero",
        "series": series,
    }


def dominancia(r: dict) -> dict:
    """Dispersão: a riqueza rarefeita cai quanto mais um único conjunto de dados domina a faixa."""
    rel = r["relacoes"]["riqueza rarefeita x fração do maior conjunto"]
    rho = _n(rel["rho"], 2)
    pior = max(r["por_faixa"], key=lambda f: f["fração do maior conjunto"])
    fp, fracao = _faixa(pior["faixa"]), _p(pior["fração do maior conjunto"])
    posto, total = _ordinal(pior["posto pela riqueza rarefeita"]), len(r["por_faixa"])
    n_ref = _milhar(r["resumo"]["n_ref"])
    return {
        "tipo": "pontos",
        "titulo": {
            "pt": f"A correção tem limite: quanto mais um conjunto domina a faixa, menos espécies ({rho['pt']})",
            "en": f"The fix has a limit: the more one dataset dominates a band, the fewer species ({rho['en']})",
            "es": f"La corrección tiene límite: si un conjunto domina la franja, hay menos especies ({rho['es']})",
        },
        "leitura": {
            "pt": f"Cada ponto é uma faixa. Em {fp['pt']}, um único conjunto de dados responde por {fracao['pt']} dos registros e a faixa fica em {posto['pt']} entre {total}: a rarefação corrige quanto se coletou, não quem coletou nem o quê.",
            "en": f"Each point is a band. In {fp['en']}, a single dataset accounts for {fracao['en']} of the records and the band ranks {posto['en']} of {total}: rarefaction corrects how much was collected, not who collected it or what.",
            "es": f"Cada punto es una franja. En {fp['es']}, un único conjunto de datos aporta el {fracao['es']} de los registros y la franja queda en el puesto {posto['es']} de {total}: la rarefacción corrige cuánto se recolectó, no quién recolectó ni qué.",
        },
        "eixo_x": {
            "pt": "Fração dos registros que vem do maior conjunto de dados",
            "en": "Share of records from the largest dataset",
            "es": "Fracción de los registros que viene del mayor conjunto de datos",
        },
        "eixo_y": {"pt": f"Espécies em {n_ref['pt']} registros", "en": f"Species in {n_ref['en']} records", "es": f"Especies en {n_ref['es']} registros"},
        "formato_x": "percentual",
        "formato_y": "numero",
        "series": [
            {
                "nome": {"pt": "Faixa de 2° de latitude", "en": "2° latitude band", "es": "Franja de 2° de latitud"},
                "papel": "principal",
                "pontos": [[round(f["fração do maior conjunto"], 4), round(f["riqueza rarefeita"], 1)] for f in r["por_faixa"]],
            }
        ],
    }


def fontes_das_tartarugas(r: dict) -> dict:
    """Barras por faixa, uma série por tipo de fonte, para os registros de tartarugas-marinhas."""
    t = r["tartarugas"]
    por_faixa = t["por_faixa"]
    rotulos = _rotulos([f["faixa"] for f in por_faixa])
    sem_levantamento = _p(1 - t["por_tipo"].get("levantamento ou coleção", {"fração": 0})["fração"])
    total = _milhar(t["total"])
    papeis = {"ciência cidadã": "principal", "telemetria": "alternativa", "levantamento ou coleção": "neutro"}
    cidada = {f["faixa"]: f.get("ciência cidadã", 0) for f in por_faixa}
    topo = max(cidada, key=cidada.get)
    soma_topo = sum(v for k, v in next(f for f in por_faixa if f["faixa"] == topo).items() if k != "faixa")
    ft, ct, st = _faixa(topo), _milhar(cidada[topo]), _milhar(soma_topo)
    series = [
        {
            "nome": dict(zip(IDIOMAS, TIPOS_DE_FONTE[tipo])),
            "papel": papeis[tipo],
            "pontos": [[rotulos["pt"][k], int(f.get(tipo, 0))] for k, f in enumerate(por_faixa)],
            "rotulos": rotulos,
        }
        for tipo in TIPOS_DE_FONTE
        if tipo in t["por_tipo"]
    ]
    return {
        "tipo": "barras",
        "titulo": {
            "pt": f"{sem_levantamento['pt']} dos registros de tartarugas são ciência cidadã ou telemetria",
            "en": f"{sem_levantamento['en']} of sea-turtle records are citizen science or telemetry",
            "es": f"El {sem_levantamento['es']} de los registros de tortugas son ciencia ciudadana o telemetría",
        },
        "leitura": {
            "pt": f"Os {total['pt']} registros das cinco espécies por faixa e tipo de fonte. A ciência cidadã segue as pessoas ({ct['pt']} dos {st['pt']} registros de {ft['pt']}) e a telemetria segue poucos animais: o retrato mostra onde há celulares e transmissores, não onde há mais tartarugas.",
            "en": f"The {total['en']} records of the five species by band and source type. Citizen science follows people ({ct['en']} of the {st['en']} records in {ft['en']}) and telemetry follows a few animals: the picture shows where phones and transmitters are, not where turtles are most common.",
            "es": f"Los {total['es']} registros de las cinco especies por franja y tipo de fuente. La ciencia ciudadana sigue a las personas ({ct['es']} de los {st['es']} registros de {ft['es']}) y la telemetría sigue a pocos animales: el retrato muestra dónde hay celulares y transmisores, no dónde hay más tortugas.",
        },
        "eixo_x": {"pt": "Faixa de latitude, do norte ao sul", "en": "Latitude band, north to south", "es": "Franja de latitud, de norte a sur"},
        "eixo_y": {"pt": "Registros de tartarugas-marinhas", "en": "Sea-turtle records", "es": "Registros de tortugas marinas"},
        "formato_x": "numero",
        "formato_y": "numero",
        "series": series,
    }


def graficos_extras(r: dict) -> list[dict]:
    """As cinco especificações, do achado mais importante para o menos."""
    return [riqueza_x_esforco(r), troca_de_ranking(r), curvas_de_rarefacao(r), dominancia(r), fontes_das_tartarugas(r)]
