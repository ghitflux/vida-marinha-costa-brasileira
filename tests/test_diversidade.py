import numpy as np
import pytest

from vida_marinha import diversidade as d


def test_rarefacao_nos_extremos():
    contagens = np.array([50, 30, 10, 5, 3, 1, 1])
    assert d.rarefacao(contagens, 0)[0] == pytest.approx(0.0)
    assert d.rarefacao(contagens, 1)[0] == pytest.approx(1.0)
    assert d.rarefacao(contagens, contagens.sum())[0] == pytest.approx(len(contagens))


def test_rarefacao_cresce_com_n_e_nunca_passa_da_riqueza_observada():
    contagens = np.array([400, 120, 60, 30, 8, 4, 2, 1, 1, 1])
    ns = np.arange(0, contagens.sum() + 1, 25)
    curva = d.rarefacao(contagens, ns)
    assert (np.diff(curva) >= -1e-9).all()
    assert curva.max() <= len(contagens) + 1e-9


def test_rarefacao_bate_com_a_formula_exata_em_caso_pequeno():
    # Duas espécies com 2 e 1 registros; sorteando 2 dos 3 registros:
    # espécie A falta com chance C(1,2)/C(3,2) = 0; espécie B falta com chance C(2,2)/C(3,2) = 1/3.
    assert d.rarefacao(np.array([2, 1]), 2)[0] == pytest.approx(2 - 1 / 3)


def test_rarefacao_bate_com_o_sorteio():
    gerador = np.random.default_rng(0)
    contagens = gerador.geometric(0.02, size=300)
    esperado = d.rarefacao(contagens, 2000)[0]
    media, baixo, alto = d.intervalo_por_sorteio(contagens, 2000, repeticoes=400)
    assert media == pytest.approx(esperado, rel=0.01)
    assert baixo <= esperado <= alto


def test_rarefacao_rejeita_n_maior_que_o_total():
    with pytest.raises(ValueError):
        d.rarefacao(np.array([3, 2]), 6)


def test_area_mais_uniforme_tem_mais_riqueza_rarefeita():
    # Mesma riqueza e mesmo total; numa área um único grupo domina os registros.
    uniforme = np.full(50, 100)
    dominada = np.array([4951] + [1] * 49)
    assert d.rarefacao(uniforme, 500)[0] > d.rarefacao(dominada, 500)[0] * 5


def test_chao1_sem_especies_raras_e_a_propria_riqueza():
    assert d.chao1(np.array([10, 8, 5, 3])) == 4
    assert d.completude(np.array([10, 8, 5, 3])) == 1.0


def test_chao1_cresce_com_especies_vistas_uma_vez():
    poucas_raras = np.array([10, 8, 5, 2, 2, 1])
    muitas_raras = np.array([10, 8, 5, 2, 1, 1, 1, 1, 1, 1])
    assert d.chao1(muitas_raras) - len(muitas_raras) > d.chao1(poucas_raras) - len(poucas_raras)
    # f1 = 6, f2 = 1: 10 + 6 * 5 / (2 * 2) = 17,5
    assert d.chao1(muitas_raras) == pytest.approx(17.5)
    assert d.completude(muitas_raras) == pytest.approx(10 / 17.5)


def test_chance_de_especie_nova():
    assert d.chance_de_especie_nova(np.array([97, 1, 1, 1])) == pytest.approx(0.03)
    assert d.chance_de_especie_nova(np.array([50, 50])) == 0.0


def test_zeros_sao_ignorados():
    assert d.chao1(np.array([5, 0, 3, 0])) == 2
    assert d.rarefacao(np.array([5, 0, 3]), 8)[0] == pytest.approx(2.0)
