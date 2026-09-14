#!/usr/bin/env python3
# ============================================================================
#  Vela Monitor — varredura de pullback (BTC/USDT e top moedas por volume)
#
#  O que faz:
#   - Lê o watchlist (lista fixa de moedas) e busca candles de 4h na Binance
#     (API pública, sem necessidade de conta/autenticação).
#   - Identifica a última perna de impulso (fundo -> topo, ou topo -> fundo)
#     usando pivôs (fractals) no gráfico de 4h.
#   - Verifica se o preço atual está corrigindo dentro da zona do Fibonacci
#     0.382 dessa perna.
#   - Confirma se os fundos (ou topos) recentes dentro da correção estão
#     ascendentes (ou descendentes), igual ao padrão descrito no manual do
#     Vela Trader.
#   - Compara o volume atual com a média — se estiver abaixo da média, o
#     alerta ainda é enviado, mas com o aviso de "volume abaixo da média"
#     (mesma lógica do exemplo que você mostrou).
#   - Envia o alerta formatado para o seu bot do Telegram.
#
#  Isso é um SCANNER TÉCNICO baseado em regras (fibonacci + estrutura +
#  volume) — não é sinal de compra/venda garantido nem recomendação
#  financeira. É uma ferramenta de apoio, do jeito que você já usa o
#  indicador no TradingView.
#
#  Onde rodar: este script PRECISA rodar fora do sandbox do Claude (a
#  Binance e o Telegram estão bloqueados por política da organização tanto
#  no container de nuvem quanto na VM do bridge do computador). Rode
#  localmente no seu Mac (cron/launchd) ou via GitHub Actions — instruções
#  completas no README_vela_monitor_bot.md.
# ============================================================================

import os
import sys
import time
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------------

# Token e chat id vêm de variáveis de ambiente — NUNCA coloque o token direto
# no código (veja o README para como configurar isso no seu Mac ou no
# GitHub Actions).
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Watchlist fixa — top pares USDT por volume na Binance (pode editar
# livremente, é só uma lista de strings).
WATCHLIST = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "TRXUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT",
    "XLMUSDT", "ETCUSDT", "FILUSDT", "APTUSDT", "ARBUSDT",
    "OPUSDT", "NEARUSDT", "INJUSDT", "SUIUSDT", "TONUSDT",
]

INTERVAL = "4h"          # timeframe usado pra estrutura + confirmação
KLINES_LIMIT = 200       # quantos candles de 4h buscar (200 * 4h ≈ 33 dias)
PIVOT_LEN = 3            # velas de cada lado pra confirmar um pivô (fractal)
FIB_LEVEL = 0.382        # nível de fibonacci que estamos monitorando
FIB_TOLERANCE = 0.006    # tolerância em % de preço ao redor do nível (0.6%)
VOLUME_LOOKBACK = 20     # média de volume (em candles de 4h)
MIN_ASCENDING_BOTTOMS = 2  # quantos fundos ascendentes confirmam o padrão

BINANCE_BASE = "https://api.binance.com"
TELEGRAM_BASE = "https://api.telegram.org"


# ----------------------------------------------------------------------------
# DADOS DA BINANCE
# ----------------------------------------------------------------------------

def fetch_klines(symbol: str, interval: str = INTERVAL, limit: int = KLINES_LIMIT):
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
    return candles


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
    pivot_highs = []
    pivot_lows = []
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
    Encontra a perna de impulso mais recente confirmada: ou fundo -> topo
    (perna de alta, pra procurar padrão de COMPRA no pullback) ou
    topo -> fundo (perna de baixa, pra procurar padrão de VENDA no repique).
    Retorna dict com direção, índice/preço do início e do fim da perna.
    """
    if not pivot_highs or not pivot_lows:
        return None

    last_high_idx, last_high_price = pivot_highs[-1]
    last_low_idx, last_low_price = pivot_lows[-1]

    if last_high_idx > last_low_idx:
        # o topo veio depois do fundo -> perna de alta (fundo -> topo)
        # procura o fundo relevante ANTES desse topo
        candidates = [p for p in pivot_lows if p[0] < last_high_idx]
        if not candidates:
            return None
        start_idx, start_price = candidates[-1]
        return {
            "direction": "alta",
            "start_idx": start_idx, "start_price": start_price,
            "end_idx": last_high_idx, "end_price": last_high_price,
        }
    else:
        # o fundo veio depois do topo -> perna de baixa (topo -> fundo)
        candidates = [p for p in pivot_highs if p[0] < last_low_idx]
        if not candidates:
            return None
        start_idx, start_price = candidates[-1]
        return {
            "direction": "baixa",
            "start_idx": start_idx, "start_price": start_price,
            "end_idx": last_low_idx, "end_price": last_low_price,
        }


def fib_level_price(leg, level=FIB_LEVEL):
    """Preço do nível de fibonacci `level` dentro da perna (retração)."""
    if leg["direction"] == "alta":
        # perna subiu de start_price (fundo) até end_price (topo);
        # retração de X% desce a partir do topo
        return leg["end_price"] - level * (leg["end_price"] - leg["start_price"])
    else:
        # perna caiu de start_price (topo) até end_price (fundo);
        # retração de X% sobe a partir do fundo
        return leg["end_price"] + level * (leg["start_price"] - leg["end_price"])


def price_in_fib_zone(price, fib_price, tolerance=FIB_TOLERANCE):
    return abs(price - fib_price) / fib_price <= tolerance


def ascending_or_descending_bottoms(candles, leg, pivot_highs, pivot_lows):
    """
    Dentro da correção (depois do fim da perna), olha os últimos pivôs de
    fundo (se perna de alta -> queremos fundos ascendentes) ou de topo (se
    perna de baixa -> queremos topos descendentes).
    Retorna True se confirmado.
    """
    end_idx = leg["end_idx"]
    if leg["direction"] == "alta":
        recent = [p for p in pivot_lows if p[0] > end_idx]
        if len(recent) < MIN_ASCENDING_BOTTOMS:
            return False, recent
        prices = [p[1] for p in recent[-MIN_ASCENDING_BOTTOMS:]]
        ok = all(prices[i] < prices[i + 1] for i in range(len(prices) - 1))
        return ok, recent
    else:
        recent = [p for p in pivot_highs if p[0] > end_idx]
        if len(recent) < MIN_ASCENDING_BOTTOMS:
            return False, recent
        prices = [p[1] for p in recent[-MIN_ASCENDING_BOTTOMS:]]
        ok = all(prices[i] > prices[i + 1] for i in range(len(prices) - 1))
        return ok, recent


def volume_status(candles, lookback=VOLUME_LOOKBACK):
    if len(candles) < lookback + 1:
        return None, None, None
    recent = candles[-lookback - 1:-1]
    avg_vol = sum(c["volume"] for c in recent) / len(recent)
    current_vol = candles[-1]["volume"]
    ratio = current_vol / avg_vol if avg_vol > 0 else None
    return current_vol, avg_vol, ratio


# ----------------------------------------------------------------------------
# ANÁLISE POR MOEDA
# ----------------------------------------------------------------------------

def analyze_symbol(symbol):
    candles = fetch_klines(symbol)
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

    structure_ok, recent_pivots = ascending_or_descending_bottoms(
        candles, leg, pivot_highs, pivot_lows
    )
    if not structure_ok:
        return None

    current_vol, avg_vol, vol_ratio = volume_status(candles)
    volume_abaixo_media = vol_ratio is not None and vol_ratio < 1.0

    # alvos: 3 extensões simples a partir do fim da perna, na direção do
    # movimento esperado (retorno na direção original da perna)
    leg_size = abs(leg["end_price"] - leg["start_price"])
    if leg["direction"] == "alta":
        acao = "COMPRAR"
        stop = min(p[1] for p in recent_pivots[-MIN_ASCENDING_BOTTOMS:]) * 0.995
        targets = [
            leg["end_price"],
            leg["end_price"] + 0.272 * leg_size,
            leg["end_price"] + 0.618 * leg_size,
        ]
    else:
        acao = "VENDER"
        stop = max(p[1] for p in recent_pivots[-MIN_ASCENDING_BOTTOMS:]) * 1.005
        targets = [
            leg["end_price"],
            leg["end_price"] - 0.272 * leg_size,
            leg["end_price"] - 0.618 * leg_size,
        ]

    return {
        "symbol": symbol,
        "acao": acao,
        "price_now": price_now,
        "fib_price": fib_price,
        "leg": leg,
        "stop": stop,
        "targets": targets,
        "volume_abaixo_media": volume_abaixo_media,
        "vol_ratio": vol_ratio,
    }


# ----------------------------------------------------------------------------
# MENSAGEM E ENVIO PRO TELEGRAM
# ----------------------------------------------------------------------------

def format_message(result):
    sym = result["symbol"].replace("USDT", "/USDT")
    seta = "🟢" if result["acao"] == "COMPRAR" else "🔴"
    leg = result["leg"]
    leg_txt = f"{leg['start_price']:.4g} → {leg['end_price']:.4g}"
    targets_txt = " > ".join(f"{t:.4g}" for t in result["targets"])

    linhas = [
        f"{seta} VELA MONITOR — {result['acao']} {sym}",
        f"(pullback da perna de {leg['direction']}, {leg_txt})",
        "",
        f"Preço agora: {result['price_now']:.4g}",
        f"Zona Fibonacci 0.382: {result['fib_price']:.4g}",
        f"Stop sugerido: {result['stop']:.4g}",
        f"Alvos: {targets_txt}",
        "",
        f"Estrutura de {'fundos' if leg['direction'] == 'alta' else 'topos'} "
        f"{'ascendentes' if leg['direction'] == 'alta' else 'descendentes'} "
        f"confirmada no gráfico de {INTERVAL}.",
    ]
    if result["volume_abaixo_media"]:
        ratio_pct = result["vol_ratio"] * 100
        linhas.append("")
        linhas.append(
            f"⚠️ Alerta: volume atual está {ratio_pct:.0f}% da média — "
            f"volume abaixo da média enfraquece o setup."
        )
    linhas.append("")
    linhas.append(
        "Isto é uma leitura técnica automática (fibonacci + estrutura + "
        "volume), não é recomendação de investimento."
    )
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
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
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
# MAIN
# ----------------------------------------------------------------------------

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Iniciando varredura de "
          f"{len(WATCHLIST)} moedas...")
    encontrados = 0
    for symbol in WATCHLIST:
        try:
            result = analyze_symbol(symbol)
        except Exception as e:
            print(f"  {symbol}: erro na análise ({e})")
            continue
        if result:
            encontrados += 1
            msg = format_message(result)
            print("-" * 60)
            print(msg)
            ok = send_telegram_message(msg)
            print("  -> enviado pro Telegram" if ok else "  -> FALHOU ao enviar")
        else:
            print(f"  {symbol}: sem setup no momento")
        time.sleep(0.3)  # respeita rate limit da Binance
    print(f"[{datetime.now(timezone.utc).isoformat()}] Varredura concluída. "
          f"{encontrados} moeda(s) com setup encontrado.")


if __name__ == "__main__":
    main()
