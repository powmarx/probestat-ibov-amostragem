"""Testes da inferência: casos calculados à mão e os valores oficiais do trabalho (Painel 3 e README)."""
import numpy as np
import pandas as pd
import pytest

import inferencia as I
import preparar_dados as PD


@pytest.fixture(scope='module')
def P():
    return pd.read_parquet(PD.SAIDA / 'populacao.parquet')


@pytest.fixture(scope='module')
def A():
    return pd.read_parquet(PD.SAIDA / 'amostra.parquet')


@pytest.fixture(scope='module')
def linhas(A, P):
    return {l.hipotese.codigo: l for l in I.analisar(A, P)}


@pytest.fixture(scope='module')
def sim(P, A):
    return I.simular(P, len(A))


# ---------------------------------------------------------------- casos à mão
def test_proporcao_caso_a_mao():
    # 60 sucessos em 100, H0 p = 0,5: z = (0,6 − 0,5) / √(0,25/100) = 2
    r = I.teste_proporcao(60, 100, 0.5)
    assert r.z == pytest.approx(2.0)
    assert r.p_valor == pytest.approx(0.0455, abs=1e-4)
    ep = np.sqrt(0.6 * 0.4 / 100)
    assert r.ic == pytest.approx((0.6 - 1.959964 * ep, 0.6 + 1.959964 * ep), abs=1e-6)
    assert r.limite_unilateral is None
    u = I.teste_proporcao(60, 100, 0.5, 'greater')
    assert u.p_valor == pytest.approx(r.p_valor / 2)
    assert u.limite_unilateral == pytest.approx(0.6 - 1.644854 * ep, abs=1e-6)


def test_media_caso_a_mao():
    # x = 1..5, H0 μ = 2: média 3, dp 1,5811, ep 0,7071, t = 1,4142, gl 4, p = 0,2302
    r = I.teste_media([1, 2, 3, 4, 5], 2)
    assert (r.media, r.gl) == (3.0, 4)
    assert r.dp == pytest.approx(1.5811, abs=1e-4)
    assert r.t == pytest.approx(1.4142, abs=1e-4)
    assert r.p_valor == pytest.approx(0.2302, abs=1e-4)
    meia = 2.776445 * 1.5811388 / np.sqrt(5)
    assert r.ic == pytest.approx((3 - meia, 3 + meia), abs=1e-5)


def test_sinal_caso_a_mao():
    s = I.teste_sinal([1, 2, -1, 0, 3])
    assert (s['positivos'], s['negativos'], s['zeros']) == (3, 1, 1)
    assert s['p_valor'] == pytest.approx(0.625)          # binomial(3 de 4, 0,5), bilateral


def test_formatos_brasileiros():
    assert I._num(-1234.5678, 2) == '−1.234,57'
    assert I._pct(0.6946) == '69,46%'
    assert I._pval(3e-5) == '< 0,0001'


# ---------------------------------------------------------------- valores oficiais (Painel 3 e README)
def test_parametros_da_populacao(linhas):
    assert linhas['P1'].parametro == pytest.approx(0.6946, abs=5e-5)
    assert linhas['P2'].parametro == pytest.approx(0.4986, abs=5e-5)
    assert linhas['M1'].parametro == pytest.approx(0.0525, abs=5e-5)     # após a conferência TradingView
    assert linhas['M2'].parametro == pytest.approx(0.0904, abs=5e-5)


def test_p1(linhas):
    r = linhas['P1'].resultado
    assert (r.x, r.n) == (1598, 2311)
    assert r.z == pytest.approx(18.41, abs=0.005) and r.rejeita
    assert r.ic == pytest.approx((0.6726, 0.7103), abs=5e-5)


def test_p2(linhas):
    r = linhas['P2'].resultado
    assert (r.x, r.n) == (1109, 2311)
    assert r.z == pytest.approx(-1.935, abs=5e-4)
    assert r.p_valor == pytest.approx(0.0530, abs=5e-5) and not r.rejeita
    assert r.p_valor_exato == pytest.approx(0.0556, abs=5e-5)
    assert r.ic_wilson == pytest.approx((0.4596, 0.5003), abs=5e-5)


def test_m1_m2(linhas):
    m1, m2 = linhas['M1'].resultado, linhas['M2'].resultado
    assert m1.t == pytest.approx(-0.972, abs=5e-4) and m1.p_valor == pytest.approx(0.3311, abs=5e-5)
    assert m1.ic == pytest.approx((-0.1725, 0.0582), abs=5e-5)
    assert m2.t == pytest.approx(1.367, abs=5e-4) and m2.p_valor == pytest.approx(0.1717, abs=5e-5)
    assert m2.ic == pytest.approx((-0.0205, 0.1146), abs=5e-5)
    assert not m1.rejeita and not m2.rejeita


def test_complementares(linhas):
    p1b, m2b = linhas['P1-b'].resultado, linhas['M2-b'].resultado
    assert p1b.z == pytest.approx(2.53, abs=0.005) and p1b.p_valor == pytest.approx(0.0057, abs=5e-5)
    assert p1b.p_valor_exato == pytest.approx(0.0058, abs=5e-5) and p1b.rejeita
    assert m2b.p_valor == pytest.approx(0.0859, abs=5e-5) and not m2b.rejeita
    assert m2b.p_valor == pytest.approx(linhas['M2'].resultado.p_valor / 2)
    assert m2b.limite_unilateral == pytest.approx(-0.0096, abs=5e-5)


def test_todos_os_ics_contem_a_populacao(linhas):
    assert all(l.ic_cobre for l in linhas.values())


def test_conferencia_do_sinal(linhas):
    m2 = linhas['M2'].conferencia['sinal']
    assert (m2['positivos'], m2['negativos']) == (1206, 953) and m2['p_valor'] < 1e-4
    # na M1 o teste do sinal é a própria P2 (mesmo evento, mesmo domínio)
    assert linhas['M1'].conferencia['sinal']['p_valor'] == pytest.approx(linhas['P2'].resultado.p_valor_exato)


def test_bonferroni_nao_muda_nada(linhas):
    b = I.bonferroni(list(linhas.values()))
    assert b['alfa'] == pytest.approx(0.05 / 6)
    assert b['muda'] == []
    assert [c for c, v in b['rejeita'].items() if v] == ['P1', 'P1-b']


def test_sensibilidade_m2(A):
    s = I.sensibilidade_m2(A).set_index('variante')
    assert s.loc['Oficial (todas)', 'p_valor'] == pytest.approx(0.1717, abs=5e-5)
    assert s.loc['Sem 26/10/2026', 'n'] == 2340
    assert s.loc['Sem 26/10/2026', 'p_valor'] == pytest.approx(0.0045, abs=5e-5)
    assert s.loc['Winsorizada a 0,5%', 'p_valor'] == pytest.approx(0.0018, abs=5e-5)
    assert s.loc['Teste do sinal (mediana)', 'p_valor'] < 1e-4


def test_condicoes(A, P):
    for h in I.HIPOTESES:
        cond = I.condicoes(h, A, len(P))
        assert all(c['ok'] for c in cond if c['ok'] is not None)            # as condições de verdade
        informativas = [c for c in cond if c['ok'] is None]                  # forma: só informativo
        assert len(informativas) == (1 if h.tipo == 'media' else 0)


def test_conclusao_gerada_dos_numeros(linhas):
    t = I.conclusao(linhas['M2'])
    assert 'Não se rejeita H₀' in t and '0,1717' in t and 'o contém' in t
    assert 'Limite inferior unilateral' in I.conclusao(linhas['M2-b'])


# ---------------------------------------------------------------- simulação (2.000 AAS, semente 1)
def test_simulacao_reproduz_os_valores_oficiais(sim):
    # contagens exatas em 2.000 réplicas (o Painel 3 mostra as mesmas taxas em %)
    rejeicoes = {c: round(v * 2000) for c, v in sim['rejeicao'].items()}
    assert rejeicoes == {'P1': 2000, 'P2': 107, 'M1': 295, 'M2': 1573, 'P1-b': 1789, 'M2-b': 1723}
    coberturas = {c: round(v * 2000) for c, v in sim['cobertura'].items()}
    assert coberturas == {'P1': 1887, 'P2': 1904, 'M1': 1908, 'M2': 1923, 'P1-b': 1887, 'M2-b': 1923}
    assert all(0.93 <= c <= 0.97 for c in sim['cobertura'].values())


def test_decisao_x_verdade(linhas, sim):
    d = I.decisao_x_verdade(list(linhas.values()), sim).set_index('codigo')
    assert (d['h0_populacao'] == 'falsa').all()                    # nenhum parâmetro satisfaz H0 na população
    assert d['resultado'].to_dict() == {'P1': 'acerto', 'P2': 'erro tipo II', 'M1': 'erro tipo II',
                                        'M2': 'erro tipo II', 'P1-b': 'acerto', 'M2-b': 'erro tipo II'}
    assert d['poder_igual_alfa'].to_dict() == {'P1': False, 'P2': True, 'M1': False, 'M2': False,
                                               'P1-b': False, 'M2-b': False}
    assert d.loc['P2', 'distancia'] == '0,14 p.p.' and d.loc['M2', 'distancia'] == '0,090 p.p.'


def test_h0_na_populacao():
    assert I.h0_na_populacao(0.5, 0.5, 'two-sided') == 'verdadeira'
    assert I.h0_na_populacao(0.4986, 0.5, 'two-sided') == 'falsa'
    assert I.h0_na_populacao(0.60, 2 / 3, 'greater') == 'verdadeira'      # H0: p ≤ 2/3
    assert I.h0_na_populacao(0.6946, 2 / 3, 'greater') == 'falsa'


# ---------------------------------------------------------------- Painel 3
def test_limite_poder_igual_alfa():
    assert I.limite_poder_igual_alfa(2000) == pytest.approx(0.05 + 1.959964 * np.sqrt(0.05 * 0.95 / 2000), abs=1e-6)
    assert round(I.limite_poder_igual_alfa(2000) * 100, 2) == 5.96


def test_amostra_exercicio_e_outra_aas(P, A):
    X = I.amostra_exercicio(P, len(A), 10_001)
    assert len(X) == len(A) and X['id'].is_unique
    assert set(X['id']) != set(A['id'])
    assert I.amostra_exercicio(P, len(A), 10_001)['id'].tolist() == X['id'].tolist()   # reproduzível


def test_licao():
    assert I.licao('erro tipo II', 'falsa', 0.7865).startswith('Erro tipo II') and '21,35%' in I.licao(
        'erro tipo II', 'falsa', 0.7865)
    assert 'efeito existe' in I.licao('acerto', 'falsa', 1.0)
    p2 = I.licao('erro tipo II', 'falsa', 0.0535, '0,14 p.p.', True)
    assert p2.startswith('Erro tipo II, mas inevitável') and '0,14 p.p.' in p2 and 'não se distingue de' in p2
    assert 'erro tipo I' in I.licao('acerto', 'verdadeira', 0.05)


def test_tabela_comparacao(linhas, sim):
    t = I.tabela_comparacao(list(linhas.values()), sim).set_index('hipótese')
    assert list(t.index) == ['P1', 'P2', 'M1', 'M2', 'P1-b (compl.)', 'M2-b (compl.)']
    assert (t['IC contém a população'] == 'sim').all()
    assert t.loc['M2', 'resultado'] == 'erro tipo II' and t.loc['P2', 'H₀ na população'] == 'falsa'
    assert t.loc['P2', 'resultado'] == 'erro tipo II (poder ≈ α)'
    assert t.loc['P1', 'população'] == '69,46%' and t.loc['M2', 'amostra'] == '0,047%'
