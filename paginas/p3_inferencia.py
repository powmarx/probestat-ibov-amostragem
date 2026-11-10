"""Painel 3 — Inferência estatística e comparação dos resultados."""
import numpy as np
import pandas as pd
import streamlit as st

import comum as C
import formato as F
import inferencia as I

P = C.populacao()
A = C.amostra()
N, n = len(P), len(A)

# cinco cartões lado a lado em cada aba: valores um pouco menores, para nenhum ser cortado com "…"
st.html('<style>[data-testid="stMetricValue"] { font-size: 1.75rem !important; }</style>')


@st.cache_data(show_spinner='Sorteando 2.000 amostras da população (alguns segundos)...')
def _simulacao(versao: float, n: int) -> dict:
    return I.simular(C.populacao(), n)


@st.cache_data(show_spinner=False)
def _analise(versao: float) -> list:
    return I.analisar(C.amostra(), C.populacao())


versao = (C.DADOS / 'populacao.parquet').stat().st_mtime + (C.DADOS / 'amostra.parquet').stat().st_mtime
linhas = _analise(versao)
L = {l.hipotese.codigo: l for l in linhas}
sim = _simulacao(versao, n)
dv = I.decisao_x_verdade(linhas, sim).set_index('codigo')
lim_alfa = I.limite_poder_igual_alfa(sim['r'])

st.title('Painel 3 — Inferência estatística e comparação dos resultados')
st.markdown(
    f'Os testes e os intervalos usam **só a amostra** ({F.inteiro(n)} linhas). O valor de cada parâmetro na '
    f'**população** ({F.inteiro(N)} linhas) foi calculado diretamente e só entra aqui para a comparação: '
    'é o que permite ver quando a amostra acertou e quando errou.')
st.markdown(
    '**Métodos, iguais em todas as hipóteses:** nível de significância **α = 5%**; proporções com o teste z '
    '(p₀ no erro-padrão) e o intervalo de Wald 95%, conferidos pelo binomial exato e pelo intervalo de Wilson; '
    'médias com o teste t de uma amostra e o intervalo t 95% (gl = n − 1), conferidos pelo teste do sinal. '
    f'A correção de população finita (√(1 − n/N) = {F.num(np.sqrt(1 - n / N), 3)}) mudaria os erros-padrão '
    f'em {F.pct(1 - np.sqrt(1 - n / N), 1)} e não é aplicada.')

LEITURA = {
    'P1': ('As ações acompanham a direção do Ibovespa na maioria dos dias.',
           'Não há evidência de que as ações acompanhem o Ibovespa mais do que o acaso.'),
    'P2': ('A chance de um dia de alta é diferente de 50%.',
           'A direção de um dia se comporta como "cara ou coroa": não há evidência de que a chance de alta '
           'seja diferente de 50%.'),
    'M1': ('O retorno médio diário é diferente de zero.',
           'Não há evidência de que o retorno médio diário seja diferente de zero. Isso não quer dizer que '
           'ele seja zero.'),
    'M2': ('O gap médio de abertura é diferente de zero.',
           'Não há evidência, nesta amostra, de que o gap médio de abertura seja diferente de zero.'),
    'P1-b': ('As ações acompanham o Ibovespa em mais de dois terços dos dias.',
             'Não há evidência de que o acompanhamento passe de dois terços dos dias.'),
    'M2-b': ('As ações abrem, em média, acima do fechamento anterior.',
             'Não há evidência, nesta amostra, de que o gap médio seja positivo.'),
}

# ---------------------------------------------------------------- hipóteses
st.header('1. As hipóteses')
st.caption('Quatro hipóteses principais (P1, P2, M1, M2), duas de proporção e duas de média, e duas '
           'complementares (P1-b, M2-b), que fazem um segundo teste sobre o mesmo parâmetro.')
abas = st.tabs([l.hipotese.codigo for l in linhas])
for aba, l in zip(abas, linhas):
    h, r = l.hipotese, l.resultado
    d = dv.loc[h.codigo]
    with aba:
        st.subheader(f'{h.codigo} — {h.titulo}')
        if h.complementar:
            st.info('Hipótese complementar, acrescentada depois das quatro principais para atender a uma segunda '
                    'leitura do enunciado: duas hipóteses sobre o mesmo parâmetro de proporção e duas sobre o '
                    'mesmo parâmetro de média. Usa a mesma amostra e os mesmos métodos; o resultado oficial do '
                    'trabalho continua sendo o das quatro principais.', icon=':material/info:')
        st.markdown(f'**Pergunta:** {h.pergunta}')
        tipo = 'Proporção' if h.tipo == 'proporcao' else 'Média'
        st.markdown(f'**{"Evento" if h.tipo == "proporcao" else "Variável"} ({tipo.lower()}):** {h.definicao}.')
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'**H₀:** {h.h0}')
        c2.markdown(f'**H₁:** {h.h1} ({"bilateral" if h.alternativa == "two-sided" else "unilateral"})')
        c3.markdown('**α:** 5%')
        st.caption(f'Por que esta hipótese: {h.justificativa}.')

        with st.expander('Condições de aplicação', icon=':material/rule:'):
            cond = I.condicoes(h, A, N)
            # tabelas estáticas dentro das abas: a tabela interativa não calcula a largura em aba escondida
            st.table(pd.DataFrame({'condição': [c['condicao'] for c in cond],
                                   'valor': [c['valor'] for c in cond],
                                   'atendida': ['—' if c['ok'] is None else 'sim' if c['ok'] else 'não'
                                                for c in cond]}).set_index('condição'))
            if h.tipo == 'media':
                st.caption(f'Os valores têm caudas pesadas. Com n = {F.inteiro(r.n)}, o Teorema Central do Limite '
                           'faz a média amostral ficar aproximadamente normal, mas a regra "n ≥ 30" sozinha não '
                           'garante isso com caudas tão pesadas. A evidência é a simulação da seção 3: o intervalo t '
                           f'cobre a média da população em {F.pct(sim["cobertura"][h.codigo], 2)} das '
                           f'{F.inteiro(sim["r"])} amostras, perto dos 95% prometidos. Os QQ-plots estão no Painel 2.')
                st.page_link('paginas/p2_amostra.py', label='Ver os QQ-plots no Painel 2 (seção 4)',
                             icon=':material/show_chart:')
            else:
                st.caption('As proporções usam só os dias com retorno ≠ 0 '
                           f'({F.inteiro(r.n)} linhas da amostra).')

        m = st.columns([1.2, 2, 1.3, 1, 1.6])        # o IC (até "−0,173 a 0,058") precisa caber inteiro
        if h.tipo == 'proporcao':
            m[0].metric('Estimativa', F.pct(r.p_hat), help=f'na amostra: {F.inteiro(r.x)} de {F.inteiro(r.n)}')
            m[1].metric('IC 95% (%)', f'{F.num(r.ic[0] * 100, 2)} a {F.num(r.ic[1] * 100, 2)}',
                        help=f'[{F.pct(r.ic[0])}; {F.pct(r.ic[1])}]')
            m[2].metric('Estatística', f'z = {F.num(r.z, 2)}')
            pop_txt = F.pct(l.parametro)
        else:
            m[0].metric('Estimativa', f'{F.num(r.media)}%', help=f'na amostra: n = {F.inteiro(r.n)}; '
                        f'desvio {F.num(r.dp, 2)}')
            m[1].metric('IC 95% (%)', f'{F.num(r.ic[0], 3)} a {F.num(r.ic[1], 3)}',
                        help=f'[{F.num(r.ic[0])}%; {F.num(r.ic[1])}%]')
            m[2].metric('Estatística', f't = {F.num(r.t, 2)}', help=f'gl = {F.inteiro(r.gl)}')
            pop_txt = f'{F.num(l.parametro)}%'
        m[3].metric('Valor-p', F.pval(r.p_valor))
        m[4].metric('Decisão sobre H₀', 'rejeita' if r.rejeita else 'não rejeita')

        C.mostrar(C.grafico_ic(l), f'p3_ic_{h.codigo}')
        st.caption(f'Barra laranja: o IC 95% da amostra, com a estimativa no círculo. Losango azul: o valor da '
                   f'população ({pop_txt}), calculado nas {F.inteiro(N)} linhas. Linha cinza tracejada: o valor de H₀.' +
                   (' Traço marrom: o limite unilateral de 95%, que corresponde ao teste unilateral.'
                    if r.limite_unilateral is not None else ''))

        st.markdown(f'**Conclusão:** {I.conclusao(l)}')
        st.markdown(f'**Na prática:** {LEITURA[h.codigo][0 if r.rejeita else 1]}')
        st.markdown('**Comparação com a população:** ' + I.licao(d['resultado'], d['h0_populacao'], d['taxa_rejeicao'],
                                                                 d['distancia'], d['poder_igual_alfa']))

        conf = l.conferencia
        if h.tipo == 'proporcao':
            w = conf['Wilson']
            st.caption(f'Conferência: binomial exato, valor-p {F.pval(conf["binomial exato"])}; intervalo de '
                       f'Wilson [{F.pct(w[0])}; {F.pct(w[1])}]. A decisão é a mesma.')
        else:
            s = conf['sinal']
            st.caption(f'Conferência pela mediana (teste do sinal): {F.inteiro(s["positivos"])} valores positivos e '
                       f'{F.inteiro(s["negativos"])} negativos ({F.inteiro(s["zeros"])} zeros fora), mediana '
                       f'{F.num(s["mediana"])}%, valor-p {F.pval(s["p_valor"])}.' +
                       (' Na M1, esse teste é a própria P2 (mesmo evento: alta entre os dias com variação).'
                        if h.codigo == 'M1' else ''))

        if h.codigo == 'M2':
            st.markdown('**Por que a M2 não rejeitou (sensibilidade, só como complemento)**')
            cb = A[A['data'] == I.DIA_CIRCUIT_BREAKER].sort_values('gap')
            lista = ', '.join(f'{a} ({F.num(g, 1)}%)' for a, g in zip(cb['ativo'], cb['gap']))
            s = I.sensibilidade_m2(A)
            sem = s.iloc[1]
            st.markdown(
                f'A amostra sorteou {len(cb)} linhas de {F.data(I.DIA_CIRCUIT_BREAKER)}, o dia do circuit breaker, '
                f'com gaps de {lista}. Sem elas, a média do gap seria {F.num(sem["estimativa"])}% e o valor-p, '
                f'{F.pval(sem["p_valor"])}.')
            st.table(pd.DataFrame({
                'variante': s['variante'], 'n': s['n'].map(F.inteiro),
                'estimativa (%)': s['estimativa'].map(F.num),
                'IC 95%': [('—' if pd.isna(a) else f'[{F.num(a)}; {F.num(b)}]') for a, b in zip(s['ic_baixo'], s['ic_alto'])],
                'valor-p': s['p_valor'].map(F.pval),
                'rejeita H₀ a 5%': s['rejeita'].map({True: 'sim', False: 'não'})}).set_index('variante'))
            st.caption('O resultado oficial é o da primeira linha. Tirar o dia 26/10 depois de ver o resultado seria '
                       'escolher os dados pela conclusão. A tabela mostra só o peso de poucos valores extremos na '
                       'média e no teste t; o teste do sinal, que olha a mediana, não é afetado.')

# ---------------------------------------------------------------- comparação
st.header('2. Amostra × população: decisão e verdade')
st.dataframe(I.tabela_comparacao(linhas, sim), hide_index=True, width='stretch')
# P1 e P1-b (e M2 e M2-b) estimam o mesmo parâmetro com o mesmo intervalo: conta-se cada intervalo uma vez
intervalos = {}
for l in linhas:
    intervalos.setdefault((round(l.resultado.ic[0], 12), round(l.resultado.ic[1], 12)), []).append(l)
grupos = [' e '.join(x.hipotese.codigo for x in g) for g in intervalos.values() if len(g) > 1]
repetidos = (f'{grupos[0]} usam o mesmo' + ''.join(f', assim como {g}' for g in grupos[1:])) if grupos else ''
cobrem = sum(g[0].ic_cobre for g in intervalos.values())
erros2 = [c for c in dv.index if dv.loc[c, 'resultado'] == 'erro tipo II']
st.markdown(
    f'**Estimativa e intervalo.** {"Os" if cobrem == len(intervalos) else f"{cobrem} dos"} {len(intervalos)} '
    'intervalos de 95% da amostra' + (f' ({repetidos})' if grupos else '')
    + ' contêm o valor da população. A estimativa pontual quase nunca é igual ao valor real; o intervalo diz '
    'quanto ela pode errar só pelo acaso do sorteio.')
verdadeiras = [c for c in dv.index if dv.loc[c, 'h0_populacao'] == 'verdadeira']
indetectaveis = [c for c in erros2 if dv.loc[c, 'poder_igual_alfa']]
st.markdown(
    f'**Decisões.** {len(linhas) - len(erros2)} decisões corretas e {len(erros2)} erros tipo II '
    f'({", ".join(erros2) or "nenhum"}). Nos erros tipo II o intervalo contém o valor real, mas também o valor de '
    'H₀: a amostra não tem precisão para separar os dois. O erro está na decisão do teste, não na estimativa.'
    + (f' Na {", ".join(indetectaveis)}, o erro era inevitável: a diferença é pequena demais para qualquer amostra '
       'deste tamanho.' if indetectaveis else ''))
with st.expander('Como se sabe se H₀ é verdadeira na população', icon=':material/help:'):
    st.markdown(
        f'Comparando o valor de H₀ com o parâmetro calculado nas {F.inteiro(N)} linhas da população. '
        + (f'Em nenhuma das {len(linhas)} hipóteses H₀ é verdadeira, então a taxa de rejeição da seção 3 é o '
           '**poder** de cada teste, e não há erro tipo I real neste trabalho. ' if not verdadeiras else '')
        + 'Ser falsa não quer dizer ser detectável: o que decide é o tamanho da diferença diante do erro-padrão. '
        f'Na P2, a população dá {F.pct(L["P2"].parametro)}, a só {dv.loc["P2", "distancia"]} de 50%; o teste rejeita '
        f'em {F.pct(dv.loc["P2", "taxa_rejeicao"], 2)} das amostras, o que não se distingue de α = 5% nesta simulação '
        f'(até {F.pct(lim_alfa, 2)} com {F.inteiro(sim["r"])} amostras). Ou seja, ela se comporta como se H₀ fosse '
        'verdadeira: a taxa de rejeição dela é praticamente a de um erro tipo I.')
    st.dataframe(pd.DataFrame({
        'hipótese': dv.index,
        'H₀': [L[c].hipotese.h0 for c in dv.index],
        'distância entre a população e H₀': dv['distancia'],
        'H₀ na população': dv['h0_populacao'],
        f'poder (rejeição em {F.inteiro(sim["r"])} amostras)': dv['taxa_rejeicao'].map(lambda v: F.pct(v, 2))}),
        hide_index=True, width='stretch')

b = I.bonferroni(linhas)
st.markdown(
    f'**Seis testes ao mesmo tempo.** Com {len(linhas)} testes a 5%, a chance de ao menos uma rejeição falsa (se as '
    f'H₀ fossem verdadeiras) passa de 5%. Com a correção de Bonferroni (α = 5% / {len(linhas)} = '
    f'{F.pct(b["alfa"], 2)}), '
    + (f'{" e ".join(c for c, v in b["rejeita"].items() if v)} continuam rejeitando, e nenhuma decisão muda.'
       if not b['muda'] else f'mudam as decisões de {", ".join(b["muda"])}.'))

# ---------------------------------------------------------------- variabilidade
st.header('3. Variabilidade amostral')
st.markdown(
    f'Para ver o efeito do acaso, foram sorteadas **{F.inteiro(sim["r"])} amostras** de {F.inteiro(sim["n"])} linhas '
    f'da população (semente {sim["semente"]}, diferente da semente 2026 da amostra oficial), e em cada uma os '
    'seis testes foram refeitos.')
st.dataframe(pd.DataFrame({
    'hipótese': dv.index,
    'rejeita H₀ (poder)': dv['taxa_rejeicao'].map(lambda v: F.pct(v, 2)),
    'IC 95% contém a população': dv['cobertura'].map(lambda v: F.pct(v, 2)),
    'decisão da amostra oficial': dv['decisao'], 'resultado': dv['rotulo']}), hide_index=True, width='stretch')
st.markdown(
    f'Os intervalos de 95% cobrem o valor da população em {F.pct(min(sim["cobertura"].values()), 2)} a '
    f'{F.pct(max(sim["cobertura"].values()), 2)} das amostras, como prometido: o método funciona mesmo com '
    f'retornos de caudas pesadas. Já a decisão depende do poder: a M1 rejeita em só '
    f'{F.pct(sim["rejeicao"]["M1"], 2)} das amostras, e a M2 em {F.pct(sim["rejeicao"]["M2"], 2)}. A amostra '
    'oficial caiu entre as que não rejeitam.')
esc = st.selectbox('Hipótese', [l.hipotese.codigo for l in linhas], index=3, key='p3_sim')
C.mostrar(C.grafico_simulacao(sim, L[esc]), 'p3_hist_sim')
st.caption(f'Cada barra cinza conta quantas das {F.inteiro(sim["r"])} amostras deram aquela estimativa. Linha azul '
           'contínua: o valor da população; laranja pontilhada: a estimativa da amostra oficial; cinza tracejada: '
           'o valor de H₀. Quando H₀ fica longe das barras (como na P1, em que fica fora da escala e o eixo '
           'mostra só as estimativas), quase nenhuma amostra deixaria de '
           'rejeitá-lo; quando fica no meio delas (como na M1), quase nenhuma o rejeitaria.')

st.subheader('Exercício: sortear outra amostra')
st.markdown('Sorteia uma nova AAS do mesmo tamanho e refaz os seis testes. **A amostra oficial do trabalho '
            'continua a da semente 2026**; este exercício só mostra que a conclusão muda de amostra para amostra.')
if 'p3_sorteios' not in st.session_state:
    st.session_state['p3_sorteios'] = 0
if st.button('Sortear outra amostra', icon=':material/casino:', key='p3_sortear'):
    st.session_state['p3_sorteios'] += 1
k = st.session_state['p3_sorteios']
if k:
    semente = 10_000 + k
    outras = {l.hipotese.codigo: l for l in I.analisar(I.amostra_exercicio(P, n, semente), P)}
    st.dataframe(pd.DataFrame({
        'hipótese': list(outras),
        'amostra oficial': [F.pval(L[c].resultado.p_valor) + (' (rejeita)' if L[c].resultado.rejeita else '')
                            for c in outras],
        f'nova amostra (semente {semente})': [F.pval(o.resultado.p_valor) + (' (rejeita)' if o.resultado.rejeita else '')
                                               for o in outras.values()],
        'IC da nova amostra contém a população': ['sim' if o.ic_cobre else 'não' for o in outras.values()]}),
        hide_index=True, width='stretch')
    mud = [c for c in outras if outras[c].resultado.rejeita != L[c].resultado.rejeita]
    st.caption('Valor-p de cada teste. ' + (f'Decisões diferentes da amostra oficial: {", ".join(mud)}.' if mud
                                             else 'Nesta nova amostra, as decisões são as mesmas da oficial.'))

# ---------------------------------------------------------------- limitações
st.header('4. Limitações')
conf_tv = P['conferencia_tv'].value_counts()
n_cb = int((A['data'] == I.DIA_CIRCUIT_BREAKER).sum())
corr_amostra = int((A['conferencia_tv'] == 'corrigido pelo TradingView').sum())
st.markdown(f"""
- **População restrita.** São as 40 ações que o coletor do autor acompanha (16 componentes do Ibovespa e 24 de
  liquidez intermediária e baixa, escolhidas em 2026), de 31/10/2016 a 30/10/2026. As conclusões valem para
  esta população, não para a bolsa inteira nem para outros períodos (viés de sobrevivência: a escolha foi feita
  em 2026, entre ações ainda negociadas; as que saíram da bolsa antes disso não estão aqui).
- **Dependência entre linhas.** Ações do mesmo dia andam juntas. A inferência continua válida porque vem do
  sorteio (AAS de uma população finita, n/N = {F.pct(n / N, 1)}), e a simulação confirma a cobertura de ~95%.
- **Qualidade da fonte.** A base do Yahoo foi conferida com o TradingView: {F.pct(conf_tv.get('idêntico', 0) / N, 1)}
  das linhas são idênticas, {F.inteiro(conf_tv.get('corrigido pelo TradingView', 0))} linhas com diferença acima de
  5 p.p. foram corrigidas ({F.inteiro(corr_amostra)} na amostra), e {F.inteiro(conf_tv.get('diferença até 5 p.p.', 0))}
  com diferenças menores ficaram como estão. Dois pregões faltam no Yahoo (29/05/2017 e 20/11/2020).
- **Dividendos.** Os retornos não incluem dividendos e JCP, que fazem o preço cair na data-ex; por isso o retorno
  e o gap médios ficam um pouco subestimados. O tamanho desse efeito não foi medido: exigiria uma fonte de
  proventos com data-ex, valor e separação entre dividendos e JCP, que esta base não tem, e a qualidade desses
  dados no Yahoo não foi conferida.
- **Valores extremos.** A M2 depende de {n_cb} linhas do circuit breaker de {F.data(I.DIA_CIRCUIT_BREAKER)}
  (seção 1, aba M2).
- **Muitos testes.** Seis testes aumentam a chance de uma rejeição falsa; com Bonferroni nenhuma decisão muda.
- **Hipóteses complementares.** P1-b e M2-b foram acrescentadas depois das quatro principais, para atender à
  segunda leitura do enunciado (duas hipóteses sobre o mesmo parâmetro), e não por causa de um resultado. O valor
  2/3 da P1-b é um valor redondo, sem base teórica; na M2-b, a direção unilateral vem de Cliff, Cooper e Gulen
  (2008), não da amostra.
- **Variáveis descritivas.** O setor é a classificação atual da B3 aplicada aos 10 anos.
""")
