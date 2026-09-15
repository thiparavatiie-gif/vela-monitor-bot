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
#   3) CASCATA DE RSI (scalp) — RSI em sobrevenda/sobrecompra ao mesmo
#      tempo no 15m E no 1h: a ideia da "cascata fractal" do canal, onde a
#      sobrevenda/sobrecompra nos tempos curtos antecede um repique/correção
#      rápida antes mesmo do diário se mexer.
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
#   8) MERCADO EM CONSOLIDAÇÃO / RANGE (swing curto) — quando não tem
#      tendência clara (últimos candles de 4h comprimidos numa faixa
#      estreita) e o preço está perto de uma das bordas dessa faixa, sugere
#      operar o próprio range: comprar perto do fundo mirando o topo, ou
#      vender perto do topo mirando o fundo, com stop logo fora da faixa. É
#      o "o que fazer quando o mercado fica parado", em vez de ficar sem
#      nenhuma ideia quando não tem uma tendência definida.
#
#   9) CONFLUÊNCIA MULTI-INDICADOR (mais de um timeframe) — em vez de exigir
#      só UM critério isolado, soma quantos fatores técnicos diferentes
#      (fibonacci em mais de um nível — 0.382/0.5/0.618 —, EMAs em mais de
#      um período — 12/21/50/200 — no 4h e no 15m, e RSI em sobrevenda/
#      sobrecompra no 15m e no 1h) estão alinhados na mesma direção ao
#      mesmo tempo. Pensado pro tipo de leitura manual que junta "fib 0.618
#      no 15m perto da EMA200, aproximando da EMA12 no 4h" — cada indicador
#      sozinho não dispara os outros sinais, mas a combinação de vários
#      sim.
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

# --- Cascata de RSI (scalp) ---
SCALP_RSI_OVERSOLD = 30
SCALP_RSI_OVERBOUGHT = 70

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
# de 50, que virou a maior fonte de poluição no Telegram). BTC/ETH/XRP são
# fixos; as outras CORE_EXTRA_ALTS_N são escolhidas a cada rodada pelas que
# estão com sinal ativo ou mais perto de bater um (ver
# select_core_extra_altcoins) ---
CORE_SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
CORE_EXTRA_ALTS_N = 2

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

    leg_txt = f"{leg['start_price']:.4g} → {leg['end_price']:.4g}"
    detalhes = [
        f"Preço agora: {price_now:.4g}",
        f"Zona Fibonacci 0.382: {fib_price:.4g}",
        f"Stop sugerido: {stop:.4g}",
        f"Alvos: {' > '.join(f'{t:.4g}' for t in targets)}",
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
        checklist.append((f"Preço {'acima' if leg['direction'] == 'alta' else 'abaixo'} da EMA{EMA_TREND_PERIOD} ({ema:.4g})", segurando))

    return {
        "symbol": symbol, "estilo": "SWING", "acao": acao,
        "titulo": f"Pullback ({leg['direction']}, {leg_txt})",
        "timeframe": INTERVAL,
        "detalhes": detalhes,
        "checklist": checklist,
        "explicacao": (
            f"Correção dentro da zona de Fibonacci 0.382 da última perna de "
            f"{leg['direction']}, com {estrutura_txt} confirmando que a estrutura "
            f"continua a favor do movimento."
        ),
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
    detalhes = [
        f"Preço agora: {price_now:.4g}",
        f"RSI ({INTERVAL}): {rsi:.1f}",
        f"Volume: {vol_ratio:.1f}x a média",
    ]
    if acao == "VENDER" and pivot_lows:
        detalhes.append(f"Alvo técnico: {pivot_lows[-1][1]:.4g} (último fundo relevante no {INTERVAL})")
    elif acao == "COMPRAR" and pivot_highs:
        detalhes.append(f"Alvo técnico: {pivot_highs[-1][1]:.4g} (último topo relevante no {INTERVAL})")

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
        "explicacao": (
            f"RSI muito esticado ({rsi:.1f}) combinado com volume {vol_ratio:.1f}x acima "
            f"da média costuma marcar exaustão do movimento — a força predominante "
            f"pode estar perto de se esgotar."
        ),
        "aviso": None,
    }


# ----------------------------------------------------------------------------
# SINAL 3 — CASCATA DE RSI (scalp)
# ----------------------------------------------------------------------------

def check_scalp_cascade(symbol, candles_15m, candles_1h):
    rsi_15m = compute_rsi([c["close"] for c in candles_15m])
    rsi_1h = compute_rsi([c["close"] for c in candles_1h])
    if rsi_15m is None or rsi_1h is None:
        return None

    if rsi_15m <= SCALP_RSI_OVERSOLD and rsi_1h <= SCALP_RSI_OVERSOLD:
        acao, lado = "COMPRAR", "sobrevenda"
    elif rsi_15m >= SCALP_RSI_OVERBOUGHT and rsi_1h >= SCALP_RSI_OVERBOUGHT:
        acao, lado = "VENDER", "sobrecompra"
    else:
        return None

    price_now = candles_15m[-1]["close"]
    pivot_highs_1h, pivot_lows_1h = find_pivots(candles_1h, PIVOT_LEN)
    detalhes = [
        f"Preço agora: {price_now:.4g}",
        f"RSI 15m: {rsi_15m:.1f}  |  RSI 1h: {rsi_1h:.1f}",
    ]
    if acao == "VENDER" and pivot_lows_1h:
        detalhes.append(f"Alvo técnico: {pivot_lows_1h[-1][1]:.4g} (último fundo no 1h)")
    elif acao == "COMPRAR" and pivot_highs_1h:
        detalhes.append(f"Alvo técnico: {pivot_highs_1h[-1][1]:.4g} (último topo no 1h)")

    checklist = [
        (f"RSI 15m em {lado} ({rsi_15m:.1f})", True),
        (f"RSI 1h em {lado} ({rsi_1h:.1f})", True),
    ]

    return {
        "symbol": symbol, "estilo": "SCALP", "acao": acao,
        "titulo": f"Cascata de RSI — {lado} no 15m e 1h",
        "timeframe": "15m + 1h",
        "detalhes": detalhes,
        "checklist": checklist,
        "explicacao": (
            "Os dois timeframes curtos em " + lado + " ao mesmo tempo — pela lógica "
            "da cascata fractal, isso tende a antecipar um repique/correção rápida "
            "antes mesmo do timeframe diário reagir. Sinal de movimento curto, não "
            "de mudança de tendência maior."
        ),
        "aviso": "Sinal de scalp: movimento rápido, use gestão de risco mais apertada.",
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

    detalhes = [
        f"Preço agora: {price_now:.4g}",
        f"Máxima histórica: {ath:.4g}  ({drawdown * 100:.0f}% abaixo)",
        f"Zona de entrada sugerida: {entry_low:.4g} – {entry_high:.4g}",
        f"Stop sugerido: {stop:.4g}",
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

    detalhes = [
        f"Preço agora: {price_now:.4g}",
        f"Topo dos últimos {lookback}d: {swing_high_price:.4g}  ({drawdown * 100:.0f}% abaixo)",
        f"Zona de entrada sugerida: {entry_low:.4g} – {entry_high:.4g}",
        f"Stop sugerido: {stop:.4g}",
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
                        f"Preço agora: {price_now:.4g}",
                        f"Suporte rompido e recuperado: {ref_price:.4g}",
                        f"Alvo técnico (movimento medido): {alvo:.4g}",
                        f"Stop sugerido: {stop:.4g}",
                    ],
                    "checklist": [
                        ("Suporte relevante identificado por pivô", True),
                        ("Rompimento do suporte sem continuidade de queda", True),
                        ("Recuperação de volta pra cima do nível", True),
                        (f"Volume forte no rompimento/recuperação (≥{FAILED_BREAK_VOLUME_RATIO}x)", True),
                    ],
                    "explicacao": (
                        f"O preço rompeu o suporte em {ref_price:.4g} mas não teve "
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
                        f"Preço agora: {price_now:.4g}",
                        f"Resistência rompida e devolvida: {ref_price:.4g}",
                        f"Alvo técnico (movimento medido): {alvo:.4g}",
                        f"Stop sugerido: {stop:.4g}",
                    ],
                    "checklist": [
                        ("Resistência relevante identificada por pivô", True),
                        ("Rompimento da resistência sem continuidade de alta", True),
                        ("Devolução de volta pra dentro do nível", True),
                        (f"Volume forte no rompimento/devolução (≥{FAILED_BREAK_VOLUME_RATIO}x)", True),
                    ],
                    "explicacao": (
                        f"O preço rompeu a resistência em {ref_price:.4g} mas não teve "
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
# SINAL 8 — MERCADO EM CONSOLIDAÇÃO / RANGE (swing curto)
# ----------------------------------------------------------------------------

def check_range_market(symbol, candles):
    """
    "O que fazer quando o mercado fica parado": em vez de precisar de uma
    tendência clara, procura uma faixa estreita (RANGE_MAX_PCT de amplitude)
    nos últimos RANGE_LOOKBACK candles de 4h. Se o preço está perto de uma
    das bordas dessa faixa, sugere operar o próprio range — comprar perto do
    fundo mirando o topo, ou vender perto do topo mirando o fundo — com stop
    logo fora da faixa. Só dispara perto das bordas: no meio do range não
    tem um ponto de entrada com risco/retorno bom.
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

    if posicao <= RANGE_EDGE_ZONE_PCT:
        acao, lado_txt = "COMPRAR", "perto do fundo do range"
        stop = avoid_round_number_stop(range_low * 0.995, "compra")
        alvo = range_high
    elif posicao >= (1 - RANGE_EDGE_ZONE_PCT):
        acao, lado_txt = "VENDER", "perto do topo do range"
        stop = avoid_round_number_stop(range_high * 1.005, "venda")
        alvo = range_low
    else:
        return None  # parado, mas no meio da faixa — sem ponto de entrada bom agora

    checklist = [
        (f"Faixa estreita nos últimos {RANGE_LOOKBACK} candles ({range_pct * 100:.1f}% ≤ {RANGE_MAX_PCT * 100:.0f}%)", True),
        (f"Preço {lado_txt}", True),
    ]

    return {
        "symbol": symbol, "estilo": "RANGE", "acao": acao,
        "titulo": "Mercado em consolidação — operação de range",
        "timeframe": INTERVAL,
        "detalhes": [
            f"Preço agora: {price_now:.4g} ({lado_txt})",
            f"Range dos últimos {RANGE_LOOKBACK} candles: {range_low:.4g} – {range_high:.4g} "
            f"({range_pct * 100:.1f}% de amplitude)",
            f"Alvo (borda oposta do range): {alvo:.4g}",
            f"Stop sugerido: {stop:.4g}",
        ],
        "checklist": checklist,
        "explicacao": (
            f"Sem tendência clara — os últimos candles ficaram comprimidos numa faixa "
            f"estreita ({range_pct * 100:.1f}% de amplitude). Quando não tem direção "
            f"definida, a ideia é operar o próprio range: entrar perto de uma borda "
            f"mirando a borda oposta, com stop logo fora dela."
        ),
        "aviso": (
            "Setup de range tende a ter alvo e risco menores que um movimento de "
            "tendência — considere reduzir o tamanho da posição em relação a um "
            "swing/pullback de verdade, e saia se o preço romper a faixa com força "
            "(aí deixou de ser range)."
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


def _confluence_fatores(candles_4h, candles_15m, candles_1h):
    """
    Monta a lista de fatores técnicos alinhados (fibonacci de mais de um
    nível, EMAs de mais de um período em dois timeframes, RSI em
    sobrevenda/sobrecompra no 15m e no 1h) na direção sugerida pela última
    perna de 4h. Compartilhado pelo sinal de verdade e pelo diagnóstico
    (near-miss) — só muda o corte de quantos fatores contam como "bastante".
    """
    if len(candles_4h) < (2 * PIVOT_LEN + 10) or not candles_15m or not candles_1h:
        return None
    pivot_highs, pivot_lows = find_pivots(candles_4h, PIVOT_LEN)
    leg = last_impulse_leg(pivot_highs, pivot_lows)
    if leg is None:
        return None

    price_now = candles_4h[-1]["close"]
    price_15m = candles_15m[-1]["close"]
    rsi_15m = compute_rsi([c["close"] for c in candles_15m])
    rsi_1h = compute_rsi([c["close"] for c in candles_1h])

    fatores = []
    for level in CONFLUENCE_FIB_LEVELS:
        fib_price = fib_level_price(leg, level)
        if price_in_fib_zone(price_now, fib_price, CONFLUENCE_FIB_TOLERANCE):
            fatores.append(f"Preço na zona de Fibonacci {level} da perna de 4h ({fib_price:.4g})")
            break  # um nível já basta como fator — não soma os 3 juntos

    for periodo, ema, dist in _ema_hits([c["close"] for c in candles_4h], price_now):
        fatores.append(f"Preço a {abs(dist) * 100:.1f}% da EMA{periodo} no 4h ({ema:.4g})")

    for periodo, ema, dist in _ema_hits([c["close"] for c in candles_15m], price_15m):
        fatores.append(f"Preço a {abs(dist) * 100:.1f}% da EMA{periodo} no 15m ({ema:.4g})")

    if leg["direction"] == "alta":
        if rsi_15m is not None and rsi_15m <= CONFLUENCE_RSI_OVERSOLD:
            fatores.append(f"RSI do 15m em sobrevenda ({rsi_15m:.1f})")
        if rsi_1h is not None and rsi_1h <= CONFLUENCE_RSI_OVERSOLD:
            fatores.append(f"RSI do 1h em sobrevenda ({rsi_1h:.1f})")
    else:
        if rsi_15m is not None and rsi_15m >= CONFLUENCE_RSI_OVERBOUGHT:
            fatores.append(f"RSI do 15m em sobrecompra ({rsi_15m:.1f})")
        if rsi_1h is not None and rsi_1h >= CONFLUENCE_RSI_OVERBOUGHT:
            fatores.append(f"RSI do 1h em sobrecompra ({rsi_1h:.1f})")

    return {"leg": leg, "price_now": price_now, "price_15m": price_15m, "fatores": fatores}


def check_confluence(symbol, candles_4h, candles_15m, candles_1h):
    """
    Em vez de exigir só UM critério isolado (fib OU EMA OU RSI), soma
    quantos fatores técnicos diferentes — fibonacci (0.382/0.5/0.618) da
    perna de 4h, EMAs (12/21/50/200) no 4h e no 15m, e RSI em sobrevenda/
    sobrecompra no 15m e no 1h — estão alinhados na mesma direção ao mesmo
    tempo. Pensado pro tipo de leitura manual que junta "fib 0.618 no 15m
    perto da EMA200, aproximando da EMA12 no 4h": cada indicador sozinho
    não vira sinal de verdade em nenhum dos outros checks, mas a
    combinação de vários ao mesmo tempo sim.
    """
    dados = _confluence_fatores(candles_4h, candles_15m, candles_1h)
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
        f"Preço agora (4h): {price_now:.4g}  |  Preço agora (15m): {price_15m:.4g}",
        f"Fatores alinhados ({len(fatores)}):",
    ]
    detalhes.extend(f"  • {f}" for f in fatores)
    detalhes.append(f"Alvo técnico: {alvo:.4g} (último {'topo' if leg['direction'] == 'alta' else 'fundo'} da perna de 4h)")
    detalhes.append(f"Stop sugerido: {stop:.4g}")

    return {
        "symbol": symbol, "estilo": "CONFLUÊNCIA", "acao": acao,
        "titulo": titulo,
        "timeframe": "4h + 15m + 1h",
        "detalhes": detalhes,
        "checklist": [(f, True) for f in fatores],
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


def diagnose_confluence(candles_4h, candles_15m, candles_1h):
    """
    Versão near-miss do check_confluence: mostra os fatores já alinhados
    mesmo quando ainda não chegou no mínimo pra virar sinal de verdade.
    """
    dados = _confluence_fatores(candles_4h, candles_15m, candles_1h)
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
                  f"0.382 ({fib_price:.4g}) — {estrutura_txt}."),
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


def diagnose_scalp(rsi_15m, rsi_1h):
    if rsi_15m is None or rsi_1h is None:
        return None
    if rsi_15m <= SCALP_RSI_OVERSOLD and rsi_1h <= SCALP_RSI_OVERSOLD:
        return None  # já teria virado sinal de verdade
    if rsi_15m >= SCALP_RSI_OVERBOUGHT and rsi_1h >= SCALP_RSI_OVERBOUGHT:
        return None
    algum_sobrevenda = rsi_15m <= SCALP_RSI_OVERSOLD or rsi_1h <= SCALP_RSI_OVERSOLD
    outro_perto_sobrevenda = (rsi_15m <= SCALP_RSI_OVERSOLD + SCALP_DIAG_RSI_BAND
                               and rsi_1h <= SCALP_RSI_OVERSOLD + SCALP_DIAG_RSI_BAND)
    if algum_sobrevenda and outro_perto_sobrevenda:
        dist = max(abs(rsi_15m - SCALP_RSI_OVERSOLD), abs(rsi_1h - SCALP_RSI_OVERSOLD))
        return {
            "tipo": "Cascata de RSI",
            "score": dist / SCALP_DIAG_RSI_BAND,
            "texto": (f"Cascata scalp (sobrevenda): RSI 15m {rsi_15m:.0f} / RSI 1h "
                      f"{rsi_1h:.0f} — só falta o outro timeframe confirmar."),
        }
    algum_sobrecompra = rsi_15m >= SCALP_RSI_OVERBOUGHT or rsi_1h >= SCALP_RSI_OVERBOUGHT
    outro_perto_sobrecompra = (rsi_15m >= SCALP_RSI_OVERBOUGHT - SCALP_DIAG_RSI_BAND
                                and rsi_1h >= SCALP_RSI_OVERBOUGHT - SCALP_DIAG_RSI_BAND)
    if algum_sobrecompra and outro_perto_sobrecompra:
        dist = max(abs(SCALP_RSI_OVERBOUGHT - rsi_15m), abs(SCALP_RSI_OVERBOUGHT - rsi_1h))
        return {
            "tipo": "Cascata de RSI",
            "score": dist / SCALP_DIAG_RSI_BAND,
            "texto": (f"Cascata scalp (sobrecompra): RSI 15m {rsi_15m:.0f} / RSI 1h "
                      f"{rsi_1h:.0f} — só falta o outro timeframe confirmar."),
        }
    return None


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
                    "texto": f"Rompeu o suporte em {ref_price:.4g} mas falta confirmar: {', '.join(faltando)}.",
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
                    "texto": f"Rompeu a resistência em {ref_price:.4g} mas falta confirmar: {', '.join(faltando)}.",
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
            "tipo": "Mercado em consolidação",
            "score": 0.5,
            "texto": (f"Mercado parado ({range_pct * 100:.1f}% de amplitude, "
                      f"{range_low:.4g}-{range_high:.4g}) — no meio do range, "
                      f"aguardando aproximar de uma borda pra ter entrada."),
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
            sym = d["symbol"].replace("USDT", "/USDT")
            linhas.append(f"• {sym} — {d['texto']}")
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


def build_symbol_deep_dive(symbol_input):
    symbol = normalize_symbol(symbol_input)
    if not symbol:
        return "⚠️ Não veio nenhuma moeda no campo de análise."

    try:
        candles_4h = fetch_klines(symbol, INTERVAL, KLINES_LIMIT)
        candles_d = fetch_klines(symbol, "1d", 200)
        candles_w = fetch_klines(symbol, "1w", 1000)
        candles_15m = fetch_klines(symbol, "15m", CONFLUENCE_15M_LIMIT)
        candles_1h = fetch_klines(symbol, "1h", 100)
    except urllib.error.HTTPError as e:
        return (f"⚠️ Não consegui buscar dados de {symbol} na Binance (erro {e.code}). "
                f"Confira se o par existe (ex.: SOLUSDT, XRPUSDT).")
    except Exception as e:
        return f"⚠️ Erro buscando dados de {symbol}: {e}"

    if not candles_4h:
        return f"⚠️ Não veio nenhum candle 4h pra {symbol} — confira se o par existe."

    price_now = candles_4h[-1]["close"]
    linhas = [f"🧭 VELA MONITOR — ANÁLISE — {symbol.replace('USDT', '/USDT')}", "",
              f"Preço agora: {price_now:.4g}"]

    sinais_ativos = []
    for fn in (check_pullback, check_exhaustion_climax, check_failed_breakout_reversal, check_range_market):
        try:
            sig = fn(symbol, candles_4h)
            if sig:
                sinais_ativos.append(sig)
        except Exception:
            pass

    rsi_15m = rsi_1h = None
    if candles_15m and candles_1h:
        try:
            sig = check_scalp_cascade(symbol, candles_15m, candles_1h)
            if sig:
                sinais_ativos.append(sig)
        except Exception:
            pass
        try:
            sig = check_confluence(symbol, candles_4h, candles_15m, candles_1h)
            if sig:
                sinais_ativos.append(sig)
        except Exception:
            pass
        rsi_15m = compute_rsi([c["close"] for c in candles_15m])
        rsi_1h = compute_rsi([c["close"] for c in candles_1h])

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
        diagnose_scalp(rsi_15m, rsi_1h) if (rsi_15m is not None and rsi_1h is not None) else None,
        diagnose_bottom_fishing(candles_d, candles_w) if (candles_d and candles_w) else None,
        diagnose_light_reversal(candles_d) if candles_d else None,
        diagnose_confluence(candles_4h, candles_15m, candles_1h) if (candles_15m and candles_1h) else None,
    ) if d]

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
    return "Mercado geral" if symbol == "MERCADO" else symbol.replace("USDT", "/USDT")


def _checklist_linhas(checklist):
    if not checklist:
        return []
    linhas = ["", "Checklist:"]
    for label, ok in checklist:
        linhas.append(f"  {'✅' if ok else '❌'} {label}")
    return linhas


def format_signal_message(sig):
    """
    Mensagem de UM sinal, formato enxuto e direto: ação + moeda no topo,
    número (entrada/alvo/stop) logo abaixo, checklist do que confirmou o
    sinal, e só depois a explicação — pra dar pra ler em 5 segundos e ainda
    ter os detalhes de quem quiser conferir.
    """
    emoji = _acao_emoji(sig["acao"])
    sym = _fmt_symbol(sig["symbol"])

    linhas = [
        f"{emoji} {sig['acao']} — {sym}",
        f"{sig['estilo']} · {sig['titulo']} · {sig['timeframe']}",
        "",
    ]
    linhas.extend(sig["detalhes"])
    linhas.extend(_checklist_linhas(sig.get("checklist")))
    linhas.append("")
    linhas.append(f"Por quê: {sig['explicacao']}")
    if sig.get("aviso"):
        linhas.append(f"⚠️ {sig['aviso']}")
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
    linhas = [f"🧩 {sym} bateu {len(sinais)} estratégias ao mesmo tempo", ""]
    acoes = {s["acao"] for s in sinais}
    if len(acoes) > 1:
        linhas.append("⚠️ Atenção: as estratégias abaixo sugerem lados opostos (compra x venda) — é conflito, não reforço.")
        linhas.append("")

    for sig in sinais:
        emoji = _acao_emoji(sig["acao"])
        linhas.append(f"{emoji} {sig['acao']} — {sig['estilo']} · {sig['titulo']} ({sig['timeframe']})")
        for d in sig["detalhes"]:
            linhas.append(f"    {d}")
        linhas.extend(f"  {l}" if l else "" for l in _checklist_linhas(sig.get("checklist")))
        linhas.append("")

    if len(acoes) == 1:
        linhas.append(
            "Mais de uma estratégia concordando na mesma direção ao mesmo tempo costuma "
            "ser um reforço do setup."
        )
        linhas.append("")
    linhas.append("Leitura técnica automática — não é recomendação de investimento.")
    return "\n".join(linhas)


def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("ERRO: defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID nas variáveis de ambiente.")
        return False
    url = f"{TELEGRAM_BASE}/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
        return True
    except urllib.error.HTTPError as e:
        print(f"Erro ao enviar pro Telegram: {e.code} {e.read()}")
        return False
    except Exception as e:
        print(f"Erro ao enviar pro Telegram: {e}")
        return False


# ----------------------------------------------------------------------------
# ANÁLISE POR MOEDA — roda os checks por-moeda, junta os sinais e também
# coleta diagnósticos de proximidade (near-miss) pra quem não disparou nada
# ----------------------------------------------------------------------------

def analyze_symbol(symbol, tier=None):
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

    # cascata de RSI e confluência usam 15m/1h — busca uma vez só e reaproveita
    try:
        candles_15m = fetch_klines(symbol, "15m", CONFLUENCE_15M_LIMIT)
        candles_1h = fetch_klines(symbol, "1h", 100)
    except Exception as e:
        print(f"  {symbol}: erro ao buscar candles 15m/1h ({e})")
        candles_15m, candles_1h = [], []

    if candles_15m and candles_1h:
        try:
            sig = check_scalp_cascade(symbol, candles_15m, candles_1h)
            if sig:
                sinais.append(sig)
            else:
                rsi_15m = compute_rsi([c["close"] for c in candles_15m])
                rsi_1h = compute_rsi([c["close"] for c in candles_1h])
                diag = diagnose_scalp(rsi_15m, rsi_1h)
                if diag:
                    diagnosticos.append({"symbol": symbol, **diag})
        except Exception as e:
            print(f"  {symbol}: erro no check de cascata scalp ({e})")

        try:
            sig = check_confluence(symbol, candles_4h, candles_15m, candles_1h)
            if sig:
                sinais.append(sig)
            else:
                diag = diagnose_confluence(candles_4h, candles_15m, candles_1h)
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
            situacao = (f"o preço já rompeu o topo anterior ({nivel:.4g}) e está em "
                        f"{price_now:.4g} ({dist_pct * 100:+.1f}% acima dele)")
        elif dist_pct < -0.10:
            longe = True
            situacao = (f"o preço já caiu bem abaixo do topo anterior ({nivel:.4g}), "
                        f"pra {price_now:.4g} ({dist_pct * 100:+.1f}%) — esse nível está "
                        f"meio distante agora, serve mais de referência do que de zona "
                        f"imediata de entrada")
        else:
            situacao = f"o preço está perto do topo anterior ({nivel:.4g}), em {price_now:.4g}"

        short_low, short_high = nivel * 0.995, nivel * 1.01
        entrada_txt = (
            f"se o preço voltar a se aproximar dessa região, entre {short_low:.4g} e "
            f"{short_high:.4g}" if longe else
            f"dá pra especular um short entre {short_low:.4g} e {short_high:.4g} (perto desse topo)"
        )
        bear = (
            f"🔴 Pensando em VENDER: {situacao}. Enquanto não vier rompimento de "
            f"verdade com volume forte, {entrada_txt}, stop acima "
            f"dele, mirando a zona de Fibonacci 0.382 dessa perna ({fib_price:.4g}) "
            f"como primeiro alvo — principalmente porque {vol_txt}, o que "
            f"enfraquece a chance de continuidade da alta e favorece um topo "
            f"descendente."
        )
        bull = (
            f"🟢 Pensando em COMPRAR: o cenário de alta só fica confirmado de "
            f"verdade com rompimento e sustentação acima de {nivel:.4g} com "
            f"volume forte. Nesse caso o setup mais saudável não é comprar o "
            f"rompimento na hora — é esperar o pullback seguinte formar um fundo "
            f"ascendente (mais alto que o anterior) antes de entrar, de olho na "
            f"região perto de {fib_price:.4g} (fib 0.382 da perna atual) como "
            f"referência de onde esse próximo fundo tende a aparecer."
        )
    else:
        # nivel = último fundo confirmado dessa perna de baixa
        longe = False
        if dist_pct < -0.02:
            situacao = (f"o preço já rompeu o fundo anterior ({nivel:.4g}) e está em "
                        f"{price_now:.4g} ({dist_pct * 100:+.1f}% abaixo dele)")
        elif dist_pct > 0.10:
            longe = True
            situacao = (f"o preço já subiu bem acima do fundo anterior ({nivel:.4g}), "
                        f"pra {price_now:.4g} ({dist_pct * 100:+.1f}%) — esse nível está "
                        f"meio distante agora, serve mais de referência do que de zona "
                        f"imediata de entrada")
        else:
            situacao = f"o preço está perto do fundo anterior ({nivel:.4g}), em {price_now:.4g}"

        long_low, long_high = nivel * 0.99, nivel * 1.005
        entrada_txt = (
            f"se o preço voltar a se aproximar dessa região, entre {long_low:.4g} e "
            f"{long_high:.4g}" if longe else
            f"dá pra especular uma compra entre {long_low:.4g} e {long_high:.4g} (perto desse fundo)"
        )
        bull = (
            f"🟢 Pensando em COMPRAR: {situacao}. Enquanto não vier rompimento de "
            f"baixa de verdade com volume forte, {entrada_txt}, stop abaixo "
            f"dele, mirando a zona de Fibonacci 0.382 dessa perna ({fib_price:.4g}) "
            f"como primeiro alvo — principalmente porque {vol_txt}, o que "
            f"enfraquece a chance de continuidade da queda e favorece um fundo "
            f"ascendente."
        )
        bear = (
            f"🔴 Pensando em VENDER: o cenário de baixa só fica confirmado de "
            f"verdade com rompimento e sustentação abaixo de {nivel:.4g} com "
            f"volume forte. Nesse caso o setup mais saudável não é vender o "
            f"rompimento na hora — é esperar o pullback seguinte formar um topo "
            f"descendente (mais baixo que o anterior) antes de entrar, de olho na "
            f"região perto de {fib_price:.4g} (fib 0.382 da perna atual) como "
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
                linhas.append(f"• {nome}: SEM SWING ATIVO agora (preço {cenario['price_now']:.4g}). Dois cenários:")
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


def build_core_status_message(core_symbols, sinais_por_moeda, diagnosticos_lista_por_moeda, candles_d_extra):
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
    partes = ["🔭 VELA MONITOR — STATUS (BTC, ETH, XRP + destaques)"]
    for symbol in core_symbols:
        nome = symbol.replace("USDT", "/USDT")
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
                bloco.append(f"Cenário de swing (preço {cenario['price_now']:.4g}):")
                bloco.append(f"  {cenario['bull']}")
                bloco.append(f"  {cenario['bear']}")
            if not diags and not cenario:
                bloco.append("Sem setup próximo e sem dado suficiente pro cenário agora.")
            partes.append("\n".join(bloco))
    partes.append("Leitura técnica automática — não é recomendação de investimento.")
    return "\n\n".join(partes)


def build_full_categorized_report(watchlist, tiers, sinais_por_moeda, candles_d_extra=None):
    """
    Organiza o que a varredura já achou por horizonte de operação, em vez de
    mandar sinal solto: swing principal (BTC/ETH sempre aparecem), swing
    secundário (XRP + top 10 CoinMarketCap), altcoins pequenas, scalp e
    bottom fishing — cada seção limitada e filtrada pelas melhores, pra não
    lotar o Telegram (pedido depois de um relatório de diagnóstico que saiu
    com quase 40 moedas de uma vez).
    """
    candles_d_extra = candles_d_extra or {}
    linhas = ["📊 VELA MONITOR — RELATÓRIO DO DIA (swing)", ""]

    # 1) Swing principal — BTC e ETH sempre aparecem
    linhas.append("🏆 SWING PRINCIPAL")
    linhas.extend(_build_btc_eth_lines(sinais_por_moeda, candles_d_extra))
    linhas.append("")

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
                sinais, _ = analyze_symbol(symbol, tier=tiers.get(symbol))
            except Exception:
                sinais = []
        if sinais:
            sig = sinais[0]
            destaques.append(f"• {symbol.replace('USDT', '/USDT')}: {sig['titulo']} ({sig['acao']}, {sig['timeframe']}).")
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
            linhas.append(f"• {symbol.replace('USDT', '/USDT')}: {sig['titulo']} ({sig['acao']}, {sig['timeframe']}).")
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
            linhas.append(f"• {symbol.replace('USDT', '/USDT')}: {sig['titulo']} ({sig['acao']}).")
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
            linhas.append(f"• {symbol.replace('USDT', '/USDT')}: {sig['titulo']} — porte: {tiers.get(symbol, '?')}.")
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

    print(f"[{datetime.now(timezone.utc).isoformat()}] Iniciando varredura de "
          f"{len(watchlist)} moedas (pullback + exaustão + cascata scalp + "
          f"bottom fishing + reversão leve + rompimento falho + consolidação/range)...")
    # A varredura roda em TODO o watchlist (pra escolher as melhores altcoins
    # do momento e alimentar o relatório categorizado), mas NÃO manda mais
    # uma mensagem solta pra cada moeda que bater um sinal — isso virou a
    # maior fonte de poluição no Telegram. As mensagens em tempo real agora
    # ficam só pro grupo "core" (ver build_core_status_message), mandado uma
    # vez por rodada logo abaixo.
    sinais_moeda_count = 0
    todos_diagnosticos = []
    sinais_por_moeda = {}
    for symbol in watchlist:
        try:
            sinais, diagnosticos = analyze_symbol(symbol, tier=tiers.get(symbol))
        except Exception as e:
            print(f"  {symbol}: erro na análise ({e})")
            continue
        sinais_por_moeda[symbol] = sinais
        sinais_moeda_count += len(sinais)
        if sinais:
            print(f"  {symbol}: {len(sinais)} sinal(is) — {', '.join(s['titulo'] for s in sinais)}")
        else:
            print(f"  {symbol}: sem setup no momento")
        todos_diagnosticos.extend(diagnosticos)

    diagnosticos_lista_por_moeda = {}
    for d in todos_diagnosticos:
        diagnosticos_lista_por_moeda.setdefault(d["symbol"], []).append(d)

    encontrados = sinais_moeda_count

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

    is_manual = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    print(f"[{datetime.now(timezone.utc).isoformat()}] Montando status core (BTC, ETH, XRP + destaques)...")
    extra_alts = select_core_extra_altcoins(watchlist, sinais_por_moeda, diagnosticos_lista_por_moeda)
    core_symbols = CORE_SYMBOLS + extra_alts
    print(f"  altcoins escolhidas pro status dessa rodada: {', '.join(extra_alts) or '(nenhuma)'}")
    candles_d_extra = {}
    for sym in core_symbols:
        try:
            candles_d_extra[sym] = fetch_klines(sym, "1d", 200)
        except Exception as e:
            print(f"  erro buscando candle diário de {sym} ({e})")
    try:
        status_msg = build_core_status_message(core_symbols, sinais_por_moeda, diagnosticos_lista_por_moeda, candles_d_extra)
        ok = send_telegram_message(status_msg)
        print("  -> status core enviado" if ok else "  -> FALHOU ao enviar o status core")
    except Exception as e:
        print(f"  erro montando o status core ({e})")

    # O relatório categorizado completo só dispara pelo relógio (não em
    # execuções manuais) — testar manualmente perto de um dos horários não
    # deve empilhar o relatório inteiro em cima da varredura + diagnóstico.
    agora = datetime.now(timezone.utc)
    agora_min = agora.hour * 60 + agora.minute
    is_report_time = (not is_manual) and any(
        abs(agora_min - (h * 60 + m)) <= REPORT_TIME_TOLERANCE_MIN
        for h, m in REPORT_TIMES_UTC
    )
    if is_report_time:
        print(f"[{datetime.now(timezone.utc).isoformat()}] Horário de relatório categorizado — montando...")
        try:
            report_msg = build_full_categorized_report(watchlist, tiers, sinais_por_moeda, candles_d_extra)
            ok = send_telegram_message(report_msg)
            print("  -> relatório categorizado enviado" if ok else "  -> FALHOU ao enviar o relatório categorizado")
        except Exception as e:
            print(f"  erro montando o relatório categorizado ({e})")

    if is_manual:
        print(f"[{datetime.now(timezone.utc).isoformat()}] Montando diagnóstico de proximidade...")
        try:
            diag_msg = build_diagnostic_message(todos_diagnosticos)
            ok = send_telegram_message(diag_msg)
            print("  -> diagnóstico enviado" if ok else "  -> FALHOU ao enviar o diagnóstico")
        except Exception as e:
            print(f"  erro montando o diagnóstico ({e})")

        symbol_query = os.environ.get("SYMBOL_QUERY", "").strip()
        if symbol_query:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Analisando moeda pedida: {symbol_query}")
            try:
                deep_msg = build_symbol_deep_dive(symbol_query)
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
