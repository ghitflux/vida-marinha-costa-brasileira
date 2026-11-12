"""Roda a análise completa sobre o extrato em data/ e grava reports/resultados.json e as figuras."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from vida_marinha import analise, dados, graficos, site

SAIDA = Path("reports")
FIGURAS = SAIDA / "figuras"
FAIXAS_DAS_CURVAS = [-20, -24, -16, -18]


def _json(tabela: pd.DataFrame, orient: str = "index"):
    return json.loads(tabela.to_json(orient=orient, force_ascii=False))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    FIGURAS.mkdir(parents=True, exist_ok=True)

    tabelas = dados.carregar()
    tabela = analise.tabela_por_faixa(tabelas)
    resumo = analise.resumo_geral(tabelas, tabela)
    relacoes = analise.relacoes(tabela)
    lei = analise.lei_de_esforco(tabela)
    curvas = analise.curvas_de_rarefacao(tabelas, FAIXAS_DAS_CURVAS)
    peixes, peixes_x_todos = analise.so_peixes(tabelas, tabela)
    prioridade = analise.prioridade(tabela)
    tart = analise.tartarugas(tabelas)

    figuras = {
        "perfil_latitudinal": graficos.perfil_latitudinal(tabela, analise.N_REF),
        "riqueza_x_esforco": graficos.riqueza_x_esforco(tabela, relacoes, analise.N_REF),
        "curvas_de_rarefacao": graficos.curvas_de_rarefacao(curvas, analise.N_REF),
        "troca_de_ranking": graficos.troca_de_ranking(tabela, analise.N_REF),
        "fontes_das_tartarugas": graficos.fontes_das_tartarugas(tart["por_faixa"], tart["por_tipo"]),
    }
    for nome, figura in figuras.items():
        figura.savefig(FIGURAS / f"{nome}.png")
        plt.close(figura)

    resultados = {
        "coletado_em": dados.data_da_coleta(),
        "fonte": "OBIS (https://obis.org), área 'Brazil: all', faixas de 2 graus de latitude",
        "resumo": resumo,
        "por_faixa": json.loads(tabela.reset_index().to_json(orient="records", force_ascii=False)),
        "relacoes": _json(relacoes),
        "lei_de_esforco": lei,
        "curvas_de_rarefacao": json.loads(curvas.reset_index().to_json(orient="records", force_ascii=False)),
        "so_peixes": {"por_faixa": _json(peixes), "postos_peixes_x_todos": peixes_x_todos, "n": analise.N_PEIXES},
        "prioridade": json.loads(prioridade.reset_index().to_json(orient="records", force_ascii=False)),
        "tartarugas": {
            "total": int(tart["por_tipo"]["registros"].sum()),
            "por_tipo": _json(tart["por_tipo"]),
            "por_conjunto": json.loads(tart["por_conjunto"].head(12).to_json(orient="records", force_ascii=False)),
            "por_faixa": json.loads(tart["por_faixa"].reset_index().to_json(orient="records", force_ascii=False)),
            "por_especie": json.loads(tart["por_especie"].reset_index().to_json(orient="records", force_ascii=False)),
        },
    }
    # O texto e o gráfico principal do site vêm de outro arquivo; daqui saem só os gráficos extras, calculados a
    # partir do próprio dicionário de resultados (passado por JSON para usar exatamente os números gravados).
    resultados["para_o_site"] = {"graficos_extras": site.graficos_extras(json.loads(json.dumps(resultados, ensure_ascii=False)))}
    (SAIDA / "resultados.json").write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.float_format", lambda v: f"{v:.3f}")
    print(resumo)
    print(lei)
    print(relacoes.to_string())
    print(tabela.drop(columns=["maior conjunto"]).to_string())
    print(peixes.to_string(), peixes_x_todos)
    print(prioridade.head(6).to_string())
    for nome, t in tart.items():
        print("==", nome)
        print(t.head(12).to_string())
    print(f"\nGravado em {SAIDA / 'resultados.json'} e {FIGURAS}")


if __name__ == "__main__":
    main()
