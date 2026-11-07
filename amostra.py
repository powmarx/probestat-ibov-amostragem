"""Dimensionamento e seleção da amostra aleatória simples (AAS) sem reposição.

Tamanho: estimação de uma proporção com correção para população finita
    n0 = z² · p · (1 − p) / e²        n = n0 / (1 + (n0 − 1) / N)
com 95% de confiança (z = 1,959964), margem e = 2 p.p., p = 0,5 (pior caso), efeito do desenho 1 e
perda 0%. Referência: Bolfarine, H.; Bussab, W. O. Elementos de Amostragem. Blucher, 2005.
O cálculo é feito aqui, sem calculadora externa (o professor dispensou a da USP/Bauru, sugerida no
enunciado).

Seleção: numpy.random.default_rng(SEMENTE).choice(N, n, replace=False) sobre os ids 0..N−1 da
população, na ordem fixa (ativo, data). Todo elemento tem a mesma probabilidade n/N.

    python amostra.py        # grava dados/amostra.parquet, dados/amostra.csv e dados/manifesto.json
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent
DADOS = RAIZ / 'dados'
SEMENTE = 2026
Z = {95: 1.959963984540054, 99: 2.5758293035489004}


def tamanho(N: int, confianca: int = 95, erro_pp: float = 2.0, proporcao_pct: float = 50.0,
            efeito_desenho: float = 1.0, perda_pct: float = 0.0) -> dict:
    """Tamanho para estimar uma proporção: confiança, margem, proporção, N, efeito do desenho e perda.

    Correção para população finita de Cochran (1977): n = n0 / (1 + (n0 − 1)/N).
    """
    z, e, p = Z[confianca], erro_pp / 100, proporcao_pct / 100
    n0 = z ** 2 * p * (1 - p) / e ** 2
    n_fin = n0 / (1 + (n0 - 1) / N)
    n_des = n_fin * efeito_desenho
    n_final = n_des / (1 - perda_pct / 100)
    return {'z': z, 'n0': n0, 'n_infinita': math.ceil(n0), 'n_finita_exato': n_fin,
            'n': math.ceil(n_final - 1e-9)}


def sortear(N: int, n: int, semente: int = SEMENTE) -> np.ndarray:
    return np.random.default_rng(semente).choice(N, n, replace=False)


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    P = pd.read_parquet(DADOS / 'populacao.parquet')
    N = len(P)
    assert (P['id'].values == np.arange(N)).all(), 'ids da população fora da ordem 0..N−1'
    t = tamanho(N)
    ids = sortear(N, t['n'])
    assert len(set(ids)) == t['n'] and (sortear(N, t['n']) == ids).all()
    A = P.iloc[ids].assign(ordem_sorteio=np.arange(1, t['n'] + 1)).sort_values('id')
    A.to_parquet(DADOS / 'amostra.parquet', index=False)
    A.to_csv(DADOS / 'amostra.csv', index=False, date_format='%Y-%m-%d', float_format='%.6f')
    man = {
        'gerado_em': datetime.now().isoformat(timespec='seconds'),
        'populacao': {'N': N, 'inicio': P['data'].min().date().isoformat(),
                      'fim': P['data'].max().date().isoformat(), 'acoes': int(P['ativo'].nunique()),
                      'pregoes': int(P['data'].nunique()),
                      'sha256_csv': _sha256(DADOS / 'populacao.csv')},
        'dimensionamento': {'confianca_pct': 95, 'erro_pp': 2.0, 'proporcao_pct': 50.0,
                            'efeito_desenho': 1.0, 'perda_pct': 0.0, **t},
        'selecao': {'metodo': 'AAS sem reposição', 'semente': SEMENTE,
                    'codigo': f'numpy.random.default_rng({SEMENTE}).choice({N}, {t["n"]}, replace=False)',
                    'numpy': np.__version__, 'sha256_csv': _sha256(DADOS / 'amostra.csv')},
    }
    (DADOS / 'manifesto.json').write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'n0 = {t["n0"]:.1f} -> n = {t["n_finita_exato"]:.1f} -> {t["n"]} (N = {N})')
    print(f'Amostra: {t["n"]} pares ação-dia sorteados com a semente {SEMENTE}; '
          f'{A["ativo"].nunique()} ações, {A["data"].nunique()} pregões distintos.')


if __name__ == '__main__':
    main()
