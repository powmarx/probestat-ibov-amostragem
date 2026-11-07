"""Testes das funções descritivas (Painéis 1 e 2) e da formatação."""
import numpy as np
import pandas as pd
import pytest

import descritiva as D
import formato as F
import preparar_dados as PD


@pytest.fixture(scope='module')
def P():
    return pd.read_parquet(PD.SAIDA / 'populacao.parquet')


def test_formato():
    assert F.num(1234.5, 1) == '1.234,5'
    assert F.num(-0.0572) == '−0,057'
    assert F.pct(0.5) == '50,00%'
    assert F.pct(float('nan')) == '—'
    assert F.inteiro(96610) == '96.610'
    assert F.data(pd.Timestamp('2016-10-31')) == '31/10/2016'


def test_medidas_caso_a_mao():
    m = D.medidas([1, 2, 3, 4, 100])
    assert (m['n'], m['media'], m['mediana'], m['minimo'], m['maximo']) == (5, 22, 3, 1, 100)
    assert (m['q1'], m['q3']) == (2, 4)
    assert m['dp'] == pytest.approx(np.std([1, 2, 3, 4, 100], ddof=1))
    assert m['assimetria'] > 1                              # cauda à direita


def test_medidas_da_populacao(P):
    m = D.medidas(P['ret'])
    assert m['n'] == 96_610
    assert m['media'] == pytest.approx(0.0525, abs=5e-5)
    assert m['dp'] == pytest.approx(2.868, abs=5e-4)


def test_tabela_medidas_tem_as_cinco_variaveis(P):
    t = D.tabela_medidas(P)
    assert list(t['variável']) == [v['nome'] for v in D.QUANTITATIVAS.values()]
    assert t.loc[0, 'n'] == '96.610'


def test_frequencias_ordem_e_soma(P):
    f = D.frequencias(P['dia_semana'], D.QUALITATIVAS['dia_semana']['ordem'])
    assert list(f['categoria']) == ['segunda', 'terça', 'quarta', 'quinta', 'sexta']
    assert f['n'].sum() == len(P) and f['proporcao'].sum() == pytest.approx(1)
    h = D.frequencias(P['humor_ant'], D.QUALITATIVAS['humor_ant']['ordem'])
    assert list(h['categoria'])[-1] == D.SEM_REF
    a = D.frequencias(P['ano'])
    assert list(a['categoria']) == [str(x) for x in range(2016, 2027)]


def test_todas_as_qualitativas_somam_n(P):
    for c, info in D.QUALITATIVAS.items():
        assert D.frequencias(P[c], info['ordem'])['n'].sum() == len(P), c


def test_histograma_recorta_so_o_eixo(P):
    h = D.histograma(P['ret'])
    assert h['contagens'].sum() + h['abaixo'] + h['acima'] == h['n'] == len(P)
    assert 0 < h['abaixo'] + h['acima'] < 0.011 * len(P)
    hl = D.histograma(P['fin'], log=True)
    assert hl['log'] and hl['zeros_excluidos'] == 0          # volume > 0 em toda a população


def test_caixa(P):
    c = D.caixa([1, 2, 3, 4, 100])
    assert (c['q1'], c['mediana'], c['q3']) == (2, 3, 4)
    assert c['bigode_alto'] == 4 and c['fora'] == 1
    cp = D.caixa(P['gap'])
    assert cp['bigode_baixo'] <= cp['q1'] <= cp['mediana'] <= cp['q3'] <= cp['bigode_alto']


def test_agitados_por_ano(P):
    a = D.agitados_por_ano(P).set_index('ano')
    assert a['n'].sum() == len(P)
    assert a.loc[2020, 'proporcao'] == pytest.approx(0.455, abs=0.001)
    assert a.loc[2024, 'proporcao'] == pytest.approx(0.267, abs=0.001)


def test_nota_sem_referencia(P):
    assert '95 linhas' in D.nota_sem_referencia(P, 'faixa_volume')
    assert '17.403 linhas' in D.nota_sem_referencia(P, 'humor_ant')
    assert D.nota_sem_referencia(P, 'setor') is None


def test_dicionario_cobre_as_27_colunas():
    nomes = set()
    for coluna, _, _ in D.DICIONARIO:
        nomes.update(c.strip() for c in coluna.split(','))
    assert nomes == set(PD.COLUNAS_POPULACAO)


def test_frase_forma(P):
    t = D.frase_forma(P['ret'], '%')
    assert '0,053%' in t and 'acima da mediana' in t and 'caudas muito mais pesadas' in t
    assert 'R$' in D.frase_forma(P['fin'], 'R$ milhões')
    # amplitude e volume: cauda à direita, mediana como dia típico
    amp = D.frase_forma(P['amp'], '%', positiva=True)
    assert 'assimétrica à direita' in amp and '(2,998%)' in amp
    fin = D.frase_forma(P['fin'], 'R$ milhões', positiva=True)
    assert 'assimétrica à direita' in fin and 'R$ 132,2 milhões' in fin
    assert 'assimétrica à direita' not in t                                   # retorno: não se aplica


def test_grafico_caixa_com_e_sem_pontos(P):
    import comum as C
    sem, nota_sem = C.grafico_caixa([(P, 'População', C.COR_POP)], 'ret')
    com, nota_com = C.grafico_caixa([(P, 'População', C.COR_POP)], 'ret', pontos=True)
    assert len(sem.data) == 1 and len(com.data) == 2
    assert len(com.data[1].y) == D.caixa(P['ret'])['fora'] == 5010        # todos, sem amostrar
    textos = [a.text for a in sem.layout.annotations]
    assert any('máximo na população: +139,13%<br>PCAR3, 01/02/2017' in t for t in textos)
    assert any('MGLU3, 26/10/2026<br>▼ mínimo na população: −58,23%' in t for t in textos)
    assert 'não aparecem como pontos' in nota_sem and '5.010 linhas' in nota_sem
    assert 'Pontos:' in nota_com
    _, nota_log = C.grafico_caixa([(P, 'População', C.COR_POP)], 'fin')
    assert 'R$' in ' '.join(a.text for a in _.layout.annotations)
    # volume pequeno não pode aparecer como zero (rótulo, tabela, eixo e nota)
    assert any('mínimo na população: R$ 1,3 mil' in a.text for a in _.layout.annotations)
    assert D.tabela_medidas(P).set_index('variável').loc['Volume financeiro', 'mínimo'] == '0,0013'
    assert '0,001' in _.layout.yaxis.ticktext
    assert 'não volume zero' in nota_log and '916 linhas' in nota_log and 'R$ 1,3 mil (ENEV3, 22/06/2017' in nota_log


def test_reais_mi():
    assert F.reais_mi(132.17) == 'R$ 132,2 mi'
    assert F.reais_mi(11601.24) == 'R$ 11.601,2 mi'
    assert F.reais_mi(0.0013) == 'R$ 1,3 mil'


def test_tabela_conferencia(P):
    t = D.tabela_conferencia(P)
    assert list(t['categoria'])[:3] == ['idêntico', 'diferença até 5 p.p.', 'corrigido pelo TradingView']
    assert t.set_index('categoria').loc['corrigido pelo TradingView', 'linhas'] == '19'
    assert t['regra'].notna().all()


# ---------------------------------------------------------------- Painel 2: amostra × população
@pytest.fixture(scope='module')
def A():
    return pd.read_parquet(PD.SAIDA / 'amostra.parquet')


def test_resumo_medias(P, A):
    R = D.resumo_medias(P, A).set_index('coluna')
    assert list(R.index) == list(D.QUANTITATIVAS)
    ep = P['ret'].std() / np.sqrt(len(A)) * np.sqrt((len(P) - len(A)) / (len(P) - 1))
    assert R.loc['ret', 'ep'] == pytest.approx(ep)
    assert R.loc['ret', 'z'] == pytest.approx((A['ret'].mean() - P['ret'].mean()) / ep)
    assert (R['z'].abs() <= 2).all()                      # todas dentro de 2 erros-padrão
    assert 'Todas estão dentro de 2 erros-padrão' in D.frase_medias(R)


def test_comparar_frequencias(P, A):
    for c in D.QUALITATIVAS:
        C = D.comparar_frequencias(P, A, c)
        assert C['pop'].sum() == pytest.approx(1) and C['amostra'].sum() == pytest.approx(1)
        assert C['n_amostra'].sum() == len(A)
    dia = D.comparar_frequencias(P, A, 'dia_semana').set_index('categoria')
    assert dia.loc['terça', 'z'] == pytest.approx(-2.06, abs=0.01)
    t = D.frase_frequencias(P, A)
    assert '1 passa de 2 erros-padrão' in t and 'terça' in t


def test_comparar_medidas_formatada(P, A):
    t = D.comparar_medidas(P, A, 'ret').set_index('medida')
    assert t.loc['n', 'população'] == '96.610' and t.loc['n', 'amostra'] == '2.343'
    assert t.loc['média', 'amostra'] == '−0,057'


def test_qq(A):
    q = D.qq(A['gap'])
    assert q['n'] == len(A) and len(q['teoricos']) == len(A)
    assert q['teoricos'][0] < 0 < q['teoricos'][-1]
    assert q['alem3'] > q['esperado3'] * q['n']           # caudas pesadas
    assert q['min'] < -20                                 # TOTS3 em 26/10/2026
    assert 'caudas são mais pesadas' in D.frase_qq(q, 'Gap')


# ---------------------------------------------------------------- extras 1a, 1b, 1c
def test_decis_volume(P, A):
    T = D.decis_volume(P)
    assert len(T) == 10 and T['n'].sum() == P['vol_rel'].notna().sum()
    assert T.loc[0, 'vol_mediano'] == pytest.approx(0.51, abs=0.005)
    assert T.loc[9, 'vol_mediano'] == pytest.approx(2.29, abs=0.005)
    assert T.loc[0, 'agitados'] == pytest.approx(0.1443, abs=5e-4)
    assert T.loc[9, 'agitados'] == pytest.approx(0.603, abs=5e-4)
    assert T['agitados'].is_monotonic_increasing
    # amostra com os cortes da população
    Ta = D.decis_volume(A, D.cortes_volume(P))
    assert Ta['n'].sum() == A['vol_rel'].notna().sum()
    c = D.correlacao_volume(P)
    assert c['relativo'] == pytest.approx(0.309, abs=0.001) and c['bruto'] < 0.15
    assert 'Spearman 0,31' in D.frase_volume(T, c)


def test_concentracao(P):
    c = D.concentracao(P)
    assert c['fatia_mediana'] == pytest.approx(0.495, abs=0.001)
    assert round(c['equivalente']) == 14
    assert list(c['por_acao'].index[:2]) == ['PETR4', 'VALE3']
    assert c['por_acao'].sum() == pytest.approx(1)
    assert '14 ações' in D.frase_concentracao(c)


def test_tabela_humor(P, A):
    T = D.tabela_humor(P).set_index('faixa')
    assert list(T.index) == ['medo extremo', 'medo', 'neutro', 'ganância', 'ganância extrema']
    assert T['n'].sum() == (P['humor_ant'] != D.SEM_REF).sum()
    assert T.loc['medo extremo', 'agitados'] == pytest.approx(0.420, abs=0.001)
    assert T['alta'].between(0.48, 0.52).all()
    assert 'o humor de ontem não diz para onde' in D.frase_humor(D.tabela_humor(P))
    assert D.frase_humor(D.tabela_humor(P[P['ano'] == 2017])).startswith('Sem linhas')


def test_graficos_extras(P, A):
    import comum as C
    f1, f2 = C.graficos_volume([(P, 'População', C.COR_POP), (A, 'Amostra', C.COR_AMOSTRA)])
    assert len(f1.data) == 2 and len(f1.data[0].x) == 10
    g1, g2 = C.graficos_concentracao(D.concentracao(P))
    assert len(g2.data[0].y) == 10
    h1, _ = C.graficos_humor([(P, 'População', C.COR_POP)])
    assert len(h1.data[0].x) == 5
