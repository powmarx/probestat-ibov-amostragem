"""Painel 1 — Análise descritiva da população."""
import pandas as pd
import streamlit as st

import comum as C
import descritiva as D
import formato as F

P = C.populacao()
r = D.resumo_base(P)

st.title('Painel 1 — Análise descritiva da população')
st.markdown(
    f'A **população** são todos os pares ação-dia de **{r["acoes"]} ações da B3** em '
    f'**{F.inteiro(r["pregoes"])} pregões**, de {F.data(r["inicio"])} a {F.data(r["fim"])}: '
    f'{F.inteiro(r["n"])} linhas. A **unidade amostral** é uma ação em um pregão. Os números desta página '
    'são da população inteira; a inferência do Painel 3 usa só a amostra.')

m = st.columns(6)
m[0].metric('Observações (N)', F.inteiro(r['n']))
m[1].metric('Ações', r['acoes'])
m[2].metric('Pregões', F.inteiro(r['pregoes']))
m[3].metric('Período', f'{round((r["fim"] - r["inicio"]).days / 365.25)} anos',
            help=f'{F.data(r["inicio"])} a {F.data(r["fim"])}')
m[4].metric('Setores (B3)', r['setores'])
m[5].metric('Variáveis', len(P.columns))

# ---------------------------------------------------------------- sobre a base
with st.expander('Sobre a base de dados: fonte, construção e variáveis', icon=':material/database:'):
    ident = int((P['conferencia_tv'] == 'idêntico').sum())
    corr = int((P['conferencia_tv'] == 'corrigido pelo TradingView').sum())
    st.markdown(f"""
**Fonte dos preços.** Yahoo Finance, cotações diárias (abertura, máxima, mínima, fechamento e volume)
de {r["acoes"]} ações da B3 e do Ibovespa. Página de histórico de cada ação, por exemplo
[VALE3.SA]({C.FONTE_YAHOO}); dados obtidos pela API pública `{C.API_YAHOO}`.

**As {r["acoes"]} ações e o critério de escolha.** São as que o coletor de dados do autor acompanha. Ele foi
montado na disciplina IA001 – Análise e Visualização de Dados com Python e Ferramentas Assistidas por IA, para
estudar se as três maiores ações do Ibovespa (VALE3, ITUB4 e PETR4) antecipam o índice. A Atividade 01 da
disciplina escolheu 16 componentes do índice com liquidez variada, para ver se as três maiores se destacavam
entre elas. Na Atividade 02, essa cesta se mostrou líquida demais para medir o atraso do índice (só 1% a 4%
das ações ficavam sem negócio em cada minuto), e na Atividade 03 foram acrescentadas 24 ações de liquidez
intermediária e baixa. A população é, portanto, o conjunto definido por esse estudo, e não uma amostra da
bolsa nem as ações mais negociadas.

**Fonte do setor.** [B3, Classificação setorial]({C.FONTE_B3}), consultada em 31/10/2026 pela API de
empresas listadas que essa página usa.

**Base completa.** O CSV da população está no [repositório do trabalho]({C.REPO}), compactado:
[dados/populacao.zip]({C.ZIP_POPULACAO}). A cópia congelada das cotações e o código que monta a
população também estão lá.

**Contexto e objetivo.** Os preços vêm do coletor diário que o autor montou na disciplina IA001, que guarda
10 anos de cotações diárias. Aqui eles servem para descrever como as ações se comportam dia a dia e testar afirmações comuns sobre a bolsa: se a
ação acompanha o índice, se a alta é "cara ou coroa", se o retorno e o gap médios são zero.

**Construção da população.**
- 10 anos exatos, de {F.data(r["inicio"])} a {F.data(r["fim"])}; base congelada em 31/10/2026 para não
  mudar com novas coletas.
- Só dias com negócio (volume > 0). O fechamento anterior é o do último pregão com negócio da ação.
- Preços ajustados pela fonte por desdobramentos, grupamentos e bonificações. **Dividendos e JCP não
  estão incluídos**: o preço cai na data-ex, então o retorno e o gap médios ficam um pouco subestimados.
  O tamanho desse efeito não foi medido (ver as limitações no Painel 3).
- Faltam dois pregões, porque faltam no Yahoo: 29/05/2017 (sem negócio na fonte) e 20/11/2020.
- Tamanho: **{F.inteiro(len(P))} observações e {len(P.columns)} variáveis**.

**Conferência com uma segunda fonte.** Todas as linhas foram comparadas com as cotações do TradingView
(lidas por uma biblioteca não oficial e congeladas junto com a base). Em **{F.pct(ident / len(P), 1)}**
das linhas o retorno do dia é idêntico nas duas fontes. As **{corr} linhas** com diferença acima de
5 p.p., com o mesmo pregão anterior, foram tratadas como erros do Yahoo e receberam os preços do
TradingView (em várias, o Yahoo põe o movimento no dia errado ou não ajusta um evento societário);
nenhuma delas está na amostra. O resultado de cada linha está na coluna `conferencia_tv`.
""")
    st.dataframe(D.tabela_conferencia(P), hide_index=True, width='stretch')
    st.caption('Detalhes, a lista das linhas corrigidas e a justificativa do limite de 5 p.p.: '
               f'[docs/conferencia_tradingview.md]({C.DOC_TV}), no repositório do trabalho.')
    st.markdown('**Dicionário de variáveis**')
    st.dataframe(pd.DataFrame(D.DICIONARIO, columns=['coluna', 'tipo', 'descrição']), hide_index=True,
                 width='stretch', height=35 * (len(D.DICIONARIO) + 1) + 3)   # sem rolagem interna
    st.caption('vol_rel e fg_ant precisam de histórico anterior: nas linhas em que ele ainda não existe, a coluna '
               'fica vazia (e a faixa, no arquivo, "sem referência"). Os gráficos e tabelas das faixas usam só as '
               'linhas que têm o dado, e a nota de cada um diz quantas são.')

f = C.filtros(P, 'p1')
if f.empty:
    st.warning('Nenhuma linha com esses filtros.')
    st.stop()
if len(f) < len(P):
    st.info(f'Filtros ativos: os gráficos e tabelas abaixo usam {F.inteiro(len(f))} das '
            f'{F.inteiro(len(P))} linhas da população.', icon=':material/filter_alt:')

# ---------------------------------------------------------------- quantitativas
st.header('Variáveis quantitativas')
var = st.selectbox('Variável', list(D.QUANTITATIVAS), key='p1_quant',
                   format_func=lambda c: f'{D.QUANTITATIVAS[c]["nome"]} ({D.QUANTITATIVAS[c]["unidade"]})')
info = D.QUANTITATIVAS[var]
st.caption(f'Definição: {info["definicao"]}.')
g1, g2 = st.columns([2, 1])
with g1:
    fig, nota = C.grafico_histograma([(f, 'População', C.COR_POP)], var)
    C.mostrar(fig, 'p1_hist')
    st.caption(nota)
with g2:
    pontos = st.toggle('Mostrar os valores além dos bigodes', value=False, key='p1_pontos')
    fig, nota = C.grafico_caixa([(f, 'População', C.COR_POP)], var, pontos=pontos)
    C.mostrar(fig, 'p1_caixa')
    st.caption(C.md(nota))
st.markdown(C.md(D.frase_forma(f[var], info['unidade'], positiva=info.get('positiva', False))))

st.subheader('Medidas descritivas das cinco variáveis quantitativas')
C.tabela(D.tabela_medidas(f))
st.caption('Assimetria e curtose: coeficientes de momento, sem correção de viés. A curtose é em excesso (0 na '
           'distribuição normal). Assimetria e curtose não têm unidade. '
           'Volume financeiro em R$ milhões.')

# ---------------------------------------------------------------- qualitativas
st.header('Variáveis qualitativas')
q = st.selectbox('Variável', list(D.QUALITATIVAS), key='p1_quali',
                 format_func=lambda c: D.QUALITATIVAS[c]['nome'])
b1, b2 = st.columns([1.6, 1])
with b1:
    C.mostrar(C.grafico_barras([(f, 'População', C.COR_POP)], q), 'p1_barras')
with b2:
    C.tabela(C.tabela_frequencias(f, q))
for nota in (D.NOTAS_QUALITATIVAS.get(q), D.nota_base_faixa(f, q, C.LINK_HUMOR_P1)):
    if nota:
        st.caption(nota)

# ---------------------------------------------------------------- tempo
st.header('Ao longo do tempo')
a = D.agitados_por_ano(f)
completos = a[~a['ano'].isin([2016, 2026])] if len(a) > 2 else a
alto, baixo = completos.loc[completos['proporcao'].idxmax()], completos.loc[completos['proporcao'].idxmin()]
st.markdown(f'**Dias agitados (|ret| > 2%) por ano.** O ano mais agitado foi {int(alto["ano"])}, com '
            f'{F.pct(alto["proporcao"], 0)} dos dias; o mais calmo, {int(baixo["ano"])}, com '
            f'{F.pct(baixo["proporcao"], 0)}.')
C.mostrar(C.grafico_agitados([(f, 'População', C.COR_POP)]), 'p1_agitados')
st.caption('2016 (nov. e dez.) e 2026 (até 30/10) são anos incompletos e ficam fora da comparação do texto.')

# ---------------------------------------------------------------- extras descritivos
st.header('Volume e humor do mercado')
st.caption('Três olhares descritivos, sem teste de hipótese, que ajudam a entender a população. Eles não fazem '
           'parte das hipóteses do Painel 3.')

st.subheader('Dias de volume acima do normal têm movimentos maiores')
pop = [(f, 'População', C.COR_POP)]
if f['vol_rel'].notna().sum() >= 100:
    v1, v2 = st.columns(2)
    fa, fb = C.graficos_volume(pop)
    with v1:
        C.mostrar(fa, 'p1_vol_agit')
    with v2:
        C.mostrar(fb, 'p1_vol_abs')
    st.markdown(D.frase_volume(D.decis_volume(f), D.correlacao_volume(f)))
else:
    st.info('Poucas linhas com volume relativo nestes filtros.')
st.caption(D.NOTA_VOLUME)

st.subheader('Concentração do volume')
conc = D.concentracao(f)
c1, c2 = st.columns(2)
ca, cb = C.graficos_concentracao(conc)
with c1:
    C.mostrar(ca, 'p1_conc_ano')
with c2:
    C.mostrar(cb, 'p1_conc_acao')
st.markdown(D.frase_concentracao(conc))
st.caption(D.NOTA_CONCENTRACAO)

st.subheader('O humor de ontem não diz para onde a ação vai, mas diz quanto ela se mexe', anchor=C.ANCORA_HUMOR)
with st.expander('Como o Fear & Greed B3 é calculado', icon=':material/psychology:'):
    st.markdown(D.EXPLICACAO_HUMOR)
if (f['humor_ant'] != D.SEM_REF).any():
    h1, h2 = st.columns(2)
    ha, hb = C.graficos_humor(pop)
    with h1:
        C.mostrar(ha, 'p1_humor_alta')
    with h2:
        C.mostrar(hb, 'p1_humor_agit')
st.markdown(D.frase_humor(D.tabela_humor(f)))
st.caption(D.NOTA_HUMOR)
