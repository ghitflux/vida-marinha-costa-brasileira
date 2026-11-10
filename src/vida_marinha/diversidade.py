"""Medidas de diversidade a partir de contagens de registros por espécie.

Todas as funções recebem um vetor com o número de registros de cada espécie numa área.
"""

from __future__ import annotations

import numpy as np
from scipy.special import gammaln


def rarefacao(contagens: np.ndarray, n: np.ndarray | int) -> np.ndarray:
    """Riqueza esperada numa subamostra aleatória de `n` registros (Hurlbert, 1971).

    E[S_n] = soma, sobre as espécies, de 1 - C(N - N_i, n) / C(N, n): a chance de cada espécie
    aparecer ao menos uma vez quando se sorteiam n dos N registros sem reposição.
    É o que permite comparar áreas com esforços de coleta diferentes: pergunta-se quantas
    espécies cada uma teria mostrado se todas tivessem sido amostradas com o mesmo n.
    """
    contagens = np.asarray(contagens, dtype=float)
    contagens = contagens[contagens > 0]
    total = contagens.sum()
    n = np.atleast_1d(np.asarray(n, dtype=float))
    if (n > total).any() or (n < 0).any():
        raise ValueError("n precisa estar entre 0 e o total de registros da área.")
    resto = total - contagens[:, None]  # N - N_i, uma linha por espécie
    n_linha = n[None, :]
    # log C(resto, n) - log C(total, n); onde resto < n a espécie aparece com certeza.
    possivel = resto >= n_linha
    resto_seguro = np.where(possivel, resto, n_linha)
    log_ausente = (
        gammaln(resto_seguro + 1)
        - gammaln(resto_seguro - n_linha + 1)
        - gammaln(total + 1)
        + gammaln(total - n_linha + 1)
    )
    prob_ausente = np.where(possivel, np.exp(log_ausente), 0.0)
    return (1.0 - prob_ausente).sum(axis=0)


def chao1(contagens: np.ndarray) -> float:
    """Estimativa mínima do total de espécies, contando as que ainda não apareceram (Chao, 1984).

    Usa as espécies vistas uma vez só (f1) e duas vezes (f2): muitas espécies raras indicam que
    ainda há várias por encontrar. Forma com correção de viés, que não quebra quando f2 = 0.
    """
    contagens = np.asarray(contagens)
    contagens = contagens[contagens > 0]
    f1 = int((contagens == 1).sum())
    f2 = int((contagens == 2).sum())
    return float(len(contagens) + f1 * (f1 - 1) / (2 * (f2 + 1)))


def completude(contagens: np.ndarray) -> float:
    """Fração das espécies estimadas (Chao1) que já foi registrada."""
    contagens = np.asarray(contagens)
    observadas = int((contagens > 0).sum())
    return observadas / chao1(contagens) if observadas else float("nan")


def chance_de_especie_nova(contagens: np.ndarray) -> float:
    """Chance de o próximo registro ser de uma espécie ainda não vista (Good-Turing): f1 / N."""
    contagens = np.asarray(contagens)
    contagens = contagens[contagens > 0]
    return float((contagens == 1).sum() / contagens.sum())


def intervalo_por_sorteio(
    contagens: np.ndarray, n: int, repeticoes: int = 300, semente: int = 42
) -> tuple[float, float, float]:
    """Média e faixa de 95% da riqueza em subamostras sorteadas de `n` registros.

    Confere a fórmula de rarefação por simulação e dá uma faixa. A faixa só reflete o acaso do
    sorteio; não cobre o viés de quem coletou, onde e com que método.
    """
    contagens = np.asarray(contagens, dtype=np.int64)
    contagens = contagens[contagens > 0]
    gerador = np.random.default_rng(semente)
    sorteios = gerador.multivariate_hypergeometric(contagens, n, size=repeticoes, method="marginals")
    riquezas = (sorteios > 0).sum(axis=1)
    return float(riquezas.mean()), float(np.quantile(riquezas, 0.025)), float(np.quantile(riquezas, 0.975))
