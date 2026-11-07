"""Congela a base bruta e monta a população do trabalho.

Etapa 1 (congelar, só uma vez): copia de dados_mercado/serie/1d os arquivos diários das 40 ações e
do Ibovespa até a DATA_FIM, sem a coluna interna `coletado_em`, para dados/bruto/1d/. Depois disso o
trabalho não depende mais do coletor, que continua gravando dias novos.

Etapa 2 (setores): a partir da resposta da API da B3 (dados/b3_classificacao_setorial.json), grava
dados/setores.csv com setor, subsetor e segmento das 40 ações, com as vírgulas dos nomes oficiais
restauradas (a API troca vírgula por ponto).

Etapa 3 (população): a partir de dados/bruto/1d/, um registro por ação e pregão entre DATA_INICIO e
DATA_FIM, só dias com negócio (volume > 0). O fechamento anterior é o do último pregão com negócio da
mesma ação. Cada linha é conferida com o TradingView (dados/bruto/tv_1d/, conferir_tradingview.py): as
linhas com diferença > 5 p.p. no retorno, com o mesmo pregão anterior, recebem os preços dessa fonte
(coluna `conferencia_tv`; comparação completa em dados/conferencia_tradingview.parquet; ver
docs/conferencia_tradingview.md). Ordem fixa: ativo (alfabética) e data; `id` de 0 a N−1. Grava dados/populacao.parquet,
dados/populacao.csv e dados/populacao.zip (o CSV compactado, que é o que vai para o GitHub). Colunas descritivas extras: `setor`, `vol_rel`, `faixa_volume` (volume do dia
contra a mediana dos 20 pregões anteriores) e `fg_ant`, `humor_ant` (Fear & Greed B3 do pregão
anterior, humor.py). Elas não mudam os ids nem a amostra.

    python preparar_dados.py             # monta a população a partir do bruto congelado
    python preparar_dados.py --congelar  # copia o bruto de dados_mercado (recusa se já existir)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import conferir_tradingview as CT
import humor

RAIZ = Path(__file__).resolve().parent
ORIGEM = RAIZ.parents[1] / 'dados_mercado' / 'serie' / '1d'
BRUTO = RAIZ / 'dados' / 'bruto' / '1d'
SAIDA = RAIZ / 'dados'

DATA_INICIO = pd.Timestamp('2016-10-31')   # 10 anos exatos até o último pregão antes do congelamento
DATA_FIM = pd.Timestamp('2026-10-30')
INDICE = 'IBOV'
NAO_ACOES = {'IBOV', 'BOVA11', 'WIN', 'IND'}
COLUNAS = ['open', 'high', 'low', 'close', 'volume']

# Erros da fonte: cada linha é conferida com o TradingView (conferir_tradingview.py). As linhas com
# diferença > 5 p.p. no retorno, com o mesmo pregão anterior, recebem os preços do TradingView.
# Ver docs/conferencia_tradingview.md.
CONFERENCIA = SAIDA / 'conferencia_tradingview.parquet'

FAIXAS = [(-np.inf, 1, 'calmo'), (1, 2, 'normal'), (2, 5, 'agitado'), (5, np.inf, 'extremo')]
DIAS = ['segunda', 'terça', 'quarta', 'quinta', 'sexta']

JSON_B3 = SAIDA / 'b3_classificacao_setorial.json'
SETORES = SAIDA / 'setores.csv'
JANELA_VOLUME = 20                          # pregões anteriores na referência do volume relativo
FAIXAS_VOLUME = [(0.75, 'baixo'), (1.5, 'normal'), (np.inf, 'alto')]   # limite superior aberto
SEM_REFERENCIA = humor.SEM_REFERENCIA


def _nome_oficial(s: str) -> str:
    """A API da B3 troca ', ' por '. ' ('Petróleo. Gás e Biocombustíveis'); restaura a vírgula."""
    return s.strip().replace(' . ', ', ').replace('..', '., ').replace('. ', ', ')


def gerar_setores() -> pd.DataFrame:
    dados = json.loads(JSON_B3.read_text(encoding='utf-8'))
    linhas = []
    for e in dados['empresas']:
        setor, subsetor, segmento = [_nome_oficial(p) for p in e['classificacao_b3'].split(' / ')]
        linhas.append({'ativo': e['ativo'], 'empresa': e['nome'], 'codigo_cvm': e['codeCVM'],
                       'setor': setor, 'subsetor': subsetor, 'segmento': segmento})
    S = pd.DataFrame(linhas).sort_values('ativo').reset_index(drop=True)
    S.to_csv(SETORES, index=False, encoding='utf-8')
    return S


def vol_relativo(d: pd.DataFrame) -> pd.Series:
    """Volume financeiro do dia ÷ mediana dos 20 pregões ANTERIORES com negócio da mesma ação.

    `d` já filtrado para volume > 0. Usa só o passado (shift(1) antes da janela)."""
    fin = d['close'] * d['volume']
    ref = fin.shift(1).rolling(JANELA_VOLUME, min_periods=JANELA_VOLUME).median()
    return fin / ref


def _faixa_volume(v: pd.Series) -> pd.Series:
    out = pd.Series(SEM_REFERENCIA, index=v.index, dtype=object)
    lo = -np.inf
    for hi, nome in FAIXAS_VOLUME:
        out[(v >= lo) & (v < hi)] = nome
        lo = hi
    return out.astype(str)


def ler_bruto() -> dict[str, pd.DataFrame]:
    return {p.stem: pd.read_parquet(p) for p in sorted(BRUTO.glob('*.parquet'))}


def congelar() -> None:
    if BRUTO.exists() and any(BRUTO.glob('*.parquet')):
        sys.exit(f'{BRUTO} já existe: a base já foi congelada e não deve ser sobrescrita.')
    BRUTO.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(p for p in ORIGEM.glob('*.parquet') if p.stem not in NAO_ACOES - {INDICE})
    for p in arquivos:
        d = pd.read_parquet(p)[COLUNAS]
        d.index = d.index.normalize()
        d = d[~d.index.duplicated(keep='last')].sort_index()
        d.loc[:DATA_FIM].to_parquet(BRUTO / p.name)
    man = {'congelado_em': datetime.now().isoformat(timespec='seconds'), 'origem': str(ORIGEM),
           'data_fim': DATA_FIM.date().isoformat(), 'arquivos': len(arquivos),
           'fonte': 'Yahoo Finance, https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}.SA'
                    '?interval=1d&range=10y'}
    (BRUTO.parent / 'manifesto_bruto.json').write_text(json.dumps(man, indent=2, ensure_ascii=False),
                                                       encoding='utf-8')
    print(f'Congelados {len(arquivos)} arquivos em {BRUTO} (até {DATA_FIM:%d/%m/%Y}).')


def _faixa(r: pd.Series) -> pd.Series:
    """|ret| ≤ 1% calmo; (1, 2] normal; (2, 5] agitado; > 5% extremo."""
    return pd.cut(r.abs(), bins=[f[0] for f in FAIXAS] + [np.inf],
                  labels=[f[2] for f in FAIXAS]).astype(str)


def _corrigir_pelo_tradingview(P: pd.DataFrame, M: pd.DataFrame) -> pd.DataFrame:
    """Nas linhas 'corrigido pelo TradingView', preços do TradingView e razões recalculadas.

    Ficam do Yahoo: volume, fin, vol_rel, ret_ibov, a data do pregão anterior (igual nas duas fontes)."""
    k = M.index[M['conferencia_tv'] == CT.CORRIGIDO]
    P = P.copy()
    for col, tv in (('abertura', 'abertura_tv'), ('maxima', 'maxima_tv'), ('minima', 'minima_tv'),
                    ('fechamento', 'fechamento_tv'), ('fechamento_anterior', 'fechamento_anterior_tv')):
        P.loc[k, col] = M.loc[k, tv]
    c = P.loc[k]
    P.loc[k, 'ret'] = (c['fechamento'] / c['fechamento_anterior'] - 1) * 100
    P.loc[k, 'gap'] = (c['abertura'] / c['fechamento_anterior'] - 1) * 100
    P.loc[k, 'intra'] = (c['fechamento'] / c['abertura'] - 1) * 100
    P.loc[k, 'amp'] = (c['maxima'] - c['minima']) / c['fechamento_anterior'] * 100
    return P


def populacao(bruto: dict[str, pd.DataFrame] | None = None, setores: pd.DataFrame | None = None,
              tv: pd.DataFrame | None = None, devolver_conferencia: bool = False):
    if bruto is None:
        if not (BRUTO / f'{INDICE}.parquet').exists():
            sys.exit(f'Falta a base congelada em {BRUTO}. Rode: python preparar_dados.py --congelar')
        bruto = ler_bruto()
    if setores is None:
        setores = pd.read_csv(SETORES) if SETORES.exists() else gerar_setores()
    ib = bruto[INDICE]['close']

    partes = []
    for nome in sorted(bruto):                           # ordem alfabética dos tickers
        if nome in NAO_ACOES:
            continue
        d = bruto[nome].dropna(subset=['open', 'high', 'low', 'close'])
        d = d[d['volume'] > 0]
        fech_ant = d['close'].shift(1)
        x = pd.DataFrame({
            'ativo': nome,
            'abertura': d['open'], 'maxima': d['high'], 'minima': d['low'], 'fechamento': d['close'],
            'data_anterior': pd.Series(d.index, index=d.index).shift(1),
            'fechamento_anterior': fech_ant, 'volume': d['volume'],
            'ret': (d['close'] / fech_ant - 1) * 100,
            'gap': (d['open'] / fech_ant - 1) * 100,
            'intra': (d['close'] / d['open'] - 1) * 100,
            'amp': (d['high'] - d['low']) / fech_ant * 100,
            'fin': d['close'] * d['volume'] / 1e6,
            'vol_rel': vol_relativo(d),                  # calculado antes do corte da janela
        }, index=d.index)
        partes.append(x.iloc[1:])                        # 1º dia da ação: sem fechamento anterior
    P = pd.concat(partes)
    P.index.name = 'data'
    P = P.reset_index()
    P = P[(P['data'] >= DATA_INICIO) & (P['data'] <= DATA_FIM)]

    # Ibovespa no MESMO intervalo do retorno da ação: do último pregão com negócio da ação até hoje.
    # (Em 94 linhas a ação ficou dias sem negócio, ou a fonte não tem o dia, como 29/05/2017.)
    P['ret_ibov'] = (ib.reindex(P['data']).values / ib.reindex(P['data_anterior']).values - 1) * 100

    # conferência com o TradingView, antes das variáveis que dependem do retorno
    M = CT.comparar(P, tv)
    P = _corrigir_pelo_tradingview(P, M)
    P['conferencia_tv'] = M['conferencia_tv']

    P['ano'] = P['data'].dt.year
    P['dia_semana'] = P['data'].dt.dayofweek.map(dict(enumerate(DIAS)))
    P['direcao'] = np.select([P['ret'] > 0, P['ret'] < 0], ['alta', 'baixa'], 'sem variação')
    P['segue_ibov'] = np.where(P['ret'] == 0, 'sem variação',
                               np.where(np.sign(P['ret']) == np.sign(P['ret_ibov']), 'sim', 'não'))
    P['faixa'] = _faixa(P['ret'])
    P['faixa_volume'] = _faixa_volume(P['vol_rel'])

    # Fear & Greed B3 do pregão ANTERIOR (o do próprio dia usa os preços do dia: seria circular)
    h = humor.humor_anterior(bruto)
    P['fg_ant'] = h['fg_ant'].reindex(P['data']).values
    P['humor_ant'] = rotular_humor(P['fg_ant'])

    P['setor'] = P['ativo'].map(setores.set_index('ativo')['setor'])

    P = P.sort_values(['ativo', 'data'], kind='mergesort')
    M = M.loc[P.index].reset_index(drop=True)
    P = P.reset_index(drop=True)
    P.insert(0, 'id', np.arange(len(P)))
    if not devolver_conferencia:
        return P[COLUNAS_POPULACAO]
    M.insert(0, 'id', P['id'])
    colunas = ['id', 'ativo', 'data', 'data_anterior', 'data_anterior_tv', 'ret', 'ret_tv', 'gap', 'gap_tv',
               'diferenca', 'conferencia_tv', 'fechamento_tv', 'fechamento_anterior_tv']
    return P[COLUNAS_POPULACAO], M[colunas].rename(columns={'ret': 'ret_yahoo', 'gap': 'gap_yahoo'})


def rotular_humor(fg: pd.Series) -> pd.Series:
    return pd.Series(humor.rotular(pd.Series(fg)).values, index=fg.index)


COLUNAS_POPULACAO = [
    'id', 'data', 'ativo', 'setor',
    'abertura', 'maxima', 'minima', 'fechamento', 'volume', 'data_anterior', 'fechamento_anterior',
    'ret', 'gap', 'intra', 'amp', 'fin', 'ret_ibov', 'vol_rel', 'fg_ant',
    'ano', 'dia_semana', 'direcao', 'segue_ibov', 'faixa', 'faixa_volume', 'humor_ant', 'conferencia_tv',
]


ZIP_POPULACAO = SAIDA / 'populacao.zip'


def compactar_csv(csv: Path = SAIDA / 'populacao.csv', destino: Path = ZIP_POPULACAO) -> None:
    """Grava o CSV da população dentro de um zip (é o que vai para o GitHub; o CSV tem ~24 MB).

    Data interna fixa, para o zip sair igual a cada execução.
    """
    import zipfile
    info = zipfile.ZipInfo(csv.name, date_time=(2026, 10, 31, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(destino, 'w') as z:
        z.writestr(info, csv.read_bytes(), compresslevel=9)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--congelar', action='store_true')
    args = ap.parse_args()
    if args.congelar:
        congelar()
    S = gerar_setores()
    P, M = populacao(setores=S, devolver_conferencia=True)
    M.to_parquet(CONFERENCIA, index=False)
    assert P['ret_ibov'].notna().all(), 'pregão de ação sem Ibovespa'
    assert P[['ret', 'gap', 'intra', 'amp']].notna().all().all()
    assert P['setor'].notna().all(), 'ação sem setor em setores.csv'
    P.to_parquet(SAIDA / 'populacao.parquet', index=False)
    P.to_csv(SAIDA / 'populacao.csv', index=False, date_format='%Y-%m-%d', float_format='%.6f')
    compactar_csv()
    n_fmt = f'{len(P):,}'.replace(',', '.')
    print(f'População: N = {n_fmt} pares ação-dia, {P["ativo"].nunique()} ações, '
          f'{P["data"].nunique()} pregões, {P["data"].min():%d/%m/%Y} a {P["data"].max():%d/%m/%Y}. '
          f'Conferência TradingView: {P["conferencia_tv"].value_counts().to_dict()}. {len(P.columns)} colunas. '
          f'{S["setor"].nunique()} setores. vol_rel vazio em {int(P["vol_rel"].isna().sum())} linhas; '
          f'fg_ant em {P["fg_ant"].notna().mean() * 100:.1f}% das linhas.')


if __name__ == '__main__':
    main()
