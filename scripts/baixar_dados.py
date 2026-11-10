"""Regenera o extrato agregado em data/ a partir da API do OBIS (leva alguns minutos)."""

import sys

from vida_marinha.dados import baixar

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    coleta = baixar()
    print(f"Coleta de {coleta['coletado_em']}: {coleta['linhas']}")
