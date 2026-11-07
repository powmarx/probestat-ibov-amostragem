"""Peças comuns do app: leitura dos dados (com cache), cores, gráficos e filtros."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import descritiva as D
import formato as F

RAIZ = Path(__file__).resolve().parent
DADOS = RAIZ / 'dados'

TITULO = 'Amostragem e inferência em 10 anos de pregões da B3'
AUTOR = 'Paulo Luis Silva Marques'

# cores fixas em todo o app
COR_POP = '#1f77b4'          # população: azul
COR_AMOSTRA = '#ff7f0e'      # amostra: laranja
COR_REF = '#7f7f7f'          # linhas de referência: cinza tracejado
TRACO_REF = '5px,4px'

FONTE_YAHOO = 'https://finance.yahoo.com/quote/VALE3.SA/history'
API_YAHOO = 'https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}.SA?interval=1d&range=10y'
FONTE_B3 = ('https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/acoes/'
            'consultas/classificacao-setorial/')
REPO = 'https://github.com/powmarx/probestat-ibov-amostragem'
ZIP_POPULACAO = f'{REPO}/raw/main/dados/populacao.zip'
DOC_TV = f'{REPO}/blob/main/docs/conferencia_tradingview.md'
CONFIG_PLOTLY = {'displayModeBar': False}


# ---------------------------------------------------------------- aparência
ESTILO = """
<style>
/* notas explicativas (st.caption): mais perto do texto normal e com mais contraste */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    font-size: 0.95rem !important; color: #4a4d57 !important; line-height: 1.5;
}
/* nomes das abas (hipóteses do Painel 3) */
[data-testid="stTab"] p { font-size: 1.15rem !important; font-weight: 600; }
[data-testid="stTab"] { padding-left: 0.6rem !important; padding-right: 0.6rem !important; }
/* barra lateral mais larga: o nome "3. Inferência e comparação" cabe inteiro */
section[data-testid="stSidebar"] { width: 330px !important; min-width: 330px !important; }
/* menu lateral com os links dos painéis */
[data-testid="stSidebarNav"] a span, [data-testid="stSidebarNav"] a p { font-size: 1.05rem !important; }
[data-testid="stSidebarNav"] a { padding-top: 0.35rem; padding-bottom: 0.35rem; }
/* textos da barra lateral (filtros e créditos) */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { font-size: 0.92rem !important; }
/* rótulos dos cartões de números */
[data-testid="stMetricLabel"] p { font-size: 0.95rem !important; }
/* tabelas */
[data-testid="stTable"] td, [data-testid="stTable"] th { font-size: 0.95rem !important; }
</style>
"""


def estilo() -> None:
    st.html(ESTILO)


# ---------------------------------------------------------------- dados
def _versao(p: Path) -> float:
    return p.stat().st_mtime


@st.cache_data(show_spinner=False)
def _parquet(caminho: str, versao: float) -> pd.DataFrame:
    return pd.read_parquet(caminho)


def populacao() -> pd.DataFrame:
    p = DADOS / 'populacao.parquet'
    return _parquet(str(p), _versao(p))


def amostra() -> pd.DataFrame:
    p = DADOS / 'amostra.parquet'
    return _parquet(str(p), _versao(p))


@st.cache_data(show_spinner=False)
def _csv(caminho: str, versao: float) -> pd.DataFrame:
    return pd.read_csv(caminho)


def setores() -> pd.DataFrame:
    p = DADOS / 'setores.csv'
    return _csv(str(p), _versao(p))


def manifesto() -> dict:
    return json.loads((DADOS / 'manifesto.json').read_text(encoding='utf-8'))


# ---------------------------------------------------------------- filtros (só visualização)
def filtros(d: pd.DataFrame, chave: str) -> pd.DataFrame:
    """Filtros de setor e ano na barra lateral. Não mudam a população nem a amostra."""
    st.sidebar.markdown('**Filtros da visualização**')
    todos = sorted(d['setor'].unique())
    escolhidos = st.sidebar.multiselect('Setores', todos, default=[], key=f'{chave}_setor',
                                        placeholder='Todos os setores',
                                        help='Vazio = todos os setores.')
    anos = (int(d['ano'].min()), int(d['ano'].max()))
    lo, hi = st.sidebar.slider('Anos', anos[0], anos[1], anos, key=f'{chave}_ano')
    escolhidos = escolhidos or todos
    f = d[d['setor'].isin(escolhidos) & d['ano'].between(lo, hi)]
    st.sidebar.caption(f'Mostrando {F.inteiro(len(f))} de {F.inteiro(len(d))} linhas. Os filtros só '
                       'mudam os gráficos e tabelas desta página; a base é sempre a mesma.')
    return f


# ---------------------------------------------------------------- gráficos
def layout(fig: go.Figure, altura: int = 320, x: str | None = None, y: str | None = None,
           legenda: bool = False) -> go.Figure:
    fig.update_layout(template='plotly_white', separators=',.', height=altura,
                      margin=dict(l=10, r=10, t=30, b=10), showlegend=legenda,
                      font=dict(family='Source Sans Pro, Segoe UI, Arial, sans-serif', size=14),
                      legend=dict(orientation='h', x=1, xanchor='right', y=1.08, yanchor='bottom'),
                      bargap=0.05)
    fig.update_xaxes(title=x, gridcolor='#eee')
    fig.update_yaxes(title=y, gridcolor='#eee')
    return fig


def _eixo_log(fig: go.Figure, eixo: str = 'x') -> None:
    vals = [0, 1, 2, 3, 4]
    texto = ['1', '10', '100', '1.000', '10.000']
    (fig.update_xaxes if eixo == 'x' else fig.update_yaxes)(tickvals=vals, ticktext=texto)


def linha_ref(fig: go.Figure, valor: float, texto: str, eixo: str = 'x', posicao: str = 'top') -> None:
    kw = dict(line_dash=TRACO_REF, line_color=COR_REF, line_width=1,
              annotation_text=f'<b>{texto}</b>', annotation_font_size=12)
    if eixo == 'x':
        fig.add_vline(x=valor, annotation_position=f'{posicao} right', **kw)
    else:
        fig.add_hline(y=valor, annotation_position=f'{posicao} right', **kw)


def grafico_histograma(conjuntos: list[tuple[pd.DataFrame, str, str]], coluna: str,
                       altura: int = 330) -> tuple[go.Figure, str]:
    """Histograma em % das linhas. O primeiro conjunto define as classes; os outros usam as mesmas."""
    info = D.QUANTITATIVAS[coluna]
    log = info.get('log', False)
    base = D.histograma(conjuntos[0][0][coluna], log=log)
    bordas = base['bordas']
    largura = bordas[1] - bordas[0]
    fig = go.Figure()
    for d, nome, cor in conjuntos:
        x = d[coluna].dropna()
        v = np.log10(x[x > 0]) if log else x
        cont, _ = np.histogram(v[(v >= bordas[0]) & (v <= bordas[-1])], bins=bordas)
        fig.add_bar(x=base['centros'], y=100 * cont / len(v), width=largura, name=nome,
                    marker_color=cor, opacity=0.85 if len(conjuntos) == 1 else 0.55,
                    hovertemplate='%{y:.2f}% das linhas<extra>' + nome + '</extra>')
    if len(conjuntos) > 1:
        fig.update_layout(barmode='overlay')
    unidade = 'R$ milhões, escala log' if log else info['unidade']
    layout(fig, altura, x=f'{info["nome"]} ({unidade})', y='% das linhas', legenda=len(conjuntos) > 1)
    if log:
        _eixo_log(fig)
    elif len(conjuntos) == 1:
        m = D.medidas(conjuntos[0][0][coluna])
        fig.add_vline(x=m['media'], line_dash=TRACO_REF, line_color=COR_REF, line_width=1)
        fig.add_vline(x=m['mediana'], line_dash='dot', line_color='#333', line_width=1)
        fig.update_layout(margin=dict(t=10))
    else:                                       # comparação: a média de cada conjunto, na cor dele
        for d, _, cor in conjuntos:
            fig.add_vline(x=float(d[coluna].mean()), line_dash=TRACO_REF, line_color=cor, line_width=1.5)
    nota = (f'O eixo mostra do percentil 0,5 ao 99,5 da {conjuntos[0][1].lower()}: '
            f'{F.inteiro(base["abaixo"] + base["acima"])} linhas extremas ficam fora do gráfico, mas entram '
            'em todas as medidas.')
    if not log and len(conjuntos) == 1:
        nota += ' Linha tracejada: média; pontilhada: mediana.'
    elif not log:
        nota += (' As barras usam as mesmas classes nos dois conjuntos, em % das linhas de cada um; '
                 'linhas tracejadas: a média de cada um, na cor dele.')
    if base['zeros_excluidos']:
        nota += f' {F.inteiro(base["zeros_excluidos"])} linhas com volume zero não entram na escala log.'
    return fig, nota


def _valor(v: float, log: bool) -> str:
    if log:
        return f'R$ {F.num(v, 1)} mi'
    return ('+' if v > 0 else '') + f'{F.num(v, 2)}%'


def _onde(d: pd.DataFrame, i) -> str:
    return f'{d.at[i, "ativo"]}, {F.data(d.at[i, "data"])}'


def grafico_caixa(conjuntos: list[tuple[pd.DataFrame, str, str]], coluna: str, pontos: bool = False,
                  altura: int = 330) -> tuple[go.Figure, str]:
    """Boxplot com as estatísticas já calculadas (bigodes a 1,5 × IIQ).

    pontos=False: só a caixa; o mínimo e o máximo ficam escritos nas bordas, sem esticar o eixo.
    pontos=True: todos os valores além dos bigodes, como pontos (espalhados na horizontal só para não
    se sobreporem); o eixo vai do mínimo ao máximo.
    """
    info = D.QUANTITATIVAS[coluna]
    log = info.get('log', False)
    fig = go.Figure()
    rng = np.random.default_rng(0)            # espalhamento fixo: o gráfico não muda a cada execução
    contagens, extremos = [], []
    for k, (d, nome, cor) in enumerate(conjuntos):
        x = d[coluna].dropna()
        v = np.log10(x[x > 0]) if log else x
        c = D.caixa(v)
        fig.add_box(x=[k], name=nome, q1=[c['q1']], median=[c['mediana']], q3=[c['q3']],
                    lowerfence=[c['bigode_baixo']], upperfence=[c['bigode_alto']], mean=[c['media']],
                    marker_color=cor, boxpoints=False, width=0.5)
        fora = v[(v < c['bigode_baixo']) | (v > c['bigode_alto'])]
        if pontos and len(fora):
            reais = x.loc[fora.index] if log else fora
            fig.add_trace(go.Scattergl(
                x=k + rng.uniform(-0.18, 0.18, len(fora)), y=fora.values, mode='markers',
                marker=dict(color=cor, size=3, opacity=0.35), showlegend=False, customdata=reais.values,
                hovertemplate=('R$ %{customdata:,.1f} mi' if log else '%{y:.2f}%') + f'<extra>{nome}</extra>'))
        contagens.append((nome, c['fora'], c['n']))
        imin, imax = x.idxmin(), x.idxmax()
        extremos.append((k, (x[imin], _onde(d, imin)), (x[imax], _onde(d, imax)), c, nome.lower()))
    unidade = 'R$ milhões, escala log' if log else info['unidade']
    layout(fig, altura, y=f'{info["nome"]} ({unidade})')
    fig.update_xaxes(tickvals=list(range(len(conjuntos))), ticktext=[n for _, n, _ in conjuntos],
                     range=[-0.6, len(conjuntos) - 0.4])
    if log:
        _eixo_log(fig, 'y')
    if not pontos:
        lo = min(e[3]['bigode_baixo'] for e in extremos)
        hi = max(e[3]['bigode_alto'] for e in extremos)
        folga = (hi - lo) * (0.40 if len(extremos) > 1 else 0.26)
        fig.update_yaxes(range=[lo - folga, hi + folga])
        nome_var = info['nome'].lower()
        varias = len(extremos) > 1          # lado a lado: rótulo curto, o nome já está no eixo
        for k, (vmin, onde_min), (vmax, onde_max), _, quem in extremos:   # dentro da área, na folga
            topo = f'▲ máx. {_valor(vmax, log)}' if varias else f'▲ máximo na {quem}: {_valor(vmax, log)}'
            base = f'▼ mín. {_valor(vmin, log)}' if varias else f'▼ mínimo na {quem}: {_valor(vmin, log)}'
            onde_max_txt = onde_max.replace(', ', '<br>') if varias else onde_max
            onde_min_txt = onde_min.replace(', ', '<br>') if varias else onde_min
            fig.add_annotation(x=k, y=1, yref='paper', yanchor='top', showarrow=False, align='center',
                               text=f'{topo}<br>{onde_max_txt}', font=dict(size=10 if varias else 11, color='#555'))
            fig.add_annotation(x=k, y=0, yref='paper', yanchor='bottom', showarrow=False, align='center',
                               text=f'{onde_min_txt}<br>{base}', font=dict(size=10 if varias else 11, color='#555'))

    if len(contagens) == 1:
        _, f, n = contagens[0]
        fora_txt = f'{F.inteiro(f)} linhas, {F.pct(f / n, 1)}'
    else:
        fora_txt = '; '.join(f'{nome}: {F.inteiro(f)} linhas, {F.pct(f / n, 1)}' for nome, f, n in contagens)
    base = ('Caixa: 1º quartil, mediana e 3º quartil; tracejado dentro da caixa: média; bigodes: até 1,5 × a '
            'distância entre os quartis. ')
    if pontos:
        nota = (f'Pontos: os valores além dos bigodes ({fora_txt}), espalhados na horizontal só para não se '
                'sobreporem. O eixo vai do mínimo ao máximo, por isso a caixa fica pequena: é o peso das '
                'caudas.')
    else:
        nota = (f'Os valores além dos bigodes ({fora_txt}) não aparecem como pontos, para não poluir o '
                f'gráfico; o menor e o maior valor de {nome_var} estão escritos nas bordas, com a ação e o '
                'dia, e na tabela de medidas. Todos entram nas medidas.')
    return fig, base + nota


def grafico_barras(conjuntos: list[tuple[pd.DataFrame, str, str]], coluna: str,
                   altura: int = 330) -> go.Figure:
    info = D.QUALITATIVAS[coluna]
    fig = go.Figure()
    for d, nome, cor in conjuntos:
        f = D.frequencias(d[coluna], info['ordem'])
        fig.add_bar(x=f['categoria'], y=100 * f['proporcao'], name=nome, marker_color=cor,
                    text=[F.pct(p, 1) for p in f['proporcao']], textposition='outside', cliponaxis=False,
                    customdata=f['n'], hovertemplate='%{x}: %{y:.2f}% (%{customdata:,} linhas)<extra>'
                                                      + nome + '</extra>')
    layout(fig, altura, y='% das linhas', legenda=len(conjuntos) > 1)
    fig.update_layout(barmode='group', bargap=0.25)
    fig.update_xaxes(type='category')
    topo = max(t.y.max() for t in fig.data)
    fig.update_yaxes(range=[0, topo * 1.18], ticksuffix='%')
    return fig


def tabela_frequencias(d: pd.DataFrame, coluna: str) -> pd.DataFrame:
    f = D.frequencias(d[coluna], D.QUALITATIVAS[coluna]['ordem'])
    return pd.DataFrame({D.QUALITATIVAS[coluna]['nome']: f['categoria'],
                         'frequência': [F.inteiro(v) for v in f['n']],
                         'proporção': [F.pct(p, 2) for p in f['proporcao']]})


def grafico_agitados(conjuntos: list[tuple[pd.DataFrame, str, str]], altura: int = 300) -> go.Figure:
    fig = go.Figure()
    for d, nome, cor in conjuntos:
        a = D.agitados_por_ano(d)
        fig.add_bar(x=a['ano'].astype(str), y=100 * a['proporcao'], name=nome, marker_color=cor,
                    text=[F.pct(p, 0) for p in a['proporcao']], textposition='outside', cliponaxis=False,
                    customdata=a['n'], hovertemplate='%{x}: %{y:.1f}% de %{customdata:,} linhas<extra>'
                                                      + nome + '</extra>')
    layout(fig, altura, y='% de dias agitados', legenda=len(conjuntos) > 1)
    fig.update_layout(barmode='group', bargap=0.25)
    fig.update_xaxes(type='category')
    fig.update_yaxes(range=[0, max(t.y.max() for t in fig.data) * 1.2], ticksuffix='%')
    return fig


def grafico_qq(x, nome: str, cor: str = COR_AMOSTRA, altura: int = 380) -> tuple[go.Figure, dict]:
    """QQ-plot normal: quantis teóricos × valores padronizados. A reta é a distribuição normal."""
    q = D.qq(x)
    fig = go.Figure()
    fig.add_trace(go.Scattergl(x=q['teoricos'], y=q['padronizados'], mode='markers', name=nome,
                               marker=dict(color=cor, size=4, opacity=0.6),
                               hovertemplate='normal: %{x:.2f} · amostra: %{y:.2f} desvios<extra></extra>'))
    lim = float(np.abs(q['teoricos']).max())
    fig.add_trace(go.Scatter(x=[-lim, lim], y=[-lim, lim], mode='lines', name='normal',
                             line=dict(color=COR_REF, dash=TRACO_REF, width=1), hoverinfo='skip'))
    layout(fig, altura, x='quantil da normal padrão', y='amostra, em desvios-padrão')
    fig.update_layout(title=dict(text=f'<b>{nome}</b>: amostra × normal', x=0, font=dict(size=14)),
                      margin=dict(l=10, r=10, t=40, b=10))
    return fig, q


def _escala(h) -> tuple[float, str]:
    return (100.0, '%') if h.tipo == 'proporcao' else (1.0, '%')


def grafico_ic(linha, altura: int = 260) -> go.Figure:
    """Intervalo de confiança da amostra, com o valor de H0 e o valor real da população.

    Cada elemento tem cor e forma próprias e o valor escrito na legenda, acima do gráfico."""
    h, r = linha.hipotese, linha.resultado
    k, u = _escala(h)
    casas = 2 if h.tipo == 'proporcao' else 3
    est = (r.p_hat if h.tipo == 'proporcao' else r.media) * k
    lo, hi = r.ic[0] * k, r.ic[1] * k
    pop, h0 = linha.parametro * k, h.valor_h0 * k

    def v(x):
        return f'{F.num(x, casas)}{u}'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[h0, h0], y=[-0.8, 0.8], mode='lines', name=f'H₀: {v(h0)}',
                             line=dict(color='#555555', dash='dash', width=2.5), hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[0, 0], mode='lines', line=dict(color=COR_AMOSTRA, width=8),
                             name=f'IC 95% da amostra: {v(lo)} a {v(hi)}', hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=[est], y=[0], mode='markers', name=f'estimativa da amostra: {v(est)}',
                             marker=dict(color='#d95f02', size=18, line=dict(color='white', width=2)),
                             hovertemplate=f'estimativa: {v(est)}<extra></extra>'))
    fig.add_trace(go.Scatter(x=[pop], y=[0], mode='markers', name=f'população: {v(pop)}',
                             marker=dict(color=COR_POP, size=20, symbol='diamond', line=dict(color='white', width=2)),
                             hovertemplate=f'população: {v(pop)}<extra></extra>'))
    if r.limite_unilateral is not None:
        lim = r.limite_unilateral * k
        fig.add_trace(go.Scatter(x=[lim, lim], y=[-0.35, 0.35], mode='lines', name=f'limite unilateral 95%: {v(lim)}',
                                 line=dict(color='#7f2704', width=4), hoverinfo='skip'))
    folga = (hi - lo) * 0.35
    xs = [lo, hi, pop, h0]
    layout(fig, altura, x=f'{"proporção" if h.tipo == "proporcao" else "média"} ({u})', legenda=True)
    fig.update_yaxes(visible=False, range=[-1, 1])
    fig.update_xaxes(range=[min(xs) - folga, max(xs) + folga], ticksuffix=u)
    fig.update_layout(margin=dict(t=70, b=10),
                      legend=dict(orientation='h', x=0, xanchor='left', y=1.02, yanchor='bottom', font=dict(size=14)))
    return fig


def grafico_simulacao(sim: dict, linha, altura: int = 460) -> go.Figure:
    """Distribuição das estimativas em 2.000 AAS, com a população, H0 e a amostra oficial.

    Barras em cinza-claro (são muitas amostras); as três referências são linhas grossas e coloridas,
    identificadas na legenda com o valor de cada uma."""
    h = linha.hipotese
    k, u = _escala(h)
    est = sim['estimativas'][h.codigo] * k
    oficial = (linha.resultado.p_hat if h.tipo == 'proporcao' else linha.resultado.media) * k
    cont, bordas = np.histogram(est, bins=40)
    topo = cont.max() * 1.08
    casas = 2 if h.tipo == 'proporcao' else 3
    fig = go.Figure(go.Bar(x=(bordas[:-1] + bordas[1:]) / 2, y=cont, width=bordas[1] - bordas[0],
                           marker_color='#cfd3da', marker_line_color='white', marker_line_width=1,
                           name=f'estimativas das {F.inteiro(sim["r"])} amostras',
                           hovertemplate='%{y} amostras<extra></extra>'))
    linhas = [(h.valor_h0 * k, f'H₀: {F.num(h.valor_h0 * k, casas)}{u}', '#555555', 'dash', 2.5),
              (linha.parametro * k, f'população: {F.num(linha.parametro * k, casas)}{u}', COR_POP, 'solid', 4),
              (oficial, f'amostra oficial: {F.num(oficial, casas)}{u}', '#d95f02', 'dot', 4)]
    for x, nome, cor, traco, larg in linhas:
        fig.add_trace(go.Scatter(x=[x, x], y=[0, topo], mode='lines', name=nome,
                                 line=dict(color=cor, dash=traco, width=larg),
                                 hovertemplate=nome + '<extra></extra>'))
    layout(fig, altura, x=f'estimativa em cada amostra ({u})', y='número de amostras', legenda=True)
    fig.update_layout(bargap=0, legend=dict(orientation='h', x=0, xanchor='left', y=1.02, yanchor='bottom',
                                            font=dict(size=14)), margin=dict(t=50))
    fig.update_xaxes(ticksuffix=u)
    fig.update_yaxes(range=[0, topo])
    return fig


def _barras_agrupadas(series: list[tuple[list, list, str, str, list]], titulo: str, y: str,
                      altura: int, ref: float | None = None, ref_txt: str = '') -> go.Figure:
    """series: (x, y em %, nome, cor, textos de hover)."""
    fig = go.Figure()
    varios = len(series) > 1                      # comparação: valores só no hover, para não amontoar
    for x, v, nome, cor, hov in series:
        fig.add_bar(x=x, y=v, name=nome, marker_color=cor, customdata=hov,
                    text=None if varios else [F.num(t, 0) + '%' for t in v],
                    textposition='outside', cliponaxis=False,
                    hovertemplate='%{customdata}<extra>' + nome + '</extra>')
    layout(fig, altura, y=y, legenda=varios)
    fig.update_layout(barmode='group', bargap=0.25,
                      title=dict(text=f'<b>{titulo}</b>', x=0, y=0.97, yanchor='top', font=dict(size=14)),
                      margin=dict(t=80 if varios else 45, r=70 if ref is not None else 10),
                      legend=dict(y=1.02, yanchor='bottom'))
    fig.update_xaxes(type='category')
    valores = [v for s in series for v in s[1] if v == v]
    topo = max(valores + [ref or 0, 1])
    fig.update_yaxes(range=[0, topo * 1.2], ticksuffix='%')
    if ref is not None:
        ref_lateral(fig, ref, ref_txt)
    return fig


def ref_lateral(fig: go.Figure, valor: float, texto: str) -> None:
    """Linha de referência horizontal com o rótulo fora da área das barras, à direita."""
    fig.add_hline(y=valor, line_dash=TRACO_REF, line_color=COR_REF, line_width=1)
    fig.add_annotation(x=1, xref='paper', xanchor='left', y=valor, yref='y', showarrow=False,
                       text=f'<b>{texto}</b>', font=dict(size=12, color='#555'), xshift=4)


def graficos_volume(conjuntos: list[tuple[pd.DataFrame, str, str]], altura: int = 340) -> tuple[go.Figure, go.Figure]:
    """1a. Decis de volume relativo (cortes da primeira base): % agitados e |ret| médio."""
    cortes = D.cortes_volume(conjuntos[0][0])
    tabs = [(D.decis_volume(d, cortes), nome, cor) for d, nome, cor in conjuntos]
    ref = tabs[0][0]
    x = [f'{k}º<br>{F.num(v, 2)}×' for k, v in zip(ref['decil'], ref['vol_mediano'])]
    ag = [(x, list(100 * t['agitados']), nome, cor,
           [f'{F.pct(a, 1)} agitados em {F.inteiro(n)} linhas' for a, n in zip(t['agitados'], t['n'])])
          for t, nome, cor in tabs]
    ab = [(x, list(t['absret']), nome, cor,
           [f'|ret| médio {F.num(a, 2)}% em {F.inteiro(n)} linhas' for a, n in zip(t['absret'], t['n'])])
          for t, nome, cor in tabs]
    f1 = _barras_agrupadas(ag, '% de dias agitados (|ret| > 2%)', '% dos dias', altura)
    f2 = _barras_agrupadas(ab, 'Movimento médio do dia (|ret|)', '|ret| médio (%)', altura)
    for f in (f1, f2):
        f.update_xaxes(title='decil do volume relativo (volume típico do decil)')
    if len(tabs) == 1:
        f2.update_traces(texttemplate='%{y:.1f}%')
    return f1, f2


def graficos_concentracao(c: dict, altura: int = 340) -> tuple[go.Figure, go.Figure]:
    """1b. Fatia das 5 maiores no volume do dia, por ano, e participação de cada ação nos 10 anos."""
    pa = c['por_ano']
    f1 = go.Figure(go.Bar(x=[str(a) for a in pa.index], y=100 * pa.values, marker_color=COR_POP,
                          text=[F.pct(v, 0) for v in pa.values], textposition='outside', cliponaxis=False,
                          hovertemplate='%{x}: %{y:.1f}% do volume do dia (mediana)<extra></extra>'))
    layout(f1, altura, y='% do volume do dia')
    f1.update_layout(title=dict(text=f'<b>Fatia das {c["top"]} maiores no volume do dia</b> (mediana por ano)',
                                x=0, font=dict(size=14)), margin=dict(t=45))
    f1.update_xaxes(type='category')
    f1.update_yaxes(range=[0, 100 * pa.max() * 1.2], ticksuffix='%')
    ref_lateral(f1, 100 * c['fatia_mediana'], f'mediana<br>{F.pct(c["fatia_mediana"], 1)}')
    f1.update_layout(margin=dict(r=75))
    top = c['por_acao'].head(10)[::-1]
    f2 = go.Figure(go.Bar(x=100 * top.values, y=top.index, orientation='h', marker_color=COR_POP,
                          text=[F.pct(v, 1) for v in top.values], textposition='outside', cliponaxis=False,
                          hovertemplate='%{y}: %{x:.1f}% do volume dos 10 anos<extra></extra>'))
    layout(f2, altura, x='% do volume financeiro dos 10 anos')
    f2.update_layout(title=dict(text='<b>As 10 ações com mais volume</b>', x=0, font=dict(size=14)),
                     margin=dict(t=45, r=40))
    f2.update_xaxes(range=[0, 100 * top.max() * 1.25], ticksuffix='%')
    return f1, f2


def graficos_humor(conjuntos: list[tuple[pd.DataFrame, str, str]], altura: int = 340) -> tuple[go.Figure, go.Figure]:
    """1c. Por faixa do humor no pregão anterior: % de dias de alta e % de dias agitados."""
    tabs = [(D.tabela_humor(d), nome, cor) for d, nome, cor in conjuntos]
    for t, _, _ in tabs:                          # rótulos em duas linhas: sem texto inclinado
        t['faixa'] = t['faixa'].str.replace(' ', '<br>', n=1)
    alta = [(list(t['faixa']), list(100 * t['alta']), nome, cor,
             [f'{F.pct(a, 1)} de alta em {F.inteiro(n)} linhas' for a, n in zip(t['alta'], t['n'])])
            for t, nome, cor in tabs]
    ag = [(list(t['faixa']), list(100 * t['agitados']), nome, cor,
           [f'{F.pct(a, 1)} agitados em {F.inteiro(n)} linhas' for a, n in zip(t['agitados'], t['n'])])
          for t, nome, cor in tabs]
    f1 = _barras_agrupadas(alta, '% de dias de alta (entre os dias com variação)', '% dos dias', altura,
                           ref=50, ref_txt='50%')
    f2 = _barras_agrupadas(ag, '% de dias agitados (|ret| > 2%)', '% dos dias', altura)
    for f in (f1, f2):
        f.update_xaxes(title='humor no pregão anterior (Fear & Greed B3)', tickangle=0)
    f1.update_yaxes(range=[0, 70])
    return f1, f2


def mostrar(fig: go.Figure, chave: str) -> None:
    st.plotly_chart(fig, width='stretch', config=CONFIG_PLOTLY, key=chave)
