#!/usr/bin/env python3
# ============================================================================
#  Vela Monitor — varredura multi-sinal (BTC/USDT e top moedas por volume)
#
#  O que faz, por tipo de sinal (cada um pode disparar independente):
#
#   1) PULLBACK (swing) — perna de impulso (fundo->topo ou topo->fundo) no
#      4h, correção dentro da zona de Fibonacci 0.382, fundos/topos
#      ascendentes/descendentes confirmando, e status do volume.
#
#   2) CLÍMAX DE EXAUSTÃO (qualquer estilo) — RSI muito esticado (>=85 ou
#      <=15) junto com volume muito acima da média no 4h: costuma marcar
#      topo ou fundo de um movimento.
#
#   3) PRIMEIRO TOQUE DE RSI EM ZONA DE EXTREMO (5m = day trade, 1h = swing,
#      4h = setup raro de alta convicção) — o "cardápio de trade" do Diego:
#      TRÊS sinais SEPARADOS (não uma condição conjunta), cada um disparando
#      só no PRIMEIRO toque do RSI na zona de extremo (o RSI cruzou pra
#      dentro da zona nesta vela, não estava lá na vela anterior — assim não
#      repete o mesmo aviso vela após vela enquanto o RSI continua
#      esticado). Primeiro toque no 5m depois de um movimento forte = janela
#      rápida de repique/correção (day trade). Primeiro toque no 1h = ponto
#      de entrada de SWING, porque tende a coincidir com o diário formando
#      uma base de preço quando os tempos gráficos maiores estão alinhados
#      na mesma direção (o Diego comenta que deixa um alarme de RSI em ~31
#      configurado no 1h justamente pra pegar esse momento). Primeiro toque
#      no 4h (`check_scalp_4h`) é o mais raro dos três — o RSI de um tempo
#      gráfico tão largo só chega nesses extremos depois de várias semanas
#      de movimento — por isso é tratado como o setup de MAIOR convicção do
#      cardápio, mesmo ainda exigindo stop como qualquer outro sinal.
#
#   3b) RETESTE APÓS 1º TOQUE DE RSI NO 4H (swing, `check_retest_4h`) —
#      segunda etapa do sinal acima: depois do primeiro toque no 4h, o preço
#      costuma dar um repique de verdade (não é só ruído) e depois voltar
#      pra RETESTAR o fundo/topo daquela vela específica. Se segurar ali
#      (sem romper de verdade), é a base de um possível fundo/topo
#      ascendente/descendente num tempo gráfico maior (semanal) — "escada"
#      onde cada tempo gráfico maior forma sua própria base quando o tempo
#      gráfico imediatamente abaixo entra em sobrevenda/sobrecompra. O stop
#      usa o próprio fundo/topo do toque original como referência, e quando
#      o semanal está disponível o sinal também soma (sem exigir) fatores
#      extra de confluência semanal — EMA12 e Fibonacci 0.382 da última
#      perna semanal — e um segundo alvo mais ambicioso, mirando o próximo
#      pivô do semanal além do alvo técnico do 4h.
#
#   3c) CLASSIFICADOR DE BANDEIRA DE ALTA/BAIXA (contexto, `classifica_bandeira`)
#      — depois de toda perna de impulso no 4h, a correção que vem em seguida
#      só continua valendo como "bandeira" (pausa que tende a continuar na
#      mesma direção da perna) enquanto ela não recuar além de 0.382 de fibo
#      da perna E o volume durante a correção vier caindo. Se a correção já
#      passou de 0.382 E o volume nos repiques contra a perna vem crescendo,
#      isso invalida a leitura de bandeira — o mais provável passa a ser uma
#      continuação na direção OPOSTA à da perna original, um grau acima do
#      que parecia ser só uma pausa. É um sinal de CONTEXTO (não gera
#      COMPRAR/VENDER isolado), mostrado junto com os outros blocos de
#      leitura técnica no status horário e na análise detalhada — roda tanto
#      no 4h quanto no 3D (o Diego comenta que, quando o gráfico menor fica
#      "poluído"/confuso, o tempo gráfico de 3 dias costuma dar uma leitura
#      mais limpa da mesma bandeira).
#
#   3d) ROMPIMENTO DE LINHA DE TENDÊNCIA DIAGONAL — LTB/LTA
#      (`check_trendline_breakout`) — até aqui todo sinal de estrutura usava
#      só níveis HORIZONTAIS (pivô, fibo, EMA). Esse sinal ajusta uma reta
#      DIAGONAL aos dois pivôs mais distantes que ainda "seguram" o preço
#      entre eles — a LTB (linha de tendência de baixa, topos descendentes,
#      resistência) ou a LTA (linha de tendência de alta, fundos
#      ascendentes, suporte) — e dispara no primeiro fechamento além dela.
#      Alvo pelo próximo pivô na direção do rompimento; stop além do
#      pivô/linha de referência.
#
#   3e) PADRÃO OMBRO-CABEÇA-OMBRO — CLÁSSICO (topo, `check_oco_pattern`,
#      reversão de baixa) E INVERTIDO (OCOi, fundo, reversão de alta) —
#      heurística sobre os 3 últimos pivôs relevantes (ombro-cabeça-ombro,
#      com a cabeça claramente mais funda/alta e os ombros com
#      profundidade/altura parecida) e o "pescoço" entre eles. Dispara no
#      primeiro rompimento do pescoço, com alvo pela distância clássica
#      cabeça↔pescoço projetada, e stop além do ombro mais recente.
#
#   4) BOTTOM FISHING (posição) — moeda muito abaixo (55%+) da própria máxima
#      HISTÓRICA e formando fundos ascendentes no diário, indicando possível
#      base de longo prazo se formando.
#
#   4b) REVERSÃO DE TENDÊNCIA COM BASE (posição/swing) — versão mais leve do
#      bottom fishing: correção moderada (30%-55%) desde o topo dos últimos
#      ~180 dias (não a máxima histórica), com fundos ascendentes. Pega
#      reversões de médio prazo, não só quedas históricas extremas.
#
#   5) DOMINÂNCIA BTC / ALTSEASON (mercado, uma vez por rodada) — compara o
#      retorno do BTC nos últimos 7 dias com a média do watchlist de
#      altcoins no mesmo período. Não é o índice oficial de dominância (que
#      vem de market cap total, uma fonte que não temos aqui) — é um proxy
#      baseado em performance relativa, mas segue a mesma lógica da regra:
#      BTC forte na frente das alts = dominância subindo; alts fortes na
#      frente do BTC = dominância caindo / altseason.
#
#   6) REVERSÃO POR ROMPIMENTO FALHO (swing) — o preço rompe um suporte ou
#      resistência relevante (já confirmado por pivô), mas não tem
#      continuidade nessa direção e já recupera pro outro lado com volume
#      acima da média. Foi descrito numa das lives como o mecanismo por trás
#      de um alerta que o robô próprio do canal soltou automaticamente no
#      grupo dele — rompimento sem seguimento tende a invalidar o movimento
#      e antecipar uma reversão forte na direção contrária.
#
#   7) TERMÔMETRO DE FASE DE CICLO (mercado, uma vez por rodada) — compara a
#      performance de um conjunto de memecoins conhecidas com o BTC e com o
#      watchlist de alts. A ideia, de uma live, é que bull market roda em
#      ordem (BTC/ETH primeiro, depois alts de maior porte, memecoins por
#      último) — memecoins muito à frente dos outros dois grupos ao mesmo
#      tempo tende a marcar fase mais avançada/especulativa do movimento.
#
#   8) PADRÃO DE EQUILÍBRIO (swing curto) — quando não tem tendência clara
#      (últimos candles de 4h comprimidos numa faixa estreita, alternando
#      fundo/topo sem romper) e o preço está perto de uma das bordas dessa
#      faixa, sugere operar o próprio padrão: comprar perto do fundo mirando
#      o topo, ou vender perto do topo mirando o fundo, com stop logo além
#      do último fundo/topo formado. É o "o que fazer quando o mercado fica
#      parado", em vez de ficar sem nenhuma ideia quando não tem uma
#      tendência definida. Alvo segue o "padrão de equilíbrio" do Diego —
#      "quanto mais tempo lateralizado,
#      maior o impulso no rompimento": se o preço já está contido nessa
#      faixa por bem mais tempo que o mínimo exigido, o alvo estende além
#      da borda oposta (proporcional ao tempo extra, com teto), em vez de
#      mirar sempre só a borda oposta.
#
#   9) CONFLUÊNCIA MULTI-INDICADOR (mais de um timeframe) — em vez de exigir
#      só UM critério isolado, soma quantos fatores técnicos diferentes
#      (fibonacci em mais de um nível — 0.382/0.5/0.618 —, EMAs em mais de
#      um período — 12/21/50/200 — no 4h e no 15m, suporte/resistência
#      "recente" no 4h e no 1h — o fundo/topo dos últimos candles, mesmo
#      antes de virar um pivô confirmado — e RSI em sobrevenda/sobrecompra
#      no 15m, no 1h e no 5m extremo) estão alinhados na mesma direção ao
#      mesmo tempo. Pensado pro tipo de leitura manual que junta "fib 0.618
#      no 15m perto da EMA200, aproximando da EMA12 no 4h" ou "suporte no
#      4h em X com o 5m em sobrevenda extrema e o 1h perto de um suporte" —
#      cada indicador sozinho não dispara os outros sinais, mas a
#      combinação de vários sim. A mensagem também traz uma linha de
#      invalidação (o que costuma acontecer se o stop for rompido).
#
#  FILTROS DE QUALIDADE (valem pra TODO sinal COMPRAR/VENDER de qualquer um
#  dos 9 sinais acima, não é mais um sinal isolado):
#
#   a) Risco/retorno mínimo de 1:2 — o alvo técnico tem que valer pelo menos
#      o dobro da distância até o stop. Sinal que bate o critério técnico
#      mas fica abaixo disso é suprimido (não é enviado), e vira um
#      diagnóstico explicando o motivo.
#   b) Tendência majoritária do mercado — calculada a partir do BTC,
#      cruzando 3 tempos gráficos (diário, semanal e mensal, cada um com
#      seu próprio par de EMAs) uma vez por rodada: só vira "alta" ou
#      "baixa" quando o diário dá o veredito E nenhum dos tempos gráficos
#      maiores discorda dele — do jeito que o Diego explica nos vídeos,
#      "você nunca vai querer shortar um ativo que está numa tendência de
#      alta em todos os tempos gráficos" (e vice-versa). Sinal de VENDER
#      com o mercado em tendência de alta (ou de COMPRAR com o mercado em
#      tendência de baixa) é suprimido pelo mesmo motivo — "remar contra a
#      maré" tende a dar errado mesmo quando o setup local parece certo.
#      Mercado sem tendência clara, ou com os tempos gráficos discordando
#      entre si (neutro) não filtra nada.
#
#  PLANO B E PRESSÃO DE VOLUME (todo sinal COMPRAR/VENDER com stop): o bot
#  aponta o próximo nível técnico (EMA ou suporte/resistência, no mesmo
#  tempo gráfico e num zoom out pro diário) se o stop for rompido — ver
#  `adiciona_plano_b`. Além disso, checa a "pressão de volume" contrária à
#  posição (`analisa_pressao_volume`): se o volume do lado oposto (vendedor
#  pra quem comprou, comprador pra quem vendeu) está crescendo nos candles
#  mais recentes — "o volume é a gasolina do mercado" — isso vira um alerta
#  no próprio sinal (risco pra entrada agora) e deixa o plano B mais
#  enfático (o rompimento fica mais provável, não é só uma possibilidade
#  remota).
#
#  MEMÓRIA DA ÚLTIMA OPERAÇÃO (por símbolo, BTC/ETH): o bot guarda os dados
#  da última operação de verdade (COMPRAR/VENDER) de cada moeda numa
#  mensagem FIXADA (pin) no próprio chat do Telegram — sem tocar no
#  repositório git nem depender de cache do GitHub Actions. A cada rodada,
#  antes de montar o status, ele pergunta pro Telegram qual é a mensagem
#  fixada agora (`getChat`), lê os dados dela, e se saiu operação nova
#  atualiza só aquele símbolo e fixa a versão nova (editando a mesma
#  mensagem, não acumulando pin antigo). O status de toda rodada passa a
#  trazer, pra cada símbolo sem sinal ativo no momento, um bloco "📍 Última
#  operação enviada" com: quando foi, os valores (entrada/stop/alvo), há
#  quanto tempo, e como o preço andou desde então (inclusive se já passou do
#  stop ou do alvo) — ver `atualiza_memoria_ultima_operacao`,
#  `get_memoria_pinned` e `_ultima_operacao_texto`. Quando a operação ainda
#  está aberta (não passou nem do stop nem do alvo) e o preço já andou pelo
#  menos 1x a distância entrada→stop (1R) a favor, esse mesmo bloco soma uma
#  sugestão de mover o stop pra zero a zero (o preço de entrada) — trava o
#  risco em zero sem precisar sair da operação, ideia comentada nas lives
#  como forma de proteger o lucro já formado sem abrir mão do resto do
#  movimento (ver `BREAKEVEN_STOP_R_MULT`).
#
#  "FIQUE DE OLHO" (por símbolo, BTC/ETH, dentro do status horário): pra quem
#  não tem sinal nem confluência batendo ainda, o status passa a trazer
#  também o próximo nível técnico relevante que o preço ainda não tocou
#  (fibonacci da perna de 4h, EMA de 4h, ou o suporte/resistência anterior à
#  perna atual) — mesmo que ainda esteja longe. Antes isso só aparecia numa
#  consulta manual por moeda (`build_entry_outlook`); agora roda toda rodada
#  também pra avisar com antecedência quando o preço está se aproximando de
#  uma EMA ou suporte num tempo gráfico maior, não só quando já chegou lá.
#
#  RESTRIÇÃO TEMPORÁRIA (SOMENTE_CORE_SYMBOLS, ligada por padrão): por
#  pedido, o bot não analisa nem manda mensagem de NENHUMA moeda fora de
#  CORE_SYMBOLS (BTC/ETH) — a varredura completa do watchlist (itens 3-7
#  acima pra outras moedas, dominância, ciclo) e as seções extras do
#  relatório categorizado (item 10 abaixo) ficam pausadas. A consulta manual
#  por symbol continua funcionando pra qualquer par. Ver a constante perto
#  de CORE_SYMBOLS pra reverter.
#
#  Cada mensagem de sinal vem com um checklist (✅/❌) dos itens que
#  confirmaram aquele setup (RSI, volume, estrutura, EMA de contexto) e,
#  quando fizer sentido, um alvo técnico de lucro (próximo topo/fundo
#  relevante ou movimento medido) além do stop. Quando a MESMA moeda bate
#  mais de uma estratégia ao mesmo tempo, o bot manda uma mensagem só
#  explicando isso ("bateu 2 estratégias"), em vez de mensagens cheias
#  repetidas (o que parecia "operação clonada").
#
#  A varredura horária roda em TODO o watchlist por baixo dos panos, mas só
#  manda UMA mensagem de status por rodada, sempre com BTC, ETH e XRP
#  (fixos) + 2 altcoins escolhidas entre as que têm sinal ativo ou estão
#  mais perto de bater um — pra cada uma delas, mostra o sinal ativo, ou o
#  near-miss (diagnóstico) mais os cenários de alta/baixa quando não tem
#  nada disparado nem perto.
#
#  10) RELATÓRIO CATEGORIZADO (enviado em horários fixos do dia, ver
#      REPORT_TIMES_UTC) — organiza o que a varredura já achou por horizonte
#      de operação, em vez de mandar sinal por sinal solto: swing principal
#      (BTC e ETH, sempre aparecem — com sinal ativo, ou os dois cenários
#      touro/urso com faixa de preço quando não tem sinal), swing secundário
#      (XRP + top 10 moedas por market cap da CoinMarketCap), até
#      REPORT_SMALL_ALTS_N altcoins pequenas em setup, até REPORT_SCALP_N
#      scalps ativos e até REPORT_BOTTOM_FISHING_N bottom fishing — sempre
#      filtrando pelas melhores (porte/liquidez) pra não lotar o Telegram.
#      Segue a mesma ideia dos vídeos do Diego de casar o timeframe do
#      gráfico com o horizonte da operação (day trade -> 1h, swing de 1
#      semana -> 4h, swing de 1 mês -> 1d, que ele trata como o setup mais
#      forte de todos). Petróleo, ouro e mercado americano ficam de fora
#      dessa versão (não existem na Binance) — só cripto por enquanto.
#
#  DIAGNÓSTICO E CONSULTA SOB DEMANDA (só nas execuções manuais, pelo botão
#  "Run workflow" no GitHub Actions):
#
#   - Diagnóstico de proximidade: mesmo quando nenhum sinal de verdade
#     dispara, a varredura calcula o quão perto cada moeda está de bater
#     algum dos critérios acima (ex.: "RSI a 6 pontos do gatilho de
#     exaustão", "a 1,8% da zona de Fibonacci") e manda um resumo com as
#     mais próximas — pra você filtrar o que vale acompanhar de perto.
#
#   - Consulta por moeda: o campo opcional "symbol" do Run workflow permite
#     pedir uma análise específica de uma moeda (ex.: SOLUSDT) — roda todos
#     os checks nela na hora, mostra o que está mais perto de disparar e um
#     pouco de contexto (força relativa contra o BTC). É uma leitura
#     automática baseada nas mesmas regras de sempre, não uma opinião gerada
#     por um modelo de IA (o script não chama nenhum modelo de linguagem).
#
#  Watchlist dinâmica: em vez de uma lista fixa, a varredura busca os
#  TOP_N_SYMBOLS pares USDT de maior volume na Binance a cada rodada (ideia
#  de uma live do canal: a IA dele varre um universo grande de moedas, não
#  uma lista fixa pequena). Cada moeda recebe uma tag de "porte" (grande/
#  médio/pequeno) baseada no rank de volume dentro do próprio watchlist —
#  um PROXY de market cap, já que a Binance não fornece isso — usada nos
#  sinais de reversão porque o canal comentou preferir moedas de menor
#  porte pra esse tipo de setup.
#
#  Stops também passam por um ajuste anti-número-redondo: nunca deixamos o
#  stop logo abaixo (compra) ou acima (venda) de um nível psicológico
#  redondo (tipo 75.000, 80.000) — outra ideia direto de uma live.
#
#  Todos os sinais são leitura técnica automática baseada em regras (RSI,
#  volume, estrutura, fibonacci, drawdown) — não são recomendação de
#  investimento nem garantia de resultado.
#
#  Onde rodar: este script PRECISA rodar fora do sandbox do Claude (a
#  Binance e o Telegram estão bloqueados por política da organização tanto
#  no container de nuvem quanto na VM do bridge do computador). Rode
#  localmente no seu Mac (cron/launchd) ou via GitHub Actions — instruções
#  completas no README_vela_monitor_bot.md.
# ============================================================================

import os
import math
import time
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------------

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Watchlist — em vez de uma lista fixa pequena, a varredura busca dinamicamente
# os N pares USDT de maior volume na Binance a cada rodada (ideia tirada de uma
# live do canal: a IA dele varre um universo grande de moedas, não só uma
# lista fixa, pra pegar oportunidades fora do radar). Se a busca falhar por
# qualquer motivo, cai no fallback fixo abaixo.
TOP_N_SYMBOLS = 50

FALLBACK_WATCHLIST = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "TRXUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT",
    "XLMUSDT", "ETCUSDT", "FILUSDT", "APTUSDT", "ARBUSDT",
    "OPUSDT", "NEARUSDT", "INJUSDT", "SUIUSDT", "TONUSDT",
]

# Moedas que não fazem sentido entrar na varredura de padrão técnico: outras
# stablecoins contra USDT (não têm tendência de verdade) e tokens alavancados.
STABLE_BASES = {
    "USDC", "FDUSD", "TUSD", "BUSD", "DAI", "USDP", "PYUSD", "USDE",
    "EUR", "GBP", "AEUR", "USDS", "USTC",
}
LEVERAGED_SUFFIXES = ("UP", "DOWN", "BULL", "BEAR")

# --- Pullback (swing) ---
INTERVAL = "4h"
KLINES_LIMIT = 200
PIVOT_LEN = 3
FIB_LEVEL = 0.382
FIB_TOLERANCE = 0.006
VOLUME_LOOKBACK = 20
MIN_ASCENDING_BOTTOMS = 2

# --- Clímax de exaustão ---
RSI_PERIOD = 14
CLIMAX_RSI_HIGH = 85
CLIMAX_RSI_LOW = 15
CLIMAX_VOLUME_RATIO = 2.0

# --- EMA usada só como item extra do checklist (contexto, não filtro) ---
EMA_TREND_PERIOD = 21

# --- Primeiro toque de RSI em zona de extremo (SIGNAL 3), separado por
# tempo gráfico — cardápio de trade do Diego: primeiro toque no 5m = repique
# rápido de day trade; primeiro toque no 1h = entrada de swing (porque tende
# a coincidir com o diário formando base, quando os tempos maiores estão
# alinhados). Mantém os nomes antigos (SCALP_RSI_*) como os limiares do 5m
# pra não quebrar nada que ainda os referencie.
SCALP_RSI_OVERSOLD = 30
SCALP_RSI_OVERBOUGHT = 70
SCALP_5M_RSI_OVERSOLD = SCALP_RSI_OVERSOLD
SCALP_5M_RSI_OVERBOUGHT = SCALP_RSI_OVERBOUGHT
SCALP_1H_RSI_OVERSOLD = 31     # o Diego comenta um alarme de RSI ~31 no 1h
SCALP_1H_RSI_OVERBOUGHT = 69
SCALP_4H_RSI_OVERSOLD = SCALP_RSI_OVERSOLD    # mesmo limiar clássico 30/70,
SCALP_4H_RSI_OVERBOUGHT = SCALP_RSI_OVERBOUGHT  # mas no 4h isso é bem mais raro

# --- Reteste do fundo/topo depois do 1º toque de RSI no 4h (SIGNAL 3b,
# "escada de fundo ascendente" — depois do 1º toque em sobrevenda/sobrecompra
# no 4h, o preço costuma dar um repique e depois voltar pra retestar aquele
# fundo/topo; se segurar ali, pode ser a base de um fundo/topo ascendente/
# descendente no semanal, com o próprio nível do toque original como stop) ---
RETEST_4H_LOOKBACK = 60          # candles de 4h pra procurar o toque mais recente (~10 dias)
RETEST_4H_MIN_BOUNCE_PCT = 0.03  # precisa ter se afastado pelo menos 3% do nível antes de voltar
RETEST_4H_ZONE_TOLERANCE = 0.02  # até 2% de distância do nível original já conta como reteste
RETEST_4H_STOP_BUFFER = 0.005    # stop um pouco além do fundo/topo original, não exatamente em cima

# --- Sugestão de mover o stop pra zero a zero (memória da última operação) ---
# múltiplo de R (distância entrada→stop) que o preço precisa andar a favor,
# ainda com a operação aberta, pra memória sugerir travar o risco no zero a zero
BREAKEVEN_STOP_R_MULT = 1.0

# --- Classificador de bandeira de alta/baixa via Fibonacci + volume ---
# regra: uma correção (bandeira) só continua válida enquanto ela não recua
# mais que 0.382 de fibo da perna de impulso E o volume durante a correção
# vem caindo (sem força compradora/vendedora de verdade nos repiques). Se a
# correção passa de 0.382 E o volume vira ascendente nos repiques contra a
# tendência, a leitura de bandeira se inverte: o que parecia correção agora
# parece o início de uma continuação na direção contrária, um grau acima.
BANDEIRA_VOLUME_TREND_MIN_PCT = 0.15  # dif. mínima entre 1ª e 2ª metade do volume pra contar como tendência clara

# --- Rompimento de linha de tendência diagonal (LTB/LTA) ---
# diferente dos níveis horizontais (pivô, fibo, EMA) que o resto do bot já
# usa, aqui a referência é uma reta diagonal ajustada aos dois pivôs mais
# distantes que ainda "seguram" o preço entre eles — a mesma lógica de
# desenhar uma LTB (topos descendentes, resistência) ou LTA (fundos
# ascendentes, suporte) num gráfico. Só dispara no primeiro fechamento além
# da linha.
TRENDLINE_LOOKBACK = 90          # candles pra trás pra procurar pivôs que formem a linha (~15 dias no 4h)
TRENDLINE_MIN_SPAN = 10          # distância mínima (em candles) entre as duas âncoras da linha
TRENDLINE_TOUCH_TOLERANCE = 0.012  # tolerância pra uma vela "furar" a linha no meio sem invalidar
TRENDLINE_MIN_SLOPE_PCT = 0.0005   # inclinação mínima por vela, pra não confundir com nível ~horizontal
TRENDLINE_BREAK_BUFFER = 0.002     # margem além da linha pra contar como rompimento de verdade
TRENDLINE_STOP_BUFFER = 0.005      # margem do stop além do pivô/linha de referência

# --- Padrão Ombro-Cabeça-Ombro (OCO clássico = topo/reversão de baixa) e
# invertido (OCOi = fundo/reversão de alta) ---
# heurística baseada nos 3 últimos pivôs relevantes (ombro-cabeça-ombro) e
# no "pescoço" (linha entre os dois topos/fundos intermediários) — dispara
# no primeiro rompimento do pescoço, com alvo pela distância cabeça-pescoço
# projetada (medida clássica do padrão).
OCO_LOOKBACK = 150                    # candles pra trás pra procurar os 3 pivôs do padrão (~25 dias no 4h)
OCO_SHOULDER_SYMMETRY_TOLERANCE = 0.15  # até 15% de diferença de profundidade/altura entre os dois ombros
OCO_MIN_HEAD_DEPTH_PCT = 0.02           # cabeça precisa ser pelo menos 2% mais funda/alta que os ombros
OCO_NECKLINE_BREAK_BUFFER = 0.003       # margem além do pescoço pra contar como rompimento de verdade
OCO_STOP_BUFFER = 0.005                 # margem do stop além do ombro 2 (o mais recente)

# --- Bottom fishing (posição) — drawdown profundo desde a máxima histórica ---
BOTTOM_FISHING_MIN_DRAWDOWN = 0.55   # pelo menos 55% abaixo da máxima histórica
BOTTOM_FISHING_PIVOT_LEN = 3
BOTTOM_FISHING_MIN_ASCENDING = 2

# --- Reversão de tendência com base (posição/swing) — drawdown mais moderado,
# desde a máxima "recente" (não a histórica), pra pegar reversões de médio
# prazo tipo a que o canal descreveu numa live (moeda de menor porte saindo
# de tendência de baixa, formando base nítida) ---
LIGHT_REVERSAL_LOOKBACK_DAYS = 180
LIGHT_REVERSAL_PIVOT_LEN = 5
LIGHT_REVERSAL_MIN_DRAWDOWN = 0.30
LIGHT_REVERSAL_MAX_DRAWDOWN = BOTTOM_FISHING_MIN_DRAWDOWN  # acima disso, já é bottom fishing

# --- Classificação de "porte" por volume (proxy de market cap) — a Binance
# não fornece market cap, então usamos o rank de volume dentro do próprio
# watchlist do dia como aproximação de porte, do jeito que o canal comentou
# preferir moedas "com menos dinheiro enfiado nelas" pra reversões. Não é o
# market cap real, é só um proxy — deixamos isso claro na mensagem.
VOLUME_TIER_SMALL_PCT = 0.34   # terço de menor volume do watchlist
VOLUME_TIER_LARGE_PCT = 0.34   # terço de maior volume do watchlist

# --- Dominância BTC / altseason (proxy) ---
DOMINANCE_LOOKBACK_DAYS = 7
DOMINANCE_DIVERGENCE_PP = 6.0  # diferença mínima (pontos percentuais) pra alertar

# --- Termômetro de fase de ciclo (mania de memecoin) — lista curada porque a
# Binance não classifica "memecoin" como categoria; pares que não existirem
# mais (ou ainda não existirem) são simplesmente pulados na busca ---
MEME_COIN_SYMBOLS = [
    "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT", "BONKUSDT",
    "WIFUSDT", "MEMEUSDT", "1000SATSUSDT", "ORDIUSDT",
]
CYCLE_LOOKBACK_DAYS = DOMINANCE_LOOKBACK_DAYS  # mesmo período do check de dominância
MEME_MANIA_DIVERGENCE_PP = 12.0  # memecoins precisam estar bem à frente pra soar o alerta

# --- Reversão por rompimento falho (swing) ---
FAILED_BREAK_LOOKBACK = 6              # candles recentes onde procuramos o rompimento
FAILED_BREAK_PENETRATION_PCT = 0.001   # rompimento mínimo (0.1%) além do nível de referência
FAILED_BREAK_RECOVERY_PCT = 0.001      # recuperação mínima (0.1%) de volta pro outro lado
FAILED_BREAK_VOLUME_RATIO = 1.3        # volume mínimo (x média) no rompimento ou na recuperação

# --- Mercado em consolidação / range (swing curto) — "o que fazer quando o
# mercado fica parado": sem tendência clara, opera o próprio range em vez de
# ficar sem nenhuma ideia ---
RANGE_LOOKBACK = 20          # candles de 4h (~3,3 dias) usados pra definir o range
RANGE_MAX_PCT = 0.05         # até 5% de amplitude entre topo e fundo = mercado "parado"
RANGE_EDGE_ZONE_PCT = 0.25   # % da faixa (a partir de cada borda) considerada zona de entrada
# "Quanto mais tempo lateralizado, maior o impulso durante o rompimento" (padrão
# de equilíbrio do Diego) — depois de achar o range nos últimos RANGE_LOOKBACK
# candles, olha pra trás mais um pouco (até RANGE_BREAKOUT_MAX_LOOKBACK_MULT x
# RANGE_LOOKBACK no total) pra ver há quanto tempo o preço já está contido
# nessa mesma faixa, e usa isso pra dar um alvo mais ambicioso que só a borda
# oposta — capado em RANGE_BREAKOUT_EXTENSION_CAP x a altura do range.
RANGE_BREAKOUT_MAX_LOOKBACK_MULT = 4
RANGE_BREAKOUT_EXTENSION_CAP = 1.5
RANGE_BREAKOUT_EDGE_TOLERANCE = 0.5   # tolerância extra (x RANGE_MAX_PCT) pra não cortar por um pavio isolado

# --- Confluência multi-indicador (SINAL 9) — em vez de exigir só UM
# critério isolado, soma quantos fatores técnicos diferentes (fibonacci em
# mais de um nível, EMAs em mais de um período, RSI em mais de um
# timeframe) estão alinhados na mesma direção ao mesmo tempo. Pensado pro
# tipo de leitura manual tipo "fib 0.618 no 15m perto da EMA200, e
# aproximando da EMA12 no 4h" — cada indicador sozinho não vira sinal, mas
# a combinação sim ---
CONFLUENCE_FIB_LEVELS = [0.382, 0.5, 0.618]
CONFLUENCE_FIB_TOLERANCE = 0.008
CONFLUENCE_EMA_PERIODS = [12, 21, 50, 200]
CONFLUENCE_EMA_TOLERANCE = 0.006
CONFLUENCE_RSI_OVERSOLD = 35
CONFLUENCE_RSI_OVERBOUGHT = 65
CONFLUENCE_MIN_FACTORS = 3       # quantos fatores alinhados pra virar sinal de verdade
CONFLUENCE_DIAG_MIN_FACTORS = 2  # quantos já alinhados pra virar diagnóstico (near-miss)
CONFLUENCE_15M_LIMIT = 300       # candles de 15m suficientes pra dar pra calcular EMA200 nesse timeframe
CONFLUENCE_5M_LIMIT = 100        # candles de 5m só pra RSI — não precisa de EMA200 aqui
CONFLUENCE_RECENT_LOOKBACK = 20  # janela (em candles) pra suporte/resistência "recente" ainda não confirmada como pivô
CONFLUENCE_RECENT_TOLERANCE = 0.006
CONFLUENCE_RSI_5M_OVERSOLD = 20   # sobrevenda "extrema" no 5m — mais apertado que o RSI padrão (35) por ser timeframe curto
CONFLUENCE_RSI_5M_OVERBOUGHT = 80

# --- Diagnóstico de proximidade (near-miss) — só usado nas execuções manuais,
# pra mostrar quais moedas estão perto de bater algum critério mesmo sem ter
# disparado um sinal de verdade ainda. Fica só com o diagnóstico MAIS próximo
# de cada moeda (não um por tipo de sinal) pra não virar uma lista gigante ---
PULLBACK_DIAG_MAX_PCT = 0.025      # até 2,5% da zona fib já entra no diagnóstico
EXHAUSTION_DIAG_RSI_BAND = 15      # RSI dentro de 15 pontos do gatilho (70-85 ou 15-30)
SCALP_DIAG_RSI_BAND = 10           # RSI dentro de 10 pontos do gatilho de scalp
REVERSAL_DRAWDOWN_DIAG_BAND = 0.05  # até 5 pontos percentuais abaixo do drawdown mínimo
DIAGNOSTIC_TOP_N = 6                # quantas moedas (já deduplicadas) entram no resumo

# Hosts pra dados públicos da Binance, em ordem de tentativa. O primeiro é o
# espelho oficial de dados públicos (sem autenticação) — ele evita o bloqueio
# geográfico (HTTP 451) que o api.binance.com às vezes devolve dependendo de
# em qual região o runner do GitHub Actions caiu daquela vez. O segundo é o
# host normal, como fallback caso o espelho fique fora do ar.
BINANCE_BASES = [
    "https://data-api.binance.vision",
    "https://api.binance.com",
]
TELEGRAM_BASE = "https://api.telegram.org"

API_SLEEP = 0.2   # pausa entre chamadas à Binance (respeita rate limit)

# --- Notícias de fallback (quando a rodada não acha nenhum setup) ---
# A Reuters não oferece mais um feed público de graça pra puxar direto sem
# passar por scraping (o que evitamos de propósito — não é uma forma
# confiável nem respeita os termos do site). Em vez disso usamos o plano
# gratuito da NewsAPI.org filtrando o domínio reuters.com — só título e
# resumo curto de cada notícia (nunca o texto completo do artigo), com o
# link original, e traduzido pro português via MyMemory (tradução gratuita,
# sem precisar de chave). Precisa cadastrar o secret NEWS_API_KEY no GitHub
# com uma chave gratuita de newsapi.org — sem isso, esse recurso simplesmente
# fica desligado (não quebra a varredura).
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "").strip()
NEWS_API_BASE = "https://newsapi.org/v2"
NEWS_MAX_HEADLINES = 4
TRANSLATE_BASE = "https://api.mymemory.translated.net/get"

# --- Top 10 por market cap (CoinMarketCap) — usado no relatório categorizado
# pra saber quais moedas entram no "swing secundário" além do XRP. Precisa
# do secret CMC_API_KEY (cadastro grátis em coinmarketcap.com/api) — sem
# ele, cai numa lista fixa aproximada (pode ficar desatualizada se o
# ranking mudar bastante) ---
CMC_API_KEY = os.environ.get("CMC_API_KEY", "").strip()
CMC_API_BASE = "https://pro-api.coinmarketcap.com/v1"
CMC_TOP_N = 10
CMC_FALLBACK_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "SOLUSDT",
    "DOGEUSDT", "ADAUSDT", "TRXUSDT", "LINKUSDT", "AVAXUSDT",
]

# --- Relatório categorizado (swing longo + destaques) — em vez de rodar em
# TODA execução horária, só monta e manda nos horários abaixo (hora:minuto
# em UTC). Pedido pra bater com a rotina de mercado americano (abertura,
# meio do pregão, 20h, fechamento do candle diário) no horário da Irlanda —
# como a Irlanda muda de fuso (IST/GMT) duas vezes por ano e o cron do
# GitHub Actions só entende UTC fixo, esses horários valem pro horário de
# verão europeu (IST, UTC+1); no horário de inverno (GMT) tudo sai 1h mais
# cedo do que o pretendido, a menos que a lista seja ajustada ---
REPORT_TIMES_UTC = [(5, 0), (13, 0), (13, 30), (18, 45), (19, 15), (22, 0)]
REPORT_TIME_TOLERANCE_MIN = 8   # tolerância pra atraso do runner do GitHub Actions
REPORT_SMALL_ALTS_N = 5
REPORT_SCALP_N = 2
REPORT_BOTTOM_FISHING_N = 2

# --- Status "core" — mandado em TODA rodada horária, mas só pra um punhado
# fixo de moedas (em vez de mensagem solta pra qualquer moeda do watchlist
# de 50, que virou a maior fonte de poluição no Telegram, além de deixar a
# rodada lenta). Por pedido, reduzido pra só BTC/ETH por enquanto — pra
# voltar a incluir XRP e altcoins em destaque, é só colocar de volta em
# CORE_SYMBOLS e usar CORE_EXTRA_ALTS_N > 0 (nesse caso a rodada volta a
# rodar mais devagar, porque contava com a varredura completa do watchlist
# rodando toda hora, e isso agora só acontece nos horários do relatório ou
# manualmente — ver do_full_scan em main()) ---
CORE_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
CORE_EXTRA_ALTS_N = 2

# Restrição temporária, por pedido: enquanto isso estiver True, o bot não
# analisa (nem manda mensagem de) NENHUMA moeda fora de CORE_SYMBOLS — nem
# a varredura completa do watchlist (scalp/altcoins/bottom fishing/
# dominância/ciclo), nem o XRP + top 10 CoinMarketCap do relatório
# categorizado. Pra voltar a cobrir o resto do mercado, é só voltar isso
# pra False.
SOMENTE_CORE_SYMBOLS = True

# Pivô usado só no cenário touro/urso (swing longo, candle diário) — mais
# largo que o PIVOT_LEN do 4h porque no diário pivôs curtos viram ruído.
SCENARIO_PIVOT_LEN = 5


# ----------------------------------------------------------------------------
# DADOS DA BINANCE
# ----------------------------------------------------------------------------

def _binance_get(path, timeout=20):
    """
    GET num endpoint público da Binance, tentando os hosts de BINANCE_BASES
    em ordem. Existe por causa do erro 451 (bloqueio geográfico) que
    api.binance.com às vezes devolve dependendo de onde o runner do GitHub
    Actions está hospedado — o espelho de dados públicos (data-api.binance.
    vision) tentado primeiro evita isso na maioria dos casos.
    """
    last_error = None
    for base in BINANCE_BASES:
        url = f"{base}{path}"
        req = urllib.request.Request(url, headers={"User-Agent": "vela-monitor-bot/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            last_error = e
            continue
    raise last_error


def fetch_klines(symbol: str, interval: str, limit: int):
    """Busca candles públicos da Binance. Não precisa de API key."""
    raw = _binance_get(f"/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}")
    candles = []
    for row in raw:
        candles.append({
            "open_time": row[0],
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
        })
    time.sleep(API_SLEEP)
    return candles


def fetch_top_usdt_symbols(limit=TOP_N_SYMBOLS):
    """
    Busca todos os pares USDT da Binance com seu volume das últimas 24h e
    devolve os `limit` de maior volume — a varredura "grande", em vez de uma
    lista fixa. Remove stablecoins contra USDT e tokens alavancados, que não
    fazem sentido pra análise de padrão técnico.
    """
    raw = _binance_get("/api/v3/ticker/24hr", timeout=30)
    time.sleep(API_SLEEP)

    candidatos = []
    for row in raw:
        symbol = row.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue
        base = symbol[:-4]
        if base in STABLE_BASES:
            continue
        if base.endswith(LEVERAGED_SUFFIXES):
            continue
        try:
            quote_volume = float(row.get("quoteVolume", 0))
        except (TypeError, ValueError):
            continue
        if quote_volume <= 0:
            continue
        candidatos.append((symbol, quote_volume))

    candidatos.sort(key=lambda x: x[1], reverse=True)
    top = candidatos[:limit]
    return top  # lista de (symbol, quoteVolume), já ordenada por volume desc


def classify_volume_tiers(top_symbols):
    """
    Recebe a lista [(symbol, quoteVolume), ...] já ordenada por volume desc
    e devolve um dict symbol -> "grande" | "médio" | "pequeno", como proxy de
    porte (não é market cap real, é rank de volume dentro do watchlist).
    """
    n = len(top_symbols)
    if n == 0:
        return {}
    large_cut = int(n * VOLUME_TIER_LARGE_PCT)
    small_cut = int(n * (1 - VOLUME_TIER_SMALL_PCT))
    tiers = {}
    for i, (symbol, _) in enumerate(top_symbols):
        if i < large_cut:
            tiers[symbol] = "grande"
        elif i >= small_cut:
            tiers[symbol] = "pequeno"
        else:
            tiers[symbol] = "médio"
    return tiers


# ----------------------------------------------------------------------------
# INDICADORES BÁSICOS
# ----------------------------------------------------------------------------

def compute_rsi(closes, period=RSI_PERIOD):
    """RSI clássico (suavização de Wilder). Retorna o valor mais recente."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_ema(closes, period=EMA_TREND_PERIOD):
    """
    Média móvel exponencial clássica. Usada só como item extra do checklist
    (preço segurando ou não a EMA) — não decide sozinha se um sinal dispara.
    """
    if len(closes) < period:
        return None
    ema = sum(closes[:period]) / period
    k = 2 / (period + 1)
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return ema


def fmt_price(x):
    """
    Formata preço com 4 dígitos significativos como o resto do bot já fazia
    (":.4g"), mas sem cair em notação científica pra moedas de preço alto
    (o ".4g" puro vira "7.751e+04" pra qualquer coisa acima de ~10 mil, o
    que é exatamente o preço do BTC — ficava ilegível nas mensagens). Preço
    alto usa separador de milhar com 2 casas; preço baixo (moedas menores)
    mantém decimais suficientes sem notação científica.
    """
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    texto = f"{x:.4g}"
    if "e" in texto or "E" in texto:
        if abs(x) >= 1:
            texto = f"{x:,.2f}"
        else:
            texto = f"{x:.8f}".rstrip("0").rstrip(".")
    return texto


def volume_status(candles, lookback=VOLUME_LOOKBACK):
    if len(candles) < lookback + 1:
        return None, None, None
    recent = candles[-lookback - 1:-1]
    avg_vol = sum(c["volume"] for c in recent) / len(recent)
    current_vol = candles[-1]["volume"]
    ratio = current_vol / avg_vol if avg_vol > 0 else None
    return current_vol, avg_vol, ratio


# ----------------------------------------------------------------------------
# NÚMEROS PSICOLÓGICOS REDONDOS — ajuste de stop
#
# Ideia de uma das lives: nunca deixe seu ponto de stop/liquidação logo
# abaixo (compra) ou acima (venda) de um número redondo (tipo 75, 80, 100
# mil) — o preço "gosta" de visitar esses níveis pra caçar stops. Prefira um
# stop com uma margem melhor, ex.: 73900 em vez de 74900.
# ----------------------------------------------------------------------------

ROUND_NUMBER_PROXIMITY_PCT = 0.006   # considera "perto" de um redondo dentro de 0.6%
ROUND_NUMBER_EXTRA_BUFFER_PCT = 0.004  # quanto empurrar o stop pra além do redondo


def _round_number_candidates(price):
    if price <= 0:
        return []
    magnitude = 10 ** math.floor(math.log10(price))
    candidates = set()
    for step in (magnitude, magnitude / 2, magnitude / 4, magnitude / 10):
        if step <= 0:
            continue
        base = round(price / step) * step
        for k in range(-2, 3):
            candidates.add(round(base + k * step, 10))
    return [c for c in candidates if c > 0]


def avoid_round_number_stop(stop_price, side):
    """
    `side` = "compra" (stop fica abaixo do preço, empurra mais pra baixo se
    estiver colado num redondo) ou "venda" (stop acima do preço, empurra
    mais pra cima).
    """
    for candidate in _round_number_candidates(stop_price):
        diff_pct = abs(stop_price - candidate) / candidate
        if diff_pct > ROUND_NUMBER_PROXIMITY_PCT:
            continue
        if side == "compra" and stop_price <= candidate:
            return candidate * (1 - ROUND_NUMBER_EXTRA_BUFFER_PCT)
        if side == "venda" and stop_price >= candidate:
            return candidate * (1 + ROUND_NUMBER_EXTRA_BUFFER_PCT)
    return stop_price


# ----------------------------------------------------------------------------
# ESTRUTURA: PIVÔS, PERNA DE IMPULSO, FIBONACCI, FUNDOS/TOPOS ASCENDENTES
# ----------------------------------------------------------------------------

def find_pivots(candles, length=PIVOT_LEN):
    """
    Marca pivôs de alta (topo) e baixa (fundo) — uma vela é pivô se for a
    maior/menor entre `length` velas antes e `length` velas depois dela.
    Retorna duas listas de (índice, preço): pivot_highs, pivot_lows.
    """
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    n = len(candles)
    pivot_highs, pivot_lows = [], []
    for i in range(length, n - length):
        window_h = highs[i - length:i + length + 1]
        if highs[i] == max(window_h) and window_h.count(highs[i]) == 1:
            pivot_highs.append((i, highs[i]))
        window_l = lows[i - length:i + length + 1]
        if lows[i] == min(window_l) and window_l.count(lows[i]) == 1:
            pivot_lows.append((i, lows[i]))
    return pivot_highs, pivot_lows


def last_impulse_leg(pivot_highs, pivot_lows):
    """
    Encontra a perna de impulso mais recente confirmada: fundo -> topo
    (perna de alta) ou topo -> fundo (perna de baixa).
    """
    if not pivot_highs or not pivot_lows:
        return None
    last_high_idx, last_high_price = pivot_highs[-1]
    last_low_idx, last_low_price = pivot_lows[-1]
    if last_high_idx > last_low_idx:
        candidates = [p for p in pivot_lows if p[0] < last_high_idx]
        if not candidates:
            return None
        start_idx, start_price = candidates[-1]
        return {"direction": "alta", "start_idx": start_idx, "start_price": start_price,
                "end_idx": last_high_idx, "end_price": last_high_price}
    else:
        candidates = [p for p in pivot_highs if p[0] < last_low_idx]
        if not candidates:
            return None
        start_idx, start_price = candidates[-1]
        return {"direction": "baixa", "start_idx": start_idx, "start_price": start_price,
                "end_idx": last_low_idx, "end_price": last_low_price}


def fib_level_price(leg, level=FIB_LEVEL):
    if leg["direction"] == "alta":
        return leg["end_price"] - level * (leg["end_price"] - leg["start_price"])
    else:
        return leg["end_price"] + level * (leg["start_price"] - leg["end_price"])


def price_in_fib_zone(price, fib_price, tolerance=FIB_TOLERANCE):
    return abs(price - fib_price) / fib_price <= tolerance


def ascending_or_descending_bottoms(leg, pivot_highs, pivot_lows, min_count=MIN_ASCENDING_BOTTOMS):
    end_idx = leg["end_idx"]
    if leg["direction"] == "alta":
        recent = [p for p in pivot_lows if p[0] > end_idx]
        if len(recent) < min_count:
            return False, recent
        prices = [p[1] for p in recent[-min_count:]]
        ok = all(prices[i] < prices[i + 1] for i in range(len(prices) - 1))
        return ok, recent
    else:
        recent = [p for p in pivot_highs if p[0] > end_idx]
        if len(recent) < min_count:
            return False, recent
        prices = [p[1] for p in recent[-min_count:]]
        ok = all(prices[i] > prices[i + 1] for i in range(len(prices) - 1))
        return ok, recent


def _volume_trend(candles, min_pct=BANDEIRA_VOLUME_TREND_MIN_PCT):
    """
    Compara o volume médio da 1ª metade com o da 2ª metade de uma sequência
    de candles (tipicamente a correção/bandeira depois de uma perna de
    impulso). Retorna "descendente" (volume caindo, correção "saudável"),
    "ascendente" (volume crescendo, força de verdade entrando contra a
    perna), "estável" (sem diferença clara), ou None se não há candles
    suficientes pra uma leitura razoável.
    """
    n = len(candles)
    if n < 6:
        return None
    meio = n // 2
    vol1 = [c.get("volume", 0) for c in candles[:meio]]
    vol2 = [c.get("volume", 0) for c in candles[meio:]]
    media1 = sum(vol1) / len(vol1) if vol1 else 0
    media2 = sum(vol2) / len(vol2) if vol2 else 0
    if media1 <= 0:
        return None
    variacao = (media2 - media1) / media1
    if variacao <= -min_pct:
        return "descendente"
    if variacao >= min_pct:
        return "ascendente"
    return "estável"


def classifica_bandeira(symbol, candles, timeframe_label="4h", pivot_len=PIVOT_LEN, fib_level=FIB_LEVEL):
    """
    Classifica a correção atual (depois da última perna de impulso) como uma
    bandeira "intacta", "invalidada" ou "indefinida", usando a regra de
    Fibonacci 0.382 + direção do volume que aparece nas lives do Diego.
    `timeframe_label` é só pro texto — a função funciona em qualquer tempo
    gráfico, e o Diego já mencionou essa leitura tanto no 4h quanto no 3D:

      - INTACTA: a correção não recuou além de 0.382 da perna de impulso, e
        o volume durante a correção vem caindo (ou está estável) — a
        bandeira segue viva, favorece continuação na direção da perna.
      - INVALIDADA: a correção já passou de 0.382 E o volume nos repiques
        contra a perna vem crescendo — isso derruba a leitura de bandeira;
        o mais provável passa a ser uma continuação na direção OPOSTA à da
        perna original (um grau acima).
      - INDEFINIDA: dados insuficientes ou sinais mistos (ex.: passou de
        0.382 mas o volume não confirma, ou não deu pra medir volume) — não
        há leitura clara o bastante pra ser útil.

    Retorna None se não há perna de impulso identificável (poucos pivôs).
    """
    min_candles = 2 * pivot_len + 10
    if len(candles) < min_candles:
        return None
    pivot_highs, pivot_lows = find_pivots(candles, pivot_len)
    leg = last_impulse_leg(pivot_highs, pivot_lows)
    if leg is None:
        return None

    leg_range = abs(leg["end_price"] - leg["start_price"])
    if leg_range <= 0:
        return None

    price_now = candles[-1]["close"]
    correcao = candles[leg["end_idx"]:]

    if leg["direction"] == "baixa":
        # perna de baixa -> a correção é o repique pra cima; bandeira "de baixa"
        tipo_bandeira = "de baixa"
        direcao_perna_txt = "baixa"
        oposto_txt = "alta"
        retracao_pct = max(0.0, (price_now - leg["end_price"]) / leg_range)
    else:
        # perna de alta -> a correção é o puxão pra baixo; bandeira "de alta"
        tipo_bandeira = "de alta"
        direcao_perna_txt = "alta"
        oposto_txt = "baixa"
        retracao_pct = max(0.0, (leg["end_price"] - price_now) / leg_range)

    vol_trend = _volume_trend(correcao)
    contida = retracao_pct <= fib_level

    vol_txt_map = {
        "descendente": "volume caindo na correção",
        "ascendente": "volume crescendo na correção",
        "estável": "volume estável na correção",
        None: "volume da correção sem leitura clara",
    }
    vol_txt = vol_txt_map[vol_trend]

    if contida and vol_trend in ("descendente", "estável", None):
        status = "intacta"
        texto = (
            f"🚩 Bandeira {tipo_bandeira} intacta em {symbol} ({timeframe_label}): a correção ainda não "
            f"passou de {fib_level:.0%} da última perna de {direcao_perna_txt} (recuo atual "
            f"~{retracao_pct:.0%}), e {vol_txt} — nada de errado com a bandeira, o viés técnico segue a "
            f"favor de continuação em {direcao_perna_txt}."
        )
    elif (not contida) and vol_trend == "ascendente":
        status = "invalidada"
        texto = (
            f"🚩 Bandeira {tipo_bandeira} invalidada em {symbol} ({timeframe_label}): a correção já passou "
            f"de {fib_level:.0%} da última perna de {direcao_perna_txt} (recuo atual ~{retracao_pct:.0%}) "
            f"E {vol_txt} — isso derruba a leitura de bandeira. Mais provável agora é uma continuação em "
            f"{oposto_txt}, um grau acima do que parecia ser só uma correção."
        )
    else:
        status = "indefinida"
        texto = (
            f"🚩 Bandeira {tipo_bandeira} em {symbol} ({timeframe_label}) com leitura mista: recuo atual "
            f"~{retracao_pct:.0%} frente aos {fib_level:.0%} de referência, e {vol_txt} — sinais não "
            f"bateram o suficiente pra confirmar se a bandeira segue intacta ou já foi invalidada."
        )

    return {
        "status": status,
        "tipo_bandeira": tipo_bandeira,
        "direcao_perna": leg["direction"],
        "retracao_pct": retracao_pct,
        "volume_trend": vol_trend,
        "timeframe": timeframe_label,
        "texto": texto,
    }


# ----------------------------------------------------------------------------
# ROMPIMENTO DE LINHA DE TENDÊNCIA DIAGONAL (LTB/LTA)
# ----------------------------------------------------------------------------
#
# Até aqui todo o resto do bot só enxerga níveis HORIZONTAIS (pivô, fibo,
# EMA). Mas boa parte da análise visual do Diego usa retas DIAGONAIS — a LTB
# (linha de tendência de baixa, conectando topos descendentes, funcionando
# como resistência) e a LTA (linha de tendência de alta, conectando fundos
# ascendentes, funcionando como suporte). Aqui a linha é ajustada aos dois
# pivôs mais distantes (dentro do lookback) que ainda "seguram" o preço
# entre eles — ou seja, nenhuma vela no meio do caminho fecha/fura a linha
# além de uma pequena tolerância — e só dispara no PRIMEIRO fechamento além
# dela (não repete enquanto o preço segue do mesmo lado).

def _fit_trendline(pivots, candles, direction, lookback):
    """
    Acha o par de pivôs (mais distante entre si, ou seja a linha mais
    "estabelecida") que forma uma linha de tendência válida:
      - direction="baixa" (LTB): usa pivot_highs, topos descendentes
        (p1 > p2), valida que nenhuma vela no meio ultrapassa a linha pelo
        HIGH.
      - direction="alta" (LTA): usa pivot_lows, fundos ascendentes
        (p1 < p2), valida que nenhuma vela no meio ultrapassa a linha pelo
        LOW.
    Retorna (idx1, p1, idx2, p2, slope) da melhor linha achada, ou None.
    """
    n = len(candles)
    limite = max(0, n - lookback)
    pts = [p for p in pivots if p[0] >= limite]
    if len(pts) < 2:
        return None

    melhor = None
    melhor_span = -1
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            idx1, p1 = pts[i]
            idx2, p2 = pts[j]
            if direction == "baixa" and not (p1 > p2):
                continue
            if direction == "alta" and not (p1 < p2):
                continue
            span = idx2 - idx1
            if span < TRENDLINE_MIN_SPAN:
                continue
            slope = (p2 - p1) / (idx2 - idx1)
            if p1 <= 0 or abs(slope) / p1 < TRENDLINE_MIN_SLOPE_PCT:
                continue  # inclinação fraca demais — já é coberto pelos níveis horizontais

            valido = True
            for k in range(idx1 + 1, idx2):
                linha_k = p1 + slope * (k - idx1)
                if direction == "baixa" and candles[k]["high"] > linha_k * (1 + TRENDLINE_TOUCH_TOLERANCE):
                    valido = False
                    break
                if direction == "alta" and candles[k]["low"] < linha_k * (1 - TRENDLINE_TOUCH_TOLERANCE):
                    valido = False
                    break
            if valido and span > melhor_span:
                melhor = (idx1, p1, idx2, p2, slope)
                melhor_span = span
    return melhor


def _monta_sinal_trendline(symbol, candles, acao, tipo_linha, ancora1, ancora2, linha_agora,
                            pivot_highs, pivot_lows, timeframe_label):
    idx1, p1 = ancora1
    idx2, p2 = ancora2
    price_now = candles[-1]["close"]

    if acao == "COMPRAR":
        candidatos_alvo = [p[1] for p in pivot_highs if p[1] > price_now]
        alvo = min(candidatos_alvo) if candidatos_alvo else None
        candidatos_stop = [p[1] for p in pivot_lows if p[0] > idx1]
        nivel_stop = max(candidatos_stop) if candidatos_stop else min(p1, p2)
        stop = avoid_round_number_stop(nivel_stop * (1 - TRENDLINE_STOP_BUFFER), "compra")
    else:
        candidatos_alvo = [p[1] for p in pivot_lows if p[1] < price_now]
        alvo = max(candidatos_alvo) if candidatos_alvo else None
        candidatos_stop = [p[1] for p in pivot_highs if p[0] > idx1]
        nivel_stop = min(candidatos_stop) if candidatos_stop else max(p1, p2)
        stop = avoid_round_number_stop(nivel_stop * (1 + TRENDLINE_STOP_BUFFER), "venda")
    if alvo is None:
        return None  # sem alvo técnico pra checar risco/retorno

    nome_linha = "LTB (topos descendentes)" if tipo_linha == "LTB" else "LTA (fundos ascendentes)"
    papel = "resistência" if tipo_linha == "LTB" else "suporte"
    direcao_txt = "alta" if acao == "COMPRAR" else "baixa"

    detalhes = [
        f"Preço agora: {fmt_price(price_now)}",
        f"Rompeu a {nome_linha} desenhada entre {fmt_price(p1)} e {fmt_price(p2)}",
        f"Nível da linha nesta vela: {fmt_price(linha_agora)}",
        f"Alvo técnico: {fmt_price(alvo)}",
        f"Stop sugerido: {fmt_price(stop)}",
    ]
    checklist = [
        (f"Fechamento além da {tipo_linha} nesta vela (primeiro rompimento)", True),
    ]
    explicacao = (
        f"O preço rompeu a {nome_linha} que vinha funcionando como {papel} diagonal no {timeframe_label} "
        f"— quando isso acontece, o cenário técnico passa a favorecer continuação em {direcao_txt}, desde "
        "que a estrutura se confirme nos candles seguintes."
    )
    aviso = (
        "Rompimento de linha de tendência pode ser falso (o preço volta pra dentro da linha) — vale "
        "esperar confirmação nos candles seguintes antes de aumentar convicção."
    )
    return {
        "symbol": symbol, "estilo": "SWING", "acao": acao,
        "titulo": f"Rompimento de {tipo_linha} no {timeframe_label}",
        "timeframe": timeframe_label,
        "detalhes": detalhes,
        "checklist": checklist,
        "entry_price": price_now, "target_price": alvo, "stop_price": stop,
        "resumo": f"Rompimento da {tipo_linha} em {fmt_price(linha_agora)} no {timeframe_label}.",
        "explicacao": explicacao,
        "aviso": aviso,
    }


def check_trendline_breakout(symbol, candles, timeframe_label="4h", pivot_len=PIVOT_LEN):
    """
    Detecta o primeiro rompimento de uma LTB (linha de tendência de baixa,
    resistência diagonal) pra cima, ou de uma LTA (linha de tendência de
    alta, suporte diagonal) pra baixo — ver `_fit_trendline` pra critério de
    validação da linha. Prioriza LTB (mais comum nas lives como setup de
    reversão/continuação de alta); só olha LTA se não achou LTB rompida.
    """
    n = len(candles)
    if n < TRENDLINE_MIN_SPAN + 5:
        return None
    price_now = candles[-1]["close"]
    price_prev = candles[-2]["close"] if n > 1 else None
    if price_prev is None:
        return None

    pivot_highs, pivot_lows = find_pivots(candles, pivot_len)

    ltb = _fit_trendline(pivot_highs, candles, "baixa", TRENDLINE_LOOKBACK)
    if ltb is not None:
        idx1, p1, idx2, p2, slope = ltb
        linha_agora = p1 + slope * (n - 1 - idx1)
        linha_antes = p1 + slope * (n - 2 - idx1)
        buffer_ = linha_agora * TRENDLINE_BREAK_BUFFER
        if price_prev <= linha_antes + buffer_ and price_now > linha_agora + buffer_:
            sinal = _monta_sinal_trendline(
                symbol, candles, "COMPRAR", "LTB", (idx1, p1), (idx2, p2), linha_agora,
                pivot_highs, pivot_lows, timeframe_label,
            )
            if sinal is not None:
                return sinal

    lta = _fit_trendline(pivot_lows, candles, "alta", TRENDLINE_LOOKBACK)
    if lta is not None:
        idx1, p1, idx2, p2, slope = lta
        linha_agora = p1 + slope * (n - 1 - idx1)
        linha_antes = p1 + slope * (n - 2 - idx1)
        buffer_ = linha_agora * TRENDLINE_BREAK_BUFFER
        if price_prev >= linha_antes - buffer_ and price_now < linha_agora - buffer_:
            return _monta_sinal_trendline(
                symbol, candles, "VENDER", "LTA", (idx1, p1), (idx2, p2), linha_agora,
                pivot_highs, pivot_lows, timeframe_label,
            )

    return None


# ----------------------------------------------------------------------------
# PADRÃO OMBRO-CABEÇA-OMBRO (OCO = topo/reversão de baixa) E INVERTIDO
# (OCOi = fundo/reversão de alta)
# ----------------------------------------------------------------------------
#
# Heurística baseada nos 3 últimos pivôs relevantes formando ombro-cabeça-
# ombro (cabeça claramente mais funda/alta que os dois ombros, ombros com
# profundidade/altura parecida) e no "pescoço" — a linha entre os dois
# topos/fundos intermediários (entre ombro1-cabeça e cabeça-ombro2). Dispara
# só no primeiro rompimento do pescoço, com alvo técnico pela distância
# clássica cabeça↔pescoço projetada a partir do ponto de rompimento.

def _find_oco_estrutura(pivot_extremos, pivot_opostos, lookback_limite, invertido):
    """
    pivot_extremos: pivot_lows (OCOi) ou pivot_highs (OCO clássico) — onde
    procuramos ombro1/cabeça/ombro2.
    pivot_opostos: pivot_highs (OCOi) ou pivot_lows (OCO clássico) — onde
    procuramos os dois pontos do pescoço.
    """
    pts = [p for p in pivot_extremos if p[0] >= lookback_limite]
    if len(pts) < 3:
        return None
    (idx1, p1), (idx2, p2), (idx3, p3) = pts[-3:]

    if invertido:
        if not (p2 < p1 and p2 < p3):
            return None
        prof1 = (p1 - p2) / p1 if p1 > 0 else 0
        prof3 = (p3 - p2) / p3 if p3 > 0 else 0
    else:
        if not (p2 > p1 and p2 > p3):
            return None
        prof1 = (p2 - p1) / p1 if p1 > 0 else 0
        prof3 = (p2 - p3) / p3 if p3 > 0 else 0

    if min(prof1, prof3) < OCO_MIN_HEAD_DEPTH_PCT:
        return None  # cabeça não é claramente mais funda/alta que os ombros

    diff_ombros = abs(p1 - p3) / ((p1 + p3) / 2) if (p1 + p3) > 0 else 1.0
    if diff_ombros > OCO_SHOULDER_SYMMETRY_TOLERANCE:
        return None  # ombros demais assimétricos pra contar como o mesmo padrão

    pescoco1_cands = [q for q in pivot_opostos if idx1 < q[0] < idx2]
    pescoco2_cands = [q for q in pivot_opostos if idx2 < q[0] < idx3]
    if not pescoco1_cands or not pescoco2_cands:
        return None

    if invertido:
        pescoco1 = max(pescoco1_cands, key=lambda q: q[1])
        pescoco2 = max(pescoco2_cands, key=lambda q: q[1])
    else:
        pescoco1 = min(pescoco1_cands, key=lambda q: q[1])
        pescoco2 = min(pescoco2_cands, key=lambda q: q[1])

    return {
        "ombro1": (idx1, p1), "cabeca": (idx2, p2), "ombro2": (idx3, p3),
        "pescoco1": pescoco1, "pescoco2": pescoco2,
    }


def check_oco_pattern(symbol, candles, timeframe_label="4h", pivot_len=PIVOT_LEN):
    """
    Procura um OCOi (Ombro-Cabeça-Ombro invertido, fundo/reversão de alta)
    ou um OCO clássico (topo/reversão de baixa) nos pivôs recentes, e
    dispara quando o pescoço acabou de ser rompido nesta vela. Checa OCOi
    primeiro (padrão mais comum nas lives), depois OCO.
    """
    n = len(candles)
    min_candles = 2 * pivot_len + 30
    if n < min_candles:
        return None
    price_now = candles[-1]["close"]
    price_prev = candles[-2]["close"] if n > 1 else None
    if price_prev is None:
        return None

    pivot_highs, pivot_lows = find_pivots(candles, pivot_len)
    limite = max(0, n - OCO_LOOKBACK)

    for invertido in (True, False):
        extremos = pivot_lows if invertido else pivot_highs
        opostos = pivot_highs if invertido else pivot_lows
        estrutura = _find_oco_estrutura(extremos, opostos, limite, invertido)
        if estrutura is None:
            continue

        idx_p1, val_p1 = estrutura["pescoco1"]
        idx_p2, val_p2 = estrutura["pescoco2"]
        if idx_p2 == idx_p1:
            continue
        slope = (val_p2 - val_p1) / (idx_p2 - idx_p1)
        linha_agora = val_p1 + slope * (n - 1 - idx_p1)
        linha_antes = val_p1 + slope * (n - 2 - idx_p1)
        buffer_ = linha_agora * OCO_NECKLINE_BREAK_BUFFER

        cabeca_idx, cabeca_preco = estrutura["cabeca"]
        pescoco_na_cabeca = val_p1 + slope * (cabeca_idx - idx_p1)
        distancia_alvo = abs(pescoco_na_cabeca - cabeca_preco)

        if invertido:
            rompeu = price_prev <= linha_antes + buffer_ and price_now > linha_agora + buffer_
        else:
            rompeu = price_prev >= linha_antes - buffer_ and price_now < linha_agora - buffer_
        if not rompeu:
            continue

        acao = "COMPRAR" if invertido else "VENDER"
        alvo = (linha_agora + distancia_alvo) if invertido else (linha_agora - distancia_alvo)
        ombro2_idx, ombro2_preco = estrutura["ombro2"]
        if invertido:
            stop = avoid_round_number_stop(ombro2_preco * (1 - OCO_STOP_BUFFER), "compra")
        else:
            stop = avoid_round_number_stop(ombro2_preco * (1 + OCO_STOP_BUFFER), "venda")
        if alvo <= 0 or (invertido and alvo <= price_now) or ((not invertido) and alvo >= price_now):
            continue  # medida clássica não deu um alvo coerente com a direção do sinal

        nome_padrao = "Ombro-Cabeça-Ombro invertido (OCOi)" if invertido else "Ombro-Cabeça-Ombro (OCO)"
        direcao_txt = "alta" if invertido else "baixa"
        ombro1_preco = estrutura["ombro1"][1]

        detalhes = [
            f"Preço agora: {fmt_price(price_now)}",
            f"Ombro 1: {fmt_price(ombro1_preco)} | Cabeça: {fmt_price(cabeca_preco)} | Ombro 2: {fmt_price(ombro2_preco)}",
            f"Pescoço rompido nesta vela em {fmt_price(linha_agora)}",
            f"Alvo (distância cabeça↔pescoço projetada): {fmt_price(alvo)}",
            f"Stop sugerido: {fmt_price(stop)} (além do ombro 2)",
        ]
        checklist = [
            (f"Estrutura de {nome_padrao} identificada nos pivôs recentes do {timeframe_label}", True),
            ("Cabeça claramente mais funda/alta que os dois ombros, ombros com profundidade parecida", True),
            ("Rompimento do pescoço confirmado nesta vela (primeiro fechamento além dele)", True),
        ]
        explicacao = (
            f"Formação de {nome_padrao} no {timeframe_label}: dois ombros parecidos ao redor de uma "
            f"cabeça mais {'funda' if invertido else 'alta'}, com o pescoço (linha entre os dois "
            "topos/fundos intermediários) acabando de ser rompido — padrão clássico de reversão, com "
            "alvo técnico projetado pela distância entre a cabeça e o pescoço."
        )
        aviso = (
            "Padrão identificado de forma automática a partir dos pivôs — vale conferir visualmente, "
            "porque a simetria real dos ombros pode variar mais do que o algoritmo capta."
        )
        return {
            "symbol": symbol, "estilo": "SWING", "acao": acao,
            "titulo": f"Rompimento de pescoço — {nome_padrao}",
            "timeframe": timeframe_label,
            "detalhes": detalhes,
            "checklist": checklist,
            "entry_price": price_now, "target_price": alvo, "stop_price": stop,
            "resumo": f"{nome_padrao} no {timeframe_label}, pescoço rompido em {fmt_price(linha_agora)}.",
            "explicacao": explicacao,
            "aviso": aviso,
        }

    return None


# ----------------------------------------------------------------------------
# FILTROS DE QUALIDADE DE ENTRADA — risco/retorno mínimo e tendência
# majoritária do mercado
#
# Dois critérios que os videos do Diego tratam como obrigatórios antes de
# qualquer entrada valer a pena, e que agora se aplicam a TODO sinal
# COMPRAR/VENDER, não só a um check isolado:
#
#  1) Risco/retorno mínimo de 1:2 — arriscar 1% no stop pra mirar só 1% de
#     lucro no alvo não compensa (o preço não precisa nem acertar metade
#     das vezes pra você perder dinheiro no longo prazo). O alvo técnico
#     tem que valer pelo menos o dobro da distância até o stop.
#  2) Tendência majoritária do mercado — "remar contra a maré" (entrar
#     vendido com o mercado em tendência de alta clara, ou comprado com o
#     mercado em tendência de baixa clara) tende a dar errado mesmo quando
#     o setup técnico local parece certo. A tendência é calculada a partir
#     do BTC no diário (referência do mercado como um todo), uma vez por
#     rodada, e vale pra todas as moedas.
#
# Sinais que não passam num desses dois filtros não são enviados — mas
# viram um diagnóstico explicando o motivo, em vez de simplesmente sumir.
# ----------------------------------------------------------------------------

MIN_REWARD_RISK_RATIO = 2.0   # lucro no alvo tem que ser pelo menos 2x o risco do stop
MARKET_TREND_EMA_FAST = 50
MARKET_TREND_EMA_SLOW = 200
# Semanal tem histórico de sobra (Binance BTCUSDT desde 2017 = ~470 candles
# semanais) pra usar o mesmo par EMA50/EMA200 do diário. Mensal não tem
# histórico suficiente pra EMA200 (só ~100 candles desde 2017), então usa um
# par mais curto — ainda assim reflete a tendência de mais longo prazo.
MARKET_TREND_WEEKLY_EMA_FAST = MARKET_TREND_EMA_FAST
MARKET_TREND_WEEKLY_EMA_SLOW = MARKET_TREND_EMA_SLOW
MARKET_TREND_MONTHLY_EMA_FAST = 6
MARKET_TREND_MONTHLY_EMA_SLOW = 18


def _reward_risk_ok(entry, alvo, stop, min_ratio=MIN_REWARD_RISK_RATIO):
    """(ok: bool, ratio: float|None) — ratio é lucro potencial / risco."""
    if entry is None or alvo is None or stop is None:
        return True, None  # sem dados suficientes pra checar — deixa passar
    risco = abs(entry - stop)
    retorno = abs(alvo - entry)
    if risco <= 0:
        return False, None
    ratio = retorno / risco
    return ratio >= min_ratio, ratio


def _trend_from_candles(candles, ema_fast_period, ema_slow_period):
    """
    Tendência num único tempo gráfico: preço e EMA rápida alinhados acima
    da EMA lenta = "alta"; o inverso = "baixa"; qualquer combinação
    misturada (ou dado insuficiente) = "neutra".
    """
    if len(candles) < ema_slow_period + 5:
        return "neutra"
    closes = [c["close"] for c in candles]
    ema_fast = compute_ema(closes, ema_fast_period)
    ema_slow = compute_ema(closes, ema_slow_period)
    if ema_fast is None or ema_slow is None:
        return "neutra"
    price_now = closes[-1]
    if price_now > ema_fast > ema_slow:
        return "alta"
    if price_now < ema_fast < ema_slow:
        return "baixa"
    return "neutra"


def detect_market_trend(candles_d, candles_w=None, candles_m=None):
    """
    Tendência majoritária do mercado a partir do BTC, cruzando os 3 tempos
    gráficos maiores — diário, semanal e mensal — do jeito que o Diego
    explica nos vídeos: "você nunca vai querer shortar um ativo que está
    numa tendência de alta em todos os tempos gráficos" (e vice-versa).

    O diário é a referência (é o que dá o veredito "alta"/"baixa"); o
    semanal e o mensal são usados pra CONFIRMAR — se um deles discordar do
    diário, o resultado vira "neutra" (o filtro de tendência não trava
    nada quando os tempos gráficos maiores não estão alinhados). Um tempo
    gráfico sem dado suficiente (ex.: mensal muito curto) não derruba o
    alinhamento sozinho — só entra na conta quando realmente deu um
    veredito.

    Compatível com a chamada antiga (só `candles_d`): nesse caso volta a
    ser só a leitura do diário.
    """
    trend_d = _trend_from_candles(candles_d, MARKET_TREND_EMA_FAST, MARKET_TREND_EMA_SLOW)
    if candles_w is None and candles_m is None:
        return trend_d

    trend_w = (_trend_from_candles(candles_w, MARKET_TREND_WEEKLY_EMA_FAST, MARKET_TREND_WEEKLY_EMA_SLOW)
               if candles_w else "neutra")
    trend_m = (_trend_from_candles(candles_m, MARKET_TREND_MONTHLY_EMA_FAST, MARKET_TREND_MONTHLY_EMA_SLOW)
               if candles_m else "neutra")

    if trend_d == "neutra":
        return "neutra"
    votos_com_veredito = [t for t in (trend_w, trend_m) if t != "neutra"]
    if all(v == trend_d for v in votos_com_veredito):
        return trend_d
    return "neutra"


def _alinhado_com_tendencia(acao, market_trend):
    if market_trend == "alta" and acao == "VENDER":
        return False
    if market_trend == "baixa" and acao == "COMPRAR":
        return False
    return True


def aplica_filtros_qualidade(sinais, market_trend, diagnosticos_extra=None):
    """
    Aplica os dois filtros (risco/retorno e tendência) numa lista de sinais
    já disparados. Sinais suprimidos viram diagnóstico (se `diagnosticos_extra`
    for passado) explicando exatamente por que não foram enviados.
    """
    mantidos = []
    for sig in sinais:
        if not _alinhado_com_tendencia(sig["acao"], market_trend):
            if diagnosticos_extra is not None:
                diagnosticos_extra.append({
                    "symbol": sig["symbol"],
                    "tipo": sig["titulo"],
                    "score": 0.01,
                    "texto": (
                        f"Bateu os critérios técnicos de \"{sig['titulo']}\" ({sig['acao']}), mas "
                        f"na direção contrária à tendência majoritária do mercado (BTC em "
                        f"tendência de {market_trend} no diário) — suprimido pra não sugerir "
                        f"operar contra a maré."
                    ),
                })
            continue

        ok, ratio = _reward_risk_ok(sig.get("entry_price"), sig.get("target_price"), sig.get("stop_price"))
        if not ok:
            if diagnosticos_extra is not None:
                ratio_txt = f"1:{ratio:.1f}" if ratio is not None else "indefinido"
                diagnosticos_extra.append({
                    "symbol": sig["symbol"],
                    "tipo": sig["titulo"],
                    "score": 0.01,
                    "texto": (
                        f"Bateu os critérios técnicos de \"{sig['titulo']}\" ({sig['acao']}), mas o "
                        f"risco/retorno ficou em {ratio_txt} — abaixo do mínimo de "
                        f"1:{MIN_REWARD_RISK_RATIO:.0f} pra valer a pena a entrada. Suprimido."
                    ),
                })
            continue

        if ratio is not None:
            sig["reward_risk_ratio"] = ratio
        mantidos.append(sig)
    return mantidos


# ----------------------------------------------------------------------------
# PLANO B — próximo ponto técnico se o stop for rompido
# ----------------------------------------------------------------------------
#
# Ideia: romper o stop não significa necessariamente que a tendência maior
# acabou — às vezes é só o preço procurando um fundo ascendente (ou topo
# descendente) um degrau abaixo (ou acima). Em vez de deixar isso vago
# ("fique de olho no gráfico"), o bot aponta o próximo nível técnico de
# verdade: primeiro no mesmo tempo gráfico do sinal (EMA ou suporte/
# resistência anterior além do stop), depois um "zoom out" pro diário
# (EMA26/EMA50 e o pivô anterior) — pra ver se essa correção maior ainda
# cabe dentro do quadro mais amplo. Não usa RSI pra achar um preço (RSI não
# converte de volta pra um preço futuro com confiança — é o preço que leva
# a um RSI, não o contrário), só cita como referência histórica de contexto.

PLANO_B_EMA_PERIODS_TF = CONFLUENCE_EMA_PERIODS   # mesmo conjunto usado na confluência
PLANO_B_EMA_PERIODS_DIARIO = (26, 50)

# --- Pressão de volume — "o volume é a gasolina do mercado" ---
# Ideia: um suporte/resistência não rompe sozinho, precisa de volume
# empurrando. Se o volume do lado CONTRÁRIO à posição (vendedor pra quem
# comprou perto de um suporte, comprador pra quem vendeu perto de uma
# resistência) está crescendo nos candles mais recentes, o nível tende a
# ceder com mais força ("como faca na manteiga") em vez de aos poucos.
VOLUME_PRESSURE_LOOKBACK = 6      # candles (do timeframe do sinal) considerados
VOLUME_PRESSURE_RECENT_N = 3      # quantos dos mais recentes comparar contra os anteriores
VOLUME_PRESSURE_GROWTH_MULT = 1.15  # 15%+ de aumento já conta como "crescente"


def analisa_pressao_volume(candles, lookback=VOLUME_PRESSURE_LOOKBACK, recent_n=VOLUME_PRESSURE_RECENT_N):
    """
    Compara o volume médio dos candles vermelhos (baixa, close < open) e
    verdes (alta, close > open) nos `recent_n` candles mais recentes contra
    os candles anteriores dentro da janela `lookback` — pra ver se o volume
    de um dos dois lados está crescendo. Devolve
    {"vendedor": {...}, "comprador": {...}} (só as chaves com dado
    suficiente pra comparar) ou None se não tiver candles nem pra formar as
    duas metades da janela.
    """
    if len(candles) < lookback:
        return None
    window = candles[-lookback:]
    recentes = window[-recent_n:]
    anteriores = window[:-recent_n]
    if not anteriores or not recentes:
        return None

    def _vol_medio(cs, lado):
        vols = [c["volume"] for c in cs if (c["close"] < c["open"] if lado == "vendedor" else c["close"] > c["open"])]
        return (sum(vols) / len(vols)) if vols else 0.0

    resultado = {}
    for lado in ("vendedor", "comprador"):
        vol_recente = _vol_medio(recentes, lado)
        vol_anterior = _vol_medio(anteriores, lado)
        if vol_anterior <= 0 or vol_recente <= 0:
            continue
        razao = vol_recente / vol_anterior
        resultado[lado] = {
            "vol_recente": vol_recente, "vol_anterior": vol_anterior,
            "razao": razao, "crescente": razao >= VOLUME_PRESSURE_GROWTH_MULT,
        }
    return resultado or None


def _pressao_volume_texto(acao, candles):
    """
    Se o volume do lado contrário à posição (vendedor pra COMPRAR, comprador
    pra VENDER) estiver crescendo nos candles mais recentes, devolve um
    texto de alerta sobre isso — senão None.
    """
    if acao not in ("COMPRAR", "VENDER"):
        return None
    pressao = analisa_pressao_volume(candles)
    if not pressao:
        return None
    lado_contrario = "vendedor" if acao == "COMPRAR" else "comprador"
    info = pressao.get(lado_contrario)
    if not info or not info["crescente"]:
        return None
    return (
        f"Volume {lado_contrario} crescendo nos últimos candles (~{info['razao']:.1f}x o "
        f"volume médio de {lado_contrario} de antes) — o volume é a 'gasolina' do "
        f"movimento, então isso aumenta a chance do nível ceder com força (tipo faca na "
        f"manteiga) em vez de aos poucos."
    )


def _plano_b_proximo_nivel(candles, ema_periods, acao, stop):
    """
    Nível técnico (EMA ou pivô de suporte/resistência) mais próximo do
    stop, na direção "além" dele (abaixo pra COMPRAR, acima pra VENDER) —
    ou None se não achar nenhum candidato nesses candles.
    """
    if not candles or len(candles) < max((*ema_periods, PIVOT_LEN * 2)) + 5:
        return None
    closes = [c["close"] for c in candles]
    pivot_highs, pivot_lows = find_pivots(candles, PIVOT_LEN)

    candidatos = []
    for periodo in ema_periods:
        ema = compute_ema(closes, periodo)
        if ema is None or ema <= 0:
            continue
        if (acao == "COMPRAR" and ema < stop) or (acao == "VENDER" and ema > stop):
            candidatos.append((abs(stop - ema), f"EMA{periodo} em {fmt_price(ema)}"))

    if acao == "COMPRAR":
        niveis = [p for _, p in pivot_lows if p < stop]
        if niveis:
            nivel = max(niveis)
            candidatos.append((abs(stop - nivel), f"suporte anterior em {fmt_price(nivel)}"))
    else:
        niveis = [p for _, p in pivot_highs if p > stop]
        if niveis:
            nivel = min(niveis)
            candidatos.append((abs(stop - nivel), f"resistência anterior em {fmt_price(nivel)}"))

    if not candidatos:
        return None
    candidatos.sort(key=lambda x: x[0])
    return candidatos[0][1]


def _plano_b_texto(acao, stop, candles_tf, candles_d, pressao_texto=None):
    if acao not in ("COMPRAR", "VENDER") or stop is None:
        return None

    nivel_mesmo_tf = _plano_b_proximo_nivel(candles_tf, PLANO_B_EMA_PERIODS_TF, acao, stop)
    nivel_diario = _plano_b_proximo_nivel(candles_d, PLANO_B_EMA_PERIODS_DIARIO, acao, stop)
    if nivel_mesmo_tf is None and nivel_diario is None:
        return None

    lado = "fundo ascendente" if acao == "COMPRAR" else "topo descendente"
    partes = []
    if nivel_mesmo_tf:
        partes.append(f"no mesmo tempo gráfico, o próximo nível é o {nivel_mesmo_tf}")
    if nivel_diario:
        partes.append(f"dando um zoom out pro diário, o próximo é o {nivel_diario}")

    texto = (
        f"Romper o stop não invalida necessariamente a tendência maior — pode ser só "
        f"o preço procurando um {lado} um degrau abaixo: " + "; e ".join(partes) + ". "
        f"Historicamente essas regiões tendem a coincidir com RSI em sobrevenda/"
        f"sobrecompra no tempo gráfico maior, mas isso é só referência de contexto "
        f"(RSI não dá pra converter de volta num preço calculado)."
    )
    if pressao_texto:
        texto = f"{pressao_texto} Se isso realmente empurrar o preço além do stop: {texto}"
    return texto


def adiciona_plano_b(sinais, candles_tf, candles_d):
    """
    Preenche `sig["plano_b"]` (se conseguir calcular algum nível) pra cada
    sinal COMPRAR/VENDER da lista — usa os candles do timeframe do sinal
    (`candles_tf`, ex.: candles_4h) e os candles diários (`candles_d`) já
    buscados pelo chamador, sem nenhuma chamada de rede extra. Também
    checa a pressão de volume contrária (`_pressao_volume_texto`): quando
    o volume do lado oposto à posição está crescendo, isso entra tanto no
    "aviso" do próprio sinal (é um risco pra entrada agora) quanto no
    início do texto do plano B (deixa claro que o rompimento fica mais
    provável, não é só uma possibilidade remota).
    """
    for sig in sinais:
        try:
            acao = sig.get("acao")
            pressao_texto = _pressao_volume_texto(acao, candles_tf)
            if pressao_texto:
                sig["aviso"] = (sig["aviso"] + " " + pressao_texto) if sig.get("aviso") else pressao_texto
            texto = _plano_b_texto(acao, sig.get("stop_price"), candles_tf, candles_d, pressao_texto=pressao_texto)
            if texto:
                sig["plano_b"] = texto
        except Exception:
            pass
    return sinais


# ----------------------------------------------------------------------------
# SINAL 1 — PULLBACK (swing)
# ----------------------------------------------------------------------------

def check_pullback(symbol, candles):
    if len(candles) < (2 * PIVOT_LEN + 10):
        return None
    pivot_highs, pivot_lows = find_pivots(candles, PIVOT_LEN)
    leg = last_impulse_leg(pivot_highs, pivot_lows)
    if leg is None:
        return None

    price_now = candles[-1]["close"]
    fib_price = fib_level_price(leg, FIB_LEVEL)
    if not price_in_fib_zone(price_now, fib_price):
        return None

    structure_ok, recent_pivots = ascending_or_descending_bottoms(leg, pivot_highs, pivot_lows)
    if not structure_ok:
        return None

    _, _, vol_ratio = volume_status(candles)
    leg_size = abs(leg["end_price"] - leg["start_price"])
    if leg["direction"] == "alta":
        acao = "COMPRAR"
        stop = min(p[1] for p in recent_pivots[-MIN_ASCENDING_BOTTOMS:]) * 0.995
        stop = avoid_round_number_stop(stop, "compra")
        targets = [leg["end_price"], leg["end_price"] + 0.272 * leg_size, leg["end_price"] + 0.618 * leg_size]
        estrutura_txt = "fundos ascendentes"
    else:
        acao = "VENDER"
        stop = max(p[1] for p in recent_pivots[-MIN_ASCENDING_BOTTOMS:]) * 1.005
        stop = avoid_round_number_stop(stop, "venda")
        targets = [leg["end_price"], leg["end_price"] - 0.272 * leg_size, leg["end_price"] - 0.618 * leg_size]
        estrutura_txt = "topos descendentes"

    leg_txt = f"{fmt_price(leg['start_price'])} → {fmt_price(leg['end_price'])}"
    detalhes = [
        f"Preço agora: {fmt_price(price_now)}",
        f"Zona Fibonacci 0.382: {fmt_price(fib_price)}",
        f"Stop sugerido: {fmt_price(stop)}",
        f"Alvos: {' > '.join(fmt_price(t) for t in targets)}",
    ]
    aviso = None
    if vol_ratio is not None and vol_ratio < 1.0:
        aviso = f"Volume atual está {vol_ratio * 100:.0f}% da média — volume abaixo da média enfraquece o setup."

    ema = compute_ema([c["close"] for c in candles])
    checklist = [
        ("Preço na zona de Fibonacci 0.382", True),
        (f"Estrutura de {estrutura_txt} confirmada", True),
        ("Volume no candle atual acima da média", vol_ratio is not None and vol_ratio >= 1.0),
    ]
    if ema is not None:
        segurando = price_now >= ema if leg["direction"] == "alta" else price_now <= ema
        checklist.append((f"Preço {'acima' if leg['direction'] == 'alta' else 'abaixo'} da EMA{EMA_TREND_PERIOD} ({fmt_price(ema)})", segurando))

    resumo = (
        f"Corrigiu ao 0.382 da perna {fmt_price(leg['start_price'])}→{fmt_price(leg['end_price'])} "
        f"({fmt_price(fib_price)}) com {estrutura_txt} e o {INTERVAL} confirmou."
    )
    direcao_txt = "recuando desde a máxima" if leg["direction"] == "alta" else "subindo desde a mínima"
    retomada_txt = (
        "possível retomada da tendência de alta vigente" if leg["direction"] == "alta"
        else "possível continuidade da tendência de baixa vigente"
    )
    explicacao = (
        f"O {_fmt_symbol(symbol)} vem {direcao_txt} de {fmt_price(leg['end_price'])}, testando a região de "
        f"{fmt_price(fib_price)} após a perna {leg_txt}. Corrigiu até a zona de Fibonacci 0.382 dessa perna "
        f"com {estrutura_txt} confirmando no {INTERVAL} — o pullback confirmado sugere {retomada_txt}."
    )

    return {
        "symbol": symbol, "estilo": "SWING", "acao": acao,
        "titulo": f"Pullback ({leg['direction']}, {leg_txt})",
        "timeframe": INTERVAL,
        "detalhes": detalhes,
        "checklist": checklist,
        "entry_price": price_now, "target_price": targets[0], "target_prices": targets, "stop_price": stop,
        "resumo": resumo,
        "explicacao": explicacao,
        "aviso": aviso,
    }


# ----------------------------------------------------------------------------
# SINAL 2 — CLÍMAX DE EXAUSTÃO (qualquer estilo)
# ----------------------------------------------------------------------------

def check_exhaustion_climax(symbol, candles):
    closes = [c["close"] for c in candles]
    rsi = compute_rsi(closes)
    _, _, vol_ratio = volume_status(candles)
    if rsi is None or vol_ratio is None:
        return None
    if vol_ratio < CLIMAX_VOLUME_RATIO:
        return None

    if rsi >= CLIMAX_RSI_HIGH:
        acao, lado = "VENDER", "topo"
    elif rsi <= CLIMAX_RSI_LOW:
        acao, lado = "COMPRAR", "fundo"
    else:
        return None

    price_now = candles[-1]["close"]
    pivot_highs, pivot_lows = find_pivots(candles, PIVOT_LEN)

    alvo = None
    if acao == "VENDER" and pivot_lows:
        alvo = pivot_lows[-1][1]
    elif acao == "COMPRAR" and pivot_highs:
        alvo = pivot_highs[-1][1]
    if alvo is None:
        return None  # sem alvo técnico pra checar risco/retorno, não dá pra confirmar que vale a entrada

    stop = avoid_round_number_stop(price_now * (1.015 if acao == "VENDER" else 0.985), "venda" if acao == "VENDER" else "compra")

    detalhes = [
        f"Preço agora: {fmt_price(price_now)}",
        f"RSI ({INTERVAL}): {rsi:.1f}",
        f"Volume: {vol_ratio:.1f}x a média",
        f"Alvo técnico: {fmt_price(alvo)} (último {'fundo' if acao == 'VENDER' else 'topo'} relevante no {INTERVAL})",
        f"Stop sugerido: {fmt_price(stop)}",
    ]

    checklist = [
        (f"RSI esticado ({rsi:.1f})", True),
        (f"Volume {vol_ratio:.1f}x acima da média", True),
    ]

    return {
        "symbol": symbol, "estilo": "EXAUSTÃO", "acao": acao,
        "titulo": f"Clímax de volume no {lado}",
        "timeframe": INTERVAL,
        "detalhes": detalhes,
        "checklist": checklist,
        "entry_price": price_now, "target_price": alvo, "stop_price": stop,
        "resumo": f"RSI esticado em {rsi:.1f} com volume {vol_ratio:.1f}x a média — clímax de {lado} no {INTERVAL}.",
        "explicacao": (
            f"RSI muito esticado ({rsi:.1f}) combinado com volume {vol_ratio:.1f}x acima "
            f"da média costuma marcar exaustão do movimento — a força predominante "
            f"pode estar perto de se esgotar."
        ),
        "aviso": None,
    }


# ----------------------------------------------------------------------------
# SINAL 3 — PRIMEIRO TOQUE DE RSI EM ZONA DE EXTREMO (5m = day trade rápido,
# 1h = entrada de swing) — "cardápio de trade" do Diego
# ----------------------------------------------------------------------------
#
# Antes esse sinal exigia RSI de 15m E 1h em extremo AO MESMO TEMPO (cascata
# fractal). O vídeo do Diego sobre o "cardápio de trade" deixa claro que na
# prática ele usa isso como DOIS sinais separados, por tempo gráfico: o
# primeiro toque do RSI de 5 minutos em zona de extremo depois de um
# movimento forte é uma janela rápida de repique/correção (day trade); o
# primeiro toque do RSI de 1 hora é o que ele trata como ponto de entrada de
# SWING, porque tende a coincidir com o diário formando uma base de preço
# quando os tempos gráficos maiores estão alinhados na mesma direção — daí
# ele deixar um alarme de RSI em ~31 configurado no 1h.
#
# "Primeiro toque" = o RSI cruzou pra dentro da zona de extremo NESTA vela
# (não estava lá na vela anterior). Isso evita repetir o mesmo sinal vela
# após vela enquanto o RSI continua esticado no mesmo movimento.

def _first_touch_rsi(closes, oversold, overbought):
    """
    (lado, rsi_atual) — lado é "sobrevenda"/"sobrecompra" só quando o RSI
    acabou de ENTRAR na zona de extremo nesta vela (cruzando vindo de fora
    dela na vela anterior). None se não é o primeiro toque (já estava lá
    antes, ou nunca entrou).
    """
    rsi_now = compute_rsi(closes)
    rsi_prev = compute_rsi(closes[:-1]) if len(closes) > 1 else None
    if rsi_now is None or rsi_prev is None:
        return None, rsi_now
    if rsi_now <= oversold and rsi_prev > oversold:
        return "sobrevenda", rsi_now
    if rsi_now >= overbought and rsi_prev < overbought:
        return "sobrecompra", rsi_now
    return None, rsi_now


def _build_scalp_touch_signal(symbol, candles, oversold, overbought, timeframe_label,
                               estilo, titulo_sufixo, stop_pct, explicacao, aviso):
    closes = [c["close"] for c in candles]
    lado, rsi_now = _first_touch_rsi(closes, oversold, overbought)
    if lado is None:
        return None
    acao = "COMPRAR" if lado == "sobrevenda" else "VENDER"
    price_now = candles[-1]["close"]

    pivot_highs, pivot_lows = find_pivots(candles, PIVOT_LEN)
    alvo = None
    if acao == "VENDER" and pivot_lows:
        alvo = pivot_lows[-1][1]
    elif acao == "COMPRAR" and pivot_highs:
        alvo = pivot_highs[-1][1]
    if alvo is None:
        return None  # sem alvo técnico pra checar risco/retorno, não dá pra confirmar que vale a entrada

    stop = avoid_round_number_stop(
        price_now * (1 + stop_pct if acao == "VENDER" else 1 - stop_pct),
        "venda" if acao == "VENDER" else "compra",
    )

    detalhes = [
        f"Preço agora: {fmt_price(price_now)}",
        f"RSI {timeframe_label}: {rsi_now:.1f} (primeiro toque em {lado})",
        f"Alvo técnico: {fmt_price(alvo)} (último {'fundo' if acao == 'VENDER' else 'topo'} no {timeframe_label})",
        f"Stop sugerido: {fmt_price(stop)}",
    ]

    checklist = [
        (f"RSI {timeframe_label} tocou {lado} pela primeira vez nesta vela ({rsi_now:.1f})", True),
    ]

    return {
        "symbol": symbol, "estilo": estilo, "acao": acao,
        "titulo": f"Primeiro toque de {lado} no {timeframe_label} — {titulo_sufixo}",
        "timeframe": timeframe_label,
        "detalhes": detalhes,
        "checklist": checklist,
        "entry_price": price_now, "target_price": alvo, "stop_price": stop,
        "resumo": f"Primeiro toque do RSI de {timeframe_label} em {lado} ({rsi_now:.1f}).",
        "explicacao": explicacao(lado),
        "aviso": aviso,
    }


def check_scalp_5m(symbol, candles_5m):
    return _build_scalp_touch_signal(
        symbol, candles_5m, SCALP_5M_RSI_OVERSOLD, SCALP_5M_RSI_OVERBOUGHT, "5m",
        estilo="SCALP", titulo_sufixo="repique rápido", stop_pct=0.006,
        explicacao=lambda lado: (
            f"Primeiro toque do RSI de 5 minutos em {lado} depois de um movimento "
            "forte — pelo 'cardápio de trade' do Diego, isso costuma abrir uma "
            "janela curta de repique/correção rápida, não uma troca de tendência "
            "maior. Só vale o PRIMEIRO toque: se o RSI já está esticado há várias "
            "velas, a parte rápida do movimento pode já ter passado."
        ),
        aviso="Sinal de day trade muito rápido — janela curta, use gestão de risco apertada.",
    )


def check_scalp_1h(symbol, candles_1h):
    return _build_scalp_touch_signal(
        symbol, candles_1h, SCALP_1H_RSI_OVERSOLD, SCALP_1H_RSI_OVERBOUGHT, "1h",
        estilo="SWING", titulo_sufixo="entrada de swing", stop_pct=0.015,
        explicacao=lambda lado: (
            f"Primeiro toque do RSI de 1 hora em {lado} — diferente do toque de 5m "
            "(que é só repique rápido), esse costuma coincidir com o diário formando "
            "uma base de preço quando os tempos gráficos maiores estão alinhados na "
            "mesma direção, o que dá mais peso pra uma entrada de swing."
        ),
        aviso=None,
    )


def check_scalp_4h(symbol, candles_4h):
    return _build_scalp_touch_signal(
        symbol, candles_4h, SCALP_4H_RSI_OVERSOLD, SCALP_4H_RSI_OVERBOUGHT, "4h",
        estilo="SWING", titulo_sufixo="setup raro de alta convicção", stop_pct=0.03,
        explicacao=lambda lado: (
            f"Primeiro toque do RSI de 4 horas em {lado} — o Diego trata esse "
            "extremo no tempo gráfico de 4h como o setup mais raro e de maior "
            "convicção do 'cardápio de trade': ele aparece bem menos vezes que os "
            "toques de 5m/1h, mas quando aparece costuma marcar um ponto de virada "
            "de maior peso, porque leva várias semanas de movimento pra esticar o "
            "RSI de um tempo gráfico tão largo até esses extremos."
        ),
        aviso="Sinal raro e de alta convicção, mas ainda assim exige stop — "
              "nenhum setup é garantido.",
    )


def _find_last_rsi_touch(candles, oversold, overbought, lookback):
    """
    Varre pra trás (sem contar a vela atual) até `lookback` velas, procurando
    o primeiro-toque de RSI mais recente numa zona de extremo — a mesma
    lógica de `_first_touch_rsi`, mas olhando pro passado em vez de só a
    última vela. Retorna (idx, lado, nivel) do toque mais recente achado —
    `nivel` é o fundo (sobrevenda) ou topo (sobrecompra) daquela vela — ou
    None se não achou nenhum toque dentro da janela.
    """
    n = len(candles)
    if n < 20:
        return None
    closes = [c["close"] for c in candles]
    limite = max(1, n - 1 - lookback)
    for idx in range(n - 2, limite - 1, -1):
        lado, _ = _first_touch_rsi(closes[:idx + 1], oversold, overbought)
        if lado:
            nivel = candles[idx]["low"] if lado == "sobrevenda" else candles[idx]["high"]
            return idx, lado, nivel
    return None


def check_retest_4h(symbol, candles_4h, candles_w=None):
    """
    Segunda etapa do setup de RSI extremo no 4h (SIGNAL 3b — ver
    check_scalp_4h): depois do primeiro toque, o preço costuma dar um
    repique e depois voltar pra RETESTAR o fundo/topo daquela vela — se
    segurar ali (sem romper de verdade), é a base de um possível fundo/topo
    ascendente/descendente num tempo gráfico maior (semanal), com o próprio
    fundo/topo do toque original servindo de referência pro stop. Quando
    `candles_w` vem preenchido, soma fatores extra de confluência semanal
    (EMA12 e Fibonacci 0.382 da última perna semanal) só como contexto —
    não são obrigatórios pra disparar, mas reforçam a leitura quando batem
    junto (o cenário descrito: reteste do 4h encostando na EMA12 semanal e
    perto do 0.382 do último impulso).
    """
    achado = _find_last_rsi_touch(candles_4h, SCALP_4H_RSI_OVERSOLD, SCALP_4H_RSI_OVERBOUGHT, RETEST_4H_LOOKBACK)
    if achado is None:
        return None
    idx, lado, nivel = achado
    if nivel <= 0:
        return None

    velas_depois = candles_4h[idx + 1:]
    if not velas_depois:
        return None
    acao = "COMPRAR" if lado == "sobrevenda" else "VENDER"
    price_now = candles_4h[-1]["close"]

    if acao == "COMPRAR":
        pico_depois = max(c["high"] for c in velas_depois)
        teve_repique = pico_depois >= nivel * (1 + RETEST_4H_MIN_BOUNCE_PCT)
    else:
        fundo_depois = min(c["low"] for c in velas_depois)
        teve_repique = fundo_depois <= nivel * (1 - RETEST_4H_MIN_BOUNCE_PCT)
    if not teve_repique:
        return None  # ainda não teve um repique de verdade — pode ser só ruído

    dist = abs(price_now - nivel) / nivel
    if dist > RETEST_4H_ZONE_TOLERANCE:
        return None  # longe demais do nível original pra contar como reteste

    pivot_highs, pivot_lows = find_pivots(candles_4h, PIVOT_LEN)
    if acao == "COMPRAR":
        stop = avoid_round_number_stop(nivel * (1 - RETEST_4H_STOP_BUFFER), "compra")
        candidatos = [p[1] for p in pivot_highs if p[1] > price_now]
        alvo1 = min(candidatos) if candidatos else None
    else:
        stop = avoid_round_number_stop(nivel * (1 + RETEST_4H_STOP_BUFFER), "venda")
        candidatos = [p[1] for p in pivot_lows if p[1] < price_now]
        alvo1 = max(candidatos) if candidatos else None
    if alvo1 is None:
        return None  # sem alvo técnico no 4h pra checar risco/retorno

    alvos = [alvo1]
    fatores_extra = []
    if candles_w and len(candles_w) >= (2 * PIVOT_LEN + 10):
        ema12_w = compute_ema([c["close"] for c in candles_w], 12)
        if ema12_w is not None and ema12_w > 0:
            dist_ema_w = abs(price_now - ema12_w) / ema12_w
            if dist_ema_w <= CONFLUENCE_EMA_TOLERANCE:
                fatores_extra.append(f"Preço perto da EMA12 no semanal ({fmt_price(ema12_w)})")
        pivot_highs_w, pivot_lows_w = find_pivots(candles_w, PIVOT_LEN)
        leg_w = last_impulse_leg(pivot_highs_w, pivot_lows_w)
        if leg_w is not None:
            fib_w = fib_level_price(leg_w, FIB_LEVEL)
            if price_in_fib_zone(price_now, fib_w, FIB_TOLERANCE):
                fatores_extra.append(f"Preço na zona de Fibonacci {FIB_LEVEL} da última perna semanal ({fmt_price(fib_w)})")
            if acao == "COMPRAR":
                candidatos_w = [p[1] for p in pivot_highs_w if p[1] > alvo1 * 1.01]
                alvo2 = min(candidatos_w) if candidatos_w else None
            else:
                candidatos_w = [p[1] for p in pivot_lows_w if p[1] < alvo1 * 0.99]
                alvo2 = max(candidatos_w) if candidatos_w else None
            if alvo2 is not None:
                alvos.append(alvo2)

    tempo_desde = len(candles_4h) - 1 - idx
    lado_estrutura = "fundo" if acao == "COMPRAR" else "topo"
    nivel_txt = "sobrevenda" if lado == "sobrevenda" else "sobrecompra"

    detalhes = [
        f"Preço agora: {fmt_price(price_now)}",
        f"RSI 4h tocou {nivel_txt} há {tempo_desde} vela(s) — {lado_estrutura} daquela vela em {fmt_price(nivel)}",
        f"Preço voltou a retestar essa região agora ({dist * 100:.1f}% de distância)",
        f"Stop sugerido: {fmt_price(stop)} (logo além do {lado_estrutura} original)",
        f"Alvo{'s' if len(alvos) > 1 else ''}: {' > '.join(fmt_price(a) for a in alvos)}",
    ]
    detalhes.extend(f"  • {f}" for f in fatores_extra)

    checklist = [
        (f"RSI 4h fez primeiro toque de {nivel_txt} há {tempo_desde} vela(s)", True),
        ("Repique de verdade depois do toque (não é só ruído)", True),
        (f"Preço retestando o {lado_estrutura} original sem romper de verdade", True),
    ]
    checklist.extend((f, True) for f in fatores_extra)

    extra_txt = ""
    if fatores_extra:
        extra_txt = " Reforçando ainda mais: " + "; ".join(fatores_extra) + "."

    explicacao = (
        f"Depois do primeiro toque do RSI de 4h em {nivel_txt}, o {_fmt_symbol(symbol)} deu um repique "
        f"e agora está retestando o {lado_estrutura} daquela vela ({fmt_price(nivel)}) sem romper de "
        "verdade — é o tipo de reteste que, se segurar, pode marcar a base de um "
        f"{'fundo' if acao == 'COMPRAR' else 'topo'} ascendente/descendente num tempo gráfico maior "
        f"(semanal), com o próprio nível do toque original servindo de referência pro stop.{extra_txt}"
    )
    aviso = (
        "Reteste ainda pode romper o nível original — se isso acontecer, o cenário de base muda "
        "e o stop deveria ser respeitado."
    )

    return {
        "symbol": symbol, "estilo": "SWING", "acao": acao,
        "titulo": f"Reteste do {lado_estrutura} após 1º toque de RSI no 4h",
        "timeframe": "4h" + (" + 1w" if len(alvos) > 1 or fatores_extra else ""),
        "detalhes": detalhes,
        "checklist": checklist,
        "entry_price": price_now, "target_price": alvos[0], "target_prices": alvos, "stop_price": stop,
        "resumo": f"Reteste do {lado_estrutura} de {fmt_price(nivel)} após o 1º toque de RSI no 4h, {tempo_desde} vela(s) atrás.",
        "explicacao": explicacao,
        "aviso": aviso,
    }


# ----------------------------------------------------------------------------
# SINAL 4 — BOTTOM FISHING (posição)
# ----------------------------------------------------------------------------

def _tier_note(tier):
    if tier == "pequeno":
        return (
            "Moeda de menor volume dentro do watchlist (proxy de porte menor) — "
            "menos dinheiro nela costuma significar mais facilidade pra mover o "
            "preço, pra cima ou pra baixo."
        )
    return None


def check_bottom_fishing(symbol, candles_d, candles_w, tier=None):
    if len(candles_w) < 20 or len(candles_d) < 20:
        return None
    ath = max(c["high"] for c in candles_w)
    price_now = candles_d[-1]["close"]
    drawdown = (ath - price_now) / ath
    if drawdown < BOTTOM_FISHING_MIN_DRAWDOWN:
        return None

    pivot_highs_d, pivot_lows_d = find_pivots(candles_d, BOTTOM_FISHING_PIVOT_LEN)
    if len(pivot_lows_d) < BOTTOM_FISHING_MIN_ASCENDING:
        return None
    recent_lows = pivot_lows_d[-BOTTOM_FISHING_MIN_ASCENDING:]
    prices = [p[1] for p in recent_lows]
    ascending = all(prices[i] < prices[i + 1] for i in range(len(prices) - 1))
    if not ascending:
        return None

    stop = avoid_round_number_stop(min(prices) * 0.97, "compra")
    entry_low, entry_high = min(prices), max(price_now, max(prices))
    alvo = next((p for _, p in reversed(pivot_highs_d) if p > price_now), ath)

    detalhes = [
        f"Preço agora: {fmt_price(price_now)}",
        f"Máxima histórica: {fmt_price(ath)}  ({drawdown * 100:.0f}% abaixo)",
        f"Zona de entrada sugerida: {fmt_price(entry_low)} – {fmt_price(entry_high)}",
        f"Alvo técnico: {fmt_price(alvo)} (próxima resistência relevante)",
        f"Stop sugerido: {fmt_price(stop)}",
    ]
    if tier:
        detalhes.append(f"Porte (por volume): {tier}")

    aviso = (
        "Sinal de posição/longo prazo: drawdowns grandes podem continuar por "
        "muito tempo antes de reverter de verdade — confirme com o contexto "
        "macro (BTC, dominância) antes de posicionar tamanho relevante."
    )
    tier_note = _tier_note(tier)
    if tier_note:
        aviso = tier_note + " " + aviso

    checklist = [
        (f"Drawdown de {drawdown * 100:.0f}% da máxima histórica (mín. {BOTTOM_FISHING_MIN_DRAWDOWN * 100:.0f}%)", True),
        ("Fundos ascendentes confirmados no diário", True),
    ]

    return {
        "symbol": symbol, "estilo": "POSIÇÃO", "acao": "COMPRAR",
        "titulo": "Bottom fishing — fundo histórico",
        "timeframe": "1w (máxima) + 1d (estrutura)",
        "detalhes": detalhes,
        "checklist": checklist,
        "entry_price": price_now, "target_price": alvo, "stop_price": stop,
        "entry_zone": (entry_low, entry_high),
        "resumo": f"{drawdown * 100:.0f}% abaixo da máxima histórica ({fmt_price(ath)}) com fundos ascendentes confirmando no diário.",
        "explicacao": (
            f"Moeda {drawdown * 100:.0f}% abaixo da máxima histórica e formando fundos "
            f"ascendentes no diário — indício de que uma base de longo prazo pode "
            f"estar se formando, no espírito do \"bottom fishing\" (stop sempre "
            f"abaixo da base, nunca no meio do range)."
        ),
        "aviso": aviso,
    }


# ----------------------------------------------------------------------------
# SINAL 4b — REVERSÃO DE TENDÊNCIA COM BASE (posição/swing, drawdown moderado)
# ----------------------------------------------------------------------------

def check_light_reversal(symbol, candles_d, tier=None):
    """
    Versão mais leve do bottom fishing: em vez de exigir drawdown profundo
    desde a MÁXIMA HISTÓRICA, olha só os últimos ~180 dias e procura uma
    correção moderada (30%-55%) desde o topo desse período, com fundos
    ascendentes confirmando — pra pegar reversões de médio prazo, não só
    quedas históricas extremas.
    """
    lookback = min(len(candles_d), LIGHT_REVERSAL_LOOKBACK_DAYS)
    if lookback < 30:
        return None
    window = candles_d[-lookback:]

    pivot_highs, pivot_lows = find_pivots(window, LIGHT_REVERSAL_PIVOT_LEN)
    if not pivot_highs:
        return None
    swing_high_idx, swing_high_price = max(pivot_highs, key=lambda p: p[1])

    price_now = window[-1]["close"]
    drawdown = (swing_high_price - price_now) / swing_high_price
    if drawdown < LIGHT_REVERSAL_MIN_DRAWDOWN or drawdown >= LIGHT_REVERSAL_MAX_DRAWDOWN:
        return None

    recent_lows = [p for p in pivot_lows if p[0] > swing_high_idx]
    if len(recent_lows) < BOTTOM_FISHING_MIN_ASCENDING:
        return None
    recent_lows = recent_lows[-BOTTOM_FISHING_MIN_ASCENDING:]
    prices = [p[1] for p in recent_lows]
    ascending = all(prices[i] < prices[i + 1] for i in range(len(prices) - 1))
    if not ascending:
        return None

    stop = avoid_round_number_stop(min(prices) * 0.97, "compra")
    entry_low, entry_high = min(prices), max(price_now, max(prices))
    alvo = swing_high_price

    detalhes = [
        f"Preço agora: {fmt_price(price_now)}",
        f"Topo dos últimos {lookback}d: {fmt_price(swing_high_price)}  ({drawdown * 100:.0f}% abaixo)",
        f"Zona de entrada sugerida: {fmt_price(entry_low)} – {fmt_price(entry_high)}",
        f"Alvo técnico: {fmt_price(alvo)} (topo que iniciou a correção)",
        f"Stop sugerido: {fmt_price(stop)}",
    ]
    if tier:
        detalhes.append(f"Porte (por volume): {tier}")

    aviso = _tier_note(tier)

    checklist = [
        (f"Correção de {drawdown * 100:.0f}% desde o topo do período (faixa "
         f"{LIGHT_REVERSAL_MIN_DRAWDOWN * 100:.0f}%-{LIGHT_REVERSAL_MAX_DRAWDOWN * 100:.0f}%)", True),
        ("Fundos ascendentes confirmados no diário", True),
    ]

    return {
        "symbol": symbol, "estilo": "SWING/POSIÇÃO", "acao": "COMPRAR",
        "titulo": "Reversão de tendência com base",
        "timeframe": f"1d ({lookback}d)",
        "detalhes": detalhes,
        "checklist": checklist,
        "entry_price": price_now, "target_price": alvo, "stop_price": stop,
        "entry_zone": (entry_low, entry_high),
        "resumo": f"Correção de {drawdown * 100:.0f}% desde o topo dos últimos {lookback}d ({fmt_price(swing_high_price)}) com fundos ascendentes formando base.",
        "explicacao": (
            f"Correção de {drawdown * 100:.0f}% desde o topo dos últimos {lookback} dias, "
            f"com fundos ascendentes formando uma base nítida — padrão de reversão "
            f"de tendência de médio prazo, saindo de baixa e migrando pra alta."
        ),
        "aviso": aviso,
    }


# ----------------------------------------------------------------------------
# SINAL 5 — DOMINÂNCIA BTC / ALTSEASON (uma vez por rodada, proxy)
# ----------------------------------------------------------------------------

def pct_return(candles_d, days=DOMINANCE_LOOKBACK_DAYS):
    if len(candles_d) < days + 1:
        return None
    start = candles_d[-(days + 1)]["close"]
    end = candles_d[-1]["close"]
    if start == 0:
        return None
    return (end - start) / start * 100


def compute_market_returns(watchlist):
    """
    Calcula o retorno do BTC e a média de retorno das alts do watchlist nos
    últimos DOMINANCE_LOOKBACK_DAYS dias. Centralizado aqui porque tanto o
    check de dominância quanto o termômetro de fase de ciclo (mais abaixo)
    precisam desses dois números, e assim evita buscar tudo de novo duas vezes.
    """
    btc_candles = fetch_klines("BTCUSDT", "1d", DOMINANCE_LOOKBACK_DAYS + 5)
    btc_return = pct_return(btc_candles)

    alt_returns = []
    for symbol in watchlist:
        if symbol == "BTCUSDT":
            continue
        try:
            c = fetch_klines(symbol, "1d", DOMINANCE_LOOKBACK_DAYS + 5)
            r = pct_return(c)
            if r is not None:
                alt_returns.append(r)
        except Exception:
            continue
    avg_alt_return = sum(alt_returns) / len(alt_returns) if alt_returns else None

    return btc_return, avg_alt_return


def check_dominance_altseason(btc_return, avg_alt_return):
    if btc_return is None or avg_alt_return is None:
        return None
    diff = btc_return - avg_alt_return

    if abs(diff) < DOMINANCE_DIVERGENCE_PP:
        return None

    if diff > 0:
        titulo = "Dominância do BTC em alta"
        explicacao = (
            f"BTC subiu {btc_return:.1f}% contra uma média de {avg_alt_return:.1f}% do "
            f"watchlist de altcoins nos últimos {DOMINANCE_LOOKBACK_DAYS} dias — BTC mais "
            f"forte que as alts sugere dominância subindo, cenário menos favorável pra "
            f"abrir novas posições de swing em altcoins."
        )
    else:
        titulo = "Altcoins mais fortes que o BTC (possível altseason)"
        explicacao = (
            f"O watchlist de altcoins subiu em média {avg_alt_return:.1f}% contra "
            f"{btc_return:.1f}% do BTC nos últimos {DOMINANCE_LOOKBACK_DAYS} dias — "
            f"alts mais fortes que o BTC sugere dominância caindo, sinal-chave de "
            f"rotação de capital pra altseason."
        )

    return {
        "symbol": "MERCADO", "estilo": "MACRO", "acao": "OBSERVAR",
        "titulo": titulo,
        "timeframe": f"1d, {DOMINANCE_LOOKBACK_DAYS}d",
        "detalhes": [
            f"Retorno BTC ({DOMINANCE_LOOKBACK_DAYS}d): {btc_return:+.1f}%",
            f"Retorno médio das alts ({DOMINANCE_LOOKBACK_DAYS}d): {avg_alt_return:+.1f}%",
        ],
        "explicacao": explicacao,
        "aviso": "Proxy baseado em performance relativa do watchlist, não é o índice oficial de dominância (BTC.D).",
    }


# ----------------------------------------------------------------------------
# SINAL 6 — REVERSÃO POR ROMPIMENTO FALHO (swing)
# ----------------------------------------------------------------------------

def check_failed_breakout_reversal(symbol, candles):
    """
    Procura por: (1) um suporte/resistência relevante já confirmado por pivô,
    (2) um rompimento recente desse nível que NÃO teve continuidade — o
    preço já voltou pro lado de dentro —, e (3) volume acima da média no
    rompimento ou na recuperação, confirmando força real por trás da
    reversão (e não só ruído).
    """
    if len(candles) < (2 * PIVOT_LEN + FAILED_BREAK_LOOKBACK + 5):
        return None
    pivot_highs, pivot_lows = find_pivots(candles, PIVOT_LEN)
    price_now = candles[-1]["close"]
    _, avg_vol, _ = volume_status(candles)
    if not avg_vol:
        return None

    recent_window = candles[-FAILED_BREAK_LOOKBACK:]

    def _strong_volume():
        return any((c["volume"] / avg_vol) >= FAILED_BREAK_VOLUME_RATIO for c in recent_window)

    # --- caso de alta: rompeu um SUPORTE mas não teve continuidade de queda
    # e já recuperou de volta pra cima dele, com volume forte ---
    if pivot_lows:
        ref_idx, ref_price = pivot_lows[-1]
        if ref_idx < len(candles) - FAILED_BREAK_LOOKBACK:
            broke = any(c["low"] < ref_price * (1 - FAILED_BREAK_PENETRATION_PCT) for c in recent_window)
            recovered = price_now > ref_price * (1 + FAILED_BREAK_RECOVERY_PCT)
            if broke and recovered and _strong_volume():
                stop = avoid_round_number_stop(ref_price * 0.99, "compra")
                penetration_low = min(c["low"] for c in recent_window)
                alvo = ref_price + (ref_price - penetration_low)
                return {
                    "symbol": symbol, "estilo": "SWING", "acao": "COMPRAR",
                    "titulo": "Reversão por rompimento falho (suporte)",
                    "timeframe": INTERVAL,
                    "detalhes": [
                        f"Preço agora: {fmt_price(price_now)}",
                        f"Suporte rompido e recuperado: {fmt_price(ref_price)}",
                        f"Alvo técnico (movimento medido): {fmt_price(alvo)}",
                        f"Stop sugerido: {fmt_price(stop)}",
                    ],
                    "checklist": [
                        ("Suporte relevante identificado por pivô", True),
                        ("Rompimento do suporte sem continuidade de queda", True),
                        ("Recuperação de volta pra cima do nível", True),
                        (f"Volume forte no rompimento/recuperação (≥{FAILED_BREAK_VOLUME_RATIO}x)", True),
                    ],
                    "entry_price": price_now, "target_price": alvo, "stop_price": stop,
                    "resumo": f"Rompeu o suporte em {fmt_price(ref_price)} sem continuidade e já recuperou, com volume forte.",
                    "explicacao": (
                        f"O preço rompeu o suporte em {fmt_price(ref_price)} mas não teve "
                        f"continuidade de queda — já recuperou de volta pra cima do "
                        f"nível com volume acima da média. Rompimento sem seguimento "
                        f"tende a invalidar o movimento de baixa e favorecer uma "
                        f"reversão de alta."
                    ),
                    "aviso": (
                        "Padrão de exaustão/reversão: cuidado se o preço voltar a "
                        "perder esse nível com volume — isso invalidaria a reversão."
                    ),
                }

    # --- caso de baixa: rompeu uma RESISTÊNCIA mas não teve continuidade de
    # alta e já devolveu pra dentro dela, com volume forte ---
    if pivot_highs:
        ref_idx, ref_price = pivot_highs[-1]
        if ref_idx < len(candles) - FAILED_BREAK_LOOKBACK:
            broke = any(c["high"] > ref_price * (1 + FAILED_BREAK_PENETRATION_PCT) for c in recent_window)
            recovered = price_now < ref_price * (1 - FAILED_BREAK_RECOVERY_PCT)
            if broke and recovered and _strong_volume():
                stop = avoid_round_number_stop(ref_price * 1.01, "venda")
                penetration_high = max(c["high"] for c in recent_window)
                alvo = ref_price - (penetration_high - ref_price)
                return {
                    "symbol": symbol, "estilo": "SWING", "acao": "VENDER",
                    "titulo": "Reversão por rompimento falho (resistência)",
                    "timeframe": INTERVAL,
                    "detalhes": [
                        f"Preço agora: {fmt_price(price_now)}",
                        f"Resistência rompida e devolvida: {fmt_price(ref_price)}",
                        f"Alvo técnico (movimento medido): {fmt_price(alvo)}",
                        f"Stop sugerido: {fmt_price(stop)}",
                    ],
                    "checklist": [
                        ("Resistência relevante identificada por pivô", True),
                        ("Rompimento da resistência sem continuidade de alta", True),
                        ("Devolução de volta pra dentro do nível", True),
                        (f"Volume forte no rompimento/devolução (≥{FAILED_BREAK_VOLUME_RATIO}x)", True),
                    ],
                    "entry_price": price_now, "target_price": alvo, "stop_price": stop,
                    "resumo": f"Rompeu a resistência em {fmt_price(ref_price)} sem continuidade e já devolveu, com volume forte.",
                    "explicacao": (
                        f"O preço rompeu a resistência em {fmt_price(ref_price)} mas não teve "
                        f"continuidade de alta — já devolveu pra dentro do nível com "
                        f"volume acima da média. Rompimento sem seguimento tende a "
                        f"invalidar o movimento de alta e favorecer uma reversão de "
                        f"baixa."
                    ),
                    "aviso": (
                        "Padrão de exaustão/reversão: cuidado se o preço voltar a "
                        "romper esse nível com volume — isso invalidaria a reversão."
                    ),
                }

    return None


# ----------------------------------------------------------------------------
# SINAL 7 — TERMÔMETRO DE FASE DE CICLO (mania de memecoin, mercado)
# ----------------------------------------------------------------------------

def check_cycle_phase(btc_return, avg_alt_return):
    """
    Camada extra sobre a comparação BTC x alts já feita na dominância: mede
    a performance média de um conjunto de memecoins conhecidas nos últimos
    dias e compara com o BTC e com o watchlist de alts "normais". A ideia,
    tirada de uma das lives, é que um bull market roda em ordem: primeiro
    BTC/ETH lideram, depois o capital rotaciona pras alts de maior porte, e
    só then pras memecoins puramente especulativas — memecoins disparando
    muito à frente dos dois outros grupos ao mesmo tempo tende a marcar uma
    fase mais avançada/exagerada do movimento, não o início dele.
    """
    meme_returns = []
    for symbol in MEME_COIN_SYMBOLS:
        try:
            c = fetch_klines(symbol, "1d", CYCLE_LOOKBACK_DAYS + 5)
            r = pct_return(c, days=CYCLE_LOOKBACK_DAYS)
            if r is not None:
                meme_returns.append(r)
        except Exception:
            continue
    if not meme_returns or btc_return is None or avg_alt_return is None:
        return None

    avg_meme_return = sum(meme_returns) / len(meme_returns)
    diff_vs_btc = avg_meme_return - btc_return
    diff_vs_alts = avg_meme_return - avg_alt_return

    if diff_vs_btc < MEME_MANIA_DIVERGENCE_PP or diff_vs_alts < MEME_MANIA_DIVERGENCE_PP:
        return None

    return {
        "symbol": "MERCADO", "estilo": "MACRO", "acao": "OBSERVAR",
        "titulo": "Termômetro de ciclo — mania de memecoin",
        "timeframe": f"1d, {CYCLE_LOOKBACK_DAYS}d",
        "detalhes": [
            f"Retorno médio memecoins monitoradas ({CYCLE_LOOKBACK_DAYS}d): {avg_meme_return:+.1f}%",
            f"Retorno BTC ({CYCLE_LOOKBACK_DAYS}d): {btc_return:+.1f}%",
            f"Retorno médio das alts do watchlist ({CYCLE_LOOKBACK_DAYS}d): {avg_alt_return:+.1f}%",
        ],
        "explicacao": (
            f"Memecoins subindo bem mais ({avg_meme_return:+.1f}%) que o BTC e que as "
            f"alts do watchlist ao mesmo tempo costuma marcar uma fase mais avançada "
            f"e especulativa do movimento de alta — o capital já passou de BTC pras "
            f"alts principais e agora tá indo pra ativos de puro hype, o que "
            f"historicamente acontece mais perto do fim de um ciclo do que no início."
        ),
        "aviso": (
            "Não é sinal de topo garantido, é um alerta de fase de ciclo pra aumentar "
            "a cautela (ex.: realizar parciais, apertar stops) — não uma recomendação "
            "de sair do mercado."
        ),
    }


# ----------------------------------------------------------------------------
# SINAL 8 — PADRÃO DE EQUILÍBRIO (swing curto)
# ----------------------------------------------------------------------------

def _range_consolidation_duration(candles, range_high, range_low):
    """
    Quantos candles, no total (incluindo os RANGE_LOOKBACK que definiram o
    range), o preço já passou contido nessa mesma faixa — olhando pra trás
    além da janela original, até um teto de RANGE_BREAKOUT_MAX_LOOKBACK_MULT
    x RANGE_LOOKBACK. Uma tolerância pequena evita cortar a contagem por um
    único pavio isolado que escapou da faixa por muito pouco.
    """
    tol = RANGE_MAX_PCT * RANGE_BREAKOUT_EDGE_TOLERANCE
    high_tol = range_high * (1 + tol)
    low_tol = range_low * (1 - tol)
    max_extra = RANGE_LOOKBACK * (RANGE_BREAKOUT_MAX_LOOKBACK_MULT - 1)

    extra = 0
    idx = len(candles) - RANGE_LOOKBACK - 1
    while extra < max_extra and idx >= 0:
        c = candles[idx]
        if c["high"] <= high_tol and c["low"] >= low_tol:
            extra += 1
            idx -= 1
        else:
            break
    return RANGE_LOOKBACK + extra


def check_range_market(symbol, candles):
    """
    "O que fazer quando o mercado fica parado": em vez de precisar de uma
    tendência clara, procura uma faixa estreita (RANGE_MAX_PCT de amplitude)
    nos últimos RANGE_LOOKBACK candles de 4h. Se o preço está perto de uma
    das bordas dessa faixa, sugere operar o próprio range — comprar perto do
    fundo mirando o topo, ou vender perto do topo mirando o fundo — com stop
    logo fora da faixa. Só dispara perto das bordas: no meio do range não
    tem um ponto de entrada com risco/retorno bom.

    O alvo não é sempre só a borda oposta: segue o "padrão de equilíbrio" do
    Diego — quanto mais tempo o preço ficou realmente lateralizado nessa
    faixa (olhando além da janela mínima), maior o impulso esperado no
    rompimento, e o alvo estende além da borda oposta proporcionalmente
    (capado, pra não virar alvo fantasioso numa consolidação muito longa).
    """
    if len(candles) < RANGE_LOOKBACK:
        return None
    window = candles[-RANGE_LOOKBACK:]
    range_high = max(c["high"] for c in window)
    range_low = min(c["low"] for c in window)
    if range_low <= 0 or range_high <= range_low:
        return None
    range_pct = (range_high - range_low) / range_low
    if range_pct > RANGE_MAX_PCT:
        return None

    price_now = candles[-1]["close"]
    posicao = (price_now - range_low) / (range_high - range_low)

    duracao = _range_consolidation_duration(candles, range_high, range_low)
    duracao_mult = duracao / RANGE_LOOKBACK
    extensao_mult = min(duracao_mult - 1, RANGE_BREAKOUT_EXTENSION_CAP)
    range_height = range_high - range_low
    alvo_extra = range_height * extensao_mult
    range_longo = duracao > RANGE_LOOKBACK  # achou consolidação além da janela mínima

    if posicao <= RANGE_EDGE_ZONE_PCT:
        acao, lado_txt = "COMPRAR", "perto do fundo do padrão de equilíbrio"
        stop = avoid_round_number_stop(range_low * 0.995, "compra")
        alvo = range_high + alvo_extra
    elif posicao >= (1 - RANGE_EDGE_ZONE_PCT):
        acao, lado_txt = "VENDER", "perto do topo do padrão de equilíbrio"
        stop = avoid_round_number_stop(range_high * 1.005, "venda")
        alvo = range_low - alvo_extra
    else:
        return None  # parado, mas no meio da faixa — sem ponto de entrada bom agora

    checklist = [
        (f"Padrão de equilíbrio nos últimos {RANGE_LOOKBACK} candles ({range_pct * 100:.1f}% ≤ {RANGE_MAX_PCT * 100:.0f}%)", True),
        (f"Preço {lado_txt}", True),
    ]
    if range_longo:
        checklist.append((f"Lateralizado há mais tempo ({duracao} candles, {duracao_mult:.1f}x a janela mínima) — alvo estendido", True))

    titulo = ("Padrão de equilíbrio — rompimento longo" if range_longo
              else "Padrão de equilíbrio — operação de range")
    alvo_txt = (f"Alvo (topo do padrão + extensão por consolidação longa): {fmt_price(alvo)}" if range_longo
                else f"Alvo (lado oposto do padrão de equilíbrio): {fmt_price(alvo)}")

    if acao == "COMPRAR":
        entrada_desc = (
            f"o preço está no fundo do padrão de equilíbrio — a estratégia aqui é entrar "
            f"com o stop logo abaixo do último fundo formado ({fmt_price(range_low)}) e "
            f"mirar o topo do padrão ({fmt_price(range_high)})"
        )
    else:
        entrada_desc = (
            f"o preço está no topo do padrão de equilíbrio — a estratégia aqui é entrar "
            f"com o stop logo acima do último topo formado ({fmt_price(range_high)}) e "
            f"mirar o fundo do padrão ({fmt_price(range_low)})"
        )

    return {
        "symbol": symbol, "estilo": "RANGE", "acao": acao,
        "titulo": titulo,
        "timeframe": INTERVAL,
        "detalhes": [
            f"Preço agora: {fmt_price(price_now)} ({lado_txt})",
            f"Range dos últimos {RANGE_LOOKBACK} candles: {fmt_price(range_low)} – {fmt_price(range_high)} "
            f"({range_pct * 100:.1f}% de amplitude)",
            f"Tempo lateralizado: {duracao} candles ({duracao_mult:.1f}x a janela mínima de {RANGE_LOOKBACK})",
            alvo_txt,
            f"Stop sugerido: {fmt_price(stop)}",
        ],
        "checklist": checklist,
        "entry_price": price_now, "target_price": alvo, "stop_price": stop,
        "resumo": (
            f"Padrão de equilíbrio ({range_pct * 100:.1f}% de amplitude, {duracao} candles), "
            f"preço {lado_txt}."
        ),
        "explicacao": (
            f"Isso é o que o Diego chama de padrão de equilíbrio: em vez de tendência, o "
            f"preço fica alternando entre fundo e topo dentro da mesma faixa "
            f"({fmt_price(range_low)}–{fmt_price(range_high)}, {range_pct * 100:.1f}% de "
            f"amplitude) há {duracao} candles — fundo, topo, fundo ascendente, topo "
            f"descendente, sem conseguir romper de vez pra nenhum lado ainda. A leitura "
            f"dele pra esse cenário é direta: {entrada_desc}. Se o preço romper com força "
            f"pra fora da faixa, deixou de ser equilíbrio — e, pela regra dele, quanto mais "
            f"tempo o preço ficou lateralizado, maior tende a ser o impulso desse rompimento."
            + (f" Como essa consolidação já dura bem mais que o mínimo "
               f"({duracao_mult:.1f}x), o alvo já vem estendido {extensao_mult:.1f}x a "
               f"altura do padrão além da borda oposta."
               if range_longo else "")
        ),
        "aviso": (
            "Setup de padrão de equilíbrio tende a ter alvo e risco menores que um movimento de "
            "tendência — considere reduzir o tamanho da posição em relação a um "
            "swing/pullback de verdade, e saia se o preço romper a faixa com força "
            "(aí deixou de ser um padrão de equilíbrio)."
        ),
    }


# ----------------------------------------------------------------------------
# SINAL 9 — CONFLUÊNCIA MULTI-INDICADOR (mais de um timeframe)
# ----------------------------------------------------------------------------

def _ema_hits(closes, price_ref, periods=CONFLUENCE_EMA_PERIODS, tol=CONFLUENCE_EMA_TOLERANCE):
    """Devolve as EMAs (de `periods`) que o preço está a até `tol` de distância."""
    hits = []
    for periodo in periods:
        ema = compute_ema(closes, periodo)
        if ema is None:
            continue
        dist = (price_ref - ema) / ema
        if abs(dist) <= tol:
            hits.append((periodo, ema, dist))
    return hits


def _recent_level_hit(candles, price_ref, direction, lookback=CONFLUENCE_RECENT_LOOKBACK, tol=CONFLUENCE_RECENT_TOLERANCE):
    """
    Suporte/resistência "recente": fundo (direção 'alta') ou topo (direção
    'baixa') dos últimos `lookback` candles. Diferente do fib/EMA, isso
    pega uma zona que o preço acabou de tocar mesmo que ainda não tenha
    virado um pivô confirmado (pivô sempre atrasa, porque exige velas de
    confirmação dos dois lados) — é o tipo de "suporte no 4h em X" que dá
    pra ver olhando o gráfico na hora, antes do pivô confirmar.
    """
    if len(candles) < lookback:
        return None
    window = candles[-lookback:]
    nivel = min(c["low"] for c in window) if direction == "alta" else max(c["high"] for c in window)
    if nivel <= 0:
        return None
    dist = abs(price_ref - nivel) / nivel
    return nivel if dist <= tol else None


def _confluence_fatores(candles_4h, candles_15m, candles_1h, candles_5m=None):
    """
    Monta a lista de fatores técnicos alinhados (fibonacci de mais de um
    nível, EMAs de mais de um período em três timeframes, suporte/
    resistência recente no 4h e no 1h, e RSI em sobrevenda/sobrecompra no
    15m, no 1h e — quando disponível — no 5m) na direção sugerida pela
    última perna de 4h. Compartilhado pelo sinal de verdade e pelo
    diagnóstico (near-miss) — só muda o corte de quantos fatores contam
    como "bastante".
    """
    if len(candles_4h) < (2 * PIVOT_LEN + 10) or not candles_15m or not candles_1h:
        return None
    pivot_highs, pivot_lows = find_pivots(candles_4h, PIVOT_LEN)
    leg = last_impulse_leg(pivot_highs, pivot_lows)
    if leg is None:
        return None

    price_now = candles_4h[-1]["close"]
    price_15m = candles_15m[-1]["close"]
    price_1h = candles_1h[-1]["close"]
    rsi_15m = compute_rsi([c["close"] for c in candles_15m])
    rsi_1h = compute_rsi([c["close"] for c in candles_1h])
    rsi_5m = compute_rsi([c["close"] for c in candles_5m]) if candles_5m else None

    fatores = []
    for level in CONFLUENCE_FIB_LEVELS:
        fib_price = fib_level_price(leg, level)
        if price_in_fib_zone(price_now, fib_price, CONFLUENCE_FIB_TOLERANCE):
            fatores.append(f"Preço na zona de Fibonacci {level} da perna de 4h ({fmt_price(fib_price)})")
            break  # um nível já basta como fator — não soma os 3 juntos

    for periodo, ema, dist in _ema_hits([c["close"] for c in candles_4h], price_now):
        fatores.append(f"Preço a {abs(dist) * 100:.1f}% da EMA{periodo} no 4h ({fmt_price(ema)})")

    for periodo, ema, dist in _ema_hits([c["close"] for c in candles_15m], price_15m):
        fatores.append(f"Preço a {abs(dist) * 100:.1f}% da EMA{periodo} no 15m ({fmt_price(ema)})")

    nivel_4h = _recent_level_hit(candles_4h, price_now, leg["direction"])
    if nivel_4h is not None:
        rotulo = "suporte" if leg["direction"] == "alta" else "resistência"
        fatores.append(f"Preço perto do {rotulo} dos últimos {CONFLUENCE_RECENT_LOOKBACK} candles no 4h ({fmt_price(nivel_4h)})")

    nivel_1h = _recent_level_hit(candles_1h, price_1h, leg["direction"])
    if nivel_1h is not None:
        rotulo = "suporte" if leg["direction"] == "alta" else "resistência"
        fatores.append(f"Preço perto do {rotulo} dos últimos {CONFLUENCE_RECENT_LOOKBACK} candles no 1h ({fmt_price(nivel_1h)})")

    if leg["direction"] == "alta":
        if rsi_15m is not None and rsi_15m <= CONFLUENCE_RSI_OVERSOLD:
            fatores.append(f"RSI do 15m em sobrevenda ({rsi_15m:.1f})")
        if rsi_1h is not None and rsi_1h <= CONFLUENCE_RSI_OVERSOLD:
            fatores.append(f"RSI do 1h em sobrevenda ({rsi_1h:.1f})")
        if rsi_5m is not None and rsi_5m <= CONFLUENCE_RSI_5M_OVERSOLD:
            fatores.append(f"RSI do 5m em sobrevenda extrema ({rsi_5m:.1f})")
    else:
        if rsi_15m is not None and rsi_15m >= CONFLUENCE_RSI_OVERBOUGHT:
            fatores.append(f"RSI do 15m em sobrecompra ({rsi_15m:.1f})")
        if rsi_1h is not None and rsi_1h >= CONFLUENCE_RSI_OVERBOUGHT:
            fatores.append(f"RSI do 1h em sobrecompra ({rsi_1h:.1f})")
        if rsi_5m is not None and rsi_5m >= CONFLUENCE_RSI_5M_OVERBOUGHT:
            fatores.append(f"RSI do 5m em sobrecompra extrema ({rsi_5m:.1f})")

    return {"leg": leg, "price_now": price_now, "price_15m": price_15m, "fatores": fatores}


def check_confluence(symbol, candles_4h, candles_15m, candles_1h, candles_5m=None):
    """
    Em vez de exigir só UM critério isolado (fib OU EMA OU RSI), soma
    quantos fatores técnicos diferentes — fibonacci (0.382/0.5/0.618) da
    perna de 4h, EMAs (12/21/50/200) no 4h e no 15m, suporte/resistência
    recente (ainda não confirmado como pivô) no 4h e no 1h, e RSI em
    sobrevenda/sobrecompra no 15m, no 1h e no 5m (extremo) — estão
    alinhados na mesma direção ao mesmo tempo. Pensado pro tipo de leitura
    manual que junta "fib 0.618 no 15m perto da EMA200, aproximando da
    EMA12 no 4h" ou "suporte no 4h em X com o 5m em sobrevenda extrema":
    cada indicador sozinho não vira sinal de verdade em nenhum dos outros
    checks, mas a combinação de vários ao mesmo tempo sim.
    """
    dados = _confluence_fatores(candles_4h, candles_15m, candles_1h, candles_5m)
    if dados is None or len(dados["fatores"]) < CONFLUENCE_MIN_FACTORS:
        return None

    leg = dados["leg"]
    fatores = dados["fatores"]
    price_now = dados["price_now"]
    price_15m = dados["price_15m"]

    if leg["direction"] == "alta":
        acao = "COMPRAR"
        titulo = "Confluência multi-indicador — possível fundo ascendente se formando"
        stop = avoid_round_number_stop(price_now * 0.985, "compra")
    else:
        acao = "VENDER"
        titulo = "Confluência multi-indicador — possível topo descendente se formando"
        stop = avoid_round_number_stop(price_now * 1.015, "venda")
    alvo = leg["end_price"]

    detalhes = [
        f"Preço agora (4h): {fmt_price(price_now)}  |  Preço agora (15m): {fmt_price(price_15m)}",
        f"Fatores alinhados ({len(fatores)}):",
    ]
    detalhes.extend(f"  • {f}" for f in fatores)
    detalhes.append(f"Alvo técnico: {fmt_price(alvo)} (último {'topo' if leg['direction'] == 'alta' else 'fundo'} da perna de 4h)")
    detalhes.append(f"Stop sugerido: {fmt_price(stop)}")
    detalhes.append(
        "Invalidação: rompimento do stop tende a acelerar em direção "
        + ("ao próximo suporte" if leg["direction"] == "alta" else "à próxima resistência")
        + " — fique de olho no gráfico pra achar esse próximo nível."
    )

    return {
        "symbol": symbol, "estilo": "CONFLUÊNCIA", "acao": acao,
        "titulo": titulo,
        "timeframe": "4h + 15m + 1h" + (" + 5m" if candles_5m else ""),
        "detalhes": detalhes,
        "checklist": [(f, True) for f in fatores],
        "entry_price": price_now, "target_price": alvo, "stop_price": stop,
        "resumo": f"{len(fatores)} fatores técnicos alinhados na mesma direção (fibonacci, EMA, RSI).",
        "explicacao": (
            f"{len(fatores)} indicadores técnicos diferentes (fibonacci, EMA e RSI, em "
            f"mais de um timeframe) alinhados na mesma direção ao mesmo tempo — "
            f"confluência multi-indicador, junta vários fatores em vez de depender só "
            f"de um."
        ),
        "aviso": (
            "Sinal combinado de vários indicadores técnicos ao mesmo tempo — ainda "
            "assim é leitura automática, não é confirmação garantida de reversão."
        ),
    }


def diagnose_confluence(candles_4h, candles_15m, candles_1h, candles_5m=None):
    """
    Versão near-miss do check_confluence: mostra os fatores já alinhados
    mesmo quando ainda não chegou no mínimo pra virar sinal de verdade.
    """
    dados = _confluence_fatores(candles_4h, candles_15m, candles_1h, candles_5m)
    if dados is None:
        return None
    fatores = dados["fatores"]
    n = len(fatores)
    if n < CONFLUENCE_DIAG_MIN_FACTORS or n >= CONFLUENCE_MIN_FACTORS:
        return None  # já virou sinal de verdade lá em cima, ou longe demais ainda
    lado = "fundo ascendente" if dados["leg"]["direction"] == "alta" else "topo descendente"
    return {
        "tipo": "Confluência multi-indicador",
        "score": 1.0 / n,
        "texto": (
            f"{n} fator(es) já alinhado(s) pra um possível {lado}: " + "; ".join(fatores) +
            f". Falta(m) mais {CONFLUENCE_MIN_FACTORS - n} pra virar sinal de verdade."
        ),
    }


def _fmt_candle_time(candles, idx):
    """Data/hora (UTC) de abertura de um candle, pra dar contexto de 'quando' num nível técnico."""
    try:
        ts = candles[idx]["open_time"] / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%d/%m %Hh UTC")
    except Exception:
        return "data desconhecida"


def build_entry_outlook(candles_4h, candles_15m, candles_1h, candles_5m=None):
    """
    Contexto de "última entrada" e "próxima entrada possível" calculado na
    hora, a partir dos candles que o bot já busca — sem precisar guardar
    histórico entre execuções (cada rodada do GitHub Actions começa do
    zero). "Última entrada" é a última virada de estrutura confirmada no
    4h (o pivô que deu início à perna de impulso atual — em teoria, onde
    uma entrada de swing teria feito sentido). "Próxima entrada possível" é
    o nível técnico mais próximo do preço atual que ainda não foi tocado
    (fibonacci, EMA de 4h, ou o suporte/resistência anterior à perna atual)
    — se o preço chegar perto dele, some mais um fator de confluência ao
    que já está alinhado agora.
    """
    if len(candles_4h) < (2 * PIVOT_LEN + 10):
        return None
    pivot_highs, pivot_lows = find_pivots(candles_4h, PIVOT_LEN)
    leg = last_impulse_leg(pivot_highs, pivot_lows)
    if leg is None:
        return None

    price_now = candles_4h[-1]["close"]
    lado_ultima = "fundo" if leg["direction"] == "alta" else "topo"
    linhas = [
        f"Última virada de estrutura confirmada no 4h: {lado_ultima} em "
        f"{fmt_price(leg['start_price'])} ({_fmt_candle_time(candles_4h, leg['start_idx'])}) — "
        f"foi dali que partiu o movimento até "
        f"{fmt_price(leg['end_price'])} ({_fmt_candle_time(candles_4h, leg['end_idx'])})."
    ]

    dados = _confluence_fatores(candles_4h, candles_15m, candles_1h, candles_5m)
    fatores_atuais = dados["fatores"] if dados else []

    candidatos = []
    for level in CONFLUENCE_FIB_LEVELS:
        fib_price = fib_level_price(leg, level)
        if not price_in_fib_zone(price_now, fib_price, CONFLUENCE_FIB_TOLERANCE):
            candidatos.append((abs(price_now - fib_price), f"Fibonacci {level} da perna atual", fib_price))
    for periodo in CONFLUENCE_EMA_PERIODS:
        ema = compute_ema([c["close"] for c in candles_4h], periodo)
        if ema is not None and ema > 0:
            dist = abs(price_now - ema) / ema
            if dist > CONFLUENCE_EMA_TOLERANCE:
                candidatos.append((abs(price_now - ema), f"EMA{periodo} no 4h", ema))
    pivots_mesmo_lado = pivot_lows if leg["direction"] == "alta" else pivot_highs
    anteriores = [p for p in pivots_mesmo_lado if p[0] < leg["start_idx"]]
    if anteriores:
        idx_prev, preco_prev = anteriores[-1]
        rotulo_prev = "suporte" if leg["direction"] == "alta" else "resistência"
        candidatos.append((
            abs(price_now - preco_prev),
            f"{rotulo_prev} anterior, de {_fmt_candle_time(candles_4h, idx_prev)}",
            preco_prev,
        ))

    if candidatos:
        candidatos.sort(key=lambda t: t[0])
        _, rotulo, nivel = candidatos[0]
        n_extra = len(fatores_atuais) + 1
        direcao_txt = "acima" if nivel > price_now else "abaixo"
        linhas.append(
            f"Próximo ponto de interesse: {rotulo} em {fmt_price(nivel)} ({direcao_txt} do "
            f"preço atual, {fmt_price(price_now)}). Chegando perto disso, some aos "
            f"{len(fatores_atuais)} fator(es) já alinhado(s) agora e passaria a {n_extra} — "
            f"mais perto de virar confluência de verdade."
        )
    else:
        linhas.append(
            "Não achei um próximo nível técnico relevante fora da tolerância atual — os "
            "níveis principais (fibonacci/EMA) já estão todos perto do preço agora."
        )

    return "\n".join(linhas)


# ----------------------------------------------------------------------------
# DIAGNÓSTICO DE PROXIMIDADE (near-miss) — sob demanda, execução manual
#
# Cada função abaixo espelha um dos checks de sinal acima, mas em vez de só
# dizer sim/não, calcula o quão perto a moeda está de bater o critério real.
# Só retorna algo quando está numa faixa "interessante": nem já batendo o
# critério (aí já teria virado sinal de verdade lá em cima) nem longe demais
# pra valer a pena mencionar.
# ----------------------------------------------------------------------------

def diagnose_pullback(candles):
    if len(candles) < (2 * PIVOT_LEN + 10):
        return None
    pivot_highs, pivot_lows = find_pivots(candles, PIVOT_LEN)
    leg = last_impulse_leg(pivot_highs, pivot_lows)
    if leg is None:
        return None
    price_now = candles[-1]["close"]
    fib_price = fib_level_price(leg, FIB_LEVEL)
    dist_pct = abs(price_now - fib_price) / fib_price
    if dist_pct <= FIB_TOLERANCE or dist_pct > PULLBACK_DIAG_MAX_PCT:
        return None
    structure_ok, _ = ascending_or_descending_bottoms(leg, pivot_highs, pivot_lows)
    estrutura_txt = "estrutura já confirmando" if structure_ok else "estrutura ainda não confirmou fundos/topos"
    lado = "compra" if leg["direction"] == "alta" else "venda"
    return {
        "tipo": "Pullback",
        "score": dist_pct / PULLBACK_DIAG_MAX_PCT,
        "texto": (f"Pullback ({lado}): preço a {dist_pct * 100:.1f}% da zona Fibonacci "
                  f"0.382 ({fmt_price(fib_price)}) — {estrutura_txt}."),
    }


def diagnose_exhaustion(candles):
    closes = [c["close"] for c in candles]
    rsi = compute_rsi(closes)
    _, _, vol_ratio = volume_status(candles)
    if rsi is None:
        return None
    if rsi >= CLIMAX_RSI_HIGH or rsi <= CLIMAX_RSI_LOW:
        if vol_ratio is not None and vol_ratio >= CLIMAX_VOLUME_RATIO:
            return None  # já teria virado sinal de verdade
    if rsi >= CLIMAX_RSI_HIGH - EXHAUSTION_DIAG_RSI_BAND:
        dist = max(0.0, CLIMAX_RSI_HIGH - rsi)
        lado = "topo"
    elif rsi <= CLIMAX_RSI_LOW + EXHAUSTION_DIAG_RSI_BAND:
        dist = max(0.0, rsi - CLIMAX_RSI_LOW)
        lado = "fundo"
    else:
        return None
    vol_txt = f"{vol_ratio:.1f}x a média" if vol_ratio is not None else "sem dado de volume"
    return {
        "tipo": "Clímax de exaustão",
        "score": dist / EXHAUSTION_DIAG_RSI_BAND,
        "texto": (f"Exaustão de {lado}: RSI {rsi:.0f} (faltam ~{dist:.0f} pontos pro "
                  f"gatilho), volume {vol_txt}."),
    }


def _diagnose_scalp_touch(rsi, oversold, overbought, tipo_label, tf_label):
    """
    Diagnóstico genérico pro primeiro-toque de RSI: só dispara quando o RSI
    ainda está FORA da zona de extremo mas perto dela (então o próximo
    cruzamento pra dentro seria, por definição, um primeiro toque). Se o RSI
    já está dentro da zona, não diagnostica — ou já virou sinal de verdade
    (é o primeiro toque), ou já passou do primeiro toque (não vale mais o
    diagnóstico de "quase lá").
    """
    if rsi is None:
        return None
    if rsi <= oversold or rsi >= overbought:
        return None
    if rsi <= oversold + SCALP_DIAG_RSI_BAND:
        dist = rsi - oversold
        return {
            "tipo": tipo_label,
            "score": dist / SCALP_DIAG_RSI_BAND,
            "texto": (f"{tipo_label} (sobrevenda): RSI {tf_label} em {rsi:.0f}, chegando perto "
                      f"do primeiro toque de sobrevenda (~{oversold:.0f})."),
        }
    if rsi >= overbought - SCALP_DIAG_RSI_BAND:
        dist = overbought - rsi
        return {
            "tipo": tipo_label,
            "score": dist / SCALP_DIAG_RSI_BAND,
            "texto": (f"{tipo_label} (sobrecompra): RSI {tf_label} em {rsi:.0f}, chegando perto "
                      f"do primeiro toque de sobrecompra (~{overbought:.0f})."),
        }
    return None


def diagnose_scalp_5m(rsi_5m):
    return _diagnose_scalp_touch(rsi_5m, SCALP_5M_RSI_OVERSOLD, SCALP_5M_RSI_OVERBOUGHT,
                                  "Primeiro toque 5m", "5m")


def diagnose_scalp_1h(rsi_1h):
    return _diagnose_scalp_touch(rsi_1h, SCALP_1H_RSI_OVERSOLD, SCALP_1H_RSI_OVERBOUGHT,
                                  "Primeiro toque 1h", "1h")


def diagnose_scalp_4h(rsi_4h):
    return _diagnose_scalp_touch(rsi_4h, SCALP_4H_RSI_OVERSOLD, SCALP_4H_RSI_OVERBOUGHT,
                                  "Primeiro toque 4h (setup raro)", "4h")


def diagnose_bottom_fishing(candles_d, candles_w):
    if len(candles_w) < 20 or len(candles_d) < 20:
        return None
    ath = max(c["high"] for c in candles_w)
    price_now = candles_d[-1]["close"]
    drawdown = (ath - price_now) / ath
    if drawdown >= BOTTOM_FISHING_MIN_DRAWDOWN:
        return None  # já entrou na faixa (se a estrutura confirmar, já virou sinal de verdade)
    band_start = BOTTOM_FISHING_MIN_DRAWDOWN - REVERSAL_DRAWDOWN_DIAG_BAND
    if drawdown < band_start:
        return None
    dist = BOTTOM_FISHING_MIN_DRAWDOWN - drawdown
    return {
        "tipo": "Bottom fishing",
        "score": dist / REVERSAL_DRAWDOWN_DIAG_BAND,
        "texto": (f"Bottom fishing: {drawdown * 100:.0f}% abaixo da máxima histórica "
                  f"(faltam ~{dist * 100:.1f}pp pra entrar na zona de "
                  f"{BOTTOM_FISHING_MIN_DRAWDOWN * 100:.0f}%+)."),
    }


def diagnose_light_reversal(candles_d):
    lookback = min(len(candles_d), LIGHT_REVERSAL_LOOKBACK_DAYS)
    if lookback < 30:
        return None
    window = candles_d[-lookback:]
    pivot_highs, _ = find_pivots(window, LIGHT_REVERSAL_PIVOT_LEN)
    if not pivot_highs:
        return None
    _, swing_high_price = max(pivot_highs, key=lambda p: p[1])
    price_now = window[-1]["close"]
    drawdown = (swing_high_price - price_now) / swing_high_price
    if LIGHT_REVERSAL_MIN_DRAWDOWN <= drawdown < LIGHT_REVERSAL_MAX_DRAWDOWN:
        return None  # já na faixa de sinal de verdade (se a estrutura confirmar)
    band_start = LIGHT_REVERSAL_MIN_DRAWDOWN - REVERSAL_DRAWDOWN_DIAG_BAND
    if band_start <= drawdown < LIGHT_REVERSAL_MIN_DRAWDOWN:
        dist = LIGHT_REVERSAL_MIN_DRAWDOWN - drawdown
        return {
            "tipo": "Reversão com base",
            "score": dist / REVERSAL_DRAWDOWN_DIAG_BAND,
            "texto": (f"Reversão com base: {drawdown * 100:.0f}% abaixo do topo dos "
                      f"últimos {lookback}d (faltam ~{dist * 100:.1f}pp pra entrar na "
                      f"zona de {LIGHT_REVERSAL_MIN_DRAWDOWN * 100:.0f}%+)."),
        }
    return None


def diagnose_failed_break(candles):
    if len(candles) < (2 * PIVOT_LEN + FAILED_BREAK_LOOKBACK + 5):
        return None
    pivot_highs, pivot_lows = find_pivots(candles, PIVOT_LEN)
    price_now = candles[-1]["close"]
    _, avg_vol, _ = volume_status(candles)
    if not avg_vol:
        return None
    recent_window = candles[-FAILED_BREAK_LOOKBACK:]
    max_vol_ratio = max((c["volume"] / avg_vol) for c in recent_window)

    if pivot_lows:
        ref_idx, ref_price = pivot_lows[-1]
        if ref_idx < len(candles) - FAILED_BREAK_LOOKBACK:
            broke = any(c["low"] < ref_price * (1 - FAILED_BREAK_PENETRATION_PCT) for c in recent_window)
            recovered = price_now > ref_price * (1 + FAILED_BREAK_RECOVERY_PCT)
            if broke and not (recovered and max_vol_ratio >= FAILED_BREAK_VOLUME_RATIO):
                faltando = []
                if not recovered:
                    faltando.append("ainda não recuperou de volta pra cima do suporte")
                if max_vol_ratio < FAILED_BREAK_VOLUME_RATIO:
                    faltando.append(f"volume só {max_vol_ratio:.1f}x a média (precisa {FAILED_BREAK_VOLUME_RATIO:.1f}x)")
                return {
                    "tipo": "Rompimento falho (suporte)",
                    "score": 0.3,
                    "texto": f"Rompeu o suporte em {fmt_price(ref_price)} mas falta confirmar: {', '.join(faltando)}.",
                }
    if pivot_highs:
        ref_idx, ref_price = pivot_highs[-1]
        if ref_idx < len(candles) - FAILED_BREAK_LOOKBACK:
            broke = any(c["high"] > ref_price * (1 + FAILED_BREAK_PENETRATION_PCT) for c in recent_window)
            recovered = price_now < ref_price * (1 - FAILED_BREAK_RECOVERY_PCT)
            if broke and not (recovered and max_vol_ratio >= FAILED_BREAK_VOLUME_RATIO):
                faltando = []
                if not recovered:
                    faltando.append("ainda não devolveu pra dentro da resistência")
                if max_vol_ratio < FAILED_BREAK_VOLUME_RATIO:
                    faltando.append(f"volume só {max_vol_ratio:.1f}x a média (precisa {FAILED_BREAK_VOLUME_RATIO:.1f}x)")
                return {
                    "tipo": "Rompimento falho (resistência)",
                    "score": 0.3,
                    "texto": f"Rompeu a resistência em {fmt_price(ref_price)} mas falta confirmar: {', '.join(faltando)}.",
                }
    return None


def diagnose_range_market(candles):
    if len(candles) < RANGE_LOOKBACK:
        return None
    window = candles[-RANGE_LOOKBACK:]
    range_high = max(c["high"] for c in window)
    range_low = min(c["low"] for c in window)
    if range_low <= 0 or range_high <= range_low:
        return None
    range_pct = (range_high - range_low) / range_low
    if range_pct > RANGE_MAX_PCT:
        return None
    price_now = candles[-1]["close"]
    posicao = (price_now - range_low) / (range_high - range_low)
    if RANGE_EDGE_ZONE_PCT < posicao < (1 - RANGE_EDGE_ZONE_PCT):
        return {
            "tipo": "Padrão de equilíbrio",
            "score": 0.5,
            "texto": (f"Padrão de equilíbrio se formando ({range_pct * 100:.1f}% de amplitude, "
                      f"{fmt_price(range_low)}-{fmt_price(range_high)}) — no meio da faixa, "
                      f"aguardando aproximar do fundo ou do topo pra ter entrada."),
        }
    return None  # já perto de uma borda: isso já teria virado sinal de verdade lá em cima


def build_diagnostic_message(diagnosticos):
    """
    Fica só com o diagnóstico MAIS próximo de cada moeda (não um por tipo de
    sinal) antes de cortar pro top N — senão uma moeda com vários near-miss
    ao mesmo tempo lota a lista sozinha e esconde outras oportunidades.
    """
    linhas = ["🔎 VELA MONITOR — DIAGNÓSTICO (mais perto de um setup)", ""]
    if not diagnosticos:
        linhas.append(
            "Nenhuma moeda do watchlist está particularmente perto de bater algum "
            "critério agora — ou o mercado está sem setups se formando, ou tudo já "
            "disparou como sinal de verdade lá em cima."
        )
    else:
        melhor_por_moeda = {}
        for d in diagnosticos:
            atual = melhor_por_moeda.get(d["symbol"])
            if atual is None or d["score"] < atual["score"]:
                melhor_por_moeda[d["symbol"]] = d
        ordenados = sorted(melhor_por_moeda.values(), key=lambda d: d["score"])[:DIAGNOSTIC_TOP_N]
        for d in ordenados:
            linhas.append(f"• {_fmt_symbol(d['symbol'])} — {d['texto']}")
    linhas.append("")
    linhas.append(
        "Isso é uma régua de proximidade pras mesmas regras dos sinais de verdade "
        "— não é um alerta de entrada, é pra você filtrar o que vale a pena "
        "acompanhar de perto (só a moeda mais próxima de cada uma, uma linha por "
        "moeda)."
    )
    return "\n".join(linhas)


# ----------------------------------------------------------------------------
# CONSULTA POR MOEDA — sob demanda, execução manual (campo "symbol")
# ----------------------------------------------------------------------------

def normalize_symbol(raw):
    s = (raw or "").strip().upper().replace(" ", "")
    if not s:
        return s
    if not s.endswith("USDT"):
        s = s + "USDT"
    return s


def build_symbol_deep_dive(symbol_input, market_trend="neutra"):
    symbol = normalize_symbol(symbol_input)
    if not symbol:
        return "⚠️ Não veio nenhuma moeda no campo de análise."

    try:
        candles_4h = fetch_klines(symbol, INTERVAL, KLINES_LIMIT)
        candles_d = fetch_klines(symbol, "1d", 200)
        candles_w = fetch_klines(symbol, "1w", 1000)
        candles_15m = fetch_klines(symbol, "15m", CONFLUENCE_15M_LIMIT)
        candles_1h = fetch_klines(symbol, "1h", 100)
        candles_5m = fetch_klines(symbol, "5m", CONFLUENCE_5M_LIMIT)
    except urllib.error.HTTPError as e:
        return (f"⚠️ Não consegui buscar dados de {symbol} na Binance (erro {e.code}). "
                f"Confira se o par existe (ex.: SOLUSDT, XRPUSDT).")
    except Exception as e:
        return f"⚠️ Erro buscando dados de {symbol}: {e}"

    if not candles_4h:
        return f"⚠️ Não veio nenhum candle 4h pra {symbol} — confira se o par existe."

    try:
        candles_3d = fetch_klines(symbol, "3d", 200)
    except Exception:
        candles_3d = []

    price_now = candles_4h[-1]["close"]
    linhas = [f"🧭 VELA MONITOR — ANÁLISE — {_fmt_symbol(symbol)}", "",
              f"Preço agora: {fmt_price(price_now)}"]
    if market_trend in ("alta", "baixa"):
        linhas.append(f"Tendência majoritária do mercado (BTC, diário): {market_trend}")

    sinais_ativos = []
    for fn in (check_pullback, check_exhaustion_climax, check_failed_breakout_reversal, check_range_market):
        try:
            sig = fn(symbol, candles_4h)
            if sig:
                sinais_ativos.append(sig)
        except Exception:
            pass

    rsi_4h = None
    try:
        sig = check_scalp_4h(symbol, candles_4h)
        if sig:
            sinais_ativos.append(sig)
    except Exception:
        pass
    rsi_4h = compute_rsi([c["close"] for c in candles_4h])

    try:
        sig = check_retest_4h(symbol, candles_4h, candles_w)
        if sig:
            sinais_ativos.append(sig)
    except Exception:
        pass

    try:
        sig = check_trendline_breakout(symbol, candles_4h, "4h")
        if sig:
            sinais_ativos.append(sig)
    except Exception:
        pass

    try:
        sig = check_oco_pattern(symbol, candles_4h, "4h")
        if sig:
            sinais_ativos.append(sig)
    except Exception:
        pass

    rsi_5m = rsi_1h = None
    if candles_5m:
        try:
            sig = check_scalp_5m(symbol, candles_5m)
            if sig:
                sinais_ativos.append(sig)
        except Exception:
            pass
        rsi_5m = compute_rsi([c["close"] for c in candles_5m])

    if candles_1h:
        try:
            sig = check_scalp_1h(symbol, candles_1h)
            if sig:
                sinais_ativos.append(sig)
        except Exception:
            pass
        rsi_1h = compute_rsi([c["close"] for c in candles_1h])

    if candles_15m and candles_1h:
        try:
            sig = check_confluence(symbol, candles_4h, candles_15m, candles_1h, candles_5m)
            if sig:
                sinais_ativos.append(sig)
        except Exception:
            pass

    if candles_d and candles_w:
        for fn in (check_bottom_fishing, check_light_reversal):
            try:
                sig = fn(symbol, candles_d, candles_w) if fn is check_bottom_fishing else fn(symbol, candles_d)
                if sig:
                    sinais_ativos.append(sig)
            except Exception:
                pass

    diagnosticos = [d for d in (
        diagnose_pullback(candles_4h),
        diagnose_exhaustion(candles_4h),
        diagnose_failed_break(candles_4h),
        diagnose_range_market(candles_4h),
        diagnose_scalp_5m(rsi_5m) if rsi_5m is not None else None,
        diagnose_scalp_1h(rsi_1h) if rsi_1h is not None else None,
        diagnose_scalp_4h(rsi_4h) if rsi_4h is not None else None,
        diagnose_bottom_fishing(candles_d, candles_w) if (candles_d and candles_w) else None,
        diagnose_light_reversal(candles_d) if candles_d else None,
        diagnose_confluence(candles_4h, candles_15m, candles_1h, candles_5m) if (candles_15m and candles_1h) else None,
    ) if d]

    sinais_ativos = aplica_filtros_qualidade(sinais_ativos, market_trend, diagnosticos_extra=diagnosticos)
    sinais_ativos = adiciona_plano_b(sinais_ativos, candles_4h, candles_d)

    contexto_txt = None
    if symbol != "BTCUSDT" and candles_d:
        try:
            btc_candles = fetch_klines("BTCUSDT", "1d", DOMINANCE_LOOKBACK_DAYS + 5)
            btc_ret = pct_return(btc_candles)
            moeda_ret = pct_return(candles_d)
            if btc_ret is not None and moeda_ret is not None:
                relacao = "mais forte" if moeda_ret > btc_ret else "mais fraca"
                contexto_txt = (
                    f"Nos últimos {DOMINANCE_LOOKBACK_DAYS}d essa moeda fez {moeda_ret:+.1f}% "
                    f"contra {btc_ret:+.1f}% do BTC — está {relacao} que o BTC no momento."
                )
        except Exception:
            pass

    linhas.append("")
    if sinais_ativos:
        linhas.append("✅ Sinal(is) ativo(s) agora:")
        for sig in sinais_ativos:
            linhas.append(f"  • {sig['titulo']} ({sig['estilo']}, {sig['acao']})")
        linhas.append("")
        linhas.append("Mensagem completa do sinal mais relevante:")
        linhas.append("")
        linhas.append(format_signal_message(sinais_ativos[0]))
    else:
        linhas.append("Nenhum sinal de verdade ativo agora nessa moeda.")
        if diagnosticos:
            ordenados = sorted(diagnosticos, key=lambda d: d["score"])
            melhor = ordenados[0]
            linhas.append("")
            linhas.append(f"Setup mais próximo de fazer sentido agora: {melhor['tipo']}.")
            linhas.append(melhor["texto"])
            if len(ordenados) > 1:
                linhas.append("")
                linhas.append("Outros pontos de atenção:")
                for d in ordenados[1:]:
                    linhas.append(f"  • {d['texto']}")
        else:
            linhas.append("")
            linhas.append(
                "Também não achei nada perto de disparar — RSI neutro, sem correção de "
                "Fibonacci relevante, sem drawdown expressivo. Moeda em zona neutra no "
                "momento."
            )

    if contexto_txt:
        linhas.append("")
        linhas.append(f"Contexto: {contexto_txt}")

    try:
        outlook_txt = build_entry_outlook(candles_4h, candles_15m, candles_1h, candles_5m)
    except Exception:
        outlook_txt = None
    if outlook_txt:
        linhas.append("")
        linhas.append("📍 Última entrada e próximo ponto de interesse:")
        linhas.append(outlook_txt)

    try:
        bandeira = classifica_bandeira(symbol, candles_4h, timeframe_label="4h")
    except Exception:
        bandeira = None
    if bandeira:
        linhas.append("")
        linhas.append(bandeira["texto"])

    if candles_3d and len(candles_3d) >= (2 * PIVOT_LEN + 10):
        try:
            bandeira_3d = classifica_bandeira(symbol, candles_3d, timeframe_label="3D")
        except Exception:
            bandeira_3d = None
        if bandeira_3d:
            linhas.append("")
            linhas.append(bandeira_3d["texto"])

    linhas.append("")
    linhas.append(
        "⚠️ Isso é uma leitura automática baseada nas mesmas regras dos sinais do bot "
        "— não é uma opinião gerada por um modelo de IA (o script não chama nenhum "
        "modelo de linguagem), é a aplicação mecânica das mesmas regras, só que "
        "explicada. E o setup que faz mais sentido muda conforme o cenário de mercado "
        "muda — não é uma recomendação fixa."
    )
    return "\n".join(linhas)


# ----------------------------------------------------------------------------
# MENSAGEM E ENVIO PRO TELEGRAM
# ----------------------------------------------------------------------------

def _acao_emoji(acao):
    if acao == "COMPRAR":
        return "🟢"
    elif acao == "VENDER":
        return "🔴"
    return "🔵"


def _fmt_symbol(symbol):
    return "Mercado geral" if symbol == "MERCADO" else symbol.replace("USDT", "")


def _entrada_texto(sig):
    """
    Como entrar — não é sempre "a mercado": quando o próprio sinal já
    calcula uma ZONA de entrada (`entry_zone`, ex.: bottom fishing e
    reversão com base, que miram um range de fundos ascendentes em vez de
    um ponto único), faz mais sentido fracionar a compra/venda dentro dela
    em vez de tudo de uma vez. Sinais de janela curta (scalp) pedem
    urgência — o ponto de entrada perde a força rápido. O resto (pullback,
    range, confluência, exaustão, rompimento falho) já é um ponto técnico
    específico, então é a mercado mesmo.
    """
    zona = sig.get("entry_zone")
    if zona:
        low, high = zona
        return (f"Fracionada (compra escalonada) entre {fmt_price(low)} e {fmt_price(high)} "
                f"— zona ampla, não um ponto único, então monta a posição aos poucos em vez "
                f"de tudo de uma vez.")
    if sig.get("estilo") == "SCALP":
        return "A mercado, com urgência — janela curta, o ponto de entrada perde a força rápido."
    return "A mercado — ponto técnico específico, não precisa fracionar."


def _checklist_linhas(checklist):
    if not checklist:
        return []
    linhas = ["", "Checklist:"]
    for label, ok in checklist:
        linhas.append(f"  {'✅' if ok else '❌'} {label}")
    return linhas


def _render_signal_core(sig, indent=""):
    """
    Bloco central de UM sinal, no formato enxuto tipo "cartão de operação":
    📍 como entrar (a mercado ou fracionada, ver `_entrada_texto`), 🔴 stop
    da corretora, 🎯 alvo(s) (com nota de realizar parcial/segurar quando
    for mais de um alvo, típico de swing), 💡 resumo de uma linha do motivo
    técnico, 💰 preço agora, 🧠 explicação com contexto, 🚨 alerta quando
    tiver, e 🗺️ o "plano B" (próximo nível técnico, no mesmo tempo gráfico
    e num zoom out pro diário, se o stop for rompido — ver `adiciona_plano_b`)
    quando o bot conseguiu calcular algum. Compartilhado entre a mensagem
    de sinal único e a combinada — só muda a indentação (usada quando o
    bloco entra dentro de uma mensagem maior).
    """
    entry = sig.get("entry_price")
    stop = sig.get("stop_price")
    alvo = sig.get("target_price")
    alvos_lista = sig.get("target_prices")

    linhas = [f"{indent}📍 Entrada: {_entrada_texto(sig)}"]
    if stop is not None:
        linhas.append(f"{indent}🔴 Stop corretora: {fmt_price(stop)}")
    if alvos_lista:
        linhas.append(f"{indent}🎯 Alvos: {' > '.join(fmt_price(t) for t in alvos_lista)}")
        linhas.append(f"{indent}   (bateu um alvo: considere realizar parcial e segurar o "
                       f"resto — swing pensa no lucro a longo prazo, não precisa sair tudo de uma vez)")
    elif alvo is not None:
        linhas.append(f"{indent}🎯 Alvo: {fmt_price(alvo)}")
    if sig.get("reward_risk_ratio") is not None:
        linhas.append(f"{indent}📊 Risco/retorno: 1:{sig['reward_risk_ratio']:.1f}")
    if sig.get("resumo"):
        linhas.append(f"{indent}💡 {sig['resumo']}")
    if entry is not None:
        linhas.append(f"{indent}💰 Preço agora: {fmt_price(entry)}")

    linhas.append("")
    linhas.append(f"{indent}🧠 {sig['explicacao']}")

    if sig.get("aviso"):
        linhas.append("")
        linhas.append(f"{indent}🚨 Alerta: {sig['aviso']}")

    if sig.get("plano_b"):
        linhas.append("")
        linhas.append(f"{indent}🗺️ Se o stop for rompido: {sig['plano_b']}")

    checklist_linhas = _checklist_linhas(sig.get("checklist"))
    if checklist_linhas:
        linhas.extend(f"{indent}{l}" if l else indent.rstrip() for l in checklist_linhas)

    return linhas


def format_signal_message(sig):
    """
    Mensagem de UM sinal, no formato "cartão de operação": ação + moeda +
    setup no topo, entrada/stop/alvo(s) logo abaixo, o motivo técnico numa
    linha, o preço agora, e um parágrafo de contexto — pra dar pra ler em
    5 segundos e ainda ter os detalhes de quem quiser conferir.
    """
    emoji = _acao_emoji(sig["acao"])
    sym = _fmt_symbol(sig["symbol"])
    acao_txt = f"{sig['acao']} AGORA" if sig["acao"] in ("COMPRAR", "VENDER") else sig["acao"]

    linhas = [
        "VELA MONITOR", "",
        f"{emoji} {acao_txt} — {sym} ({sig['titulo']})",
        "─" * 24,
    ]
    linhas.extend(_render_signal_core(sig))
    linhas.append("")
    linhas.append("Leitura técnica automática — não é recomendação de investimento.")
    return "\n".join(linhas)


def format_combined_signal_message(symbol, sinais):
    """
    Quando a mesma moeda bate mais de uma estratégia ao mesmo tempo, manda
    UMA mensagem só explicando isso — em vez de uma mensagem cheia repetida
    pra cada estratégia (o que no Telegram parecia "operação clonada").
    """
    sym = _fmt_symbol(symbol)
    linhas = ["VELA MONITOR", "", f"🧩 {sym} bateu {len(sinais)} estratégias ao mesmo tempo", ""]
    acoes = {s["acao"] for s in sinais}
    if len(acoes) > 1:
        linhas.append("⚠️ Atenção: as estratégias abaixo sugerem lados opostos (compra x venda) — é conflito, não reforço.")
        linhas.append("")

    for sig in sinais:
        emoji = _acao_emoji(sig["acao"])
        acao_txt = f"{sig['acao']} AGORA" if sig["acao"] in ("COMPRAR", "VENDER") else sig["acao"]
        linhas.append(f"{emoji} {acao_txt} · {sig['estilo']} · {sig['titulo']} ({sig['timeframe']})")
        linhas.append("─" * 20)
        linhas.extend(_render_signal_core(sig, indent="  "))
        linhas.append("")

    if len(acoes) == 1:
        linhas.append(
            "Mais de uma estratégia concordando na mesma direção ao mesmo tempo costuma "
            "ser um reforço do setup."
        )
        linhas.append("")
    linhas.append("Leitura técnica automática — não é recomendação de investimento.")
    return "\n".join(linhas)


def _telegram_request(method, payload):
    """
    Chamada genérica pra qualquer método da Bot API do Telegram (sendMessage,
    editMessageText, pinChatMessage, getChat...). Retorna o JSON já decodificado
    da resposta (dict, com "ok"/"result"/"description") ou None se deu erro de
    rede/HTTP. Usada tanto pelo envio normal de mensagem quanto pela memória da
    última operação (ver mais abaixo).
    """
    if not BOT_TOKEN:
        print("ERRO: defina TELEGRAM_BOT_TOKEN nas variáveis de ambiente.")
        return None
    url = f"{TELEGRAM_BASE}/bot{BOT_TOKEN}/{method}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Erro na chamada Telegram {method}: {e.code} {e.read()}")
        return None
    except Exception as e:
        print(f"Erro na chamada Telegram {method}: {e}")
        return None


def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("ERRO: defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID nas variáveis de ambiente.")
        return False
    resp = _telegram_request("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    })
    return bool(resp and resp.get("ok"))


# ----------------------------------------------------------------------------
# MEMÓRIA DA ÚLTIMA OPERAÇÃO — em vez de guardar arquivo no repositório ou
# depender do cache do GitHub Actions (que pode expirar/limpar), usa o
# próprio Telegram como "banco de dados": o bot mantém UMA mensagem fixada
# (pin) no chat com os dados da última operação de verdade (COMPRAR/VENDER)
# de cada símbolo em CORE_SYMBOLS. A cada rodada:
#   1) pergunta pro Telegram qual é a mensagem fixada agora (getChat) e lê
#      os dados dela (get_memoria_pinned);
#   2) se saiu operação nova nessa rodada, atualiza só aquele símbolo e
#      fixa a versão nova — editando a MESMA mensagem (editMessageText)
#      quando já existe um pin, em vez de acumular fixação antiga;
#   3) devolve os dados de ANTES da atualização, pra quem for montar o
#      "desde a última operação..." ainda usar a operação anterior mesmo
#      dentro da rodada que acabou de mandar uma nova.
# Nada disso toca no repositório git nem depende de cache — é só estado
# guardado dentro da própria conversa do Telegram.
# ----------------------------------------------------------------------------

MEMORIA_MARCADOR = "DADOS_JSON:"


def get_memoria_pinned():
    """
    Busca a mensagem fixada atual do chat (getChat) e tenta extrair o bloco
    de dados dela (linha que começa com "DADOS_JSON:"). Retorna uma tupla
    (message_id, dados_por_simbolo) — message_id é None se não tem pin
    (ou deu erro), e dados_por_simbolo é {} se não tem pin ou não deu pra
    parsear os dados.
    """
    if not BOT_TOKEN or not CHAT_ID:
        return None, {}
    resp = _telegram_request("getChat", {"chat_id": CHAT_ID})
    if not resp or not resp.get("ok"):
        return None, {}
    pinned = (resp.get("result") or {}).get("pinned_message")
    if not pinned:
        return None, {}
    message_id = pinned.get("message_id")
    texto = pinned.get("text", "") or ""
    for linha in texto.splitlines():
        if linha.startswith(MEMORIA_MARCADOR):
            try:
                dados = json.loads(linha[len(MEMORIA_MARCADOR):].strip())
                if isinstance(dados, dict):
                    return message_id, dados
            except Exception:
                pass
    return message_id, {}


def _texto_memoria(dados_por_simbolo):
    """
    Monta o texto da mensagem de memória: um resumo legível (o que aparece
    fixado no topo do chat, pra você também conseguir bater o olho) seguido
    da linha "DADOS_JSON: {...}" que é a parte que o bot de fato lê de volta
    — o resumo de cima é só cosmético, não precisa ficar sincronizado
    palavra por palavra com o parser.
    """
    linhas = [
        "📌 VELA MONITOR — memória da última operação (BTC/ETH)",
        "Não apague nem desafixe — o bot usa essa mensagem pra lembrar da "
        "última operação enviada de cada moeda.",
        "",
    ]
    for symbol in CORE_SYMBOLS:
        info = dados_por_simbolo.get(symbol)
        nome = _fmt_symbol(symbol)
        if not info:
            linhas.append(f"{nome} — nenhuma operação registrada ainda.")
        else:
            linhas.append(f"{nome} — {info.get('acao', '?')} · {info.get('titulo', '?')} "
                           f"({info.get('timeframe', '?')})")
            linhas.append(f"Enviado em: {info.get('timestamp', '?')}")
            entrada_txt = fmt_price(info["entry"]) if info.get("entry") is not None else "-"
            stop_txt = fmt_price(info["stop"]) if info.get("stop") is not None else "-"
            alvo_txt = fmt_price(info["alvo"]) if info.get("alvo") is not None else "-"
            linhas.append(f"Entrada: {entrada_txt} | Stop: {stop_txt} | Alvo: {alvo_txt}")
        linhas.append("")
    linhas.append(f"{MEMORIA_MARCADOR} {json.dumps(dados_por_simbolo)}")
    return "\n".join(linhas)


def atualiza_memoria_ultima_operacao(sinais_por_moeda):
    """
    Lê a memória fixada atual e, se saiu sinal de verdade (COMPRAR/VENDER)
    nessa rodada pra algum símbolo de CORE_SYMBOLS, atualiza o registro
    daquele símbolo e fixa a versão nova (editando a mensagem existente
    quando já tem uma fixada, senão manda uma mensagem nova e fixa ela).
    Se não saiu operação nova em nenhum símbolo, não mexe em nada no
    Telegram (evita editar/fixar à toa toda rodada).

    Retorna o dict de ANTES da atualização — é esse que build_core_status_message
    usa pra montar o "desde a última operação enviada..." de cada símbolo,
    já que o sinal novo (se saiu) já aparece no cartão normal da rodada.
    """
    if not BOT_TOKEN or not CHAT_ID:
        return {}
    message_id, dados_antigos = get_memoria_pinned()
    dados_novos = dict(dados_antigos)
    agora_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    mudou = False
    for symbol in CORE_SYMBOLS:
        sinais = sinais_por_moeda.get(symbol) or []
        sig = next((s for s in sinais if s.get("acao") in ("COMPRAR", "VENDER")), None)
        if not sig:
            continue
        alvos_lista = sig.get("target_prices")
        alvo = alvos_lista[0] if alvos_lista else sig.get("target_price")
        dados_novos[symbol] = {
            "acao": sig.get("acao"),
            "titulo": sig.get("titulo"),
            "timeframe": sig.get("timeframe"),
            "entry": sig.get("entry_price"),
            "stop": sig.get("stop_price"),
            "alvo": alvo,
            "timestamp": agora_iso,
        }
        mudou = True

    if not mudou:
        return dados_antigos

    texto = _texto_memoria(dados_novos)
    try:
        if message_id is not None:
            resp = _telegram_request("editMessageText", {
                "chat_id": CHAT_ID, "message_id": message_id, "text": texto,
                "disable_web_page_preview": True,
            })
            if resp and resp.get("ok"):
                return dados_antigos
            print("  aviso: não deu pra editar a mensagem de memória fixada — mandando uma nova")
        resp = _telegram_request("sendMessage", {
            "chat_id": CHAT_ID, "text": texto, "disable_web_page_preview": True,
        })
        if resp and resp.get("ok"):
            novo_id = resp["result"]["message_id"]
            _telegram_request("pinChatMessage", {
                "chat_id": CHAT_ID, "message_id": novo_id, "disable_notification": True,
            })
        else:
            print("  aviso: não deu pra mandar/fixar a mensagem de memória")
    except Exception as e:
        print(f"  erro atualizando a memória da última operação ({e})")
    return dados_antigos


def _ultima_operacao_texto(info_anterior, price_now):
    """
    Monta o bloco "📍 Última operação enviada" pra um símbolo, a partir do
    registro salvo na memória fixada (`info_anterior`, um dict como o
    guardado por `atualiza_memoria_ultima_operacao`) e do preço atual. Mostra
    há quanto tempo foi, os valores daquela operação, e como o preço andou
    desde então (inclusive se já passou do stop ou do alvo) — é o contexto
    que antes só aparecia como diagnóstico solto, sem nenhum vínculo com a
    última operação real que o bot mandou.
    """
    if not info_anterior:
        return ("📍 Última operação enviada: nenhuma registrada ainda (é a primeira "
                "operação real dessa moeda desde que essa memória começou a rodar).")

    ts_txt = info_anterior.get("timestamp", "?")
    tempo_txt = "tempo desconhecido"
    try:
        ts = datetime.strptime(ts_txt, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)
        delta_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
        if delta_h < 0:
            tempo_txt = "agora mesmo"
        elif delta_h < 1:
            tempo_txt = f"{int(delta_h * 60)} min atrás"
        elif delta_h < 48:
            tempo_txt = f"{delta_h:.1f}h atrás"
        else:
            tempo_txt = f"{delta_h / 24:.1f} dias atrás"
    except Exception:
        pass

    acao = info_anterior.get("acao")
    entry = info_anterior.get("entry")
    stop = info_anterior.get("stop")
    alvo = info_anterior.get("alvo")

    linhas = [
        f"📍 Última operação enviada: {acao} · {info_anterior.get('titulo', '?')} "
        f"({info_anterior.get('timeframe', '?')}) — {tempo_txt} (em {ts_txt})."
    ]
    entrada_txt = fmt_price(entry) if entry is not None else "-"
    stop_txt = fmt_price(stop) if stop is not None else "-"
    alvo_txt = fmt_price(alvo) if alvo is not None else "-"
    linhas.append(f"   Entrada no envio: {entrada_txt} | Stop: {stop_txt} | Alvo: {alvo_txt}")

    if price_now is not None and entry:
        variacao = (price_now - entry) / entry * 100
        sinal_var = "+" if variacao >= 0 else ""
        linhas.append(f"   Preço agora: {fmt_price(price_now)} ({sinal_var}{variacao:.1f}% desde a entrada)")
        if acao in ("COMPRAR", "VENDER"):
            passou_stop = (price_now <= stop) if (acao == "COMPRAR" and stop is not None) else \
                          (price_now >= stop) if (acao == "VENDER" and stop is not None) else False
            passou_alvo = (price_now >= alvo) if (acao == "COMPRAR" and alvo is not None) else \
                          (price_now <= alvo) if (acao == "VENDER" and alvo is not None) else False
            if passou_stop:
                linhas.append("   ⚠️ O preço já passou do stop dessa operação.")
            elif passou_alvo:
                linhas.append("   ✅ O preço já passou do alvo dessa operação.")
            else:
                linhas.append("   Ainda entre o stop e o alvo — operação segue em aberto.")
                if stop is not None:
                    risco_r = abs(entry - stop)
                    movimento_favoravel = (price_now - entry) if acao == "COMPRAR" else (entry - price_now)
                    if risco_r > 0 and movimento_favoravel >= risco_r * BREAKEVEN_STOP_R_MULT:
                        linhas.append(
                            f"   💡 O preço já andou pelo menos {BREAKEVEN_STOP_R_MULT:.0f}x a distância "
                            f"entrada→stop a favor — dá pra considerar mover o stop pra {fmt_price(entry)} "
                            "(zero a zero), travando a operação sem risco de prejuízo a partir daqui."
                        )

    return "\n".join(linhas)


# ----------------------------------------------------------------------------
# ANÁLISE POR MOEDA — roda os checks por-moeda, junta os sinais e também
# coleta diagnósticos de proximidade (near-miss) pra quem não disparou nada
# ----------------------------------------------------------------------------

def analyze_symbol(symbol, tier=None, market_trend="neutra"):
    sinais = []
    diagnosticos = []
    candles_4h = fetch_klines(symbol, INTERVAL, KLINES_LIMIT)
    if len(candles_4h) < (2 * PIVOT_LEN + 10):
        return sinais, diagnosticos

    try:
        sig = check_pullback(symbol, candles_4h)
        if sig:
            sinais.append(sig)
        else:
            diag = diagnose_pullback(candles_4h)
            if diag:
                diagnosticos.append({"symbol": symbol, **diag})
    except Exception as e:
        print(f"  {symbol}: erro no check de pullback ({e})")

    try:
        sig = check_exhaustion_climax(symbol, candles_4h)
        if sig:
            sinais.append(sig)
        else:
            diag = diagnose_exhaustion(candles_4h)
            if diag:
                diagnosticos.append({"symbol": symbol, **diag})
    except Exception as e:
        print(f"  {symbol}: erro no check de exaustão ({e})")

    try:
        sig = check_failed_breakout_reversal(symbol, candles_4h)
        if sig:
            sinais.append(sig)
        else:
            diag = diagnose_failed_break(candles_4h)
            if diag:
                diagnosticos.append({"symbol": symbol, **diag})
    except Exception as e:
        print(f"  {symbol}: erro no check de reversão por rompimento falho ({e})")

    try:
        sig = check_range_market(symbol, candles_4h)
        if sig:
            sinais.append(sig)
        else:
            diag = diagnose_range_market(candles_4h)
            if diag:
                diagnosticos.append({"symbol": symbol, **diag})
    except Exception as e:
        print(f"  {symbol}: erro no check de mercado em consolidação ({e})")

    try:
        sig = check_scalp_4h(symbol, candles_4h)
        if sig:
            sinais.append(sig)
        else:
            rsi_4h = compute_rsi([c["close"] for c in candles_4h])
            diag = diagnose_scalp_4h(rsi_4h)
            if diag:
                diagnosticos.append({"symbol": symbol, **diag})
    except Exception as e:
        print(f"  {symbol}: erro no check de primeiro toque 4h ({e})")

    # cascata de RSI e confluência usam 15m/1h/5m — busca uma vez só e reaproveita
    try:
        candles_15m = fetch_klines(symbol, "15m", CONFLUENCE_15M_LIMIT)
        candles_1h = fetch_klines(symbol, "1h", 100)
        candles_5m = fetch_klines(symbol, "5m", CONFLUENCE_5M_LIMIT)
    except Exception as e:
        print(f"  {symbol}: erro ao buscar candles 15m/1h/5m ({e})")
        candles_15m, candles_1h, candles_5m = [], [], []

    if candles_5m:
        try:
            sig = check_scalp_5m(symbol, candles_5m)
            if sig:
                sinais.append(sig)
            else:
                rsi_5m = compute_rsi([c["close"] for c in candles_5m])
                diag = diagnose_scalp_5m(rsi_5m)
                if diag:
                    diagnosticos.append({"symbol": symbol, **diag})
        except Exception as e:
            print(f"  {symbol}: erro no check de primeiro toque 5m ({e})")

    if candles_1h:
        try:
            sig = check_scalp_1h(symbol, candles_1h)
            if sig:
                sinais.append(sig)
            else:
                rsi_1h = compute_rsi([c["close"] for c in candles_1h])
                diag = diagnose_scalp_1h(rsi_1h)
                if diag:
                    diagnosticos.append({"symbol": symbol, **diag})
        except Exception as e:
            print(f"  {symbol}: erro no check de primeiro toque 1h ({e})")

    if candles_15m and candles_1h:
        try:
            sig = check_confluence(symbol, candles_4h, candles_15m, candles_1h, candles_5m)
            if sig:
                sinais.append(sig)
            else:
                diag = diagnose_confluence(candles_4h, candles_15m, candles_1h, candles_5m)
                if diag:
                    diagnosticos.append({"symbol": symbol, **diag})
        except Exception as e:
            print(f"  {symbol}: erro no check de confluência ({e})")

    # bottom fishing e reversão leve compartilham os candles diário/semanal
    try:
        candles_d = fetch_klines(symbol, "1d", 200)
        candles_w = fetch_klines(symbol, "1w", 1000)
    except Exception as e:
        print(f"  {symbol}: erro ao buscar candles diário/semanal ({e})")
        candles_d, candles_w = [], []

    if candles_d and candles_w:
        try:
            sig = check_bottom_fishing(symbol, candles_d, candles_w, tier=tier)
            if sig:
                sinais.append(sig)
            else:
                diag = diagnose_bottom_fishing(candles_d, candles_w)
                if diag:
                    diagnosticos.append({"symbol": symbol, **diag})
        except Exception as e:
            print(f"  {symbol}: erro no check de bottom fishing ({e})")

        try:
            sig = check_light_reversal(symbol, candles_d, tier=tier)
            if sig:
                sinais.append(sig)
            else:
                diag = diagnose_light_reversal(candles_d)
                if diag:
                    diagnosticos.append({"symbol": symbol, **diag})
        except Exception as e:
            print(f"  {symbol}: erro no check de reversão leve ({e})")

    try:
        sig = check_retest_4h(symbol, candles_4h, candles_w)
        if sig:
            sinais.append(sig)
    except Exception as e:
        print(f"  {symbol}: erro no check de reteste após toque de RSI no 4h ({e})")

    try:
        sig = check_trendline_breakout(symbol, candles_4h, "4h")
        if sig:
            sinais.append(sig)
    except Exception as e:
        print(f"  {symbol}: erro no check de rompimento de linha de tendência ({e})")

    try:
        sig = check_oco_pattern(symbol, candles_4h, "4h")
        if sig:
            sinais.append(sig)
    except Exception as e:
        print(f"  {symbol}: erro no check de padrão ombro-cabeça-ombro ({e})")

    sinais = aplica_filtros_qualidade(sinais, market_trend, diagnosticos_extra=diagnosticos)
    sinais = adiciona_plano_b(sinais, candles_4h, candles_d)
    return sinais, diagnosticos


# ----------------------------------------------------------------------------
# NOTÍCIAS DE FALLBACK (quando a rodada não encontra nenhum setup na moeda)
# ----------------------------------------------------------------------------

def fetch_reuters_headlines(limit=NEWS_MAX_HEADLINES):
    """
    Busca as manchetes mais recentes do domínio reuters.com via NewsAPI.org
    (plano gratuito). Pega só título e um resumo curto de cada notícia —
    nunca o texto completo do artigo — mais o link original. Se a chave não
    estiver configurada, ou a busca falhar por qualquer motivo, devolve uma
    lista vazia (o chamador trata isso como "sem notícia disponível").
    """
    if not NEWS_API_KEY:
        return []
    params = urllib.parse.urlencode({
        "domains": "reuters.com",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": NEWS_API_KEY,
    })
    url = f"{NEWS_API_BASE}/everything?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "vela-monitor-bot/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    artigos = data.get("articles", [])[:limit]
    noticias = []
    for a in artigos:
        titulo = (a.get("title") or "").strip()
        if not titulo:
            continue
        noticias.append({
            "titulo": titulo,
            "descricao": (a.get("description") or "").strip(),
            "url": a.get("url") or "",
        })
    return noticias


def translate_to_pt(text):
    """
    Traduz um texto curto (título/resumo de notícia) do inglês pro português
    via MyMemory (API gratuita, sem precisar de chave). Se a tradução falhar
    por qualquer motivo, devolve o texto original em inglês — nunca quebra
    o envio por causa disso.
    """
    if not text:
        return text
    try:
        params = urllib.parse.urlencode({"q": text, "langpair": "en|pt-BR"})
        url = f"{TRANSLATE_BASE}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "vela-monitor-bot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        traduzido = (data.get("responseData") or {}).get("translatedText")
        return traduzido.strip() if traduzido else text
    except Exception:
        return text


def build_news_fallback_message():
    """
    Monta a mensagem de manchetes da Reuters (traduzidas) pra mandar quando
    a rodada não encontra nenhum setup em nenhuma moeda. Devolve None se não
    tiver chave configurada ou se a busca não trouxer nada — nesse caso o
    chamador simplesmente não manda mensagem nenhuma (silêncio, como antes).
    """
    try:
        noticias = fetch_reuters_headlines()
    except Exception as e:
        print(f"  erro buscando manchetes da Reuters ({e})")
        return None
    if not noticias:
        return None

    linhas = ["📰 VELA MONITOR — sem setup nessa rodada, manchetes da Reuters", ""]
    for n in noticias:
        linhas.append(f"• {translate_to_pt(n['titulo'])}")
        if n["descricao"]:
            linhas.append(f"  {translate_to_pt(n['descricao'])}")
        if n["url"]:
            linhas.append(f"  {n['url']}")
        linhas.append("")
    linhas.append(
        "Título e resumo traduzidos automaticamente, link original da Reuters "
        "em cada notícia — conteúdo é da Reuters, não do bot."
    )
    return "\n".join(linhas)


# ----------------------------------------------------------------------------
# TOP 10 POR MARKET CAP (CoinMarketCap) — pro relatório categorizado
# ----------------------------------------------------------------------------

def fetch_cmc_top_symbols(limit=CMC_TOP_N):
    """
    Busca as `limit` maiores moedas por market cap na CoinMarketCap (precisa
    do secret CMC_API_KEY, plano gratuito) e devolve os pares USDT
    correspondentes (ex.: "BTC" -> "BTCUSDT"). Sem a chave, ou se a chamada
    falhar por qualquer motivo, cai numa lista fixa aproximada
    (CMC_FALLBACK_SYMBOLS) — nunca quebra o relatório por causa disso.
    """
    if not CMC_API_KEY:
        return list(CMC_FALLBACK_SYMBOLS)
    try:
        url = (f"{CMC_API_BASE}/cryptocurrency/listings/latest"
               f"?start=1&limit={limit}&convert=USD&sort=market_cap")
        req = urllib.request.Request(url, headers={
            "X-CMC_PRO_API_KEY": CMC_API_KEY,
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        symbols = []
        for item in data.get("data", []):
            base = (item.get("symbol") or "").upper().strip()
            if base:
                symbols.append(f"{base}USDT")
        return symbols[:limit] if symbols else list(CMC_FALLBACK_SYMBOLS)
    except Exception as e:
        print(f"  erro buscando top {limit} da CoinMarketCap ({e}) — usando lista fixa de fallback")
        return list(CMC_FALLBACK_SYMBOLS)


# ----------------------------------------------------------------------------
# CENÁRIO TOURO/URSO (swing longo, diário) — pra BTC/ETH quando não tem
# sinal de swing ativo. Mesma lógica de pivô/fibonacci dos outros sinais,
# só que descreve os dois lados em vez de só disparar de um lado.
# ----------------------------------------------------------------------------

def build_bull_bear_scenario(symbol, candles_d):
    """
    Cenário touro/urso pra quando não tem sinal de swing ativo em BTC/ETH.
    Descreve os dois lados a partir do último topo/fundo confirmado — mas
    primeiro checa a DISTÂNCIA do preço atual até esse nível, porque se o
    preço já rompeu ele (pra qualquer lado) ou já ficou longe demais, a
    ideia de "short/compra perto do nível" deixa de fazer sentido como
    entrada imediata e vira só uma referência de contexto.
    """
    if not candles_d or len(candles_d) < (2 * SCENARIO_PIVOT_LEN + 20):
        return None
    pivot_highs, pivot_lows = find_pivots(candles_d, SCENARIO_PIVOT_LEN)
    leg = last_impulse_leg(pivot_highs, pivot_lows)
    if leg is None:
        return None

    price_now = candles_d[-1]["close"]
    fib_price = fib_level_price(leg, FIB_LEVEL)
    _, _, vol_ratio = volume_status(candles_d)
    vol_txt = (f"o volume atual está em {vol_ratio * 100:.0f}% da média"
               if vol_ratio is not None else "não dá pra confirmar o volume atual")
    nivel = leg["end_price"]
    dist_pct = (price_now - nivel) / nivel

    if leg["direction"] == "alta":
        # nivel = último topo confirmado dessa perna de alta
        longe = False
        if dist_pct > 0.02:
            situacao = (f"o preço já rompeu o topo anterior ({fmt_price(nivel)}) e está em "
                        f"{fmt_price(price_now)} ({dist_pct * 100:+.1f}% acima dele)")
        elif dist_pct < -0.10:
            longe = True
            situacao = (f"o preço já caiu bem abaixo do topo anterior ({fmt_price(nivel)}), "
                        f"pra {fmt_price(price_now)} ({dist_pct * 100:+.1f}%) — esse nível está "
                        f"meio distante agora, serve mais de referência do que de zona "
                        f"imediata de entrada")
        else:
            situacao = f"o preço está perto do topo anterior ({fmt_price(nivel)}), em {fmt_price(price_now)}"

        short_low, short_high = nivel * 0.995, nivel * 1.01
        entrada_txt = (
            f"se o preço voltar a se aproximar dessa região, entre {fmt_price(short_low)} e "
            f"{fmt_price(short_high)}" if longe else
            f"dá pra especular um short entre {fmt_price(short_low)} e {fmt_price(short_high)} (perto desse topo)"
        )
        bear = (
            f"🔴 Pensando em VENDER: {situacao}. Enquanto não vier rompimento de "
            f"verdade com volume forte, {entrada_txt}, stop acima "
            f"dele, mirando a zona de Fibonacci 0.382 dessa perna ({fmt_price(fib_price)}) "
            f"como primeiro alvo — principalmente porque {vol_txt}, o que "
            f"enfraquece a chance de continuidade da alta e favorece um topo "
            f"descendente."
        )
        bull = (
            f"🟢 Pensando em COMPRAR: o cenário de alta só fica confirmado de "
            f"verdade com rompimento e sustentação acima de {fmt_price(nivel)} com "
            f"volume forte. Nesse caso o setup mais saudável não é comprar o "
            f"rompimento na hora — é esperar o pullback seguinte formar um fundo "
            f"ascendente (mais alto que o anterior) antes de entrar, de olho na "
            f"região perto de {fmt_price(fib_price)} (fib 0.382 da perna atual) como "
            f"referência de onde esse próximo fundo tende a aparecer."
        )
    else:
        # nivel = último fundo confirmado dessa perna de baixa
        longe = False
        if dist_pct < -0.02:
            situacao = (f"o preço já rompeu o fundo anterior ({fmt_price(nivel)}) e está em "
                        f"{fmt_price(price_now)} ({dist_pct * 100:+.1f}% abaixo dele)")
        elif dist_pct > 0.10:
            longe = True
            situacao = (f"o preço já subiu bem acima do fundo anterior ({fmt_price(nivel)}), "
                        f"pra {fmt_price(price_now)} ({dist_pct * 100:+.1f}%) — esse nível está "
                        f"meio distante agora, serve mais de referência do que de zona "
                        f"imediata de entrada")
        else:
            situacao = f"o preço está perto do fundo anterior ({fmt_price(nivel)}), em {fmt_price(price_now)}"

        long_low, long_high = nivel * 0.99, nivel * 1.005
        entrada_txt = (
            f"se o preço voltar a se aproximar dessa região, entre {fmt_price(long_low)} e "
            f"{fmt_price(long_high)}" if longe else
            f"dá pra especular uma compra entre {fmt_price(long_low)} e {fmt_price(long_high)} (perto desse fundo)"
        )
        bull = (
            f"🟢 Pensando em COMPRAR: {situacao}. Enquanto não vier rompimento de "
            f"baixa de verdade com volume forte, {entrada_txt}, stop abaixo "
            f"dele, mirando a zona de Fibonacci 0.382 dessa perna ({fmt_price(fib_price)}) "
            f"como primeiro alvo — principalmente porque {vol_txt}, o que "
            f"enfraquece a chance de continuidade da queda e favorece um fundo "
            f"ascendente."
        )
        bear = (
            f"🔴 Pensando em VENDER: o cenário de baixa só fica confirmado de "
            f"verdade com rompimento e sustentação abaixo de {fmt_price(nivel)} com "
            f"volume forte. Nesse caso o setup mais saudável não é vender o "
            f"rompimento na hora — é esperar o pullback seguinte formar um topo "
            f"descendente (mais baixo que o anterior) antes de entrar, de olho na "
            f"região perto de {fmt_price(fib_price)} (fib 0.382 da perna atual) como "
            f"referência de onde esse próximo topo tende a aparecer."
        )

    return {"symbol": symbol, "price_now": price_now, "bull": bull, "bear": bear}


# ----------------------------------------------------------------------------
# RELATÓRIO CATEGORIZADO — enviado nos horários fixos de REPORT_TIMES_UTC
# ----------------------------------------------------------------------------

def _tier_rank(tier):
    return {"grande": 0, "médio": 1, "pequeno": 2}.get(tier, 3)


def _build_btc_eth_lines(sinais_por_moeda, candles_d_extra):
    """
    Bloco compartilhado (usado na mensagem de BTC/ETH de toda rodada E no
    relatório categorizado): sinal de swing ativo se tiver, senão os dois
    cenários (alta/baixa) com faixa de preço.
    """
    candles_d_extra = candles_d_extra or {}
    linhas = []
    for symbol in ("BTCUSDT", "ETHUSDT"):
        nome = symbol.replace("USDT", "")
        sinais = sinais_por_moeda.get(symbol) or []
        swing_sinais = [s for s in sinais if s["estilo"] != "SCALP"]
        if swing_sinais:
            sig = swing_sinais[0]
            linhas.append(f"• {nome}: sinal ativo agora — {sig['titulo']} ({sig['acao']}, {sig['timeframe']}).")
        else:
            candles_d = candles_d_extra.get(symbol)
            cenario = build_bull_bear_scenario(symbol, candles_d) if candles_d else None
            if cenario:
                linhas.append(f"• {nome}: SEM SWING ATIVO agora (preço {fmt_price(cenario['price_now'])}). Dois cenários:")
                linhas.append(f"  {cenario['bull']}")
                linhas.append(f"  {cenario['bear']}")
            else:
                linhas.append(f"• {nome}: sem sinal ativo e sem dado suficiente pro cenário agora.")
    return linhas


def select_core_extra_altcoins(watchlist, sinais_por_moeda, diagnosticos_lista_por_moeda, n=CORE_EXTRA_ALTS_N):
    """
    Escolhe as `n` melhores altcoins (fora BTC/ETH/XRP) pra entrar no status
    de toda rodada horária: prioridade máxima pra quem já tem sinal de
    verdade ativo; sem isso, quem estiver mais perto de bater um (menor
    score de diagnóstico entre os near-miss dela).
    """
    candidatos = [s for s in watchlist if s not in CORE_SYMBOLS]

    def chave(symbol):
        if sinais_por_moeda.get(symbol):
            return (0, 0.0)
        diags = diagnosticos_lista_por_moeda.get(symbol) or []
        if diags:
            return (1, min(d["score"] for d in diags))
        return (2, 999.0)

    candidatos.sort(key=chave)
    return candidatos[:n]


def build_core_status_message(core_symbols, sinais_por_moeda, diagnosticos_lista_por_moeda, candles_d_extra, market_trend="neutra", memoria_anterior=None, candles_entry_extra=None):
    """
    Mensagem única mandada em TODA rodada horária, só pros símbolos "core"
    (ver select_core_extra_altcoins) — em vez de mensagem solta pra
    qualquer moeda do watchlist de 50 que bater um sinal, o que era a
    maior fonte de poluição no Telegram. Pra quem não tem sinal de
    verdade, mostra os near-miss (diagnóstico) — é esse pedaço que antes só
    aparecia em execuções manuais, e que faz falta pra pegar um setup se
    formando (tipo RSI caindo no 15m perto de uma zona relevante no 4h)
    antes dele virar sinal de verdade.
    """
    memoria_anterior = memoria_anterior or {}
    candles_entry_extra = candles_entry_extra or {}
    nomes_core = ", ".join(s.replace("USDT", "") for s in core_symbols)
    titulo = f"🔭 VELA MONITOR — STATUS ({nomes_core})"
    if market_trend in ("alta", "baixa"):
        titulo += f"\nTendência majoritária do mercado (BTC, diário): {market_trend}"
    partes = [titulo]
    for symbol in core_symbols:
        nome = _fmt_symbol(symbol)
        sinais = sinais_por_moeda.get(symbol) or []
        if len(sinais) > 1:
            partes.append(format_combined_signal_message(symbol, sinais))
        elif sinais:
            partes.append(format_signal_message(sinais[0]))
        else:
            diags = sorted(diagnosticos_lista_por_moeda.get(symbol) or [], key=lambda d: d["score"])
            bloco = [f"🔎 {nome} — sem sinal de verdade agora"]
            if diags:
                bloco.append("Mais perto de bater (near-miss):")
                for d in diags:
                    bloco.append(f"  • {d['tipo']}: {d['texto']}")
            candles_d = candles_d_extra.get(symbol)
            cenario = build_bull_bear_scenario(symbol, candles_d) if candles_d else None
            if cenario:
                bloco.append(f"Cenário de swing (preço {fmt_price(cenario['price_now'])}):")
                bloco.append(f"  {cenario['bull']}")
                bloco.append(f"  {cenario['bear']}")
            if not diags and not cenario:
                bloco.append("Sem setup próximo e sem dado suficiente pro cenário agora.")
            price_now = cenario["price_now"] if cenario else (candles_d[-1]["close"] if candles_d else None)
            entry_candles = candles_entry_extra.get(symbol)
            if entry_candles and entry_candles.get("4h"):
                try:
                    outlook_txt = build_entry_outlook(
                        entry_candles["4h"], entry_candles.get("15m"),
                        entry_candles.get("1h"), entry_candles.get("5m"),
                    )
                except Exception:
                    outlook_txt = None
                if outlook_txt:
                    bloco.append("")
                    bloco.append("📍 Fique de olho:")
                    bloco.append(outlook_txt)
                try:
                    bandeira = classifica_bandeira(symbol, entry_candles["4h"], timeframe_label="4h")
                except Exception:
                    bandeira = None
                if bandeira and bandeira["status"] != "indefinida":
                    bloco.append("")
                    bloco.append(bandeira["texto"])
                candles_3d = entry_candles.get("3d")
                if candles_3d and len(candles_3d) >= (2 * PIVOT_LEN + 10):
                    try:
                        bandeira_3d = classifica_bandeira(symbol, candles_3d, timeframe_label="3D")
                    except Exception:
                        bandeira_3d = None
                    if bandeira_3d and bandeira_3d["status"] != "indefinida":
                        bloco.append("")
                        bloco.append(bandeira_3d["texto"])
            bloco.append("")
            bloco.append(_ultima_operacao_texto(memoria_anterior.get(symbol), price_now))
            partes.append("\n".join(bloco))
    partes.append("Leitura técnica automática — não é recomendação de investimento.")
    return "\n\n".join(partes)


def build_full_categorized_report(watchlist, tiers, sinais_por_moeda, candles_d_extra=None, market_trend="neutra",
                                   only_core=False):
    """
    Organiza o que a varredura já achou por horizonte de operação, em vez de
    mandar sinal solto: swing principal (BTC/ETH sempre aparecem), swing
    secundário (XRP + top 10 CoinMarketCap), altcoins pequenas, scalp e
    bottom fishing — cada seção limitada e filtrada pelas melhores, pra não
    lotar o Telegram (pedido depois de um relatório de diagnóstico que saiu
    com quase 40 moedas de uma vez).

    Com `only_core=True` (restrição temporária só BTC/ETH — ver
    SOMENTE_CORE_SYMBOLS), as seções que dependem de outras moedas (swing
    secundário, altcoins pequenas, scalp, bottom fishing) nem tentam buscar
    dado de outra moeda — só avisam que estão pausadas.
    """
    candles_d_extra = candles_d_extra or {}
    linhas = ["📊 VELA MONITOR — RELATÓRIO DO DIA (swing)", ""]
    if market_trend in ("alta", "baixa"):
        linhas.append(f"Tendência majoritária do mercado (BTC, diário): {market_trend}")
        linhas.append("")

    # 1) Swing principal — BTC e ETH sempre aparecem
    linhas.append("🏆 SWING PRINCIPAL")
    linhas.extend(_build_btc_eth_lines(sinais_por_moeda, candles_d_extra))
    linhas.append("")

    if only_core:
        linhas.append(
            "Restrito a BTC/ETH por enquanto — swing secundário, altcoins "
            "pequenas, scalp e bottom fishing de outras moedas estão pausados "
            "(SOMENTE_CORE_SYMBOLS)."
        )
        linhas.append("")
        linhas.append(
            "⚠️ Leitura automática baseada nas mesmas regras dos sinais do bot — não "
            "é recomendação de investimento."
        )
        return "\n".join(linhas)

    # 2) Swing secundário — XRP + top 10 CoinMarketCap (menos BTC/ETH, já cobertos acima)
    linhas.append("📈 SWING SECUNDÁRIO (XRP + top 10 mercado)")
    try:
        cmc_top = fetch_cmc_top_symbols()
    except Exception as e:
        print(f"  erro buscando top 10 CMC pro relatório ({e})")
        cmc_top = list(CMC_FALLBACK_SYMBOLS)
    secundario_symbols = list(dict.fromkeys(["XRPUSDT"] + cmc_top))
    secundario_symbols = [s for s in secundario_symbols if s not in ("BTCUSDT", "ETHUSDT")]
    destaques = []
    for symbol in secundario_symbols:
        sinais = sinais_por_moeda.get(symbol)
        if sinais is None:
            try:
                sinais, _ = analyze_symbol(symbol, tier=tiers.get(symbol), market_trend=market_trend)
            except Exception:
                sinais = []
        if sinais:
            sig = sinais[0]
            destaques.append(f"• {_fmt_symbol(symbol)}: {sig['titulo']} ({sig['acao']}, {sig['timeframe']}).")
    if destaques:
        linhas.extend(destaques)
    else:
        linhas.append("• Nenhuma dessas moedas com sinal ativo agora.")
    linhas.append("")

    # 3) Altcoins pequenas em setup
    linhas.append(f"🔍 ALTCOINS PEQUENAS EM SETUP (até {REPORT_SMALL_ALTS_N})")
    pequenas = []
    for symbol in watchlist:
        if tiers.get(symbol) != "pequeno":
            continue
        sinais = sinais_por_moeda.get(symbol) or []
        if sinais:
            pequenas.append((symbol, sinais[0]))
    if pequenas:
        for symbol, sig in pequenas[:REPORT_SMALL_ALTS_N]:
            linhas.append(f"• {_fmt_symbol(symbol)}: {sig['titulo']} ({sig['acao']}, {sig['timeframe']}).")
    else:
        linhas.append("• Nenhuma altcoin pequena com setup ativo agora.")
    linhas.append("")

    # 4) Scalp — só os melhores (ordem do watchlist já é por volume/liquidez)
    linhas.append(f"⚡ SCALP (até {REPORT_SCALP_N})")
    scalps = []
    for symbol in watchlist:
        for sig in (sinais_por_moeda.get(symbol) or []):
            if sig["estilo"] == "SCALP":
                scalps.append((symbol, sig))
    if scalps:
        for symbol, sig in scalps[:REPORT_SCALP_N]:
            linhas.append(f"• {_fmt_symbol(symbol)}: {sig['titulo']} ({sig['acao']}).")
    else:
        linhas.append("• Nenhum scalp ativo agora.")
    linhas.append("")

    # 5) Bottom fishing — prioriza porte maior (proxy de marketcap/liquidez)
    linhas.append(f"🏺 BOTTOM FISHING (até {REPORT_BOTTOM_FISHING_N})")
    bottoms = []
    for symbol in watchlist:
        for sig in (sinais_por_moeda.get(symbol) or []):
            if sig["estilo"] == "POSIÇÃO":
                bottoms.append((symbol, sig))
    bottoms.sort(key=lambda item: _tier_rank(tiers.get(item[0])))
    if bottoms:
        for symbol, sig in bottoms[:REPORT_BOTTOM_FISHING_N]:
            linhas.append(f"• {_fmt_symbol(symbol)}: {sig['titulo']} — porte: {tiers.get(symbol, '?')}.")
    else:
        linhas.append("• Nenhuma moeda batendo o critério de bottom fishing agora.")
    linhas.append("")

    linhas.append(
        "⚠️ Leitura automática baseada nas mesmas regras dos sinais do bot — não "
        "é recomendação de investimento. Petróleo, ouro e mercado americano ainda "
        "não entram nessa versão do relatório (só cripto por enquanto)."
    )
    return "\n".join(linhas)


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

def main():
    is_manual = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    symbol_query = os.environ.get("SYMBOL_QUERY", "").strip()
    agora = datetime.now(timezone.utc)
    agora_min = agora.hour * 60 + agora.minute
    is_report_time = (not is_manual) and any(
        abs(agora_min - (h * 60 + m)) <= REPORT_TIME_TOLERANCE_MIN
        for h, m in REPORT_TIMES_UTC
    )
    # A varredura pesada no watchlist inteiro (50 moedas x ~5 chamadas cada —
    # o que estava deixando toda rodada demorada) só roda nos horários do
    # relatório categorizado, ou numa execução manual SEM moeda específica
    # pedida (aí faz sentido ver o diagnóstico de todo o watchlist). Se você
    # roda manual só pra perguntar de uma moeda (campo "symbol" preenchido),
    # pula a varredura pesada — vai direto pra análise daquela moeda, bem
    # mais rápido. Nas rodadas normais de hora em hora, o bot analisa só
    # CORE_SYMBOLS (BTC e ETH).
    do_full_scan = is_report_time or (is_manual and not symbol_query)
    # Com SOMENTE_CORE_SYMBOLS ligado, a varredura completa fica DESLIGADA de
    # verdade (nem roda por baixo dos panos) — o bot nunca analisa nem manda
    # nada de nenhuma moeda fora de CORE_SYMBOLS.
    full_scan_ativo = do_full_scan and not SOMENTE_CORE_SYMBOLS

    # Tendência majoritária do mercado (a partir do BTC, cruzando diário +
    # semanal + mensal) — calculada uma vez por rodada e aplicada a TODO
    # sinal COMPRAR/VENDER de toda moeda, pra nunca sugerir operar contra a
    # maré (ex.: sinal de venda com o mercado em tendência de alta clara em
    # todos os tempos gráficos).
    try:
        btc_candles_trend = fetch_klines("BTCUSDT", "1d", MARKET_TREND_EMA_SLOW + 20)
        btc_candles_trend_w = fetch_klines("BTCUSDT", "1w", MARKET_TREND_WEEKLY_EMA_SLOW + 20)
        btc_candles_trend_m = fetch_klines("BTCUSDT", "1M", MARKET_TREND_MONTHLY_EMA_SLOW + 20)
        market_trend = detect_market_trend(btc_candles_trend, btc_candles_trend_w, btc_candles_trend_m)
    except Exception as e:
        print(f"  erro calculando tendência majoritária do mercado ({e}) — seguindo sem filtro de tendência")
        market_trend = "neutra"
    print(f"[{datetime.now(timezone.utc).isoformat()}] Tendência majoritária do mercado (BTC, diário+semanal+mensal): {market_trend}")

    watchlist, tiers = [], {}
    sinais_por_moeda = {}
    todos_diagnosticos = []
    encontrados = 0

    if full_scan_ativo:
        print(f"[{datetime.now(timezone.utc).isoformat()}] Buscando os {TOP_N_SYMBOLS} pares "
              f"USDT de maior volume na Binance...")
        try:
            top_symbols = fetch_top_usdt_symbols(TOP_N_SYMBOLS)
            watchlist = [s for s, _ in top_symbols]
            tiers = classify_volume_tiers(top_symbols)
            if not watchlist:
                raise ValueError("lista vazia")
        except Exception as e:
            print(f"  erro ao buscar watchlist dinâmica ({e}) — usando lista fixa de fallback")
            watchlist = FALLBACK_WATCHLIST
            tiers = {}

        print(f"[{datetime.now(timezone.utc).isoformat()}] Iniciando varredura completa de "
              f"{len(watchlist)} moedas (pullback + exaustão + cascata scalp + confluência + "
              f"bottom fishing + reversão leve + rompimento falho + consolidação/range)...")
        for symbol in watchlist:
            try:
                sinais, diagnosticos = analyze_symbol(symbol, tier=tiers.get(symbol), market_trend=market_trend)
            except Exception as e:
                print(f"  {symbol}: erro na análise ({e})")
                continue
            sinais_por_moeda[symbol] = sinais
            if sinais:
                print(f"  {symbol}: {len(sinais)} sinal(is) — {', '.join(s['titulo'] for s in sinais)}")
            else:
                print(f"  {symbol}: sem setup no momento")
            todos_diagnosticos.extend(diagnosticos)

        print(f"[{datetime.now(timezone.utc).isoformat()}] Verificando dominância BTC/altseason "
              f"e termômetro de ciclo...")
        try:
            btc_return, avg_alt_return = compute_market_returns(watchlist)
        except Exception as e:
            print(f"  erro calculando retornos de mercado ({e})")
            btc_return, avg_alt_return = None, None

        try:
            dom_sig = check_dominance_altseason(btc_return, avg_alt_return)
            if dom_sig:
                encontrados += 1
                msg = format_signal_message(dom_sig)
                print("-" * 60)
                print(msg)
                ok = send_telegram_message(msg)
                print("  -> enviado pro Telegram" if ok else "  -> FALHOU ao enviar")
            else:
                print("  sem divergência relevante entre BTC e as alts no momento")
        except Exception as e:
            print(f"  erro no check de dominância ({e})")

        try:
            cycle_sig = check_cycle_phase(btc_return, avg_alt_return)
            if cycle_sig:
                encontrados += 1
                msg = format_signal_message(cycle_sig)
                print("-" * 60)
                print(msg)
                ok = send_telegram_message(msg)
                print("  -> enviado pro Telegram" if ok else "  -> FALHOU ao enviar")
            else:
                print("  sem sinal de mania de memecoin no momento")
        except Exception as e:
            print(f"  erro no termômetro de ciclo ({e})")
    else:
        if SOMENTE_CORE_SYMBOLS:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Restrito a {', '.join(CORE_SYMBOLS)} por "
                  f"enquanto (SOMENTE_CORE_SYMBOLS) — nenhuma outra moeda entra na análise.")
        else:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Rodada rápida (só {', '.join(CORE_SYMBOLS)}) "
                  f"— a varredura completa do watchlist só roda nos horários do relatório ou manualmente.")
        for symbol in CORE_SYMBOLS:
            try:
                sinais, diagnosticos = analyze_symbol(symbol, market_trend=market_trend)
            except Exception as e:
                print(f"  {symbol}: erro na análise ({e})")
                continue
            sinais_por_moeda[symbol] = sinais
            todos_diagnosticos.extend(diagnosticos)
            print(f"  {symbol}: {len(sinais)} sinal(is)" if sinais else f"  {symbol}: sem setup no momento")

    diagnosticos_lista_por_moeda = {}
    for d in todos_diagnosticos:
        diagnosticos_lista_por_moeda.setdefault(d["symbol"], []).append(d)

    sinais_moeda_count = sum(len(s) for s in sinais_por_moeda.values())
    encontrados += sinais_moeda_count

    print(f"[{datetime.now(timezone.utc).isoformat()}] Montando status core ({', '.join(CORE_SYMBOLS)}"
          f"{' + destaques' if full_scan_ativo else ''})...")
    if full_scan_ativo:
        extra_alts = select_core_extra_altcoins(watchlist, sinais_por_moeda, diagnosticos_lista_por_moeda)
        print(f"  altcoins escolhidas pro status dessa rodada: {', '.join(extra_alts) or '(nenhuma)'}")
    else:
        extra_alts = []
    core_symbols = CORE_SYMBOLS + extra_alts
    candles_d_extra = {}
    for sym in core_symbols:
        try:
            candles_d_extra[sym] = fetch_klines(sym, "1d", 200)
        except Exception as e:
            print(f"  erro buscando candle diário de {sym} ({e})")

    # candles extra só pros símbolos "core" de verdade (BTC/ETH), pra montar
    # o "📍 Fique de olho" (próxima EMA/suporte relevante, mesmo longe ainda)
    # dentro do status que já roda toda hora — sem isso, esse aviso só
    # aparecia numa consulta manual por moeda.
    candles_entry_extra = {}
    for sym in CORE_SYMBOLS:
        try:
            candles_entry_extra[sym] = {
                "4h": fetch_klines(sym, INTERVAL, KLINES_LIMIT),
                "15m": fetch_klines(sym, "15m", CONFLUENCE_15M_LIMIT),
                "1h": fetch_klines(sym, "1h", 100),
                "5m": fetch_klines(sym, "5m", CONFLUENCE_5M_LIMIT),
                "3d": fetch_klines(sym, "3d", 200),
            }
        except Exception as e:
            print(f"  erro buscando candles extra (fique de olho) de {sym} ({e})")

    try:
        memoria_anterior = atualiza_memoria_ultima_operacao(sinais_por_moeda)
    except Exception as e:
        print(f"  erro atualizando a memória da última operação ({e})")
        memoria_anterior = {}

    try:
        status_msg = build_core_status_message(core_symbols, sinais_por_moeda, diagnosticos_lista_por_moeda, candles_d_extra, market_trend=market_trend, memoria_anterior=memoria_anterior, candles_entry_extra=candles_entry_extra)
        ok = send_telegram_message(status_msg)
        print("  -> status core enviado" if ok else "  -> FALHOU ao enviar o status core")
    except Exception as e:
        print(f"  erro montando o status core ({e})")

    if is_report_time:
        print(f"[{datetime.now(timezone.utc).isoformat()}] Horário de relatório categorizado — montando...")
        try:
            report_msg = build_full_categorized_report(watchlist, tiers, sinais_por_moeda, candles_d_extra,
                                                         market_trend=market_trend, only_core=SOMENTE_CORE_SYMBOLS)
            ok = send_telegram_message(report_msg)
            print("  -> relatório categorizado enviado" if ok else "  -> FALHOU ao enviar o relatório categorizado")
        except Exception as e:
            print(f"  erro montando o relatório categorizado ({e})")

    if is_manual:
        if do_full_scan:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Montando diagnóstico de proximidade...")
            try:
                diag_msg = build_diagnostic_message(todos_diagnosticos)
                ok = send_telegram_message(diag_msg)
                print("  -> diagnóstico enviado" if ok else "  -> FALHOU ao enviar o diagnóstico")
            except Exception as e:
                print(f"  erro montando o diagnóstico ({e})")

        if symbol_query:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Analisando moeda pedida: {symbol_query}")
            try:
                deep_msg = build_symbol_deep_dive(symbol_query, market_trend=market_trend)
            except Exception as e:
                deep_msg = f"⚠️ Não consegui analisar {symbol_query}: {e}"
            ok = send_telegram_message(deep_msg)
            print("  -> análise da moeda enviada" if ok else "  -> FALHOU ao enviar a análise da moeda")

    if sinais_moeda_count == 0:
        print(f"[{datetime.now(timezone.utc).isoformat()}] Nenhum sinal de moeda nessa "
              f"rodada — buscando manchetes da Reuters como fallback...")
        try:
            news_msg = build_news_fallback_message()
            if news_msg:
                ok = send_telegram_message(news_msg)
                print("  -> manchetes enviadas" if ok else "  -> FALHOU ao enviar as manchetes")
            else:
                print("  sem NEWS_API_KEY configurada ou sem manchetes disponíveis — nada enviado")
        except Exception as e:
            print(f"  erro no fallback de notícias ({e})")

    print(f"[{datetime.now(timezone.utc).isoformat()}] Varredura concluída. "
          f"{encontrados} sinal(is) encontrado(s).")


if __name__ == "__main__":
    main()
