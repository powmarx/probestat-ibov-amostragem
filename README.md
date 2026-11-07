# Amostragem e inferência em 10 anos de pregões da B3

Trabalho final de **Probabilidade e Estatística para IA** (pós-graduação, UFRGS).
Autor: **Paulo Luis Silva Marques**.

Amostragem, intervalos de confiança e testes de hipóteses numa base grande de cotações diárias,
comparando a população com uma amostra aleatória simples em três painéis interativos.

| Entrega | Link |
|---|---|
| Painéis (Streamlit) | https://probestat-ibov-amostragem.streamlit.app/ (um app com as três páginas no menu lateral) |
| Painel 1 — População | https://probestat-ibov-amostragem.streamlit.app/ (página inicial) |
| Painel 2 — Amostra | https://probestat-ibov-amostragem.streamlit.app/p2_amostra |
| Painel 3 — Inferência e comparação | https://probestat-ibov-amostragem.streamlit.app/p3_inferencia |
| Vídeo (YouTube, não listado) | _a preencher_ |
| Base de dados (CSV da população) | [`dados/populacao.zip`](dados/populacao.zip) · fonte: [Yahoo Finance](https://finance.yahoo.com/quote/VALE3.SA/history) |

O app hiberna depois de alguns dias sem acesso. Se aparecer a tela de "app dormindo", clique para
acordá-lo; o primeiro acesso pode levar cerca de 30 segundos.

## Painéis

1. **População.** A base completa: fonte, construção, dicionário de variáveis, medidas resumo,
   histogramas, boxplots, frequências e os gráficos extras de volume, concentração e humor do mercado.
2. **Amostra.** Cálculo do tamanho da amostra (com calculadora), o sorteio, a comparação
   amostra × população em erros-padrão e os QQ-plots.
3. **Inferência e comparação.** Seis hipóteses (quatro principais e duas complementares), cada uma com
   IC, estatística de teste, valor-p e o valor da população ao lado; o quadro decisão × verdade, uma
   simulação de 2.000 amostras e as limitações.

## Fontes

- **Preços:** [Yahoo Finance](https://finance.yahoo.com/), cotações diárias (abertura, máxima, mínima,
  fechamento e volume) das 40 ações listadas abaixo e do Ibovespa, obtidas pela API pública de gráficos
  `https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}.SA?interval=1d&range=10y`. Cada ação tem
  sua página de histórico (links na tabela).
- **Setor:** [B3, Classificação setorial](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/acoes/consultas/classificacao-setorial/),
  consultada em 31/10/2026 pela API de empresas listadas que essa página usa. A resposta está em
  `dados/b3_classificacao_setorial.json`.
- **Conferência:** TradingView (bolsa `BMFBOVESPA`), lido pela biblioteca não oficial `tvdatafeed`,
  usado só para conferir a base do Yahoo (seção "Conferência com o TradingView").

Os dados são usados para fins acadêmicos e não comerciais, com as fontes citadas. Os termos de uso do
Yahoo Finance e do TradingView restringem a redistribuição; quem precisar dos dados para outro fim deve
obtê-los nas fontes.

<details>
<summary>As 40 ações, com setor e número de pregões na população</summary>

| Ação | Setor (B3) | Pregões |
|---|---|---|
| [ABEV3](https://finance.yahoo.com/quote/ABEV3.SA/history) | Consumo não Cíclico | 2.482 |
| [ALOS3](https://finance.yahoo.com/quote/ALOS3.SA/history) | Financeiro | 2.480 |
| [ALPA4](https://finance.yahoo.com/quote/ALPA4.SA/history) | Consumo Cíclico | 2.482 |
| [AXIA3](https://finance.yahoo.com/quote/AXIA3.SA/history) | Utilidade Pública | 2.481 |
| [B3SA3](https://finance.yahoo.com/quote/B3SA3.SA/history) | Financeiro | 2.481 |
| [BBAS3](https://finance.yahoo.com/quote/BBAS3.SA/history) | Financeiro | 2.479 |
| [BBDC4](https://finance.yahoo.com/quote/BBDC4.SA/history) | Financeiro | 2.480 |
| [BRAP4](https://finance.yahoo.com/quote/BRAP4.SA/history) | Materiais Básicos | 2.482 |
| [CMIN3](https://finance.yahoo.com/quote/CMIN3.SA/history) | Materiais Básicos | 1.421 |
| [COGN3](https://finance.yahoo.com/quote/COGN3.SA/history) | Consumo Cíclico | 2.482 |
| [CSAN3](https://finance.yahoo.com/quote/CSAN3.SA/history) | Petróleo, Gás e Biocombustíveis | 2.482 |
| [CSNA3](https://finance.yahoo.com/quote/CSNA3.SA/history) | Materiais Básicos | 2.482 |
| [CVCB3](https://finance.yahoo.com/quote/CVCB3.SA/history) | Consumo Cíclico | 2.480 |
| [CYRE3](https://finance.yahoo.com/quote/CYRE3.SA/history) | Consumo Cíclico | 2.481 |
| [EMBJ3](https://finance.yahoo.com/quote/EMBJ3.SA/history) | Bens Industriais | 2.481 |
| [ENEV3](https://finance.yahoo.com/quote/ENEV3.SA/history) | Utilidade Pública | 2.482 |
| [EQTL3](https://finance.yahoo.com/quote/EQTL3.SA/history) | Utilidade Pública | 2.482 |
| [GGBR4](https://finance.yahoo.com/quote/GGBR4.SA/history) | Materiais Básicos | 2.482 |
| [HAPV3](https://finance.yahoo.com/quote/HAPV3.SA/history) | Saúde | 2.115 |
| [IRBR3](https://finance.yahoo.com/quote/IRBR3.SA/history) | Financeiro | 2.295 |
| [ITUB4](https://finance.yahoo.com/quote/ITUB4.SA/history) | Financeiro | 2.481 |
| [KLBN11](https://finance.yahoo.com/quote/KLBN11.SA/history) | Materiais Básicos | 2.481 |
| [LREN3](https://finance.yahoo.com/quote/LREN3.SA/history) | Consumo Cíclico | 2.481 |
| [MGLU3](https://finance.yahoo.com/quote/MGLU3.SA/history) | Consumo Cíclico | 2.480 |
| [MRVE3](https://finance.yahoo.com/quote/MRVE3.SA/history) | Consumo Cíclico | 2.482 |
| [PCAR3](https://finance.yahoo.com/quote/PCAR3.SA/history) | Consumo não Cíclico | 1.710 |
| [PETR4](https://finance.yahoo.com/quote/PETR4.SA/history) | Petróleo, Gás e Biocombustíveis | 2.482 |
| [PRIO3](https://finance.yahoo.com/quote/PRIO3.SA/history) | Petróleo, Gás e Biocombustíveis | 2.481 |
| [RADL3](https://finance.yahoo.com/quote/RADL3.SA/history) | Saúde | 2.482 |
| [RENT3](https://finance.yahoo.com/quote/RENT3.SA/history) | Consumo Cíclico | 2.482 |
| [SBSP3](https://finance.yahoo.com/quote/SBSP3.SA/history) | Utilidade Pública | 2.482 |
| [SLCE3](https://finance.yahoo.com/quote/SLCE3.SA/history) | Consumo não Cíclico | 2.482 |
| [SMTO3](https://finance.yahoo.com/quote/SMTO3.SA/history) | Consumo não Cíclico | 2.482 |
| [SUZB3](https://finance.yahoo.com/quote/SUZB3.SA/history) | Materiais Básicos | 2.226 |
| [TOTS3](https://finance.yahoo.com/quote/TOTS3.SA/history) | Tecnologia da Informação | 2.482 |
| [UGPA3](https://finance.yahoo.com/quote/UGPA3.SA/history) | Petróleo, Gás e Biocombustíveis | 2.482 |
| [USIM5](https://finance.yahoo.com/quote/USIM5.SA/history) | Materiais Básicos | 2.481 |
| [VALE3](https://finance.yahoo.com/quote/VALE3.SA/history) | Materiais Básicos | 2.481 |
| [WEGE3](https://finance.yahoo.com/quote/WEGE3.SA/history) | Bens Industriais | 2.481 |
| [YDUQ3](https://finance.yahoo.com/quote/YDUQ3.SA/history) | Consumo Cíclico | 2.477 |

</details>

## População e unidade amostral

- **Unidade:** uma ação em um pregão (par ação-dia).
- **População:** **96.610** pares ação-dia das 40 ações, de **31/10/2016 a 30/10/2026** (10 anos,
  2.482 pregões), só dias com negócio (volume > 0). 27 colunas.
- **Base congelada** em 31/10/2026 em `dados/bruto/1d/` (41 arquivos: 40 ações e o Ibovespa), para
  não mudar com novas coletas. A população é sempre montada a partir dessa cópia.

Regras de construção (`preparar_dados.py`):

1. Excluir dias com volume zero. O fechamento anterior é o do último pregão com negócio da mesma ação.
2. Excluir o primeiro dia de cada ação, que não tem fechamento anterior (afeta as 5 ações que começam
   dentro da janela: CMIN3, HAPV3, IRBR3, PCAR3, SUZB3).
3. Manter só os pregões de 31/10/2016 a 30/10/2026.
4. Medir o retorno do Ibovespa (`ret_ibov`) no mesmo intervalo do retorno da ação.
5. Conferir cada linha com o TradingView e corrigir as 19 com diferença acima de 5 p.p. (abaixo).
6. Ordenar por ativo (ordem alfabética) e data, e numerar `id` de 0 a N−1. O sorteio depende dessa
   ordem.

Faltam dois pregões, porque faltam no Yahoo: 29/05/2017 (sem negócio na fonte) e 20/11/2020.
Desdobramentos, grupamentos e bonificações já vêm ajustados pela fonte. Dividendos e JCP não estão
incluídos (ver Limitações).

## Dicionário de variáveis

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | identificador | número da linha, de 0 a N−1, na ordem ação + data (é o que a AAS sorteia) |
| `data` | data | pregão |
| `ativo` | qualitativa | código da ação na B3 |
| `setor` | qualitativa | setor econômico da classificação oficial da B3 (9 categorias) |
| `abertura`, `maxima`, `minima`, `fechamento` | quantitativa | preços do dia em R$, ajustados por desdobramentos |
| `volume` | quantitativa | quantidade de ações negociadas |
| `data_anterior` | data | último pregão anterior com negócio da mesma ação |
| `fechamento_anterior` | quantitativa | fechamento em `data_anterior` |
| `ret` | quantitativa | retorno do dia: fechamento / fechamento_anterior − 1, em % |
| `gap` | quantitativa | gap de abertura: abertura / fechamento_anterior − 1, em % |
| `intra` | quantitativa | abertura → fechamento: fechamento / abertura − 1, em % |
| `amp` | quantitativa | amplitude: (máxima − mínima) / fechamento_anterior, em % |
| `fin` | quantitativa | volume financeiro, em R$ milhões |
| `ret_ibov` | quantitativa | retorno do Ibovespa no mesmo intervalo de `ret`, em % |
| `vol_rel` | quantitativa | volume financeiro ÷ mediana dos 20 pregões **anteriores** com negócio da ação |
| `fg_ant` | quantitativa | Fear & Greed B3 (0 a 100) do **pregão anterior** |
| `ano`, `dia_semana` | qualitativa | calendário |
| `direcao` | qualitativa | alta (ret > 0), baixa (ret < 0) ou sem variação (ret = 0) |
| `segue_ibov` | qualitativa | a ação foi na mesma direção do Ibovespa (sim, não, sem variação) |
| `faixa` | qualitativa | pelo \|ret\|: calmo (≤ 1%), normal (1–2%), agitado (2–5%), extremo (> 5%) |
| `faixa_volume` | qualitativa | pelo `vol_rel`: baixo (< 0,75), normal (0,75 a 1,5), alto (≥ 1,5) |
| `humor_ant` | qualitativa | faixa do `fg_ant`: medo extremo (0–25), medo (25–45), neutro (45–55), ganância (55–75), ganância extrema (75–100) |
| `conferencia_tv` | qualitativa | resultado da conferência com o TradingView (5 categorias, abaixo) |

"Dia agitado" no texto dos painéis significa \|ret\| > 2% (faixas agitado e extremo juntas).

**Categoria "sem referência".** Quando não há histórico anterior suficiente, a coluna numérica fica
vazia e a faixa correspondente recebe a categoria "sem referência", em vez de ficar vazia, para aparecer
nas tabelas de frequência e não sumir da contagem:

| Faixa | Linhas na população | Na amostra | Motivo |
|---|---|---|---|
| `faixa_volume` | 95 (0,1%) | 5 | os 20 primeiros pregões das 5 ações que entram depois de 31/10/2016 não têm 20 pregões anteriores |
| `humor_ant` | 17.403 (18,0%) | 421 | o Fear & Greed só existe a partir de 08/10/2018 (dois anos de histórico para os percentis) |

Nos gráficos por faixa, as médias e proporções são calculadas sem essa categoria, e a nota do painel diz
isso.

**Fear & Greed B3.** Média de cinco componentes, cada um em percentil contra a própria história
anterior: momento do Ibovespa, amplitude (ações acima da média de 50 pregões), força (perto da máxima
menos perto da mínima de 252 pregões), volume direcional e volatilidade invertida. O método vem de um
trabalho anterior do autor no curso (Visualização de Dados) e está copiado em `humor.py`. Entra com um
pregão de defasagem porque o índice do dia usa os preços do próprio dia. `vol_rel`, `faixa_volume`,
`fg_ant` e `humor_ant` são só descritivas e não entram nos testes.

## Conferência com o TradingView

Todas as 96.610 linhas foram comparadas com as cotações do TradingView, baixadas em 03/11/2026 e
congeladas em `dados/bruto/tv_1d/`. A comparação é feita no retorno do dia, que não depende do nível de
preço ajustado de cada fonte. As regras valem na ordem da tabela:

| Categoria | Regra | Linhas |
|---|---|---|
| sem dado no TradingView | o TradingView não tem negócio no dia | 2 |
| intervalo diferente | o pregão anterior não é o mesmo nas duas fontes | 101 |
| idêntico | diferença no retorno ≤ 0,01 p.p. | 94.794 (98,1%) |
| diferença até 5 p.p. | fica como no Yahoo | 1.694 |
| corrigido pelo TradingView | diferença > 5 p.p.: a linha recebe os preços do TradingView | 19 |

Nenhuma das 19 linhas corrigidas está na amostra. Os extremos reais (circuit breaker de 26/10/2026,
março de 2020) foram mantidos e são confirmados pelas duas fontes. A justificativa do limite, a lista das
linhas corrigidas e a sensibilidade a outros limites estão em
[`docs/conferencia_tradingview.md`](docs/conferencia_tradingview.md); a comparação linha a linha está em
`dados/conferencia_tradingview.parquet`.

## Tamanho da amostra e sorteio

Tamanho para estimar uma proporção com 95% de confiança e margem de 2 p.p., no pior caso p = 0,5, com
correção para população finita (Cochran, 1977):

- n₀ = z² · p · (1 − p) / e² = 1,96² × 0,5 × 0,5 / 0,02² = **2.401**
- n = n₀ / (1 + (n₀ − 1) / N) = 2.401 / (1 + 2.400 / 96.610) = 2.342,8 → **n = 2.343**

O script usa z = 1,959964 (n₀ = 2.400,9; n = 2.342,7) e chega ao mesmo 2.343. A margem de 2 p.p. separa
50% de 52%, a escala das hipóteses de proporção. Para as médias o n não é recalculado: o painel mostra a
margem que ele produz (±0,115 p.p. no retorno, ±0,068 p.p. no gap).

**Sorteio:** amostra aleatória simples sem reposição, semente **2026**, fixada antes de ver os
resultados:

```python
numpy.random.default_rng(2026).choice(96610, 2343, replace=False)   # numpy 2.5.3, sobre os ids
```

Cada linha tem a mesma probabilidade de entrar (n/N = 2,43%). A amostra está em `dados/amostra.csv`
(com a ordem do sorteio) e `dados/amostra.parquet`; `dados/manifesto.json` guarda os parâmetros, o
código do sorteio, a versão do numpy e o SHA-256 dos CSVs. O app só lê a amostra gravada e nunca sorteia
de novo.

## Hipóteses e resultados (α = 5%)

Proporções: teste z com p₀ no erro-padrão e IC de Wald 95% (conferências: binomial exato e IC de
Wilson). Médias: teste t de uma amostra e IC t 95% (conferência: teste do sinal). P1 e P2 são estimadas
entre os dias com ret ≠ 0 (2.311 linhas da amostra).

| | Pergunta | H₀ / H₁ | População | Amostra | IC 95% | Estatística | Valor-p | Decisão |
|---|---|---|---|---|---|---|---|---|
| P1 | A ação vai na mesma direção do Ibovespa? | p = 0,5 / p > 0,5 | 69,46% | 69,15% | [67,26%; 71,03%] | z = 18,41 | < 0,0001 | rejeita H₀ |
| P2 | Um dia de alta é "cara ou coroa"? | p = 0,5 / p ≠ 0,5 | 49,86% | 47,99% | [45,95%; 50,02%] | z = −1,93 | 0,0530 | não rejeita |
| M1 | O retorno médio diário é zero? | μ = 0 / μ ≠ 0 | 0,053% | −0,057% | [−0,173%; 0,058%] | t = −0,97 | 0,3311 | não rejeita |
| M2 | O gap médio de abertura é zero? | μ = 0 / μ ≠ 0 | 0,090% | 0,047% | [−0,020%; 0,115%] | t = 1,37 | 0,1717 | não rejeita |
| P1-b (compl.) | Segue o índice em mais de 2/3 dos dias? | p ≤ 2/3 / p > 2/3 | 69,46% | 69,15% | [67,26%; 71,03%] | z = 2,53 | 0,0057 | rejeita H₀ |
| M2-b (compl.) | O gap médio é positivo? | μ ≤ 0 / μ > 0 | 0,090% | 0,047% | limite inferior −0,010% | t = 1,37 | 0,0859 | não rejeita |

- Todos os intervalos contêm o valor da população.
- P1-b e M2-b foram formuladas depois da exploração dos dados e aparecem como complementares. A M2-b é
  unilateral porque a literatura (Cliff, Cooper e Gulen, 2008) prevê ganho positivo entre um pregão e
  o seguinte.
- Com a correção de Bonferroni para seis testes (α = 0,83%), nenhuma decisão muda.
- Uma simulação de 2.000 amostras de n = 2.343 (semente 1) mede o poder de cada teste e a cobertura dos
  intervalos. M1 e M2 não rejeitam embora H₀ seja falsa na população: são erros tipo II, com poder de
  ~15% na M1 e ~79% na M2. Na M2, três linhas do circuit breaker de 26/10/2026 (gaps de −40,3%, −20,6% e
  −14,3%) puxam a média da amostra para baixo; o Painel 3 mostra essa sensibilidade sem trocar o
  resultado oficial.

## Estrutura do repositório

```
app.py                     navegação das três páginas
paginas/                   p1_populacao.py, p2_amostra.py, p3_inferencia.py
comum.py                   leitura dos dados (com cache), cores, gráficos e filtros
descritiva.py              medidas, frequências, dicionário e textos descritivos
inferencia.py              testes, ICs, simulação, quadro decisão × verdade e conclusões
formato.py                 números no padrão brasileiro
preparar_dados.py          congela o bruto (uma vez) e monta a população
amostra.py                 tamanho da amostra, sorteio e manifesto
conferir_tradingview.py    download (uma vez) e comparação com o TradingView
humor.py                   Fear & Greed B3 diário
dados/bruto/1d/            cotações do Yahoo congeladas (41 arquivos) + manifesto
dados/bruto/tv_1d/         cotações do TradingView congeladas (40 arquivos) + manifesto
dados/populacao.parquet    população (lida pelo app)
dados/populacao.zip        população em CSV, compactada
dados/amostra.parquet/.csv amostra sorteada
dados/manifesto.json       parâmetros, código do sorteio, SHA-256
dados/setores.csv          setor, subsetor e segmento das 40 ações (B3)
docs/conferencia_tradingview.md  conferência com a segunda fonte e as 19 correções
tests/                     testes automáticos (pytest)
```

## Como reproduzir

Requer Python 3.12 (a versão usada no Streamlit Community Cloud). Num ambiente virtual novo:

```
pip install -r requirements.txt
python preparar_dados.py     # monta a população a partir do bruto congelado; grava parquet, csv e zip
python amostra.py            # refaz o sorteio e o manifesto
streamlit run app.py         # abre os painéis
python -m pytest             # 75 testes
```

- `preparar_dados.py` e `amostra.py` regravam os arquivos de `dados/`. Com numpy 2.5.3, eles saem
  idênticos aos publicados (mesmo SHA-256 do manifesto). Se uma versão futura do numpy sortear outra
  amostra, a oficial continua sendo a gravada em `dados/amostra.csv`.
- Para só conferir os arquivos, basta `python -m pytest`: os testes comparam a população montada do
  bruto com a gravada, o hash do CSV dentro do zip com o manifesto e o sorteio com os ids gravados.
- `python preparar_dados.py --congelar` (cópia da pasta do coletor de dados do autor, fora deste
  repositório) e `python conferir_tradingview.py --baixar` (exige a biblioteca `tvdatafeed`, fora do
  `requirements.txt`) criaram as cópias congeladas e se recusam a sobrescrevê-las. Não são necessários
  para reproduzir: as cópias estão em `dados/bruto/`.

## Limitações

- **População restrita.** São 40 ações escolhidas pela liquidez atual, de 31/10/2016 a 30/10/2026. As
  conclusões valem para esta população, não para a bolsa inteira nem para outros períodos (viés de
  sobrevivência).
- **Dependência entre linhas.** Ações do mesmo dia andam juntas. A inferência continua válida porque
  vem do sorteio (AAS de população finita, n/N = 2,4%), e a simulação confirma a cobertura de ~95%.
- **Dividendos.** Os retornos não incluem dividendos e JCP, que fazem o preço cair na data-ex (~1% das
  linhas). Pela estimativa feita na exploração, isso subestima o retorno e o gap médios em cerca de
  0,01 p.p., pouco perto das margens dos intervalos (±0,12 e ±0,07 p.p.).
- **Qualidade da fonte.** A base do Yahoo foi conferida com o TradingView (98,1% das linhas idênticas);
  1.694 linhas com diferenças de até 5 p.p. ficaram como no Yahoo.
- **Valores extremos.** O resultado da M2 depende de três linhas do circuit breaker de 26/10/2026.
- **Muitos testes.** Seis testes aumentam a chance de uma rejeição falsa; com Bonferroni nenhuma
  decisão muda.
- **Setor.** É a classificação atual da B3, aplicada aos 10 anos.

## Referências

- Bolfarine, H.; Bussab, W. O. *Elementos de Amostragem*. São Paulo: Blucher, 2005.
- Cochran, W. G. *Sampling Techniques*. 3. ed. New York: Wiley, 1977.
- Cliff, M.; Cooper, M. J.; Gulen, H. Return differences between trading and non-trading hours: like
  night and day. SSRN Working Paper, 2008.
