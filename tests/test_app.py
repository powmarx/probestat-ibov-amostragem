"""O app abre sem erro em todas as páginas e com todas as opções do Painel 1."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import descritiva as D

TEMPO = 120
APP = Path(__file__).resolve().parents[1] / 'app.py'


@pytest.fixture
def app():
    at = AppTest.from_file(str(APP), default_timeout=TEMPO)
    at.run()
    assert not at.exception, at.exception
    return at


def test_painel1_abre(app):
    assert app.title[0].value.startswith('Painel 1')
    textos = ' '.join(m.value for m in app.markdown)
    assert '96.610' in textos and '40 ações' in textos
    assert 'Spearman 0,31' in textos and '14 ações' in textos and 'humor de ontem' in textos   # extras
    assert [m.value for m in app.metric][:2] == ['96.610', '40']


def test_painel1_todas_as_variaveis(app):
    for c in D.QUANTITATIVAS:
        app.selectbox(key='p1_quant').set_value(c).run()
        assert not app.exception, (c, app.exception)
    for c in D.QUALITATIVAS:
        app.selectbox(key='p1_quali').set_value(c).run()
        assert not app.exception, (c, app.exception)


def test_painel1_pontos_alem_dos_bigodes(app):
    app.toggle(key='p1_pontos').set_value(True).run()
    for c in D.QUANTITATIVAS:
        app.selectbox(key='p1_quant').set_value(c).run()
        assert not app.exception, (c, app.exception)
    assert any('Pontos: os valores além dos bigodes' in x.value for x in app.caption)


def test_painel1_filtros(app):
    app.multiselect(key='p1_setor').set_value(['Financeiro']).run()
    assert not app.exception
    app.slider(key='p1_ano').set_value((2020, 2020)).run()
    assert not app.exception
    assert any('Filtros ativos' in i.value for i in app.info)


@pytest.mark.parametrize('pagina', ['paginas/p2_amostra.py', 'paginas/p3_inferencia.py'])
def test_outras_paginas_abrem(app, pagina):
    app.switch_page(pagina).run()
    assert not app.exception


@pytest.fixture
def p3(app):
    app.switch_page('paginas/p3_inferencia.py').run()
    assert not app.exception, app.exception
    return app


def test_painel3_abre(p3):
    assert p3.title[0].value.startswith('Painel 3')
    assert len(p3.tabs) == 6
    textos = ' '.join(m.value for m in p3.markdown)
    assert 'Rejeita-se H₀ (z = 18,41' in textos            # P1
    assert 'Não se rejeita H₀ (t = 1,37' in textos         # M2
    assert 'Erro tipo II' in textos and 'nenhuma decisão muda' in textos
    assert 'circuit breaker' in textos


def test_painel3_simulacao_e_sorteio(p3):
    for c in ['P1', 'P2', 'M1', 'M2', 'P1-b', 'M2-b']:
        p3.selectbox(key='p3_sim').set_value(c).run()
        assert not p3.exception, (c, p3.exception)
    p3.button(key='p3_sortear').click().run()
    assert not p3.exception
    assert any('semente 10001' in str(df.value.columns.tolist()) for df in p3.dataframe)


@pytest.fixture
def p2(app):
    app.switch_page('paginas/p2_amostra.py').run()
    assert not app.exception, app.exception
    return app


def test_painel2_abre(p2):
    assert p2.title[0].value.startswith('Painel 2')
    assert [m.value for m in p2.metric][:2] == ['2.343', '2,43%']
    assert any('n = 2.343' in m.value for m in p2.markdown)


def test_painel2_todas_as_variaveis_e_filtros(p2):
    for c in D.QUANTITATIVAS:
        p2.selectbox(key='p2_quant').set_value(c).run()
        assert not p2.exception, (c, p2.exception)
    for c in D.QUALITATIVAS:
        p2.selectbox(key='p2_quali').set_value(c).run()
        assert not p2.exception, (c, p2.exception)
    p2.toggle(key='p2_pontos').set_value(True).run()
    p2.multiselect(key='p2_setor').set_value(['Saúde']).run()
    assert not p2.exception
    p2.slider(key='p2_ano').set_value((2020, 2020)).run()
    assert not p2.exception
