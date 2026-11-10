"""Inferência: intervalos de confiança, testes de hipóteses e comparação com a população.

Métodos (os mesmos em todas as hipóteses; resumo no README):
  proporção  teste z com p0 no erro-padrão; IC de Wald 95%. Conferências: binomial exato e IC de Wilson.
  média      teste t de uma amostra; IC t 95% (gl = n − 1). Conferência: teste do sinal (mediana = 0).
  α = 5% em todos. A correção de população finita (√(1 − n/N) ≈ 0,988) é citada, não aplicada.

Os parâmetros populacionais são calculados diretamente na população; a inferência usa só a amostra.
A simulação de 2.000 AAS (semente 1) mede, para cada hipótese, a taxa de rejeição e a cobertura do
IC 95%. Na população nenhuma H0 é verdadeira (h0_na_populacao), então a taxa de rejeição é o poder.

Uso:  python inferencia.py      # imprime o resultado das 6 hipóteses na amostra oficial
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

import formato as F

ALFA = 0.05
CONFIANCA = 0.95
SEMENTE_SIMULACAO = 1
N_SIMULACOES = 2000
DIA_CIRCUIT_BREAKER = pd.Timestamp('2026-10-26')

ALTERNATIVAS = {'two-sided': '≠', 'greater': '>', 'less': '<'}


# ====================================================================== testes básicos
@dataclass
class ResultadoProporcao:
    x: int
    n: int
    p_hat: float
    p0: float
    alternativa: str
    z: float
    p_valor: float
    ic: tuple[float, float]               # Wald, bilateral 95%
    ic_wilson: tuple[float, float]
    p_valor_exato: float                  # binomial exato
    limite_unilateral: float | None       # Wald unilateral 95% (só em testes unilaterais)

    @property
    def rejeita(self) -> bool:
        return self.p_valor < ALFA


def teste_proporcao(x: int, n: int, p0: float, alternativa: str = 'two-sided') -> ResultadoProporcao:
    p_hat = x / n
    z = (p_hat - p0) / np.sqrt(p0 * (1 - p0) / n)
    p_valor = {'two-sided': 2 * stats.norm.sf(abs(z)), 'greater': stats.norm.sf(z),
               'less': stats.norm.cdf(z)}[alternativa]
    ep = np.sqrt(p_hat * (1 - p_hat) / n)
    zc = stats.norm.ppf(1 - (1 - CONFIANCA) / 2)
    bt = stats.binomtest(x, n, p0, alternative=alternativa)
    w = stats.binomtest(x, n).proportion_ci(CONFIANCA, method='wilson')
    lim = None
    if alternativa != 'two-sided':
        z1 = stats.norm.ppf(CONFIANCA)
        lim = p_hat - z1 * ep if alternativa == 'greater' else p_hat + z1 * ep
    return ResultadoProporcao(x, n, p_hat, p0, alternativa, float(z), float(p_valor),
                              (p_hat - zc * ep, p_hat + zc * ep), (w.low, w.high),
                              float(bt.pvalue), lim)


@dataclass
class ResultadoMedia:
    n: int
    media: float
    dp: float
    mu0: float
    alternativa: str
    t: float
    gl: int
    p_valor: float
    ic: tuple[float, float]               # t, bilateral 95%
    limite_unilateral: float | None

    @property
    def rejeita(self) -> bool:
        return self.p_valor < ALFA

    @property
    def margem(self) -> float:
        return (self.ic[1] - self.ic[0]) / 2


def teste_media(x, mu0: float = 0.0, alternativa: str = 'two-sided') -> ResultadoMedia:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    r = stats.ttest_1samp(x, mu0, alternative=alternativa)
    ic = stats.ttest_1samp(x, mu0).confidence_interval(CONFIANCA)
    lim = None
    if alternativa != 'two-sided':
        c = r.confidence_interval(CONFIANCA)
        lim = c.low if alternativa == 'greater' else c.high
    return ResultadoMedia(n, float(x.mean()), float(x.std(ddof=1)), mu0, alternativa,
                          float(r.statistic), n - 1, float(r.pvalue), (float(ic.low), float(ic.high)),
                          None if lim is None else float(lim))


def teste_sinal(x, alternativa: str = 'two-sided') -> dict:
    """Mediana = 0: binomial exato sobre os valores diferentes de zero."""
    x = np.asarray(x, dtype=float)
    pos, neg = int((x > 0).sum()), int((x < 0).sum())
    p = stats.binomtest(pos, pos + neg, 0.5, alternative=alternativa).pvalue
    return {'positivos': pos, 'negativos': neg, 'zeros': int((x == 0).sum()),
            'mediana': float(np.median(x)), 'p_valor': float(p)}


# ====================================================================== hipóteses
@dataclass(frozen=True)
class Hipotese:
    codigo: str
    tipo: str                    # 'proporcao' | 'media'
    titulo: str
    pergunta: str
    definicao: str               # evento ou variável, em palavras
    h0: str
    h1: str
    valor_h0: float
    alternativa: str
    complementar: bool = False
    justificativa: str = ''

    def evento(self, d: pd.DataFrame) -> pd.Series:
        """Proporções: o evento, já restrito ao domínio ret ≠ 0."""
        dom = d[d['ret'] != 0]
        if self.codigo.startswith('P1'):
            return dom['segue_ibov'] == 'sim'
        if self.codigo == 'P2':
            return dom['ret'] > 0
        raise KeyError(self.codigo)

    def variavel(self, d: pd.DataFrame) -> pd.Series:
        if self.codigo == 'M1':
            return d['ret']
        if self.codigo.startswith('M2'):
            return d['gap']
        raise KeyError(self.codigo)


HIPOTESES: list[Hipotese] = [
    Hipotese('P1', 'proporcao', 'A ação acompanha a direção do Ibovespa',
             'Em mais da metade dos dias, a ação vai para o mesmo lado que o Ibovespa?',
             'proporção de dias, entre os com retorno ≠ 0, em que o sinal do retorno da ação é igual ao '
             'do Ibovespa no mesmo intervalo',
             'p = 0,5', 'p > 0,5', 0.5, 'greater',
             justificativa='50% é o esperado se ação e índice fossem independentes; unilateral porque a '
                           'ação compõe o índice e os dois respondem às mesmas notícias'),
    Hipotese('P2', 'proporcao', 'Um dia de alta é "cara ou coroa"',
             'A chance de a ação subir num dia é diferente de 50%?',
             'proporção de dias de alta (retorno > 0) entre os dias com retorno ≠ 0',
             'p = 0,5', 'p ≠ 0,5', 0.5, 'two-sided',
             justificativa='na hipótese do passeio aleatório (Fama, 1965), as variações sucessivas dos '
                           'preços são independentes e a direção de um dia não é previsível; com variações '
                           'simétricas em torno de zero, a chance de alta fica em 50%. Bilateral, porque não há '
                           'direção prevista'),
    Hipotese('M1', 'media', 'O retorno médio diário é zero',
             'Em média, a ação ganha ou perde algo por dia?',
             'retorno do dia: fechamento(t) / fechamento(t−1) − 1, em %, sem dividendos',
             'μ = 0', 'μ ≠ 0', 0.0, 'two-sided',
             justificativa='bilateral, porque não há direção prevista antes dos dados'),
    Hipotese('M2', 'media', 'O gap médio de abertura é zero',
             'Em média, a ação abre acima ou abaixo do fechamento anterior?',
             'gap de abertura: abertura(t) / fechamento(t−1) − 1, em %',
             'μ = 0', 'μ ≠ 0', 0.0, 'two-sided',
             justificativa='bilateral, para não depender de uma direção escolhida depois dos dados'),
    Hipotese('P1-b', 'proporcao', 'A ação acompanha o Ibovespa em mais de dois terços dos dias',
             'O acompanhamento passa de dois terços dos dias?',
             'o mesmo evento da P1', 'p ≤ 2/3', 'p > 2/3', 2 / 3, 'greater', complementar=True,
             justificativa='segunda hipótese sobre o mesmo parâmetro da P1, com um valor de H₀ mais exigente '
                           '(2/3, um valor redondo, sem base teórica), para mostrar que, com a mesma estimativa e '
                           'o mesmo intervalo, a conclusão depende do valor testado'),
    Hipotese('M2-b', 'media', 'O gap médio de abertura é positivo',
             'A ação abre, em média, acima do fechamento anterior?',
             'a mesma variável da M2', 'μ ≤ 0', 'μ > 0', 0.0, 'greater', complementar=True,
             justificativa='unilateral porque Cliff, Cooper e Gulen (2008) documentam, nas ações americanas, '
                           'retornos maiores do fechamento à abertura seguinte do que durante o pregão; a direção '
                           'vem desse estudo, não destes dados'),
]
POR_CODIGO = {h.codigo: h for h in HIPOTESES}


def testar(h: Hipotese, d: pd.DataFrame):
    if h.tipo == 'proporcao':
        e = h.evento(d)
        return teste_proporcao(int(e.sum()), len(e), h.valor_h0, h.alternativa)
    return teste_media(h.variavel(d).values, h.valor_h0, h.alternativa)


def parametro_populacional(h: Hipotese, P: pd.DataFrame) -> float:
    return float(h.evento(P).mean()) if h.tipo == 'proporcao' else float(h.variavel(P).mean())


def condicoes(h: Hipotese, A: pd.DataFrame, N: int) -> list[dict]:
    """Condições de aplicação conferidas na amostra."""
    n_total = len(A)
    out = [{'condicao': 'Amostra aleatória simples', 'valor': 'semente 2026, sem reposição',
            'ok': True},
           {'condicao': 'Fração amostral n/N < 10% (independência)',
            'valor': F.pct(n_total / N, 2), 'ok': n_total / N < 0.10}]
    if h.tipo == 'proporcao':
        k = len(h.evento(A))
        out.append({'condicao': 'n·p₀ ≥ 10 e n·(1−p₀) ≥ 10',
                    'valor': f'{F.num(k * h.valor_h0, 0)} e {F.num(k * (1 - h.valor_h0), 0)}',
                    'ok': min(k * h.valor_h0, k * (1 - h.valor_h0)) >= 10})
    else:
        x = h.variavel(A).dropna().values
        out.append({'condicao': 'n ≥ 30 (Teorema Central do Limite)', 'valor': F.inteiro(len(x)),
                    'ok': len(x) >= 30})
        out.append({'condicao': 'Forma da distribuição (só informativo, não é condição)',
                    'valor': f'assimetria {F.num(stats.skew(x), 2)}, curtose {F.num(stats.kurtosis(x), 1)}',
                    'ok': None})
    return out


@dataclass
class Linha:
    hipotese: Hipotese
    resultado: object
    parametro: float
    conferencia: dict = field(default_factory=dict)

    @property
    def ic_cobre(self) -> bool:
        lo, hi = self.resultado.ic
        return lo <= self.parametro <= hi


def analisar(A: pd.DataFrame, P: pd.DataFrame) -> list[Linha]:
    """As 6 hipóteses na amostra, com o parâmetro populacional ao lado."""
    linhas = []
    for h in HIPOTESES:
        r = testar(h, A)
        conf = {}
        if h.tipo == 'proporcao':
            conf = {'binomial exato': r.p_valor_exato, 'Wilson': r.ic_wilson}
        else:
            conf = {'sinal': teste_sinal(h.variavel(A).values,
                                         'two-sided' if h.alternativa == 'two-sided' else h.alternativa)}
        linhas.append(Linha(h, r, parametro_populacional(h, P), conf))
    return linhas


def bonferroni(linhas: list[Linha]) -> dict:
    alfa_b = ALFA / len(linhas)
    return {'alfa': alfa_b, 'rejeita': {l.hipotese.codigo: l.resultado.p_valor < alfa_b for l in linhas},
            'muda': [l.hipotese.codigo for l in linhas
                     if (l.resultado.p_valor < alfa_b) != l.resultado.rejeita]}


# ====================================================================== sensibilidade da M2
def sensibilidade_m2(A: pd.DataFrame, winsor: float = 0.005) -> pd.DataFrame:
    """Complemento: a M2 com e sem os dias extremos. Nunca substitui o resultado oficial."""
    g = A['gap']
    q = g.quantile([winsor, 1 - winsor])
    sem_cb = g[A['data'] != DIA_CIRCUIT_BREAKER]
    variantes = [('Oficial (todas)', g), (f'Sem {DIA_CIRCUIT_BREAKER:%d/%m/%Y}', sem_cb),
                 (f'Winsorizada a {_num(winsor * 100, 1)}%', g.clip(q.iloc[0], q.iloc[1]))]
    linhas = []
    for nome, x in variantes:
        r = teste_media(x.values)
        linhas.append({'variante': nome, 'n': r.n, 'estimativa': r.media, 'ic_baixo': r.ic[0],
                       'ic_alto': r.ic[1], 'p_valor': r.p_valor, 'rejeita': r.rejeita})
    s = teste_sinal(g.values)
    linhas.append({'variante': 'Teste do sinal (mediana)', 'n': s['positivos'] + s['negativos'],
                   'estimativa': s['mediana'], 'ic_baixo': np.nan, 'ic_alto': np.nan,
                   'p_valor': s['p_valor'], 'rejeita': s['p_valor'] < ALFA})
    return pd.DataFrame(linhas)


# ====================================================================== simulação
def simular(P: pd.DataFrame, n: int, r: int = N_SIMULACOES, semente: int = SEMENTE_SIMULACAO) -> dict:
    """`r` AAS de tamanho `n` da população: estimativas, taxa de rejeição e cobertura do IC 95%."""
    N = len(P)
    rng = np.random.default_rng(semente)
    nz = (P['ret'] != 0).values
    sobe = (P['ret'] > 0).values
    segue = (P['segue_ibov'] == 'sim').values
    ret, gap = P['ret'].values, P['gap'].values
    verdade = {h.codigo: parametro_populacional(h, P) for h in HIPOTESES}
    est = {h.codigo: np.empty(r) for h in HIPOTESES}
    rej = {h.codigo: np.zeros(r, bool) for h in HIPOTESES}
    cob = {h.codigo: np.zeros(r, bool) for h in HIPOTESES}
    zc = stats.norm.ppf(1 - (1 - CONFIANCA) / 2)
    tc = stats.t.ppf(1 - (1 - CONFIANCA) / 2, n - 1)
    for k in range(r):
        i = rng.choice(N, n, replace=False)
        j = i[nz[i]]
        m = len(j)
        for h in HIPOTESES:
            if h.tipo == 'proporcao':
                ph = (segue if h.codigo.startswith('P1') else sobe)[j].mean()
                z = (ph - h.valor_h0) / np.sqrt(h.valor_h0 * (1 - h.valor_h0) / m)
                pv = stats.norm.sf(z) if h.alternativa == 'greater' else 2 * stats.norm.sf(abs(z))
                margem = zc * np.sqrt(ph * (1 - ph) / m)
            else:
                s = (ret if h.codigo == 'M1' else gap)[i]
                ph = s.mean()
                ep = s.std(ddof=1) / np.sqrt(n)
                t = (ph - h.valor_h0) / ep
                pv = stats.t.sf(t, n - 1) if h.alternativa == 'greater' else 2 * stats.t.sf(abs(t), n - 1)
                margem = tc * ep
            est[h.codigo][k] = ph
            rej[h.codigo][k] = pv < ALFA
            cob[h.codigo][k] = abs(ph - verdade[h.codigo]) <= margem
    return {'estimativas': est, 'rejeicao': {c: float(v.mean()) for c, v in rej.items()},
            'cobertura': {c: float(v.mean()) for c, v in cob.items()}, 'verdade': verdade,
            'r': r, 'n': n, 'semente': semente}


def h0_na_populacao(parametro: float, valor_h0: float, alternativa: str) -> str:
    """H0 é verdadeira ou falsa comparando o parâmetro calculado na população com o valor de H0.

    Bilateral (H0: θ = θ0): verdadeira só se o parâmetro for igual a θ0. Unilateral à direita
    (H0: θ ≤ θ0): verdadeira se o parâmetro for ≤ θ0. Unilateral à esquerda (H0: θ ≥ θ0): se for ≥ θ0.
    """
    if alternativa == 'two-sided':
        verdadeira = bool(np.isclose(parametro, valor_h0, rtol=0, atol=1e-12))
    elif alternativa == 'greater':
        verdadeira = parametro <= valor_h0
    else:
        verdadeira = parametro >= valor_h0
    return 'verdadeira' if verdadeira else 'falsa'


def limite_poder_igual_alfa(r: int = N_SIMULACOES) -> float:
    """Maior taxa de rejeição que, em r réplicas, ainda não se distingue de α: α + 1,96·√(α(1−α)/r).

    Serve só para descrever o poder ("não se distingue de α nesta simulação"); não decide se H0 é
    verdadeira, o que depende só da população (h0_na_populacao).
    """
    return float(ALFA + stats.norm.ppf(0.975) * np.sqrt(ALFA * (1 - ALFA) / r))


def amostra_exercicio(P: pd.DataFrame, n: int, semente: int) -> pd.DataFrame:
    """Outra AAS de tamanho n, só para o exercício do Painel 3. Não substitui a amostra oficial."""
    ids = np.random.default_rng(semente).choice(len(P), n, replace=False)
    return P.iloc[ids]


def licao(resultado: str, h0_populacao: str, taxa_rejeicao: float, distancia: str = '',
          poder_igual_alfa: bool = False) -> str:
    """Leitura do resultado, gerada a partir da decisão, da verdade na população e da simulação.

    `distancia`: quanto o parâmetro da população se afasta do valor de H0, já formatado.
    `poder_igual_alfa`: o poder simulado não se distingue de α (limite_poder_igual_alfa)."""
    taxa = F.pct(taxa_rejeicao, 2)          # as mesmas casas das tabelas da simulação
    nao = F.pct(1 - taxa_rejeicao, 2)
    if resultado == 'erro tipo II' and poder_igual_alfa:
        return (f'Erro tipo II, mas inevitável: H₀ é falsa na população por só {distancia}, uma diferença que '
                f'nenhuma amostra deste tamanho percebe. O poder do teste é {taxa}, que não se distingue de '
                'α = 5% nesta simulação: o teste se comporta como se H₀ fosse verdadeira.')
    if resultado == 'erro tipo II':
        return (f'Erro tipo II: H₀ é falsa na população, mas esta amostra não a rejeitou. O poder do teste é '
                f'{taxa}: em {nao} das amostras possíveis isso aconteceria.')
    if resultado == 'erro tipo I':
        return (f'Erro tipo I: H₀ é verdadeira na população, mas foi rejeitada. Isso acontece em {taxa} das '
                'amostras, perto de α = 5%.')
    if h0_populacao == 'falsa':
        return f'Acerto: o efeito existe na população e o teste o detectou, como fariam {taxa} das amostras.'
    return (f'Acerto: H₀ é verdadeira na população e não foi rejeitada. Rejeitá-la seria um erro tipo I, que '
            f'acontece em {taxa} das amostras, perto de α = 5%.')


def tabela_comparacao(linhas: list[Linha], sim: dict) -> pd.DataFrame:
    """Uma linha por hipótese: parâmetro da população, estimativa, IC, decisão e verdade."""
    dv = decisao_x_verdade(linhas, sim).set_index('codigo')
    out = []
    for l in linhas:
        h, r = l.hipotese, l.resultado
        if h.tipo == 'proporcao':
            par, est, lo, hi = F.pct(l.parametro), F.pct(r.p_hat), F.pct(r.ic[0]), F.pct(r.ic[1])
            dif = F.num((r.p_hat - l.parametro) * 100, 2) + ' p.p.'
        else:
            par, est = f'{F.num(l.parametro)}%', f'{F.num(r.media)}%'
            lo, hi = f'{F.num(r.ic[0])}%', f'{F.num(r.ic[1])}%'
            dif = F.num(r.media - l.parametro) + ' p.p.'
        d = dv.loc[h.codigo]
        resultado = d['rotulo']
        out.append({'hipótese': h.codigo + (' (compl.)' if h.complementar else ''), 'H₀': h.h0,
                    'população': par, 'amostra': est, 'diferença': dif, 'IC 95%': f'[{lo}; {hi}]',
                    'IC contém a população': 'sim' if l.ic_cobre else 'não',
                    'valor-p': F.pval(r.p_valor), 'decisão': d['decisao'],
                    'H₀ na população': d['h0_populacao'], 'resultado': resultado})
    return pd.DataFrame(out)


def distancia_h0(l: Linha) -> str:
    """Distância entre o parâmetro da população e o valor de H0, em pontos percentuais."""
    k = 100 if l.hipotese.tipo == 'proporcao' else 1
    return F.num(abs(l.parametro - l.hipotese.valor_h0) * k, 2 if l.hipotese.tipo == 'proporcao' else 3) + ' p.p.'


def decisao_x_verdade(linhas: list[Linha], sim: dict) -> pd.DataFrame:
    """Decisão da amostra oficial × verdade na população (o parâmetro calculado nas N linhas)."""
    out = []
    for l in linhas:
        h, c = l.hipotese, l.hipotese.codigo
        verdade = h0_na_populacao(l.parametro, h.valor_h0, h.alternativa)
        rejeita = l.resultado.rejeita
        if verdade == 'falsa':
            tipo = 'acerto' if rejeita else 'erro tipo II'
        else:
            tipo = 'erro tipo I' if rejeita else 'acerto'
        igual_alfa = sim['rejeicao'][c] <= limite_poder_igual_alfa(sim['r'])
        out.append({'codigo': c, 'complementar': h.complementar, 'h0_populacao': verdade,
                    'distancia': distancia_h0(l),
                    'decisao': 'rejeita H₀' if rejeita else 'não rejeita H₀', 'resultado': tipo,
                    'rotulo': tipo + (' (poder ≈ α)' if igual_alfa and tipo == 'erro tipo II' else ''),
                    'taxa_rejeicao': sim['rejeicao'][c], 'cobertura': sim['cobertura'][c],
                    'poder_igual_alfa': igual_alfa})
    return pd.DataFrame(out)


# ====================================================================== textos
_num, _pct, _pval = F.num, F.pct, F.pval          # formato brasileiro (formato.py)


def conclusao(l: Linha) -> str:
    """Frase de conclusão gerada a partir dos números (nunca digitada)."""
    h, r = l.hipotese, l.resultado
    if h.tipo == 'proporcao':
        est, par = _pct(r.p_hat), _pct(l.parametro)
        ic = f'[{_pct(r.ic[0])}; {_pct(r.ic[1])}]'
        estat = f'z = {_num(r.z, 2)}'
    else:
        est, par = f'{_num(r.media)}%', f'{_num(l.parametro)}%'
        ic = f'[{_num(r.ic[0])}%; {_num(r.ic[1])}%]'
        estat = f't = {_num(r.t, 2)}, gl {_num(r.gl, 0)}'
    decisao = ('Rejeita-se H₀' if r.rejeita else 'Não se rejeita H₀')
    leitura = ('há evidência a 5% de que ' + h.h1) if r.rejeita else \
              ('não há evidência a 5% contra ' + h.h0)
    cobre = 'contém' if l.ic_cobre else 'não contém'
    texto = (f'{decisao} ({estat}, valor-p {_pval(r.p_valor)}): {leitura}. A amostra estima {est}, '
             f'IC 95% {ic}; o valor da população é {par}, e o intervalo o {cobre}.')
    if r.limite_unilateral is not None:
        lim = _pct(r.limite_unilateral) if h.tipo == 'proporcao' else f'{_num(r.limite_unilateral)}%'
        lado = 'inferior' if h.alternativa == 'greater' else 'superior'
        if h.tipo == 'proporcao':          # Wald (p̂ no erro-padrão); o teste usa p₀: não são equivalentes
            texto += f' Limite {lado} unilateral 95% (Wald): {lim}.'
        else:                              # mesmo erro-padrão e mesma distribuição t do teste
            texto += f' Limite {lado} unilateral 95%, equivalente ao teste t: {lim}.'
    return texto


# ====================================================================== linha de comando
def main() -> None:
    from pathlib import Path
    dados = Path(__file__).resolve().parent / 'dados'
    P = pd.read_parquet(dados / 'populacao.parquet')
    A = pd.read_parquet(dados / 'amostra.parquet')
    linhas = analisar(A, P)
    for l in linhas:
        print(f'{l.hipotese.codigo:<5} {conclusao(l)}')
    b = bonferroni(linhas)
    print(f'Bonferroni (α = {b["alfa"]:.4f}): muda a decisão em {b["muda"] or "nenhuma"}')
    print(sensibilidade_m2(A).round(4).to_string(index=False))


if __name__ == '__main__':
    main()
