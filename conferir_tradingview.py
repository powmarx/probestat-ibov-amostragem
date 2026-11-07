"""Conferência da base do Yahoo com uma segunda fonte (TradingView) — docs/conferencia_tradingview.md.

Download (uma vez; precisa da biblioteca tvdatafeed, que está no venv antigo do curso):
    E:\\OneDrive\\PosIA\\.venv\\Scripts\\python.exe conferir_tradingview.py --baixar
grava dados/bruto/tv_1d/<ATIVO>.parquet (até DATA_FIM) e se recusa a sobrescrever uma cópia existente.

Comparação (usada por preparar_dados.py, sem rede e sem tvdatafeed): para cada linha da população,
o retorno do dia nas duas fontes, cada uma com o próprio fechamento anterior e só dias com negócio.
Categorias, na ordem (a primeira que vale define):
  1 sem dado no TradingView   o TradingView não tem negócio no dia
  2 intervalo diferente       o pregão anterior não é o mesmo nas duas fontes
  3 idêntico                  diferença no retorno ≤ 0,01 p.p.
  4 diferença até 5 p.p.      0,01 < diferença ≤ 5 p.p.
  5 corrigido pelo TradingView diferença > 5 p.p.: os preços da linha passam a ser os do TradingView
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent
TV = RAIZ / 'dados' / 'bruto' / 'tv_1d'
BRUTO_YAHOO = RAIZ / 'dados' / 'bruto' / '1d'
DATA_FIM = pd.Timestamp('2026-10-30')
LIMITE_IDENTICO = 0.01        # p.p.
LIMITE_CORRECAO = 5.0         # p.p.

SEM_DADO = 'sem dado no TradingView'
INTERVALO = 'intervalo diferente'
IDENTICO = 'idêntico'
PEQUENA = 'diferença até 5 p.p.'
CORRIGIDO = 'corrigido pelo TradingView'
CATEGORIAS = [IDENTICO, PEQUENA, CORRIGIDO, INTERVALO, SEM_DADO]


# ---------------------------------------------------------------- download (uma vez)
def baixar() -> None:
    if TV.exists() and any(TV.glob('*.parquet')):
        sys.exit(f'{TV} já existe: a cópia do TradingView já foi congelada e não deve ser sobrescrita.')
    import logging
    from tvDatafeed import Interval, TvDatafeed           # só aqui: o resto não precisa da biblioteca
    logging.getLogger('tvDatafeed.main').setLevel(logging.CRITICAL)
    TV.mkdir(parents=True, exist_ok=True)
    acoes = sorted(p.stem for p in BRUTO_YAHOO.glob('*.parquet') if p.stem != 'IBOV')
    tv, falhas = TvDatafeed(), []
    for a in acoes:
        x = None
        for k in range(5):
            try:
                x = tv.get_hist(symbol=a, exchange='BMFBOVESPA', interval=Interval.in_daily, n_bars=5000)
                if x is not None and not x.empty:
                    break
            except Exception:
                pass
            time.sleep(4 + 2 * k)
            tv = TvDatafeed()
        if x is None or x.empty:
            falhas.append(a)
            continue
        x.index = pd.to_datetime(x.index).normalize()
        x.index.name = 'datetime'
        x = x[~x.index.duplicated(keep='last')].sort_index()
        x.loc[:DATA_FIM, ['open', 'high', 'low', 'close', 'volume']].to_parquet(TV / f'{a}.parquet')
        time.sleep(0.8)
    gravar_manifesto(datetime.now().isoformat(timespec='seconds'), falhas)
    print(f'Congeladas {len(acoes) - len(falhas)} de {len(acoes)} ações em {TV}. Falhas: {falhas or "nenhuma"}')


def gravar_manifesto(baixado_em: str, falhas=()) -> None:
    man = {'baixado_em': baixado_em, 'data_fim': DATA_FIM.date().isoformat(),
           'arquivos': len(list(TV.glob('*.parquet'))), 'falhas': list(falhas),
           'fonte': 'TradingView, bolsa BMFBOVESPA, diário, via biblioteca tvdatafeed (não oficial), sem login',
           'uso': 'só conferência da base do Yahoo (docs/conferencia_tradingview.md)'}
    (TV.parent / 'manifesto_tv.json').write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding='utf-8')


# ---------------------------------------------------------------- comparação
def ler_tv() -> pd.DataFrame:
    """Uma linha por ação e dia com negócio no TradingView, com o fechamento anterior da própria fonte."""
    if not TV.exists():
        sys.exit(f'Falta a cópia do TradingView em {TV}. Rode: conferir_tradingview.py --baixar')
    partes = []
    for p in sorted(TV.glob('*.parquet')):
        x = pd.read_parquet(p)
        x = x[x['volume'] > 0]
        partes.append(pd.DataFrame({
            'ativo': p.stem, 'data': x.index,
            'data_anterior_tv': pd.Series(x.index, index=x.index).shift(1).values,
            'abertura_tv': x['open'].values, 'maxima_tv': x['high'].values, 'minima_tv': x['low'].values,
            'fechamento_tv': x['close'].values, 'fechamento_anterior_tv': x['close'].shift(1).values}))
    return pd.concat(partes, ignore_index=True)


def comparar(P: pd.DataFrame, tv: pd.DataFrame | None = None) -> pd.DataFrame:
    """Linha a linha (mesma ordem de P): retornos nas duas fontes, diferença e categoria."""
    tv = ler_tv() if tv is None else tv
    M = P[['ativo', 'data', 'data_anterior', 'ret', 'gap']].merge(tv, on=['ativo', 'data'], how='left')
    M['ret_tv'] = (M['fechamento_tv'] / M['fechamento_anterior_tv'] - 1) * 100
    M['gap_tv'] = (M['abertura_tv'] / M['fechamento_anterior_tv'] - 1) * 100
    M['diferenca'] = (M['ret'] - M['ret_tv']).abs()
    mesmo = M['data_anterior'] == M['data_anterior_tv']
    M['conferencia_tv'] = np.select(
        [M['ret_tv'].isna(), ~mesmo, M['diferenca'] <= LIMITE_IDENTICO, M['diferenca'] <= LIMITE_CORRECAO],
        [SEM_DADO, INTERVALO, IDENTICO, PEQUENA], CORRIGIDO)
    M.index = P.index
    return M


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--baixar', action='store_true', help='baixa e congela a cópia do TradingView (uma vez)')
    if ap.parse_args().baixar:
        baixar()
    else:
        ap.print_help()
