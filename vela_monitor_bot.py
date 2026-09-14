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

# --- Reversão por rompimento falho (swing) ---
FAILED_BREAK_LOOKBACK = 6              # candles recentes onde procuramos o rompimento
FAILED_BREAK_PENETRATION_PCT = 0.001   # rompimento mínimo (0.1%) além do nível de referência
FAILED_BREAK_RECOVERY_PCT = 0.001      # recuperação mínima (0.1%) de volta pro outro lado
FAILED_BREAK_VOLUME_RATIO = 1.3        # volume mínimo (x média) no rompimento ou na recuperação

BINANCE_BASE = "https://api.binance.com"
TELEGRAM_BASE = "https://api.telegram.org"

API_SLEEP = 0.2   # pausa entre chamadas à Binance (respeita rate limit)


# ----------------------------------------------------------------------------
# DADOS DA BINANCE
# ----------------------------------------------------------------------------

def fetch_klines(symbol: str, interval: str, limit: int):
    """Busca candles públicos da Binance. Não precisa de API key."""
    url = f"{BINANCE_BASE}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "vela-monitor-bot/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
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
    url = f"{BINANCE_BASE}/api/v3/ticker/24hr"
    req = urllib.request.Request(url, headers={"User-Agent": "vela-monitor-bot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
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

def check_scalp_cascade(symbol):
    candles_15m = fetch_klines(symbol, "15m", 100)
    candles_1h = fetch_klines(symbol, "1h", 100)
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


def check_dominance_altseason(watchlist):
    btc_candles = fetch_klines("BTCUSDT", "1d", DOMINANCE_LOOKBACK_DAYS + 5)
    btc_return = pct_return(btc_candles)
    if btc_return is None:
        return None

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

    if not alt_returns:
        return None
    avg_alt_return = sum(alt_returns) / len(alt_returns)
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


def build_test_message():
    return "\n".join([
        "🧪 VELA MONITOR — TESTE",
        "(mensagem de exemplo — não é um sinal real de compra/venda)",
        "",
        "Se essa mensagem chegou, a conexão entre o script, o GitHub Actions "
        "e o seu bot do Telegram está funcionando.",
        "",
        f"Tipos de sinal ativos agora: Pullback (swing), Clímax de exaustão, "
        f"Cascata de RSI (scalp), Bottom fishing (posição), Reversão de "
        f"tendência com base (posição/swing), Reversão por rompimento falho "
        f"(swing) e Dominância BTC/altseason (mercado). Varredura dinâmica "
        f"dos {TOP_N_SYMBOLS} pares USDT de maior volume na Binance, não "
        f"mais uma lista fixa.",
        "",
        "Exemplo de como um alerta de pullback se parece:",
        "🟢 VELA MONITOR — SWING — Pullback (alta, 67000 → 82000)",
        "BTC/USDT  (4h)",
        "Preço agora: 76720",
        "Zona Fibonacci 0.382: 76270",
        "Stop sugerido: 74500",
        "Alvos: 80800 > 82800 > 89500",
        "",
        "Por quê: Correção dentro da zona de Fibonacci 0.382 da última perna "
        "de alta, com fundos ascendentes confirmando.",
        "",
        "Esse alerta de teste é enviado sempre que você roda o workflow "
        "manualmente pelo botão \"Run workflow\" no GitHub. A varredura "
        "automática de hora em hora só avisa quando encontra um setup de "
        "verdade.",
    ])


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
# ANÁLISE POR MOEDA — roda os 4 checks por-moeda e junta os sinais
# ----------------------------------------------------------------------------

def analyze_symbol(symbol, tier=None):
    sinais = []
    candles_4h = fetch_klines(symbol, INTERVAL, KLINES_LIMIT)
    if len(candles_4h) < (2 * PIVOT_LEN + 10):
        return sinais

    try:
        sig = check_pullback(symbol, candles_4h)
        if sig:
            sinais.append(sig)
    except Exception as e:
        print(f"  {symbol}: erro no check de pullback ({e})")

    try:
        sig = check_exhaustion_climax(symbol, candles_4h)
        if sig:
            sinais.append(sig)
    except Exception as e:
        print(f"  {symbol}: erro no check de exaustão ({e})")

    try:
        sig = check_scalp_cascade(symbol)
        if sig:
            sinais.append(sig)
    except Exception as e:
        print(f"  {symbol}: erro no check de cascata scalp ({e})")

    try:
        sig = check_failed_breakout_reversal(symbol, candles_4h)
        if sig:
            sinais.append(sig)
    except Exception as e:
        print(f"  {symbol}: erro no check de reversão por rompimento falho ({e})")

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
        except Exception as e:
            print(f"  {symbol}: erro no check de bottom fishing ({e})")

        try:
            sig = check_light_reversal(symbol, candles_d, tier=tier)
            if sig:
                sinais.append(sig)
        except Exception as e:
            print(f"  {symbol}: erro no check de reversão leve ({e})")

    return sinais


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

def main():
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        print("Execução manual detectada — enviando mensagem de teste...")
        ok = send_telegram_message(build_test_message())
        print("  -> mensagem de teste enviada" if ok else "  -> FALHOU ao enviar a mensagem de teste")

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
    for symbol in watchlist:
        try:
            sinais = analyze_symbol(symbol, tier=tiers.get(symbol))
        except Exception as e:
            print(f"  {symbol}: erro na análise ({e})")
            continue
        if sinais:
            for sig in sinais:
                encontrados += 1
                msg = format_signal_message(sig)
                print("-" * 60)
                print(msg)
                ok = send_telegram_message(msg)
                print("  -> enviado pro Telegram" if ok else "  -> FALHOU ao enviar")
        else:
            print(f"  {symbol}: sem setup no momento")

    print(f"[{datetime.now(timezone.utc).isoformat()}] Verificando dominância BTC/altseason...")
    try:
        dom_sig = check_dominance_altseason(watchlist)
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

    print(f"[{datetime.now(timezone.utc).isoformat()}] Varredura concluída. "
          f"{encontrados} sinal(is) encontrado(s).")


if __name__ == "__main__":
    main()
