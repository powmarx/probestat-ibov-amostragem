# Conferência da base com uma segunda fonte (TradingView) e correção de 19 linhas

**Aplicada em 03/11/2026.** Os números abaixo são os da base atual, e os testes automáticos
(`tests/test_dados.py`) verificam as contagens e as regras.

## 1. Por que conferir

A população foi montada com as cotações diárias do Yahoo Finance. Na revisão, 12 linhas foram marcadas
como "possível erro da fonte": retornos acima de 25% sem explicação e aberturas em torno de −50% em
26/10/2026. Os dois extremos do retorno do dia (+139,13% e −66,62%) eram linhas dessa lista. Para saber
se eram erros da fonte, todas as 96.610 linhas da população foram comparadas com uma segunda fonte.

## 2. A segunda fonte

- **TradingView**, cotações diárias da bolsa `BMFBOVESPA`, obtidas pela biblioteca `tvdatafeed`, a mesma
  que o coletor de dados do autor (disciplina IA001) já usava para os futuros WIN e IND, sem login.
- A biblioteca **não é oficial**: usa o canal interno do site do TradingView. Aqui ela serve para
  **conferir** a base do Yahoo e para corrigir as 19 linhas com diferença acima de 5 p.p. (seção 5). A base
  continua sendo a do Yahoo nas demais 96.591 linhas.
- As 40 ações foram baixadas em 03/11/2026, até 30/10/2026, e a cópia está **congelada** em
  `dados/bruto/tv_1d/` (um arquivo por ação, com `dados/bruto/manifesto_tv.json`), como foi feito com o
  Yahoo. A conferência é refeita a partir dela, sem depender do site.

## 3. Como a comparação é feita

Para cada linha da população (uma ação em um pregão), calcula-se o retorno do dia nas duas fontes, cada
uma com o seu próprio fechamento anterior e só com dias com negócio (volume > 0), a mesma regra da
população. As duas fontes ajustam o histórico de forma diferente, então o preço em reais pode não bater;
por isso a comparação é feita no **retorno**, que não depende desse nível.

Cada linha recebe uma das cinco categorias da coluna nova `conferencia_tv`. As regras são aplicadas na
ordem da tabela: a primeira que vale define a categoria.

| Ordem | Categoria | Regra | Linhas | % |
|---|---|---|---|---|
| 1 | sem dado no TradingView | o TradingView não tem negócio no dia | 2 | 0,00% |
| 2 | intervalo diferente | o pregão anterior não é o mesmo nas duas fontes | 101 | 0,10% |
| 3 | idêntico | diferença no retorno ≤ 0,01 p.p. | 94.794 | 98,12% |
| 4 | diferença até 5 p.p. | 0,01 < diferença ≤ 5 p.p. | 1.694 | 1,75% |
| 5 | corrigido pelo TradingView | diferença > 5 p.p. | **19** | 0,02% |

- **Sem dado:** ALPA4 em 20/08/2018 e PCAR3 em 30/03/2017 não existem no TradingView.
- **Intervalo diferente:** os dois retornos cobrem períodos diferentes e não são comparáveis. Quase todos
  vêm de um pregão que falta no Yahoo: 20/11/2020 (39 linhas de 23/11/2020) e 29/05/2017, que aparece no
  Yahoo sem negócio (35 linhas de 30/05/2017).
- **Diferença até 5 p.p.:** diferenças pequenas (mediana 0,31 p.p.; 90% abaixo de 0,96 p.p.),
  provavelmente de ajustes de proventos e arredondamentos diferentes entre as fontes. Ficam como no Yahoo.

## 4. Por que corrigir só acima de 5 p.p.

- Uma diferença de mais de 5 pontos percentuais **num único dia** raramente se explica por
  arredondamento ou pelo ajuste de proventos: indica um preço errado ou um evento societário que uma das
  fontes não ajustou.
- O limite deixa a correção restrita a casos claros e evita trocar dados por diferenças de método entre
  as fontes.
- A regra 2 garante que as duas fontes medem o mesmo intervalo antes de comparar.

**Sensibilidade ao limite (transparência).** O limite foi escolhido pelo tamanho da diferença, não pela
amostra, mas o efeito de outros limites fica registrado:

| Limite | Linhas corrigidas | Delas, na amostra |
|---|---|---|
| 1 p.p. | 175 | 2 (KLBN11, diferenças de ~1 p.p.) |
| 2 p.p. | 71 | 0 |
| 3 p.p. | 33 | 0 |
| **5 p.p. (adotado)** | **19** | **0** |

## 5. As 19 linhas corrigidas

| Ação | Data | Retorno Yahoo | Retorno TradingView | O que os dados mostram |
|---|---|---|---|---|
| AXIA3 | 02/01/2019 | +0,25% | +20,72% | o Yahoo põe a alta no dia seguinte: o acumulado dos dois dias é igual nas duas fontes (+27,94%) |
| AXIA3 | 03/01/2019 | +27,62% | +5,98% | idem |
| AXIA3 | 22/12/2025 | −22,53% | −2,73% | salto isolado: os dias vizinhos são idênticos nas duas fontes |
| BRAP4 | 28/01/2019 | −16,66% | −24,49% | rompimento da barragem de Brumadinho (25/01/2019). O Yahoo divide a queda em dois dias (acumulado igual, −23,94%); o TradingView bate com a VALE3 no mesmo dia (−24,5% nas duas fontes) |
| BRAP4 | 29/01/2019 | −8,74% | +0,72% | idem |
| CVCB3 | 14/06/2023 | +6,50% | −1,91% | salto isolado |
| CYRE3 | 02/01/2026 | −19,11% | −2,96% | salto isolado |
| EQTL3 | 12/08/2024 | −9,68% | −0,46% | duas oscilações em sentidos opostos (12 e 14/08) |
| EQTL3 | 14/08/2024 | +10,97% | +1,31% | idem |
| IRBR3 | 24/08/2022 | +14,27% | −5,19% | salto isolado |
| ITUB4 | 04/10/2021 | −17,96% | −1,66% | salto isolado; provável cisão da participação na XP Inc. não ajustada pelo Yahoo |
| KLBN11 | 23/03/2020 | +3,52% | −1,82% | a série da KLBN11 difere entre as fontes nesse período (ver seção 10) |
| MGLU3 | 01/02/2024 | +4,88% | −1,32% | salto isolado |
| MRVE3 | 18/01/2019 | −16,98% | +0,14% | oscilação falsa no Yahoo, desfeita no dia seguinte |
| MRVE3 | 21/01/2019 | +21,14% | −0,50% | idem |
| PCAR3 | 23/08/2023 | −66,62% | +16,11% | salto isolado; provável cisão do Éxito não ajustada pelo Yahoo |
| PCAR3 | 28/02/2024 | +5,85% | +11,93% | o Yahoo distribui o movimento de três dias de outro jeito: o acumulado é igual (−1,52%) |
| PCAR3 | 01/03/2024 | +1,81% | −3,72% | idem |
| UGPA3 | 28/06/2021 | +119,33% | +1,05% | salto isolado |

"Salto isolado": só aquele dia difere, e os dias vizinhos são iguais nas duas fontes. É o padrão de um
ajuste histórico (evento societário) mal aplicado pelo Yahoo naquela data. As causas citadas como
"provável" são eventos conhecidos na data; as demais não foram pesquisadas, e a correção se apoia só na
divergência entre as fontes.

**Como a linha é corrigida.** Nas 19 linhas:
- abertura, máxima, mínima, fechamento e fechamento anterior passam a ser os do TradingView;
- recalculam-se `ret`, `gap`, `intra` e `amp`, e as qualitativas que dependem do retorno: `direcao`,
  `segue_ibov` e `faixa`;
- **continuam do Yahoo**: `volume`, `fin` (calculado com o fechamento do Yahoo), `vol_rel`,
  `faixa_volume`, `ret_ibov`, `fg_ant`, `humor_ant` e a data do pregão anterior, que é a mesma nas duas
  fontes por causa da regra 2.

**Atenção à continuidade dos preços.** Depois da correção, nas 19 linhas o fechamento anterior deixa de
ser igual ao fechamento registrado na linha do pregão anterior da mesma ação. Em 13 delas o fechamento do
dia é igual nas duas fontes e a diferença está toda no fechamento anterior; nas outras 6, o próprio
fechamento do Yahoo diverge (entre −17% e +26%). Nenhuma variável analisada é afetada, porque todas são
razões entre preços da mesma linha; só não se deve encadear os preços em reais dessas linhas com os das
vizinhas.

## 6. As 12 linhas que estavam marcadas como suspeitas

| Linhas | Resultado da conferência |
|---|---|
| 6 aberturas de 26/10/2026 em torno de −50% (−49,94% a −50,00%: B3SA3, CSAN3, CYRE3, MGLU3, MRVE3, RENT3) | **idênticas** no TradingView, inclusive abertura e volume; por isso ficam como estão |
| PCAR3 em 01/02, 05/05 e 19/05/2017 (+139,13%, +77,52%, −34,61%) | **idênticas** nas duas fontes; a ação ON era então pouco líquida (em maio, com dias sem negócio entre um e outro) |
| PCAR3 em 01/03/2021 (+112,28%) | **idêntica** |
| PCAR3 em 23/08/2023 (−66,62%) | **erro do Yahoo**: corrigida para +16,11% |
| UGPA3 em 28/06/2021 (+119,33%) | **erro do Yahoo**: corrigida para +1,05% |

A coluna `suspeito` sai da base e dá lugar à `conferencia_tv`, e a população continua com 27 colunas. O
máximo de +139,13% (PCAR3, 01/02/2017) continua na base: é idêntico nas duas fontes.

## 7. Efeito na população

| Variável | Medida | Antes | Depois |
|---|---|---|---|
| Retorno do dia | média | 0,0528% | 0,0525% |
| | desvio-padrão | 2,906 | 2,868 |
| | mínimo | −66,62% (PCAR3, 23/08/2023, erro) | −58,23% (MGLU3, 26/10/2026, nas duas fontes) |
| | máximo | +139,13% (PCAR3, 01/02/2017) | igual, idêntico nas duas fontes |
| | curtose | 131,2 | 104,2 |
| Gap de abertura | média | 0,0910% | 0,0904% |
| | desvio-padrão | 1,684 | 1,618 |
| | mínimo | −67,53% (PCAR3, erro) | −50,00% (aberturas de 26/10/2026, nas duas fontes) |
| | máximo | +139,13% (PCAR3, 01/02/2017) | igual, idêntico nas duas fontes |
| | curtose | 926,0 | 759,5 |
| Abertura ao fechamento e amplitude | média, desvio, extremos | — | praticamente iguais |
| P1 (acompanha o IBOV) | proporção | 69,462% | 69,463% |
| P2 (dia de alta) | proporção | 49,861% | 49,858% |

## 8. Efeito na amostra e nos testes

- **Nenhuma das 19 linhas corrigidas está na amostra.** Os valores das 2.343 linhas sorteadas ficam
  idênticos, e os resultados dos seis testes e dos intervalos (Painel 3) **não mudam**. O arquivo
  da amostra muda só pela troca da coluna `suspeito` por `conferencia_tv`, e o manifesto é gerado de novo.
- Na amostra: 2.311 linhas idênticas nas duas fontes, 29 com diferença até 5 p.p. e 3 com intervalo
  diferente.
- O N, os ids e o sorteio continuam os mesmos: os valores de 19 linhas foram corrigidos sem tirar nem
  pôr unidades. O cadastro do sorteio é o mesmo, e a AAS continua válida.
- Só mudam os **parâmetros da população** (seção 7). Os seis intervalos de confiança continuam contendo o
  valor da população, e o quadro decisão × verdade não muda.
- A simulação de 2.000 amostras, que sorteia da população, muda pouco (contagens em 2.000 réplicas):

| Hipótese | Rejeições antes | Depois | Cobertura do IC antes | Depois |
|---|---|---|---|---|
| P1 | 2.000 | 2.000 | 1.887 | 1.887 |
| P2 | 107 | 107 | 1.904 | 1.904 |
| M1 | 289 | 295 | 1.911 | 1.908 |
| M2 | 1.548 | 1.573 | 1.917 | 1.923 |
| P1-b | 1.791 | 1.789 | 1.887 | 1.887 |
| M2-b | 1.707 | 1.723 | 1.917 | 1.923 |

O poder da M2 passa de 77,4% para 78,7%. A taxa de rejeição da P2 continua em 5,35%.

## 9. Ordem dos fatos (transparência)

1. 31/10/2026: base congelada e população montada, já com 6 linhas marcadas como suspeitas (PCAR3 e
   UGPA3); amostra sorteada (semente 2026).
2. 31/10/2026: na revisão, mais 6 linhas marcadas (as aberturas em −50% de 26/10/2026). Nenhuma das 12
   está na amostra.
3. 03/11/2026: conferência com o TradingView, depois do sorteio e depois de ver os resultados dos testes.

A correção veio depois do sorteio, mas **não pode ter sido escolhida pelo resultado**: nenhuma linha da
amostra é alterada, então nenhum teste muda. A regra é a mesma para todas as linhas, sem escolha caso a
caso, e o efeito de outros limites está na seção 4.

## 10. Limitações que continuam

- A conferência mostra **concordância entre duas fontes**, não a verdade absoluta: as duas podem herdar
  o mesmo erro da bolsa, e o TradingView é lido por uma biblioteca não oficial.
- 1.694 linhas com diferença de até 5 p.p. e 101 com intervalo diferente ficam como no Yahoo. A KLBN11
  concentra parte das diferenças acima de 1 p.p. entre 2019 e 2021: a série dela difere entre as fontes
  nesse período.
- Dois pregões faltam na população porque faltam no Yahoo: 29/05/2017 (sem negócio na fonte) e
  20/11/2020 (ausente). O TradingView tem os dois.
- O Fear & Greed (`fg_ant`) e o volume relativo (`vol_rel`) continuam calculados com os dados do Yahoo.
- Dividendos e JCP continuam fora dos retornos (ver as limitações no README).

## 11. Reprodução

A cópia de 03/11/2026 já está congelada; o `--baixar` só é preciso para refazer tudo do zero (e se recusa
a sobrescrever a cópia existente).

```
# uma vez, num ambiente com a biblioteca tvdatafeed (fora do requirements.txt)
python conferir_tradingview.py --baixar
# sempre, no ambiente do trabalho (requirements.txt)
python preparar_dados.py   # aplica a conferência e a correção
python amostra.py          # mesma amostra
```

Depois do download, a cópia congelada dispensa a biblioteca: o `preparar_dados.py` e o app só leem os
arquivos.

## 12. Arquivos

- `dados/bruto/tv_1d/` (40 arquivos) e `dados/bruto/manifesto_tv.json`: a cópia congelada do TradingView.
- `dados/conferencia_tradingview.parquet`: a comparação linha a linha, para qualquer um conferir.
- `conferir_tradingview.py`: download e comparação; `preparar_dados.py` aplica a regra de correção.
- Coluna `conferencia_tv` da população: a categoria de cada linha (no lugar da antiga lista de suspeitos).
- Painel 1, "Sobre a base": um parágrafo sobre a conferência e a tabela de categorias.
