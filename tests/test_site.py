"""Os gráficos extras do site: forma, limites, três idiomas e valores vindos dos resultados gravados."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from vida_marinha import site

RESULTADOS = Path(__file__).resolve().parents[1] / "reports" / "resultados.json"
IDIOMAS = {"pt", "en", "es"}
PAPEIS = {"principal", "base", "alternativa", "neutro"}
FORMATOS = {"numero", "percentual", "data"}


@pytest.fixture(scope="module")
def resultados() -> dict:
    if not RESULTADOS.exists():
        pytest.skip("reports/resultados.json ainda não foi gerado")
    return json.loads(RESULTADOS.read_text(encoding="utf-8"))


def test_graficos_extras_tem_a_forma_que_o_site_espera(resultados):
    extras = site.graficos_extras(resultados)
    assert 3 <= len(extras) <= 5
    for g in extras:
        assert g["tipo"] in {"linhas", "barras", "pontos"}
        for campo in ("titulo", "leitura", "eixo_x", "eixo_y"):
            assert set(g[campo]) == IDIOMAS
            assert all(isinstance(v, str) and v.strip() for v in g[campo].values())
        assert all(len(t) <= 90 for t in g["titulo"].values()), g["titulo"]
        assert g["formato_x"] in FORMATOS and g["formato_y"] in FORMATOS
        assert 1 <= len(g["series"]) <= 4
        for serie in g["series"]:
            assert set(serie["nome"]) == IDIOMAS
            assert serie["papel"] in PAPEIS
            limite = 300 if g["tipo"] == "pontos" else 80
            assert 1 <= len(serie["pontos"]) <= limite
            for x, y in serie["pontos"]:
                assert isinstance(y, (int, float)) and math.isfinite(y)
                assert isinstance(x, str) if g["tipo"] == "barras" else isinstance(x, (int, float))
            if g["tipo"] == "barras":
                assert set(serie["rotulos"]) == IDIOMAS
                assert all(len(v) == len(serie["pontos"]) for v in serie["rotulos"].values())
                assert [p[0] for p in serie["pontos"]] == serie["rotulos"]["pt"]
        assert "faixa" not in g or g["tipo"] == "linhas"


def test_o_json_gravado_traz_os_extras_e_so_eles_no_bloco_do_site(resultados):
    assert set(resultados["para_o_site"]) == {"graficos_extras"}
    sem_bloco = {k: v for k, v in resultados.items() if k != "para_o_site"}
    assert resultados["para_o_site"]["graficos_extras"] == site.graficos_extras(sem_bloco)


def test_os_valores_dos_extras_saem_dos_resultados(resultados):
    esforco, ranking, curvas, dominancia, tartarugas = site.graficos_extras(resultados)
    por_faixa = {f["faixa"]: f for f in resultados["por_faixa"]}
    rho = resultados["relacoes"]["riqueza bruta x registros"]["rho"]
    assert f"{rho:.2f}".replace(".", ",") in esforco["titulo"]["pt"]
    assert f"{rho:.2f}" in esforco["titulo"]["en"]
    mudanca = dict(ranking["series"][0]["pontos"])
    assert all(mudanca[f] == por_faixa[f]["mudança de posto"] for f in por_faixa)
    assert len(dominancia["series"][0]["pontos"]) == len(por_faixa)
    total = sum(sum(p[1] for p in s["pontos"]) for s in tartarugas["series"])
    assert total == resultados["tartarugas"]["total"]
    assert all(s["pontos"][0][0] == 0 for s in curvas["series"])

    alterado = copy.deepcopy(resultados)
    alterado["relacoes"]["riqueza bruta x registros"]["rho"] = 0.5
    assert "0,50" in site.riqueza_x_esforco(alterado)["titulo"]["pt"]


def test_rotulos_e_ordinais_nos_tres_idiomas():
    assert site._faixa("2°S a 0°") == {"pt": "2°S a 0°", "en": "2°S to 0°", "es": "2°S a 0°"}
    assert site._ordinal(21) == {"pt": "21º", "en": "21st", "es": "21.º"}
    assert site._ordinal(12)["en"] == "12th" and site._ordinal(2)["en"] == "2nd"
    assert site._n(-0.196, 2) == {"pt": "−0,20", "en": "−0.20", "es": "−0,20"}
