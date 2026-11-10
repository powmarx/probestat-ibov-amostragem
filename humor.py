"""Fear & Greed B3 diário: o "humor" do mercado, de 0 (medo extremo) a 100 (ganância extrema).

Cópia do cálculo diário do trabalho final da disciplina IA001 – Análise e Visualização de Dados com
Python e Ferramentas Assistidas por IA ("Análise Ibovespa — Volume, Volatilidade e Top 3",
Visualizacao/trabalho_final/sentimento.py), sem mudanças no método. Copiado para este projeto não
depender da pasta antiga.

Cinco componentes, cada um em percentil (0 a 100) contra TODOS os dias anteriores (mínimo de 252),
e o índice é a média dos cinco:
  momento       Ibovespa em relação à média de 125 pregões
  amplitude     % das ações acima da própria média de 50 pregões
  forca         % das ações perto da máxima de 252 pregões − % perto da mínima
  vol_direcao   fatia do volume das ações negociada em dias de alta, últimos 10 pregões
  volatilidade  desvio de 20 pregões ÷ desvio de 252 pregões do Ibovespa (sinal invertido)
Faixas: 0–25 medo extremo | 25–45 medo | 45–55 neutro | 55–75 ganância | 75–100 ganância extrema.

Neste trabalho o índice é só descritivo e entra com UM pregão de defasagem (`fg_ant`): o índice do
dia usa os preços do próprio dia, então compará-lo com o retorno do mesmo dia seria circular.
"""
from __future__ import annotations

import bisect

import numpy as np
import pandas as pd

NAO_ACOES = {'IBOV', 'BOVA11', 'WIN', 'IND'}
MIN_DIAS_REF = 252
FAIXAS = [(0, 25, 'medo extremo'), (25, 45, 'medo'), (45, 55, 'neutro'),
          (55, 75, 'ganância'), (75, 100.0001, 'ganância extrema')]
ORDEM_FAIXAS = [f[2] for f in FAIXAS]
SEM_REFERENCIA = 'sem referência'
COMPONENTES = ['momento', 'amplitude', 'forca', 'vol_direcao', 'volatilidade']


def faixa(valor: float) -> str:
    if valor is None or not np.isfinite(valor):
        return SEM_REFERENCIA
    for lo, hi, nome in FAIXAS:
        if lo <= valor < hi:
            return nome
    return 'ganância extrema'


def rotular(serie: pd.Series) -> pd.Series:
    return serie.map(faixa)


def percentil_dias_anteriores(x: pd.Series, min_dias: int = MIN_DIAS_REF) -> pd.Series:
    """Percentil (0-100) de cada dia contra todos os dias anteriores (histórico expansivo)."""
    out = np.full(len(x), np.nan)
    hist: list[float] = []                     # valores dos dias anteriores, ordenados
    for i, v in enumerate(x.astype(float).values):
        if not np.isfinite(v):
            continue
        if len(hist) >= min_dias:
            out[i] = 100 * bisect.bisect_right(hist, v) / len(hist)
        bisect.insort(hist, v)
    return pd.Series(out, index=x.index)


def componentes_diarios(series_1d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ibov = series_1d['IBOV']['close'].sort_index()
    acoes = [t for t in series_1d if t not in NAO_ACOES]
    close = pd.DataFrame({t: series_1d[t]['close'] for t in acoes}).sort_index()
    idx = ibov.index.intersection(close.index)
    ibov, close = ibov.loc[idx], close.loc[idx]
    vol = pd.DataFrame({t: series_1d[t]['volume'] for t in acoes}).reindex(idx).fillna(0)

    mm50 = close.rolling(50, min_periods=50).mean()
    max252 = close.rolling(252, min_periods=252).max()
    min252 = close.rolling(252, min_periods=252).min()
    valido50 = mm50.notna()
    valido252 = max252.notna()
    sobe = (close.diff() > 0).astype(float)
    r = ibov.pct_change()

    c = pd.DataFrame(index=idx)
    c['momento'] = (ibov / ibov.rolling(125, min_periods=125).mean() - 1) * 100
    c['amplitude'] = ((close > mm50) & valido50).sum(axis=1) / valido50.sum(axis=1).replace(0, np.nan) * 100
    perto_max = (close >= 0.98 * max252) & valido252
    perto_min = (close <= 1.02 * min252) & valido252
    c['forca'] = (perto_max.sum(axis=1) - perto_min.sum(axis=1)) / valido252.sum(axis=1).replace(0, np.nan) * 100
    c['vol_direcao'] = ((vol * sobe).rolling(10).sum().sum(axis=1)
                        / vol.rolling(10).sum().sum(axis=1).replace(0, np.nan))
    c['volatilidade'] = -(r.rolling(20).std() / r.rolling(252).std())
    return c


def fear_greed_diario(series_1d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    brutos = componentes_diarios(series_1d)
    pct = pd.DataFrame({c: percentil_dias_anteriores(brutos[c]) for c in COMPONENTES})
    out = pct.copy()
    out['indice'] = pct.mean(axis=1, skipna=False)
    out['faixa'] = rotular(out['indice'])
    return out


def humor_anterior(series_1d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """`fg_ant` e `humor_ant` de cada pregão: o índice e a faixa do pregão ANTERIOR."""
    fg = fear_greed_diario(series_1d)
    ant = fg['indice'].shift(1)
    return pd.DataFrame({'fg_ant': ant, 'humor_ant': rotular(ant)}, index=fg.index)
