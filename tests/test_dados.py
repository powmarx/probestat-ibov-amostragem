"""Testes da base: população, amostra, setores e variáveis descritivas.

Rodar na raiz do trabalho:  D:\\venvs\\probestat312\\Scripts\\python.exe -m pytest
"""
import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import amostra as AM
import humor
import preparar_dados as PD

DADOS = PD.SAIDA
ANTIGO = Path(r'E:\OneDrive\PosIA\Visualizacao\trabalho_final\sentimento.py')


@pytest.fixture(scope='module')
def P():
    return pd.read_parquet(DADOS / 'populacao.parquet')


@pytest.fixture(scope='module')
def A():
    return pd.read_parquet(DADOS / 'amostra.parquet')


@pytest.fixture(scope='module')
def bruto():
    return PD.ler_bruto()


@pytest.fixture(scope='module')
def manifesto():
    return json.loads((DADOS / 'manifesto.json').read_text(encoding='utf-8'))


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------- população
def test_populacao_tamanho_e_ids(P):
    assert len(P) == 96_610
    assert list(P.columns) == PD.COLUNAS_POPULACAO and len(P.columns) == 27
    assert (P['id'].values == np.arange(len(P))).all()
    assert P['ativo'].nunique() == 40 and P['data'].nunique() == 2482
    assert P['data'].min() == PD.DATA_INICIO and P['data'].max() == PD.DATA_FIM


def test_populacao_ordem_ativo_data(P):
    ordenada = P.sort_values(['ativo', 'data'], kind='mergesort')
    assert (ordenada['id'].values == P['id'].values).all()
    assert not P.duplicated(['ativo', 'data']).any()


def test_populacao_sem_volume_zero_nem_nulos(P):
    assert (P['volume'] > 0).all()
    essenciais = ['abertura', 'maxima', 'minima', 'fechamento', 'fechamento_anterior',
                  'ret', 'gap', 'intra', 'amp', 'fin', 'ret_ibov', 'setor']
    assert P[essenciais].notna().all().all()
    assert (P['maxima'] >= P['minima']).all()


def test_populacao_reproduz_do_bruto(P, bruto):
    assert PD.populacao(bruto).equals(P)


def test_ret_ibov_no_mesmo_intervalo_da_acao(P, bruto):
    ib = bruto['IBOV']['close']
    esperado = (ib.reindex(P['data']).values / ib.reindex(P['data_anterior']).values - 1) * 100
    assert np.allclose(P['ret_ibov'].values, esperado)


# ---------------------------------------------------------------- conferência com o TradingView
@pytest.fixture(scope='module')
def conferencia():
    return pd.read_parquet(PD.CONFERENCIA)


def test_conferencia_categorias(P, A):
    import conferir_tradingview as CT
    assert P['conferencia_tv'].value_counts().to_dict() == {
        CT.IDENTICO: 94_794, CT.PEQUENA: 1_694, CT.INTERVALO: 101, CT.CORRIGIDO: 19, CT.SEM_DADO: 2}
    assert A['conferencia_tv'].value_counts().to_dict() == {CT.IDENTICO: 2_311, CT.PEQUENA: 29, CT.INTERVALO: 3}


def test_conferencia_regras(P, conferencia):
    import conferir_tradingview as CT
    c = conferencia.set_index('id').loc[P['id']]
    cat = c['conferencia_tv'].values
    mesmo = (c['data_anterior'] == c['data_anterior_tv']).values
    d = c['diferenca'].values
    assert (cat[c['ret_tv'].isna().values] == CT.SEM_DADO).all()
    ok = ~c['ret_tv'].isna().values
    assert (cat[ok & ~mesmo] == CT.INTERVALO).all()
    assert (d[cat == CT.IDENTICO] <= 0.01).all()
    assert ((d[cat == CT.PEQUENA] > 0.01) & (d[cat == CT.PEQUENA] <= 5)).all()
    assert (d[cat == CT.CORRIGIDO] > 5).all() and mesmo[cat == CT.CORRIGIDO].all()


def test_correcao_usa_o_retorno_do_tradingview(P, conferencia):
    import conferir_tradingview as CT
    k = P['conferencia_tv'] == CT.CORRIGIDO
    c = conferencia.set_index('id').loc[P.loc[k, 'id']]
    assert np.allclose(P.loc[k, 'ret'].values, c['ret_tv'].values)
    assert np.allclose(P.loc[k, 'gap'].values, c['gap_tv'].values)
    # nas outras linhas o retorno continua o do Yahoo
    resto = conferencia.set_index('id').loc[P.loc[~k, 'id']]
    assert np.allclose(P.loc[~k, 'ret'].values, resto['ret_yahoo'].values)


def test_correcao_nao_toca_a_amostra(A):
    import conferir_tradingview as CT
    assert not (A['conferencia_tv'] == CT.CORRIGIDO).any()


def test_casos_conhecidos(P):
    def linha(a, d):
        return P[(P['ativo'] == a) & (P['data'] == d)].iloc[0]
    assert linha('PCAR3', '2023-08-23')['ret'] == pytest.approx(16.11, abs=0.01)     # cisão do Éxito
    assert linha('UGPA3', '2021-06-28')['ret'] == pytest.approx(1.05, abs=0.01)
    assert linha('BRAP4', '2019-01-28')['ret'] == pytest.approx(-24.49, abs=0.01)    # Brumadinho
    assert linha('PCAR3', '2017-02-01')['conferencia_tv'] == 'idêntico'              # +139% é real
    assert (P[P['data'] == '2026-10-26']['conferencia_tv'] == 'idêntico').all()     # circuit breaker


# ---------------------------------------------------------------- amostra
def test_tamanho_da_amostra():
    t = AM.tamanho(96_610)
    assert round(t['n0'], 1) == 2400.9 and t['n'] == 2343
    assert AM.tamanho(96_610, confianca=99)['n'] > t['n']          # mais confiança, maior n
    assert round(t['n_finita_exato'], 2) == 2342.72          # n0 / (1 + (n0 − 1)/N)


def test_amostra_sem_repeticao_e_igual_a_populacao(P, A):
    assert len(A) == 2343 and A['id'].is_unique
    sub = P.set_index('id').loc[A['id']].reset_index()
    pd.testing.assert_frame_equal(sub[PD.COLUNAS_POPULACAO].reset_index(drop=True),
                                  A[PD.COLUNAS_POPULACAO].reset_index(drop=True))


def test_sorteio_reproduz_os_ids_gravados(A):
    if np.__version__ != '2.5.3':
        pytest.skip('o sorteio só é garantido com numpy 2.5.3; a amostra oficial é a do arquivo')
    ids = AM.sortear(96_610, 2343)
    em_ordem = A.sort_values('ordem_sorteio')['id'].values
    assert (ids == em_ordem).all()


def test_manifesto_bate_com_os_arquivos(manifesto):
    assert manifesto['populacao']['N'] == 96_610
    assert manifesto['dimensionamento']['n'] == 2343
    assert manifesto['selecao']['semente'] == 2026
    # no repositório o CSV da população só existe dentro do zip; localmente existem os dois
    with zipfile.ZipFile(PD.ZIP_POPULACAO) as z:
        assert z.namelist() == ['populacao.csv']
        dentro_do_zip = hashlib.sha256(z.read('populacao.csv')).hexdigest()
    assert manifesto['populacao']['sha256_csv'] == dentro_do_zip
    if (DADOS / 'populacao.csv').exists():
        assert manifesto['populacao']['sha256_csv'] == _sha(DADOS / 'populacao.csv')
    assert manifesto['selecao']['sha256_csv'] == _sha(DADOS / 'amostra.csv')


# ---------------------------------------------------------------- carteira do Ibovespa
def test_carteira_ibov(P):
    import descritiva as D
    c = D.carteira_ibov(P['ativo'].unique())
    assert c['data'] == '10/11/2026' and c['ativos'] == 76
    assert len(c['dentro']) == 34 and c['fora'] == ['ALPA4', 'CVCB3', 'IRBR3', 'PCAR3', 'SLCE3', 'SMTO3']
    assert c['peso'] == pytest.approx(0.692, abs=0.001)
    frase = D.frase_carteira_ibov(P['ativo'].unique())
    assert '34 das 40 ações' in frase and 'ALPA4 saiu do índice em janeiro de 2025 e CVCB3, em janeiro de 2026' in frase
    assert 'Atividade' not in frase


def test_criterio_e_representacao(P):
    import descritiva as D
    r = D.representacao(P)
    assert (r['menos_liquida'], r['mais_liquida']) == ('ALPA4', 'PETR4')
    assert round(r['liq_max'] / r['liq_min']) == 48
    assert r['corr'] == pytest.approx(0.949, abs=0.001) and r['mesma_direcao'] == pytest.approx(0.897, abs=0.001)
    assert 0.91 <= r['corr_min_ano'] and r['corr_max_ano'] <= 0.98
    t = D.frase_criterio(P)
    assert 'liquidez variada' in t and 'correlação de 0,95' in t and 'Atividade' not in t


# ---------------------------------------------------------------- setores
def test_setores_iguais_a_b3():
    S = pd.read_csv(PD.SETORES)
    b3 = json.loads(PD.JSON_B3.read_text(encoding='utf-8'))['empresas']
    assert len(S) == 40 and S['ativo'].is_unique and S['setor'].nunique() == 9
    for e in b3:
        setor_api = e['classificacao_b3'].split(' / ')[0]
        assert PD._nome_oficial(setor_api) == S.set_index('ativo').loc[e['ativo'], 'setor']
    assert 'Petróleo, Gás e Biocombustíveis' in set(S['setor'])          # vírgula restaurada
    assert not S[['setor', 'subsetor', 'segmento']].apply(lambda c: c.str.contains(r'\. ')).any().any()


# ---------------------------------------------------------------- volume relativo
def test_vol_rel_usa_so_o_passado(bruto):
    d = bruto['VALE3']
    d = d[d['volume'] > 0]
    base = PD.vol_relativo(d)
    k = 500
    d2 = d.copy()
    d2.iloc[k, d2.columns.get_loc('volume')] *= 10
    novo = PD.vol_relativo(d2)
    assert novo.iloc[k] == pytest.approx(base.iloc[k] * 10)               # o próprio dia muda só no numerador
    assert novo.iloc[:k].equals(base.iloc[:k])                            # o passado não muda
    assert not np.isclose(novo.iloc[k + 1], base.iloc[k + 1])             # o dia seguinte usa o dia k


def test_faixa_volume(P):
    v, f = P['vol_rel'], P['faixa_volume']
    assert (f[v < 0.75] == 'baixo').all()
    assert (f[(v >= 0.75) & (v < 1.5)] == 'normal').all()
    assert (f[v >= 1.5] == 'alto').all()
    assert (f[v.isna()] == humor.SEM_REFERENCIA).all() and int(v.isna().sum()) == 95


# ---------------------------------------------------------------- humor (Fear & Greed)
def test_fg_ant_e_o_indice_do_pregao_anterior(P, bruto):
    fg = humor.fear_greed_diario(bruto)['indice']
    anterior = fg.shift(1).reindex(P['data']).values
    assert np.allclose(P['fg_ant'].values, anterior, equal_nan=True)
    assert P['fg_ant'].notna().mean() == pytest.approx(0.82, abs=0.005)
    assert fg.first_valid_index() == pd.Timestamp('2018-10-08')


def test_fg_ant_nao_usa_o_proprio_dia(bruto):
    h = humor.humor_anterior(bruto)
    dia = pd.Timestamp('2022-06-15')
    alterado = {k: v.copy() for k, v in bruto.items()}
    for v in alterado.values():
        if dia in v.index:
            v.loc[dia, ['open', 'high', 'low', 'close']] *= 1.10
    h2 = humor.humor_anterior(alterado)
    assert h2.loc[dia, 'fg_ant'] == h.loc[dia, 'fg_ant']                 # o dia alterado não muda
    seguinte = h.index[h.index.get_loc(dia) + 1]
    assert h2.loc[seguinte, 'fg_ant'] != h.loc[seguinte, 'fg_ant']        # o seguinte, sim


def test_humor_igual_ao_do_trabalho_anterior(bruto):
    if not ANTIGO.exists():
        pytest.skip('pasta do trabalho anterior não disponível')
    spec = importlib.util.spec_from_file_location('sentimento_antigo', ANTIGO)
    S = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S)
    antigo = S.fear_greed_diario(bruto)
    novo = humor.fear_greed_diario(bruto)
    pd.testing.assert_frame_equal(antigo, novo)


def test_humor_ant_faixas(P):
    v, f = P['fg_ant'], P['humor_ant']
    assert (f[v < 25] == 'medo extremo').all()
    assert (f[(v >= 45) & (v < 55)] == 'neutro').all()
    assert (f[v >= 75] == 'ganância extrema').all()
    assert (f[v.isna()] == humor.SEM_REFERENCIA).all()
