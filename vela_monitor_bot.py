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

# --- Diagnóstico de proximidade (near-miss) — só usado nas execuções manuais,
# pra mostrar quais moedas estão perto de bater algum critério mesmo sem ter
# disparado um sinal de verdade ainda ---
PULLBACK_DIAG_MAX_PCT = 0.025      # até 2,5% da zona fib já entra no diagnóstico
EXHAUSTION_DIAG_RSI_BAND = 15      # RSI dentro de 15 pontos do gatilho (70-85 ou 15-30)
SCALP_DIAG_RSI_BAND = 10           # RSI dentro de 10 pontos do gatilho de scalp
REVERSAL_DRAWDOWN_DIAG_BAND = 0.05  # até 5 pontos percentuais abaixo do drawdown mínimo
DIAGNOSTIC_TOP_N = 12               # quantas moedas entram no resumo de diagnóstico

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

    return {
        "symbol": symbol, "estilo": "SWING", "acao": acao,
        "titulo": f"Pullback ({leg['direction']}, {leg_txt})",
        "timeframe": INTERVAL,
        "detalhes": detalhes,
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
    return {
        "symbol": symbol, "estilo": "EXAUSTÃO", "acao": acao,
        "titulo": f"Clímax de volume no {lado}",
        "timeframe": INTERVAL,
        "detalhes": [
            f"Preço agora: {price_now:.4g}",
            f"RSI ({INTERVAL}): {rsi:.1f}",
            f"Volume: {vol_ratio:.1f}x a média",
        ],
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
    return {
        "symbol": symbol, "estilo": "SCALP", "acao": acao,
        "titulo": f"Cascata de RSI — {lado} no 15m e 1h",
        "timeframe": "15m + 1h",
        "detalhes": [
            f"Preço agora: {price_now:.4g}",
            f"RSI 15m: {rsi_15m:.1f}  |  RSI 1h: {rsi_1h:.1f}",
        ],
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

    return {
        "symbol": symbol, "estilo": "POSIÇÃO", "acao": "COMPRAR",
        "titulo": "Bottom fishing — fundo histórico",
        "timeframe": "1w (máxima) + 1d (estrutura)",
        "detalhes": detalhes,
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

    return {
        "symbol": symbol, "estilo": "SWING/POSIÇÃO", "acao": "COMPRAR",
        "titulo": "Reversão de tendência com base",
        "timeframe": f"1d ({lookback}d)",
        "detalhes": detalhes,
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
                return {
                    "symbol": symbol, "estilo": "SWING", "acao": "COMPRAR",
                    "titulo": "Reversão por rompimento falho (suporte)",
                    "timeframe": INTERVAL,
                    "detalhes": [
                        f"Preço agora: {price_now:.4g}",
                        f"Suporte rompido e recuperado: {ref_price:.4g}",
                        f"Stop sugerido: {stop:.4g}",
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
                return {
                    "symbol": symbol, "estilo": "SWING", "acao": "VENDER",
                    "titulo": "Reversão por rompimento falho (resistência)",
                    "timeframe": INTERVAL,
                    "detalhes": [
                        f"Preço agora: {price_now:.4g}",
                        f"Resistência rompida e devolvida: {ref_price:.4g}",
                        f"Stop sugerido: {stop:.4g}",
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


def build_diagnostic_message(diagnosticos):
    linhas = ["🔎 VELA MONITOR — DIAGNÓSTICO (mais perto de um setup)", ""]
    if not diagnosticos:
        linhas.append(
            "Nenhuma moeda do watchlist está particularmente perto de bater algum "
            "critério agora — ou o mercado está sem setups se formando, ou tudo já "
            "disparou como sinal de verdade lá em cima."
        )
    else:
        ordenados = sorted(diagnosticos, key=lambda d: d["score"])[:DIAGNOSTIC_TOP_N]
        for d in ordenados:
            sym = d["symbol"].replace("USDT", "/USDT")
            linhas.append(f"• {sym} — {d['texto']}")
    linhas.append("")
    linhas.append(
        "Isso é uma régua de proximidade pras mesmas regras dos sinais de verdade "
        "— não é um alerta de entrada, é pra você filtrar o que vale a pena "
        "acompanhar de perto."
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
        candles_15m = fetch_klines(symbol, "15m", 100)
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
    for fn in (check_pullback, check_exhaustion_climax, check_failed_breakout_reversal):
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
        diagnose_scalp(rsi_15m, rsi_1h) if (rsi_15m is not None and rsi_1h is not None) else None,
        diagnose_bottom_fishing(candles_d, candles_w) if (candles_d and candles_w) else None,
        diagnose_light_reversal(candles_d) if candles_d else None,
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

def format_signal_message(sig):
    if sig["acao"] == "COMPRAR":
        emoji = "🟢"
    elif sig["acao"] == "VENDER":
        emoji = "🔴"
    else:
        emoji = "🔵"

    sym = sig["symbol"].replace("USDT", "/USDT") if sig["symbol"] != "MERCADO" else "Mercado geral"

    linhas = [
        f"{emoji} VELA MONITOR — {sig['estilo']} — {sig['titulo']}",
        f"{sym}  ({sig['timeframe']})",
        "",
    ]
    linhas.extend(sig["detalhes"])
    linhas.append("")
    linhas.append(f"Por quê: {sig['explicacao']}")
    if sig.get("aviso"):
        linhas.append("")
        linhas.append(f"⚠️ {sig['aviso']}")
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

    # cascata de RSI usa 15m/1h — busca uma vez só e reaproveita pro diagnóstico
    try:
        candles_15m = fetch_klines(symbol, "15m", 100)
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
          f"bottom fishing + reversão leve + rompimento falho)...")
    encontrados = 0
    sinais_moeda_count = 0
    todos_diagnosticos = []
    for symbol in watchlist:
        try:
            sinais, diagnosticos = analyze_symbol(symbol, tier=tiers.get(symbol))
        except Exception as e:
            print(f"  {symbol}: erro na análise ({e})")
            continue
        if sinais:
            for sig in sinais:
                encontrados += 1
                sinais_moeda_count += 1
                msg = format_signal_message(sig)
                print("-" * 60)
                print(msg)
                ok = send_telegram_message(msg)
                print("  -> enviado pro Telegram" if ok else "  -> FALHOU ao enviar")
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

    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
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
