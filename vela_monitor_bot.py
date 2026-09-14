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
#   4) BOTTOM FISHING (posição) — moeda muito abaixo da própria máxima
#      histórica (drawdown grande) e formando fundos ascendentes no diário,
#      indicando possível base de longo prazo se formando.
#
#   5) DOMINÂNCIA BTC / ALTSEASON (mercado, uma vez por rodada) — compara o
#      retorno do BTC nos últimos 7 dias com a média do watchlist de
#      altcoins no mesmo período. Não é o índice oficial de dominância (que
#      vem de market cap total, uma fonte que não temos aqui) — é um proxy
#      baseado em performance relativa, mas segue a mesma lógica da regra:
#      BTC forte na frente das alts = dominância subindo; alts fortes na
#      frente do BTC = dominância caindo / altseason.
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

# Watchlist fixa — top pares USDT por volume na Binance (edite à vontade).
WATCHLIST = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "TRXUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT",
    "XLMUSDT", "ETCUSDT", "FILUSDT", "APTUSDT", "ARBUSDT",
    "OPUSDT", "NEARUSDT", "INJUSDT", "SUIUSDT", "TONUSDT",
]

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

# --- Bottom fishing (posição) ---
BOTTOM_FISHING_MIN_DRAWDOWN = 0.55   # pelo menos 55% abaixo da máxima histórica
BOTTOM_FISHING_PIVOT_LEN = 3
BOTTOM_FISHING_MIN_ASCENDING = 2

# --- Dominância BTC / altseason (proxy) ---
DOMINANCE_LOOKBACK_DAYS = 7
DOMINANCE_DIVERGENCE_PP = 6.0  # diferença mínima (pontos percentuais) pra alertar

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
        targets = [leg["end_price"], leg["end_price"] + 0.272 * leg_size, leg["end_price"] + 0.618 * leg_size]
        estrutura_txt = "fundos ascendentes"
    else:
        acao = "VENDER"
        stop = max(p[1] for p in recent_pivots[-MIN_ASCENDING_BOTTOMS:]) * 1.005
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

def check_bottom_fishing(symbol):
    candles_w = fetch_klines(symbol, "1w", 1000)
    if len(candles_w) < 20:
        return None
    ath = max(c["high"] for c in candles_w)
    price_now = candles_w[-1]["close"]
    drawdown = (ath - price_now) / ath
    if drawdown < BOTTOM_FISHING_MIN_DRAWDOWN:
        return None

    candles_d = fetch_klines(symbol, "1d", 200)
    pivot_highs_d, pivot_lows_d = find_pivots(candles_d, BOTTOM_FISHING_PIVOT_LEN)
    if len(pivot_lows_d) < BOTTOM_FISHING_MIN_ASCENDING:
        return None
    recent_lows = pivot_lows_d[-BOTTOM_FISHING_MIN_ASCENDING:]
    prices = [p[1] for p in recent_lows]
    ascending = all(prices[i] < prices[i + 1] for i in range(len(prices) - 1))
    if not ascending:
        return None

    stop = min(prices) * 0.97
    return {
        "symbol": symbol, "estilo": "POSIÇÃO", "acao": "COMPRAR",
        "titulo": "Bottom fishing — fundo histórico",
        "timeframe": "1w (máxima) + 1d (estrutura)",
        "detalhes": [
            f"Preço agora: {price_now:.4g}",
            f"Máxima histórica: {ath:.4g}  ({drawdown * 100:.0f}% abaixo)",
            f"Stop sugerido: {stop:.4g}",
        ],
        "explicacao": (
            f"Moeda {drawdown * 100:.0f}% abaixo da máxima histórica e formando fundos "
            f"ascendentes no diário — indício de que uma base de longo prazo pode "
            f"estar se formando, no espírito do \"bottom fishing\" (stop sempre "
            f"abaixo da base, nunca no meio do range)."
        ),
        "aviso": (
            "Sinal de posição/longo prazo: drawdowns grandes podem continuar por "
            "muito tempo antes de reverter de verdade — confirme com o contexto "
            "macro (BTC, dominância) antes de posicionar tamanho relevante."
        ),
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
        "Tipos de sinal ativos agora: Pullback (swing), Clímax de exaustão, "
        "Cascata de RSI (scalp), Bottom fishing (posição) e Dominância "
        "BTC/altseason (mercado).",
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

def analyze_symbol(symbol):
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
        sig = check_bottom_fishing(symbol)
        if sig:
            sinais.append(sig)
    except Exception as e:
        print(f"  {symbol}: erro no check de bottom fishing ({e})")

    return sinais


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

def main():
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        print("Execução manual detectada — enviando mensagem de teste...")
        ok = send_telegram_message(build_test_message())
        print("  -> mensagem de teste enviada" if ok else "  -> FALHOU ao enviar a mensagem de teste")

    print(f"[{datetime.now(timezone.utc).isoformat()}] Iniciando varredura de "
          f"{len(WATCHLIST)} moedas (pullback + exaustão + cascata scalp + bottom fishing)...")
    encontrados = 0
    for symbol in WATCHLIST:
        try:
            sinais = analyze_symbol(symbol)
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
        dom_sig = check_dominance_altseason(WATCHLIST)
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
