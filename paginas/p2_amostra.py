"""Painel 2 — Análise descritiva da amostra."""
import pandas as pd
import streamlit as st

import comum as C
import descritiva as D
import formato as F

P = C.populacao()
A = C.amostra()
man = C.manifesto()
N, n = len(P), len(A)
dim = man['dimensionamento']

st.title('Painel 2 — Análise descritiva da amostra')
st.markdown(
    f'Uma **amostra aleatória simples** (AAS) de **{F.inteiro(n)} pares ação-dia**, sorteados sem reposição '
    f'entre os {F.inteiro(N)} da população. Esta página mostra como o tamanho foi calculado, como a amostra '
    'foi sorteada e se ela reproduz a população. Os testes do Painel 3 usam **só estas linhas**.')

m = st.columns(5)
m[0].metric('Tamanho da amostra (n)', F.inteiro(n))
m[1].metric('Fração amostral (n/N)', F.pct(n / N, 2))
m[2].metric('Ações na amostra', f'{A["ativo"].nunique()} de {P["ativo"].nunique()}')
m[3].metric('Pregões distintos', F.inteiro(A['data'].nunique()))
m[4].metric('Semente do sorteio', man['selecao']['semente'])

# ---------------------------------------------------------------- dimensionamento
st.header('1. Tamanho da amostra')
st.markdown(r"""
O tamanho foi calculado para **estimar uma proporção** com a margem de erro desejada, com a correção para
população finita de uma AAS sem reposição (Cochran, *Sampling Techniques*, 1977; Bolfarine e Bussab,
*Elementos de Amostragem*, 2005):
""")
st.latex(r'n_0 = \frac{z^2\,p\,(1-p)}{e^2} \qquad\qquad n = \frac{n_0}{1 + \dfrac{n_0 - 1}{N}}')
st.dataframe(pd.DataFrame([
    ('Nível de confiança', '95% (z = 1,96)', 'padrão; é o mesmo α = 5% dos testes do Painel 3'),
    ('Margem de erro (e)', '2 pontos percentuais', 'separa 50% de 52%, a escala das hipóteses de proporção'),
    ('Proporção (p)', '50%', 'pior caso: é onde p(1 − p) é máximo, então o n serve para qualquer proporção'),
    ('Tamanho da população (N)', F.inteiro(N), 'pares ação-dia da população'),
    ('Efeito do desenho', '1', 'amostra aleatória simples'),
    ('Perda', '0%', 'toda linha sorteada tem dado'),
], columns=['parâmetro', 'valor', 'justificativa']), hide_index=True, width='stretch')
n0_r = 1.96 ** 2 * 0.25 / 0.02 ** 2
st.markdown(
    f'**Conta:** n₀ = 1,96² × 0,5 × 0,5 / 0,02² = {F.inteiro(n0_r)}, e n = {F.inteiro(n0_r)} / '
    f'(1 + {F.inteiro(n0_r - 1)} / {F.inteiro(N)}) = {F.num(n0_r / (1 + (n0_r - 1) / N), 1)}, arredondado '
    f'para cima: **n = {F.inteiro(dim["n"])}**.')

st.caption('O script usa z = 1,959964 (n₀ = 2.400,9); com z arredondado para 1,96 a conta dá o mesmo n.')

k = int((A['ret'] != 0).sum())
st.caption(
    f'As proporções P1 e P2 do Painel 3 usam só os dias com variação (retorno ≠ 0): {F.inteiro(k)} das '
    f'{F.inteiro(n)} linhas da amostra. Com esse n, a margem para p = 50% fica em '
    f'{F.num(1.959964 * (0.25 / k) ** 0.5 * 100, 2)} p.p. em vez de 2,00. Para as médias o n não é '
    'recalculado: o Painel 3 mostra a margem que ele produz.')

# ---------------------------------------------------------------- sorteio
st.header('2. Sorteio da amostra')
st.markdown(f"""
1. As {F.inteiro(N)} linhas da população são numeradas de 0 a {F.inteiro(N - 1)}, na ordem **ação (alfabética) e
   data**. Esse número é a coluna `id`.
2. São sorteados {F.inteiro(n)} números **sem reposição**, com o gerador do numpy e a **semente {man["selecao"]["semente"]}**,
   fixada antes de ver qualquer resultado:
""")
st.code(man['selecao']['codigo'], language='python')
st.markdown(f"""
3. Cada linha da população tem a **mesma probabilidade** de entrar: n/N = {F.pct(n / N, 2)}.
4. A amostra fica gravada em `dados/amostra.csv`, com o `id` e a ordem do sorteio de cada linha. Qualquer um
   pode refazer o sorteio (`python amostra.py`) e conferir: o arquivo sai idêntico, e o hash SHA-256 está no
   manifesto (`{man["selecao"]["sha256_csv"][:16]}…`). O app só lê o arquivo; ele nunca sorteia de novo.
""")
primeiras = A.sort_values('ordem_sorteio').head(10)
st.markdown('**As 10 primeiras linhas sorteadas**')
st.dataframe(pd.DataFrame({
    'ordem do sorteio': primeiras['ordem_sorteio'], 'id': primeiras['id'], 'ação': primeiras['ativo'],
    'data': primeiras['data'].map(F.data), 'setor': primeiras['setor'],
    'retorno (%)': primeiras['ret'].map(lambda v: F.num(v, 2)),
    'gap (%)': primeiras['gap'].map(lambda v: F.num(v, 2))}), hide_index=True, width='stretch')


@st.cache_data(show_spinner=False)
def _csv_amostra(versao: float) -> bytes:
    return (C.DADOS / 'amostra.csv').read_bytes()


st.download_button('Baixar a amostra (CSV)', _csv_amostra((C.DADOS / 'amostra.csv').stat().st_mtime),
                   file_name='amostra.csv', mime='text/csv', icon=':material/download:', key='p2_baixar')

# ---------------------------------------------------------------- comparação
st.header('3. A amostra reproduz a população?')
f = C.filtros(P, 'p2')
if f.empty:
    st.warning('Nenhuma linha com esses filtros.')
    st.stop()
a = A[A['id'].isin(f['id'])]
if len(f) < len(P):
    st.info(f'Filtros ativos: a comparação usa {F.inteiro(len(a))} linhas da amostra e {F.inteiro(len(f))} da '
            'população, as mesmas condições dos dois lados.', icon=':material/filter_alt:')
if len(a) < 30:
    st.warning('Com esses filtros sobram menos de 30 linhas da amostra: a comparação fica pouco informativa.')
st.markdown(
    'Os gráficos e as tabelas abaixo comparam as mesmas medidas na **população** (azul) e na **amostra** '
    '(laranja). Uma diferença é "comum" se for do tamanho que o acaso do sorteio produz: para isso, cada '
    'diferença também aparece em **erros-padrão** (até 2 é comum).')
pares = [(f, 'População', C.COR_POP), (a, 'Amostra', C.COR_AMOSTRA)]

st.subheader('Variáveis quantitativas')
R = D.resumo_medias(f, a)
C.tabela(D.tabela_resumo_medias(R))
st.markdown(D.frase_medias(R))
st.caption('Erro-padrão esperado da média amostral: σ/√n × √((N − n)/(N − 1)), com o desvio-padrão σ da '
           'população. Diferença em erros-padrão = (média da amostra − média da população) ÷ erro-padrão.')

st.markdown('**Medidas descritivas das cinco variáveis quantitativas, na amostra** (a mesma tabela do Painel 1)')
C.tabela(D.tabela_medidas(a))
st.caption('Assimetria e curtose: coeficientes de momento, sem correção de viés. A curtose é em excesso (0 na '
           'distribuição normal). Volume financeiro em R$ milhões. Abaixo, escolha uma variável para ver as '
           'mesmas medidas lado a lado com as da população.')

var = st.selectbox('Variável', list(D.QUANTITATIVAS), key='p2_quant',
                   format_func=lambda c: f'{D.QUANTITATIVAS[c]["nome"]} ({D.QUANTITATIVAS[c]["unidade"]})')
info = D.QUANTITATIVAS[var]
g1, g2 = st.columns([2, 1])
with g1:
    fig, nota = C.grafico_histograma(pares, var)
    C.mostrar(fig, 'p2_hist')
    st.caption(nota)
with g2:
    pontos = st.toggle('Mostrar os valores além dos bigodes', value=False, key='p2_pontos')
    fig, nota = C.grafico_caixa(pares, var, pontos=pontos)
    C.mostrar(fig, 'p2_caixa')
    st.caption(C.md(nota))
st.markdown('**Na amostra:** ' + C.md(D.frase_forma(a[var], info['unidade'], positiva=info.get('positiva', False))))
st.dataframe(D.comparar_medidas(f, a, var), hide_index=True, width='stretch')

st.subheader('Variáveis qualitativas')
st.markdown(D.frase_frequencias(f, a))
q = st.selectbox('Variável', list(D.QUALITATIVAS), key='p2_quali',
                 format_func=lambda c: D.QUALITATIVAS[c]['nome'])
C.mostrar(C.grafico_barras(pares, q), 'p2_barras')
st.dataframe(D.tabela_frequencias_comparada(D.comparar_frequencias(f, a, q), D.QUALITATIVAS[q]['nome']),
             hide_index=True, width='stretch')
st.caption('Erro-padrão esperado da proporção amostral: √(p(1 − p)/n) × √((N − n)/(N − 1)), com a proporção '
           'p da população.')
for nota in (D.NOTAS_QUALITATIVAS.get(q), D.nota_base_faixa(a, q, C.LINK_HUMOR_P2)):
    if nota:
        st.caption(nota)

st.subheader('Ao longo do tempo')
C.mostrar(C.grafico_agitados(pares), 'p2_agitados')
por_ano = a[~a['ano'].isin([2016, 2026])].groupby('ano').size()
if len(por_ano):
    st.caption(f'Dias agitados (|ret| > 2%) por ano. Na amostra, cada ano completo tem de '
               f'{F.inteiro(por_ano.min())} a {F.inteiro(por_ano.max())} linhas, contra cerca de 10 mil na '
               'população; por isso a proporção da amostra oscila mais em torno da da população.')

st.subheader('Volume e humor do mercado (descritivo)')
st.markdown('Os mesmos olhares descritivos do Painel 1, agora com a amostra ao lado. Os decis de volume usam os '
            'limites da população, para comparar decil a decil.')
if a['vol_rel'].notna().sum() >= 30 and f['vol_rel'].notna().sum() >= 100:
    v1, v2 = st.columns(2)
    fa, fb = C.graficos_volume(pares)
    with v1:
        C.mostrar(fa, 'p2_vol_agit')
    with v2:
        C.mostrar(fb, 'p2_vol_abs')
    cp, ca_ = D.correlacao_volume(f), D.correlacao_volume(a)
    st.markdown(f'Correlação de Spearman do |ret| com o volume relativo (compara as posições dos valores, de −1 a 1): '
                f'{F.num(ca_["relativo"], 2)} na amostra e {F.num(cp["relativo"], 2)} na população.')
else:
    st.info('Poucas linhas com volume relativo nestes filtros.')
if (a['humor_ant'] != D.SEM_REF).any():
    h1, h2 = st.columns(2)
    ha, hb = C.graficos_humor(pares)
    with h1:
        C.mostrar(ha, 'p2_humor_alta')
    with h2:
        C.mostrar(hb, 'p2_humor_agit')
st.markdown('**Na amostra:** ' + D.frase_humor(D.tabela_humor(a)))
st.caption(D.NOTA_HUMOR)
st.caption('A concentração do volume do Painel 1 não é repetida aqui: a amostra tem em média '
           f'{F.num(len(A) / A["data"].nunique(), 2)} ação por pregão, então a fatia de cada ação no volume do dia '
           'não se calcula nela.')

# ---------------------------------------------------------------- condições dos testes de média
st.header('4. Condição para os testes de média')
st.markdown(
    'O Painel 3 testa as médias (M1 e M2) com o teste t, que exige que a **média** amostral seja '
    'aproximadamente normal. Os gráficos abaixo olham um passo antes: se os **valores** da amostra são '
    'normais. Se fossem, os pontos ficariam sobre a reta tracejada. Eles saem da reta nas pontas, e a '
    'conclusão abaixo explica por que o teste t vale mesmo assim.')
q1, q2 = st.columns(2)
for col, c, chave in ((q1, 'ret', 'p2_qq_ret'), (q2, 'gap', 'p2_qq_gap')):
    with col:
        nome = D.QUANTITATIVAS[c]['nome']
        fig, qd = C.grafico_qq(A[c], nome)
        C.mostrar(fig, chave)
        st.caption(D.frase_qq(qd, nome))
st.markdown(
    f'**Conclusão:** os retornos não são normais (caudas pesadas), mas com n = {F.inteiro(n)} o **Teorema Central '
    'do Limite** garante que a média amostral é aproximadamente normal, e o teste t é aplicável. O Painel 3 '
    'confere isso na prática: em 2.000 amostras sorteadas da população, os intervalos de 95% cobrem a média '
    'verdadeira em cerca de 95% das vezes. Os QQ-plots usam a amostra inteira, sem filtros.')
