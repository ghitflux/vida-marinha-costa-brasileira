import numpy as np
import pandas as pd
import pytest

from vida_marinha import analise, dados


def _tabelas_sinteticas() -> dict[str, pd.DataFrame]:
    """Três faixas com a MESMA comunidade (200 espécies, mesma distribuição) e esforços bem diferentes."""
    gerador = np.random.default_rng(0)
    proporcoes = gerador.dirichlet(np.full(200, 0.6))
    especies, faixas, conjuntos = [], [], []
    for lat, esforco in [(-24, 60_000), (-16, 6_000), (-8, 2_000)]:
        contagens = gerador.multinomial(esforco, proporcoes)
        for taxon_id, registros in enumerate(contagens):
            if registros:
                especies.append(
                    {"lat_sul": lat, "taxon_id": taxon_id, "especie": f"sp{taxon_id}", "reino": "Animalia",
                     "filo": "Chordata", "classe": "Teleostei" if taxon_id < 80 else "Bivalvia", "registros": registros}
                )
        faixas.append({"lat_sul": lat, "registros": esforco + 500})
        conjuntos += [
            {"lat_sul": lat, "conjunto_id": f"a{lat}", "titulo": "Levantamento de costão", "registros": esforco * 0.7},
            {"lat_sul": lat, "conjunto_id": f"b{lat}", "titulo": "iNaturalist Research-grade", "registros": esforco * 0.3},
        ]
    tartarugas = pd.DataFrame(
        {
            "especie": ["Chelonia mydas", "Chelonia mydas", "Caretta caretta"],
            "lat_sul": [-24, -8, -8],
            "conjunto_id": ["x", "y", "z"],
            "titulo": ["iNaturalist Research-grade", "Satellite telemetry (aggregated per 1-degree cell)", "Coleção de museu"],
            "registros": [60, 30, 10],
        }
    )
    tabelas = {
        "faixas": pd.DataFrame(faixas),
        "especies": pd.DataFrame(especies),
        "conjuntos": pd.DataFrame(conjuntos),
        "tartarugas": tartarugas,
    }
    for nome in ("conjuntos", "tartarugas"):
        tabelas[nome]["tipo_de_fonte"] = tabelas[nome]["titulo"].map(dados.tipo_de_fonte)
    return tabelas


def test_rotulos_e_faixas():
    assert dados.rotulo(-24) == "24°S a 22°S"
    assert dados.rotulo(-2) == "2°S a 0°"
    assert dados.rotulo(0) == "0° a 2°N"
    assert dados.faixas()[0] == -36 and dados.faixas()[-1] == 4 and len(dados.faixas()) == 21
    assert dados.poligono(-24).startswith("POLYGON((-60 -24,") and dados.poligono(-24).endswith("-60 -24))")


def test_tipo_de_fonte():
    assert dados.tipo_de_fonte("iNaturalist Research-grade Observations Marine Subset") == "ciência cidadã"
    assert dados.tipo_de_fonte("Ascension Island green turtles migrations") == "telemetria"
    assert dados.tipo_de_fonte("Gabon 2012: Leatherback Turtles (aggregated per 1-degree cell)") == "telemetria"
    assert dados.tipo_de_fonte("Neonates tagged off Brazil") == "telemetria"
    assert dados.tipo_de_fonte("Previous Fisheries REVIZEE Program") == "levantamento ou coleção"


def test_mesma_comunidade_esforcos_diferentes():
    """O cerne do projeto: a riqueza bruta segue o esforço; a rarefeita devolve a mesma resposta."""
    tabela = analise.tabela_por_faixa(_tabelas_sinteticas())
    bruta = tabela["riqueza bruta"]
    rarefeita = tabela["riqueza rarefeita"]
    assert bruta["24°S a 22°S"] > bruta["16°S a 14°S"] > bruta["8°S a 6°S"]
    assert rarefeita.max() - rarefeita.min() < 0.08 * rarefeita.mean()
    assert (bruta.max() - bruta.min()) / bruta.mean() > 3 * (rarefeita.max() - rarefeita.min()) / rarefeita.mean()


def test_tabela_por_faixa_e_coerente():
    tabelas = _tabelas_sinteticas()
    tabela = analise.tabela_por_faixa(tabelas)
    assert list(tabela["lat_sul"]) == [-8, -16, -24]  # do norte para o sul
    assert sorted(tabela["posto pela riqueza bruta"]) == [1, 2, 3]
    assert (tabela["rarefeita (2,5%)"] <= tabela["riqueza rarefeita"]).all()
    assert (tabela["riqueza rarefeita"] <= tabela["rarefeita (97,5%)"]).all()
    assert (tabela["riqueza rarefeita"] <= tabela["riqueza bruta"]).all()
    assert (tabela["Chao1"] >= tabela["riqueza bruta"]).all()
    assert tabela["completude"].between(0, 1).all()
    assert tabela["fração do maior conjunto"].tolist() == pytest.approx([0.7, 0.7, 0.7])
    # Quanto menos esforço, maior a chance de o próximo registro trazer espécie nova.
    assert tabela["espécies novas a cada 100 registros"].is_monotonic_decreasing


def test_curvas_param_onde_acabam_os_registros():
    curvas = analise.curvas_de_rarefacao(_tabelas_sinteticas(), [-24, -8], n_max=6_000, pontos=13)
    assert curvas["24°S a 22°S"].notna().all()
    assert curvas["8°S a 6°S"].dropna().index.max() <= 2_000
    assert curvas.iloc[0].fillna(0).sum() == 0  # nenhuma espécie com zero registros


def test_so_peixes_usa_apenas_as_classes_de_peixe():
    tabelas = _tabelas_sinteticas()
    tabela = analise.tabela_por_faixa(tabelas)
    peixes, comparacao = analise.so_peixes(tabelas, tabela, n=300)
    assert (peixes["espécies de peixes"] <= 80).all()
    assert comparacao["faixas"] == 3


def test_tartarugas_somam_e_separam_por_fonte():
    resultado = analise.tartarugas(_tabelas_sinteticas())
    por_tipo = resultado["por_tipo"]
    assert por_tipo["registros"].sum() == 100
    assert por_tipo.loc["ciência cidadã", "fração"] == pytest.approx(0.6)
    assert por_tipo.loc["telemetria", "registros"] == 30
    assert resultado["por_faixa"].to_numpy().sum() == 100
    assert len(resultado["por_faixa"]) == 21
    assert resultado["por_especie"]["total"].tolist() == [90, 10]
