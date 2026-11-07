"""Análise descritiva: medidas, frequências e dados dos gráficos, sem Streamlit.

As mesmas funções servem ao Painel 1 (população) e ao Painel 2 (amostra), para a comparação usar
exatamente o mesmo cálculo dos dois lados.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import formato as F
import humor

SEM_REF = humor.SEM_REFERENCIA

# ---------------------------------------------------------------- variáveis
QUANTITATIVAS = {
    'ret': {'nome': 'Retorno do dia', 'unidade': '%',
            'definicao': 'fechamento(t) ÷ fechamento(t−1) − 1'},
    'gap': {'nome': 'Gap de abertura', 'unidade': '%',
            'definicao': 'abertura(t) ÷ fechamento(t−1) − 1'},
    'intra': {'nome': 'Retorno da abertura ao fechamento', 'unidade': '%',
              'definicao': 'fechamento(t) ÷ abertura(t) − 1'},
    'amp': {'nome': 'Amplitude do dia', 'unidade': '%',
            'definicao': '(máxima − mínima) ÷ fechamento(t−1)', 'positiva': True},
    'fin': {'nome': 'Volume financeiro', 'unidade': 'R$ milhões',
            'definicao': 'fechamento × quantidade negociada (aproximação: a base não tem o preço médio)',
            'log': True, 'positiva': True},
}

QUALITATIVAS = {
    'setor': {'nome': 'Setor econômico (B3)', 'ordem': None},
    'ano': {'nome': 'Ano', 'ordem': None},
    'dia_semana': {'nome': 'Dia da semana', 'ordem': ['segunda', 'terça', 'quarta', 'quinta', 'sexta']},
    'direcao': {'nome': 'Direção do dia', 'ordem': ['alta', 'baixa', 'sem variação']},
    'segue_ibov': {'nome': 'Acompanha o Ibovespa', 'ordem': ['sim', 'não', 'sem variação']},
    'faixa': {'nome': 'Faixa de movimento', 'ordem': ['calmo', 'normal', 'agitado', 'extremo']},
    'faixa_volume': {'nome': 'Faixa de volume', 'ordem': ['baixo', 'normal', 'alto', SEM_REF]},
    'humor_ant': {'nome': 'Humor no pregão anterior (Fear & Greed B3)',
                  'ordem': humor.ORDEM_FAIXAS + [SEM_REF]},
}

NOTAS_QUALITATIVAS = {
    'setor': 'Distribuição das 40 ações estudadas, não da bolsa: o peso de cada setor vem do número de '
             'ações e de pregões. Classificação setorial atual da B3, aplicada aos 10 anos.',
    'ano': '2016 tem só novembro e dezembro, e 2026 vai até 30/10; por isso têm menos linhas.',
    'direcao': '"Sem variação" são os dias com fechamento igual ao anterior. As proporções P1 e P2 do '
               'Painel 3 usam só os dias com variação.',
    'segue_ibov': 'Mesma direção do Ibovespa no mesmo intervalo (do último pregão com negócio da ação '
                  'até o dia). "Sem variação": a ação fechou igual ao dia anterior.',
    'faixa': 'Pelo tamanho do retorno: calmo |ret| ≤ 1%, normal até 2%, agitado até 5%, extremo acima de '
             '5%. "Dia agitado" no texto é |ret| > 2% (agitado + extremo).',
}

# 27 colunas da população (README e Painel 1)
DICIONARIO = [
    ('id', 'identificador', 'número da linha, de 0 a N−1, na ordem ação + data (é o que a AAS sorteia)'),
    ('data', 'data', 'pregão'),
    ('ativo', 'qualitativa', 'código da ação na B3'),
    ('setor', 'qualitativa', 'setor econômico da classificação oficial da B3'),
    ('abertura, maxima, minima, fechamento', 'quantitativa', 'preços do dia em R$, ajustados por desdobramentos'),
    ('volume', 'quantitativa', 'quantidade de ações negociadas'),
    ('data_anterior', 'data', 'último pregão anterior com negócio da mesma ação'),
    ('fechamento_anterior', 'quantitativa', 'fechamento em data_anterior'),
    ('ret', 'quantitativa', 'retorno do dia, em %'),
    ('gap', 'quantitativa', 'gap de abertura, em %'),
    ('intra', 'quantitativa', 'retorno da abertura ao fechamento, em %'),
    ('amp', 'quantitativa', 'amplitude do dia, em %'),
    ('fin', 'quantitativa', 'volume financeiro, em R$ milhões'),
    ('ret_ibov', 'quantitativa', 'retorno do Ibovespa no mesmo intervalo de ret, em %'),
    ('vol_rel', 'quantitativa', 'volume financeiro ÷ mediana dos 20 pregões anteriores da ação'),
    ('fg_ant', 'quantitativa', 'Fear & Greed B3 (0 a 100) do pregão anterior'),
    ('ano, dia_semana', 'qualitativa', 'calendário'),
    ('direcao', 'qualitativa', 'alta, baixa ou sem variação'),
    ('segue_ibov', 'qualitativa', 'a ação foi na mesma direção do Ibovespa (sim, não, sem variação)'),
    ('faixa', 'qualitativa', 'calmo, normal, agitado, extremo, pelo |ret|'),
    ('faixa_volume', 'qualitativa', 'baixo (< 0,75), normal (0,75 a 1,5), alto (≥ 1,5) pelo vol_rel'),
    ('humor_ant', 'qualitativa', 'faixa do fg_ant: medo extremo, medo, neutro, ganância, ganância extrema'),
    ('conferencia_tv', 'qualitativa', 'resultado da conferência com o TradingView (5 categorias; ver acima)'),
]


def tabela_conferencia(d: pd.DataFrame) -> pd.DataFrame:
    """Contagem das categorias da conferência com o TradingView."""
    import conferir_tradingview as CT
    regras = {CT.IDENTICO: 'diferença no retorno ≤ 0,01 p.p.',
              CT.PEQUENA: 'entre 0,01 e 5 p.p.; fica como no Yahoo',
              CT.CORRIGIDO: 'mais de 5 p.p.; a linha recebe os preços do TradingView',
              CT.INTERVALO: 'o pregão anterior não é o mesmo nas duas fontes; fica como no Yahoo',
              CT.SEM_DADO: 'o TradingView não tem o dia; fica como no Yahoo'}
    f = frequencias(d['conferencia_tv'], CT.CATEGORIAS)
    return pd.DataFrame({'categoria': f['categoria'], 'regra': f['categoria'].map(regras),
                         'linhas': [F.inteiro(v) for v in f['n']],
                         'proporção': [F.pct(p, 2) for p in f['proporcao']]})


def nota_sem_referencia(d: pd.DataFrame, coluna: str) -> str | None:
    """Explica a categoria 'sem referência' com o número de linhas da base mostrada."""
    if coluna not in ('faixa_volume', 'humor_ant'):
        return None
    k = int((d[coluna] == SEM_REF).sum())
    if k == 0:
        return None
    motivo = ('os primeiros 20 pregões das ações que entram na base depois de 31/10/2016 não têm 20 '
              'pregões anteriores para a referência do volume'
              if coluna == 'faixa_volume' else
              'o Fear & Greed B3 só existe a partir de 08/10/2018 (precisa de dois anos de histórico)')
    return (f'"Sem referência": {F.inteiro(k)} linhas ({F.pct(k / len(d), 1)}), porque {motivo}. '
            'A coluna numérica fica vazia nessas linhas; a faixa ganha esta categoria para não sumir '
            'da contagem.')


# ---------------------------------------------------------------- medidas
def medidas(x) -> dict:
    x = pd.Series(x, dtype=float).dropna()
    q1, med, q3 = x.quantile([0.25, 0.5, 0.75])
    return {'n': len(x), 'media': x.mean(), 'mediana': med, 'dp': x.std(ddof=1),
            'minimo': x.min(), 'q1': q1, 'q3': q3, 'maximo': x.max(),
            'assimetria': float(stats.skew(x)), 'curtose': float(stats.kurtosis(x))}


ROTULOS_MEDIDAS = {'n': 'n', 'media': 'média', 'mediana': 'mediana', 'dp': 'desvio-padrão',
                   'minimo': 'mínimo', 'q1': '1º quartil', 'q3': '3º quartil', 'maximo': 'máximo',
                   'assimetria': 'assimetria', 'curtose': 'curtose'}


def tabela_medidas(d: pd.DataFrame, colunas=None) -> pd.DataFrame:
    """Uma linha por variável quantitativa, com as medidas já formatadas."""
    linhas = []
    for c in colunas or QUANTITATIVAS:
        m = medidas(d[c])
        casas = 2 if c == 'fin' else 3
        linha = {'variável': QUANTITATIVAS[c]['nome'], 'unidade': QUANTITATIVAS[c]['unidade']}
        for k, rot in ROTULOS_MEDIDAS.items():
            linha[rot] = F.inteiro(m[k]) if k == 'n' else F.num(m[k], 2 if k in ('assimetria', 'curtose') else casas)
        linhas.append(linha)
    return pd.DataFrame(linhas)


def frase_forma(x, unidade: str, positiva: bool = False) -> str:
    """Frase gerada dos números sobre o centro e a forma da distribuição.

    positiva=True (amplitude, volume): variável que nunca é negativa; se a assimetria passar de 1,
    acrescenta que a cauda é à direita e que a mediana representa melhor o dia típico."""
    m = medidas(x)

    def v(z):
        return f'{F.num(z)}%' if unidade == '%' else f'R$ {F.num(z, 1)} milhões'

    lado = 'acima' if m['media'] > m['mediana'] else 'abaixo'
    if m['curtose'] > 3:
        cauda = 'caudas muito mais pesadas que as da normal: os dias extremos pesam muito na média'
    else:
        cauda = 'caudas próximas às da normal'
    texto = (f'Média {v(m["media"])} e mediana {v(m["mediana"])}: a média fica {lado} da mediana. '
             f'Assimetria {F.num(m["assimetria"], 2)} e curtose {F.num(m["curtose"], 1)}, ou seja, {cauda}.')
    if positiva and m['assimetria'] > 1:
        texto += (' A distribuição é assimétrica à direita: a variável nunca é negativa e alguns dias '
                  'têm valores muito acima do normal, que puxam a média para cima. Por isso a **mediana** '
                  f'({v(m["mediana"])}) representa melhor o dia típico do que a média.')
    return texto


# ---------------------------------------------------------------- frequências
def frequencias(s: pd.Series, ordem=None) -> pd.DataFrame:
    c = s.value_counts()
    if ordem:
        cats = [o for o in ordem if o in c.index] + [o for o in c.index if o not in ordem]
        c = c.reindex(cats)
    elif s.name == 'ano':
        c = c.sort_index()
    out = c.rename('n').rename_axis('categoria').reset_index()
    out['proporcao'] = out['n'] / out['n'].sum()
    out['categoria'] = out['categoria'].astype(str)
    return out


# ---------------------------------------------------------------- gráficos
def histograma(x, bins: int = 60, recorte=(0.005, 0.995), log: bool = False) -> dict:
    """Contagens para um histograma. Recorta as caudas para o eixo (e informa quantas ficaram fora)."""
    x = pd.Series(x, dtype=float).dropna()
    v = np.log10(x[x > 0]) if log else x
    lo, hi = v.quantile(list(recorte))
    dentro = v[(v >= lo) & (v <= hi)]
    cont, bordas = np.histogram(dentro, bins=bins, range=(lo, hi))
    return {'bordas': bordas, 'contagens': cont, 'centros': (bordas[:-1] + bordas[1:]) / 2,
            'abaixo': int((v < lo).sum()), 'acima': int((v > hi).sum()), 'n': len(v), 'log': log,
            'zeros_excluidos': int((x <= 0).sum()) if log else 0}


def caixa(x) -> dict:
    """Estatísticas do boxplot (bigodes a 1,5 × IIQ, limitados aos dados)."""
    x = pd.Series(x, dtype=float).dropna()
    q1, med, q3 = x.quantile([0.25, 0.5, 0.75])
    iiq = q3 - q1
    lo = x[x >= q1 - 1.5 * iiq].min()
    hi = x[x <= q3 + 1.5 * iiq].max()
    return {'q1': q1, 'mediana': med, 'q3': q3, 'bigode_baixo': lo, 'bigode_alto': hi, 'media': x.mean(),
            'fora': int(((x < lo) | (x > hi)).sum()), 'n': len(x)}


def agitados_por_ano(d: pd.DataFrame) -> pd.DataFrame:
    """% de dias agitados (|ret| > 2%) por ano."""
    g = d.groupby('ano')['ret']
    out = pd.DataFrame({'n': g.size(), 'agitados': g.apply(lambda r: int((r.abs() > 2).sum()))})
    out['proporcao'] = out['agitados'] / out['n']
    return out.reset_index()


def resumo_base(d: pd.DataFrame) -> dict:
    return {'n': len(d), 'acoes': d['ativo'].nunique(), 'pregoes': d['data'].nunique(),
            'inicio': d['data'].min(), 'fim': d['data'].max(), 'setores': d['setor'].nunique()}


# ---------------------------------------------------------------- comparação amostra × população
LIMITE_EP = 2.0       # diferença "comum" para o acaso do sorteio: até 2 erros-padrão


def _fpc(n: int, N: int) -> float:
    """Correção de população finita do erro-padrão de uma AAS sem reposição."""
    return float(np.sqrt(max(N - n, 0) / (N - 1))) if N > 1 else 0.0


def comparar_medidas(P: pd.DataFrame, A: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Todas as medidas de uma variável quantitativa, população × amostra, já formatadas."""
    mp, ma = medidas(P[coluna]), medidas(A[coluna])
    casas = 2 if coluna == 'fin' else 3
    linhas = []
    for k, rot in ROTULOS_MEDIDAS.items():
        if k == 'n':
            linhas.append({'medida': rot, 'população': F.inteiro(mp[k]), 'amostra': F.inteiro(ma[k]),
                           'diferença (amostra − população)': '—'})
            continue
        c = 2 if k in ('assimetria', 'curtose') else casas
        dif = ma[k] - mp[k]
        linhas.append({'medida': rot, 'população': F.num(mp[k], c), 'amostra': F.num(ma[k], c),
                       'diferença (amostra − população)': ('+' if dif > 0 else '') + F.num(dif, c)})
    return pd.DataFrame(linhas)


def resumo_medias(P: pd.DataFrame, A: pd.DataFrame) -> pd.DataFrame:
    """Média de cada variável quantitativa: diferença medida em erros-padrão esperados.

    Erro-padrão esperado da média de uma AAS de tamanho n: σ/√n × √((N − n)/(N − 1)), com σ da
    população. Até 2 erros-padrão é uma diferença comum só pelo acaso do sorteio."""
    n, N = len(A), len(P)
    linhas = []
    for c, info in QUANTITATIVAS.items():
        x, y = P[c].dropna(), A[c].dropna()
        ep = x.std(ddof=1) / np.sqrt(len(y)) * _fpc(len(y), len(x))
        dif = y.mean() - x.mean()
        linhas.append({'coluna': c, 'variável': info['nome'], 'unidade': info['unidade'],
                       'pop': x.mean(), 'amostra': y.mean(), 'dif': dif, 'ep': ep, 'z': dif / ep})
    return pd.DataFrame(linhas)


def tabela_resumo_medias(R: pd.DataFrame) -> pd.DataFrame:
    def f(c, v):
        return F.num(v, 2 if c == 'fin' else 3)
    return pd.DataFrame({
        'variável': R['variável'], 'unidade': R['unidade'],
        'média na população': [f(c, v) for c, v in zip(R['coluna'], R['pop'])],
        'média na amostra': [f(c, v) for c, v in zip(R['coluna'], R['amostra'])],
        'diferença': [('+' if v > 0 else '') + f(c, v) for c, v in zip(R['coluna'], R['dif'])],
        'erro-padrão esperado': [f(c, v) for c, v in zip(R['coluna'], R['ep'])],
        'diferença em erros-padrão': [F.num(v, 2) for v in R['z']],
    })


def comparar_frequencias(P: pd.DataFrame, A: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Proporção de cada categoria na população e na amostra, com a diferença em erros-padrão.

    Erro-padrão esperado da proporção amostral: √(p(1 − p)/n) × √((N − n)/(N − 1)), com p da população."""
    ordem = QUALITATIVAS[coluna]['ordem']
    fp = frequencias(P[coluna], ordem).set_index('categoria')
    fa = frequencias(A[coluna], ordem).set_index('categoria').reindex(fp.index).fillna(0)
    n, N = len(A), len(P)
    p = fp['proporcao']
    ep = np.sqrt(p * (1 - p) / n) * _fpc(n, N)
    out = pd.DataFrame({'categoria': fp.index, 'pop': p.values, 'amostra': fa['proporcao'].values,
                        'n_amostra': fa['n'].astype(int).values})
    out['dif'] = out['amostra'] - out['pop']
    out['ep'] = ep.values
    out['z'] = np.where(out['ep'] > 0, out['dif'] / out['ep'], 0.0)
    return out


def tabela_frequencias_comparada(C: pd.DataFrame, nome: str) -> pd.DataFrame:
    return pd.DataFrame({
        nome: C['categoria'],
        'população': [F.pct(v, 2) for v in C['pop']],
        'amostra': [F.pct(v, 2) for v in C['amostra']],
        'linhas na amostra': [F.inteiro(v) for v in C['n_amostra']],
        'diferença (p.p.)': [('+' if v > 0 else '') + F.num(v * 100, 2) for v in C['dif']],
        'em erros-padrão': [F.num(v, 2) for v in C['z']],
    })


def frase_medias(R: pd.DataFrame) -> str:
    dentro = (R['z'].abs() <= LIMITE_EP)
    maior = R.loc[R['z'].abs().idxmax()]
    texto = (f'Nas {len(R)} variáveis quantitativas, a média da amostra fica a até '
             f'{F.num(abs(maior["z"]), 2)} erros-padrão da média da população (a maior diferença é a do '
             f'{maior["variável"].lower()}). ')
    if dentro.all():
        texto += ('Todas estão dentro de 2 erros-padrão, o que é comum só pelo acaso do sorteio: a amostra '
                  'reproduz bem a população.')
    else:
        fora = ', '.join(R.loc[~dentro, 'variável'].str.lower())
        texto += f'Passam de 2 erros-padrão: {fora}.'
    return texto


def frase_frequencias(P: pd.DataFrame, A: pd.DataFrame) -> str:
    """Quantas categorias, entre todas as variáveis qualitativas, passam de 2 erros-padrão."""
    total, fora = 0, []
    for c, info in QUALITATIVAS.items():
        C = comparar_frequencias(P, A, c)
        total += len(C)
        for _, r in C[C['z'].abs() > LIMITE_EP].iterrows():
            fora.append(f'{r["categoria"]} ({info["nome"].lower()}, {F.num(r["z"], 2)})')
    esperado = total * 0.0455
    texto = (f'Nas {len(QUALITATIVAS)} variáveis qualitativas há {total} categorias. ')
    if not fora:
        return texto + 'Em todas, a proporção da amostra fica a menos de 2 erros-padrão da população.'
    verbo = 'passa' if len(fora) == 1 else 'passam'
    return (texto + f'{len(fora)} {verbo} de 2 erros-padrão: {"; ".join(fora)}. Só pelo acaso, espera-se '
            f'que cerca de {F.num(esperado, 1)} delas passem (4,6% de {total}): a diferença é do tamanho '
            'esperado num sorteio, não um defeito da amostra.')


# ---------------------------------------------------------------- QQ-plot (condição dos testes de média)
def qq(x) -> dict:
    """Quantis da normal padrão × valores padronizados da amostra, e quantos passam de 3 desvios."""
    x = np.sort(pd.Series(x, dtype=float).dropna().values)
    n = len(x)
    teoricos = stats.norm.ppf((np.arange(1, n + 1) - 0.5) / n)
    z = (x - x.mean()) / x.std(ddof=1)
    alem = int((np.abs(z) > 3).sum())
    return {'teoricos': teoricos, 'padronizados': z, 'n': n, 'alem3': alem,
            'esperado3': 2 * stats.norm.sf(3), 'min': float(z.min()), 'max': float(z.max())}


def frase_qq(q: dict, nome: str) -> str:
    return (f'{nome}: numa distribuição normal, {F.pct(q["esperado3"], 2)} dos valores ficariam além de 3 '
            f'desvios-padrão; na amostra são {F.pct(q["alem3"] / q["n"], 2)} ({F.inteiro(q["alem3"])} linhas), '
            f'e os extremos chegam a {F.num(q["min"], 1)} e {F.num(q["max"], 1)} desvios. Os pontos saem da '
            'reta nas pontas: as caudas são mais pesadas que as da normal.')


# ---------------------------------------------------------------- extras: volume e humor (descritivos, sem teste)
def cortes_volume(d: pd.DataFrame) -> np.ndarray:
    """Limites dos decis de vol_rel (abertos nas pontas), calculados no conjunto de referência."""
    v = d['vol_rel'].dropna()
    if len(v) < 10:
        raise ValueError('poucas linhas com volume relativo para formar decis')
    c = np.quantile(v, np.linspace(0, 1, 11))
    c[0], c[-1] = -np.inf, np.inf
    return c


def decis_volume(d: pd.DataFrame, cortes: np.ndarray | None = None) -> pd.DataFrame:
    """Por decil de volume relativo: volume típico, |ret| médio e % de dias agitados (|ret| > 2%).

    Os cortes vêm da população; a amostra usa os mesmos, para comparar decil a decil."""
    x = d.dropna(subset=['vol_rel'])
    cortes = cortes_volume(x) if cortes is None else cortes
    dec = pd.cut(x['vol_rel'], cortes, labels=range(1, 11))
    g = x.groupby(dec, observed=False)
    out = pd.DataFrame({'n': g.size(), 'vol_mediano': g['vol_rel'].median(),
                        'absret': g['ret'].apply(lambda r: r.abs().mean()),
                        'agitados': g['ret'].apply(lambda r: (r.abs() > 2).mean())})
    out.index.name = 'decil'
    return out.reset_index()


def correlacao_volume(d: pd.DataFrame) -> dict:
    """Spearman de |ret| com o volume relativo e com o volume bruto."""
    x = d.dropna(subset=['vol_rel'])
    return {'relativo': float(stats.spearmanr(x['vol_rel'], x['ret'].abs()).statistic),
            'bruto': float(stats.spearmanr(d['fin'], d['ret'].abs()).statistic), 'n': len(x)}


def frase_volume(T: pd.DataFrame, corr: dict) -> str:
    a, z = T.iloc[0], T.iloc[-1]
    return (f'Nos dias de volume mais baixo (1º decil, cerca de {F.num(a["vol_mediano"], 2)} vez o normal da '
            f'própria ação), o movimento médio é {F.num(a["absret"], 2)}% e {F.pct(a["agitados"], 0)} dos dias são '
            f'agitados; nos de volume mais alto (10º decil, {F.num(z["vol_mediano"], 2)} vezes o normal), '
            f'{F.num(z["absret"], 2)}% e {F.pct(z["agitados"], 0)}. A relação cresce de forma regular '
            f'(Spearman {F.num(corr["relativo"], 2)}). Com o volume bruto ela quase some '
            f'(Spearman {F.num(corr["bruto"], 2)}), porque as maiores ações negociam muito todos os dias.')


def concentracao(d: pd.DataFrame, top: int = 5) -> dict:
    """Concentração do volume financeiro entre as ações, dia a dia e no período todo."""
    x = d[['data', 'fin']]
    total = x.groupby('data')['fin'].sum()
    topk = (x.sort_values(['data', 'fin'], ascending=[True, False]).groupby('data').head(top)
            .groupby('data')['fin'].sum())
    fatia = (topk / total).rename('fatia')
    participacao = x['fin'] / x.groupby('data')['fin'].transform('sum')
    hhi = (participacao ** 2).groupby(x['data']).sum()
    por_ano = fatia.groupby(fatia.index.year).median()
    por_acao = (d.groupby('ativo')['fin'].sum() / d['fin'].sum()).sort_values(ascending=False)
    return {'top': top, 'fatia_mediana': float(fatia.median()), 'por_ano': por_ano, 'por_acao': por_acao,
            'hhi_mediano': float(hhi.median()), 'equivalente': float(1 / hhi.median()),
            'n_acoes': d['ativo'].nunique()}


def frase_concentracao(c: dict) -> str:
    pa, pac = c['por_ano'], c['por_acao']
    lider = ', '.join(f'{a} {F.pct(v, 1)}' for a, v in pac.head(5).items())
    texto = (f'Num dia típico, as {c["top"]} ações mais negociadas respondem por {F.pct(c["fatia_mediana"], 1)} '
             f'do volume das {c["n_acoes"]} ações (mediana dos pregões). ')
    if len(pa) > 1:
        texto += (f'A fatia foi de {F.pct(pa.max(), 0)} em {pa.idxmax()} a {F.pct(pa.min(), 0)} em {pa.idxmin()}. ')
    texto += (f'Nos 10 anos, as maiores são {lider}; as 10 maiores somam {F.pct(pac.head(10).sum(), 0)}. Pelo '
              f'índice de concentração (HHI mediano {F.num(c["hhi_mediano"], 3)}), o volume se comporta como se '
              f'fosse dividido igualmente entre {F.num(c["equivalente"], 0)} ações.')
    return texto


def tabela_humor(d: pd.DataFrame) -> pd.DataFrame:
    """Por faixa do Fear & Greed do pregão anterior: % de dias de alta (entre ret ≠ 0), % agitados,
    |ret| médio. Sem a categoria 'sem referência'."""
    x = d[d['humor_ant'] != SEM_REF]
    linhas = []
    for faixa in humor.ORDEM_FAIXAS:
        s = x[x['humor_ant'] == faixa]
        if s.empty:
            continue
        nz = s['ret'][s['ret'] != 0]
        linhas.append({'faixa': faixa, 'n': len(s), 'alta': float((nz > 0).mean()) if len(nz) else np.nan,
                       'agitados': float((s['ret'].abs() > 2).mean()), 'absret': float(s['ret'].abs().mean())})
    return pd.DataFrame(linhas)


def frase_humor(T: pd.DataFrame) -> str:
    if T.empty:
        return 'Sem linhas com Fear & Greed nestes filtros.'
    lo, hi = T['alta'].min(), T['alta'].max()
    me = T[T['faixa'] == 'medo extremo']
    resto = T[T['faixa'] != 'medo extremo']
    texto = (f'A proporção de dias de alta fica entre {F.pct(lo, 1)} e {F.pct(hi, 1)} em todas as faixas: o humor '
             'de ontem não diz para onde a ação vai hoje. ')
    if len(me) and len(resto):
        texto += (f'Já os dias agitados sobem para {F.pct(me["agitados"].iloc[0], 0)} depois de medo extremo, contra '
                  f'{F.pct(resto["agitados"].min(), 0)} a {F.pct(resto["agitados"].max(), 0)} nas outras faixas: '
                  'o humor diz mais sobre quanto a ação se mexe.')
    return texto


NOTA_VOLUME = ('Descritivo, sem teste de hipótese. É associação, não causa: uma notícia pode provocar ao mesmo tempo '
               'o volume alto e o movimento grande. Volume relativo = volume financeiro do dia ÷ mediana dos 20 '
               'pregões anteriores da mesma ação; as linhas sem 20 pregões anteriores ficam fora.')
NOTA_CONCENTRACAO = ('Descritivo. Volume não é peso no índice: o peso no Ibovespa vem do valor de mercado das ações em '
                     'circulação, que a base não tem, e estas são 40 das cerca de 85 ações do índice. Por isso o '
                     'título fala em concentração do volume, não do índice.')
NOTA_HUMOR = ('Descritivo, sem teste de hipótese. Fear & Greed B3: índice construído no trabalho anterior do curso, '
              'não oficial, com as mesmas 40 ações (o humor de ontem inclui a própria ação). Usa o pregão anterior, '
              'porque o índice do dia é calculado com os preços do próprio dia. Só existe a partir de 08/10/2018 '
              '(as linhas "sem referência" ficam fora destas barras), e nos primeiros meses o percentil compara com '
              'pouco histórico. Parte da relação com a agitação é mecânica: um dos componentes é a volatilidade '
              'recente, e a volatilidade tende a continuar.')
