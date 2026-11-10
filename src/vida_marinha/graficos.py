"""Figuras do projeto. A cor segue a entidade: cinza é esforço, laranja é riqueza bruta, azul é riqueza rarefeita."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from vida_marinha.estilo import (
    APAGADO,
    AQUA,
    AZUL,
    EIXO,
    ESTILO,
    GRADE,
    LARANJA,
    SERIES,
    SUPERFICIE,
    TINTA,
    TINTA_SECUNDARIA,
    milhar,
    numero,
    percentual,
)


def _titulos(fig: Figure, titulo: str, subtitulo: str) -> None:
    fig.text(0.02, 0.965, titulo, fontsize=13, fontweight="bold", color=TINTA, va="top")
    fig.text(0.02, 0.915, subtitulo, fontsize=9.5, color=TINTA_SECUNDARIA, va="top")


def perfil_latitudinal(tabela: pd.DataFrame, n_ref: int) -> Figure:
    """Três painéis com as faixas de norte a sul: registros, riqueza bruta e riqueza rarefeita."""
    with plt.rc_context(ESTILO):
        fig, eixos = plt.subplots(1, 3, figsize=(8.6, 6.4), dpi=160, sharey=True)
        fig.subplots_adjust(top=0.82, left=0.13, right=0.97, bottom=0.07, wspace=0.10)
        _titulos(
            fig,
            "A faixa mais registrada lidera em espécies; corrigido o esforço, cai para o sexto lugar",
            "Costa do Brasil em faixas de 2° de latitude, do norte (em cima) ao sul. O destaque é a faixa de 24°S a 22°S.",
        )
        y = np.arange(len(tabela))
        paineis = [
            ("registros", "Registros (mil)", APAGADO, 1000),
            ("riqueza bruta", "Espécies registradas", LARANJA, 1),
            ("riqueza rarefeita", f"Espécies em {milhar(n_ref)} registros", AZUL, 1),
        ]
        destaque = tabela.index.get_loc("24°S a 22°S")
        for ax, (coluna, nome, cor, divisor) in zip(eixos, paineis):
            valores = tabela[coluna].to_numpy() / divisor
            ax.grid(axis="y", visible=False)
            ax.grid(axis="x", visible=True)
            ax.barh(y, valores, height=0.56, color=cor, zorder=3)
            ax.barh(y[destaque], valores[destaque], height=0.56, color=TINTA, zorder=4)
            casas = 0
            ax.annotate(
                milhar(valores[destaque]) if casas == 0 else numero(valores[destaque], casas),
                (valores[destaque], y[destaque]), xytext=(4, 0), textcoords="offset points",
                va="center", color=TINTA, fontsize=8.5,
            )
            ax.set_title(nome, fontsize=9.5, color=TINTA_SECUNDARIA, loc="left", pad=6)
            ax.set_xlim(0, valores.max() * 1.22)
            ax.xaxis.set_major_formatter(lambda v, _: milhar(v))
            ax.tick_params(axis="x", labelsize=8.5)
        eixos[0].set_yticks(y, list(tabela.index), fontsize=8.5)
        eixos[0].invert_yaxis()
        return fig


def riqueza_x_esforco(tabela: pd.DataFrame, relacoes: pd.DataFrame, n_ref: int) -> Figure:
    """Dois painéis: a riqueza bruta sobe com o número de registros; a rarefeita, não."""
    with plt.rc_context(ESTILO):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.6, 4.5), dpi=160)
        fig.subplots_adjust(top=0.76, left=0.09, right=0.97, bottom=0.14, wspace=0.26)
        _titulos(
            fig,
            "Mais registros, mais espécies. Com o mesmo número de registros, a relação some",
            "Cada ponto é uma faixa de 2° de latitude. Eixo horizontal em escala logarítmica.",
        )
        x = tabela["registros com espécie"]
        # Deslocamento e alinhamento de cada rótulo, escolhidos para não cobrir pontos vizinhos.
        rotulos = {
            "riqueza bruta": {
                "24°S a 22°S": ((-8, 6), "right"),
                "18°S a 16°S": ((-8, 7), "right"),
                "20°S a 18°S": ((8, 6), "left"),
                "16°S a 14°S": ((-4, 9), "center"),
                "4°N a 6°N": ((2, -13), "left"),
            },
            "riqueza rarefeita": {
                "24°S a 22°S": ((-8, 6), "right"),
                "18°S a 16°S": ((-8, 6), "right"),
                "20°S a 18°S": ((9, 4), "left"),
                "16°S a 14°S": ((-9, 0), "right"),
                "4°N a 6°N": ((5, -13), "left"),
            },
        }
        for ax, coluna, cor, chave, nome in [
            (ax1, "riqueza bruta", LARANJA, "riqueza bruta x registros", "Riqueza bruta"),
            (ax2, "riqueza rarefeita", AZUL, "riqueza rarefeita x registros", f"Riqueza em {milhar(n_ref)} registros"),
        ]:
            ax.grid(axis="x", visible=True)
            ax.plot(x, tabela[coluna], "o", color=cor, zorder=3)
            ax.set_xscale("log")
            rho = numero(relacoes.loc[chave, "rho"]).replace("-", "−")
            ax.set_title(f"{nome}   ·   correlação de postos: {rho}", fontsize=9.5, color=TINTA_SECUNDARIA, loc="left", pad=8)
            for faixa, (desloc, alinhar) in rotulos[coluna].items():
                ax.annotate(faixa, (x[faixa], tabela.loc[faixa, coluna]), xytext=desloc, textcoords="offset points", ha=alinhar, va="center", color=TINTA_SECUNDARIA, fontsize=8)
            ax.set_xlabel("registros identificados até espécie")
            ax.xaxis.set_major_formatter(lambda v, _: milhar(v))
            ax.yaxis.set_major_formatter(lambda v, _: milhar(v))
            ax.set_ylim(0, tabela[coluna].max() * 1.15)
        ax1.set_ylabel("espécies")
        return fig


def curvas_de_rarefacao(curvas: pd.DataFrame, n_ref: int) -> Figure:
    """Curvas de rarefação de quatro faixas: a ordem depende de onde se corta."""
    with plt.rc_context(ESTILO):
        fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=160)
        fig.subplots_adjust(top=0.78, left=0.09, right=0.80, bottom=0.14)
        _titulos(
            fig,
            "Comparadas com o mesmo número de registros, as faixas trocam de ordem",
            "Espécies esperadas numa subamostra aleatória dos registros de cada faixa (rarefação de Hurlbert).",
        )
        limite = curvas.index.max()
        for cor, faixa in zip(SERIES, curvas.columns):
            serie = curvas[faixa].dropna()
            x_final, valor = serie.index[-1], serie.iloc[-1]
            ax.plot(serie.index, serie.to_numpy(), color=cor, label=faixa, zorder=3)
            if x_final > 0.7 * limite:
                ax.annotate(f"{faixa}  {milhar(valor)}", (x_final, valor), xytext=(8, 0), textcoords="offset points", va="center", color=TINTA_SECUNDARIA, fontsize=8.5)
            else:
                # Curva que acaba antes: a faixa tem menos registros. O ponto marca o fim dos dados dela.
                ax.plot(x_final, valor, "o", color=cor, zorder=4)
        ax.axvline(n_ref, color=EIXO, linewidth=1.2, zorder=1)
        ax.annotate(f"régua comum:\n{milhar(n_ref)} registros", (n_ref, curvas.max().max()), xytext=(5, 0), textcoords="offset points", va="top", color=APAGADO, fontsize=8.5)
        ax.set_xlim(0, limite)
        ax.set_ylim(0, curvas.max().max() * 1.05)
        ax.set_xlabel("registros na subamostra (a curva termina onde acabam os registros da faixa)")
        ax.set_ylabel("espécies esperadas")
        ax.xaxis.set_major_formatter(lambda v, _: milhar(v))
        ax.yaxis.set_major_formatter(lambda v, _: milhar(v))
        ax.legend(loc="lower right", fontsize=8.5)
        return fig


def troca_de_ranking(tabela: pd.DataFrame, n_ref: int, salto: int = 10) -> Figure:
    """Gráfico de inclinação: posto de cada faixa pela riqueza bruta e pela rarefeita."""
    with plt.rc_context(ESTILO):
        fig, ax = plt.subplots(figsize=(8.6, 6.9), dpi=160)
        fig.subplots_adjust(top=0.80, left=0.30, right=0.70, bottom=0.03)
        _titulos(
            fig,
            "O ranking de riqueza muda quando todas as faixas são medidas com a mesma régua",
            f"Posto de cada faixa (1 = mais espécies). Em destaque, a líder em riqueza bruta e as que mudam {salto} posições ou mais.",
        )
        ax.grid(visible=False)
        for lado in ("bottom", "left"):
            ax.spines[lado].set_visible(False)
        for faixa, linha in tabela.iterrows():
            a, b = linha["posto pela riqueza bruta"], linha["posto pela riqueza rarefeita"]
            forte = abs(a - b) >= salto or a == 1
            cor = AZUL if forte else GRADE
            ax.plot([0, 1], [a, b], "-o", color=cor, linewidth=2 if forte else 1.4, zorder=3 if forte else 2,
                    markerfacecolor=cor if forte else APAGADO, markersize=7)
            tinta = TINTA if forte else TINTA_SECUNDARIA
            peso = "bold" if forte else "normal"
            ax.annotate(f"{faixa}  ·  {milhar(linha['riqueza bruta'])}", (0, a), xytext=(-10, 0), textcoords="offset points", ha="right", va="center", color=tinta, fontsize=8.5, fontweight=peso)
            ax.annotate(f"{milhar(linha['riqueza rarefeita'])}  ·  {faixa}", (1, b), xytext=(10, 0), textcoords="offset points", ha="left", va="center", color=tinta, fontsize=8.5, fontweight=peso)
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(len(tabela) + 0.7, 0.3)
        ax.set_xticks([0, 1], ["Riqueza bruta\n(espécies registradas)", f"Riqueza rarefeita\n(espécies em {milhar(n_ref)} registros)"], fontsize=9.5)
        ax.xaxis.tick_top()
        ax.tick_params(axis="x", length=0)
        ax.set_yticks([])
        return fig


def fontes_das_tartarugas(por_faixa: pd.DataFrame, por_tipo: pd.DataFrame) -> Figure:
    """Barras empilhadas por faixa: de que tipo de fonte vêm os registros de tartarugas-marinhas."""
    with plt.rc_context(ESTILO):
        fig, ax = plt.subplots(figsize=(8.6, 6.0), dpi=160)
        fig.subplots_adjust(top=0.82, left=0.13, right=0.96, bottom=0.13)
        _titulos(
            fig,
            "O mapa das tartarugas mostra onde há celulares e transmissores, não onde há tartarugas",
            "Registros das cinco espécies de tartarugas-marinhas por faixa de latitude e tipo de fonte.",
        )
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        cores = {"ciência cidadã": AZUL, "telemetria": LARANJA, "levantamento ou coleção": AQUA}
        y = np.arange(len(por_faixa))
        esquerda = np.zeros(len(por_faixa))
        for tipo in [t for t in cores if t in por_faixa.columns]:
            valores = por_faixa[tipo].to_numpy()
            fracao = por_tipo.loc[tipo, "fração"]
            ax.barh(y, valores, left=esquerda, height=0.58, color=cores[tipo], edgecolor=SUPERFICIE, linewidth=1.5,
                    label=f"{tipo} ({percentual(fracao)})", zorder=3)
            esquerda += valores
        maior = int(esquerda.argmax())
        ax.annotate(f"{milhar(esquerda[maior])} registros", (esquerda[maior], y[maior]), xytext=(5, 0), textcoords="offset points", va="center", color=TINTA, fontsize=8.5)
        ax.set_yticks(y, list(por_faixa.index), fontsize=8.5)
        ax.invert_yaxis()
        ax.set_xlim(0, esquerda.max() * 1.18)
        ax.set_xlabel("registros")
        ax.xaxis.set_major_formatter(lambda v, _: milhar(v))
        ax.legend(loc="lower right", fontsize=9)
        return fig
