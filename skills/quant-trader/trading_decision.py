#!/usr/bin/env python3
"""
量化交易决策引擎 v2
完整修复：EMA/MACD/RSI 计算 + 动态仓位 + 成交量确认 + K线形态
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Resolve futuapi scripts directory relative to this file's skill root,
# or fall back to an environment variable for non-standard layouts.
_SKILL_ROOT = Path(__file__).resolve().parent.parent  # skills/
_DEFAULT_FUTU_SCRIPTS = _SKILL_ROOT / "futuapi" / "scripts"
FUTU_SCRIPTS = os.environ.get("FUTU_SCRIPTS_DIR", str(_DEFAULT_FUTU_SCRIPTS))

# Use the Python interpreter that is currently running this script so the
# subprocess inherits the same environment (venv, conda, system, etc.).
PYTHON_BIN = os.environ.get("FUTU_PYTHON_BIN", sys.executable)

POSITION_STATES = {"无", "轻仓", "半仓", "重仓", "持有"}


# ─────────────────────────────────────────────
# 数据获取
# ─────────────────────────────────────────────

def run_futu_script(script_name: str, code: str, extra_args: str = "") -> Optional[Dict]:
    script_path = f"{FUTU_SCRIPTS}/{script_name}"
    cmd = f"{PYTHON_BIN} {script_path} {code} {extra_args} --json 2>&1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    for line in result.stdout.split("\n"):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except Exception:
                pass
    return None


def get_snapshot(code: str) -> Optional[Dict]:
    return run_futu_script("quote/get_snapshot.py", code)


def get_kline(code: str, ktype: str = "1d", num: int = 120) -> Optional[Dict]:
    return run_futu_script("quote/get_kline.py", code, f"--ktype {ktype} --num {num}")


# ─────────────────────────────────────────────
# 技术指标（全部修正为标准算法）
# ─────────────────────────────────────────────

def calculate_ema(prices: List[float], period: int) -> List[float]:
    """真正的指数加权移动平均（EMA）"""
    if not prices:
        return []
    k = 2.0 / (period + 1)
    ema_values = [prices[0]]
    for price in prices[1:]:
        ema_values.append(price * k + ema_values[-1] * (1 - k))
    return ema_values


def calculate_sma(prices: List[float], period: int) -> List[float]:
    """简单移动平均，返回完整序列"""
    result = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(prices[i - period + 1: i + 1]) / period)
    return result


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    标准 Wilder RSI
    - 顺序遍历，计算每日涨跌幅
    - 使用 Wilder 平滑（等价于 EMA alpha=1/period）
    """
    if len(prices) < period + 1:
        return 50.0

    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [max(c, 0) for c in changes]
    losses = [abs(min(c, 0)) for c in changes]

    # 初始平均
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Wilder 平滑
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)


def calculate_macd(prices: List[float], fast=12, slow=26, signal=9) -> Dict:
    """
    标准 MACD（DIF / DEA / Histogram）
    返回最新值及前一根柱值，用于判断金叉死叉
    """
    if len(prices) < slow + signal:
        return {"dif": 0.0, "dea": 0.0, "histogram": 0.0,
                "prev_histogram": 0.0, "cross": "none"}

    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    # DIF 序列（从 slow-1 开始才有意义）
    dif_series = [f - s for f, s in zip(ema_fast, ema_slow)]

    # DEA = EMA(DIF, signal)
    dea_series = calculate_ema(dif_series, signal)

    dif = dif_series[-1]
    dea = dea_series[-1]
    hist = (dif - dea) * 2  # 乘2是标准惯例

    prev_dif = dif_series[-2] if len(dif_series) >= 2 else dif
    prev_dea = dea_series[-2] if len(dea_series) >= 2 else dea
    prev_hist = (prev_dif - prev_dea) * 2

    # 金叉/死叉
    if dif > dea and prev_dif <= prev_dea:
        cross = "golden"   # 金叉
    elif dif < dea and prev_dif >= prev_dea:
        cross = "dead"     # 死叉
    elif hist > 0 and prev_hist > 0 and hist > prev_hist:
        cross = "bullish"  # 红柱扩大
    elif hist < 0 and prev_hist < 0 and hist < prev_hist:
        cross = "bearish"  # 绿柱扩大
    else:
        cross = "none"

    return {
        "dif": round(dif, 4),
        "dea": round(dea, 4),
        "histogram": round(hist, 4),
        "prev_histogram": round(prev_hist, 4),
        "cross": cross,
    }


def calculate_boll(prices: List[float], period: int = 20, multiplier: float = 2.0) -> Dict:
    """布林带（中轨SMA + 2倍标准差）"""
    if len(prices) < period:
        m = prices[-1]
        return {"upper": round(m * 1.02, 3), "middle": round(m, 3),
                "lower": round(m * 0.98, 3), "bandwidth": 0.04, "pct_b": 0.5}

    window = prices[-period:]
    middle = sum(window) / period
    variance = sum((p - middle) ** 2 for p in window) / period
    std = variance ** 0.5

    upper = middle + multiplier * std
    lower = middle - multiplier * std
    bandwidth = (upper - lower) / middle
    pct_b = (prices[-1] - lower) / (upper - lower) if upper != lower else 0.5

    return {
        "upper": round(upper, 3),
        "middle": round(middle, 3),
        "lower": round(lower, 3),
        "bandwidth": round(bandwidth, 4),  # 带宽收窄预示突破
        "pct_b": round(pct_b, 3),          # >1超上轨，<0超下轨
    }


def calculate_atr(closes: List[float], highs: List[float],
                  lows: List[float], period: int = 14) -> float:
    """Wilder ATR（真实波幅均值）"""
    if len(closes) < 2:
        return closes[-1] * 0.02

    tr_list = []
    for i in range(1, len(closes)):
        h, l, pc = highs[i], lows[i], closes[i - 1]
        tr_list.append(max(h - l, abs(h - pc), abs(l - pc)))

    if len(tr_list) < period:
        return sum(tr_list) / len(tr_list)

    # Wilder 平滑
    atr = sum(tr_list[:period]) / period
    for tr in tr_list[period:]:
        atr = (atr * (period - 1) + tr) / period
    return round(atr, 4)


def calculate_volume_ma(volumes: List[float], period: int = 20) -> float:
    if len(volumes) < period:
        return sum(volumes) / len(volumes)
    return sum(volumes[-period:]) / period


# ─────────────────────────────────────────────
# 趋势分析
# ─────────────────────────────────────────────

def analyze_trend(prices: List[float]) -> Tuple[str, str]:
    """
    趋势方向 + 强度
    用均线多头/空头排列 + 近期斜率双重确认
    """
    if len(prices) < 20:
        return "震荡", "弱势"

    ema5_series = calculate_ema(prices, 5)
    ema10_series = calculate_ema(prices, 10)
    ema20_series = calculate_ema(prices, 20)

    e5, e10, e20 = ema5_series[-1], ema10_series[-1], ema20_series[-1]
    price = prices[-1]

    # 多头排列 / 空头排列
    if price > e5 > e10 > e20:
        trend = "上涨"
    elif price < e5 < e10 < e20:
        trend = "下跌"
    else:
        trend = "震荡"

    # 斜率强度（5日EMA变化率）
    slope_5 = (ema5_series[-1] - ema5_series[-5]) / ema5_series[-5] * 100 if len(ema5_series) >= 5 else 0
    chg_20 = (prices[-1] - prices[-20]) / prices[-20] * 100 if len(prices) >= 20 else 0

    if abs(slope_5) > 2 or abs(chg_20) > 8:
        strength = "强势"
    elif abs(slope_5) > 0.5 or abs(chg_20) > 3:
        strength = "中等"
    else:
        strength = "弱势"

    return trend, strength


def analyze_weekly_trend(weekly_prices: List[float]) -> str:
    """周线趋势，三级判断"""
    if len(weekly_prices) < 5:
        return "震荡"
    ema5 = calculate_ema(weekly_prices, 5)
    e5 = ema5[-1]
    price = weekly_prices[-1]
    slope = (ema5[-1] - ema5[-5]) / ema5[-5] * 100 if len(ema5) >= 5 else 0

    if price > e5 and slope > 0.5:
        return "上涨"
    elif price < e5 and slope < -0.5:
        return "下跌"
    return "震荡"


# ─────────────────────────────────────────────
# 成交量分析
# ─────────────────────────────────────────────

def analyze_volume(closes: List[float], volumes: List[float]) -> Dict:
    """
    量价配合分析
    - 放量上涨：趋势确认
    - 缩量上涨：趋势减弱
    - 放量下跌：趋势加速
    - 缩量下跌：可能企稳
    """
    if len(volumes) < 5:
        return {"signal": "无法判断", "ratio": 1.0, "desc": ""}

    vol_ma20 = calculate_volume_ma(volumes, 20)
    vol_ma5 = calculate_volume_ma(volumes, 5)
    latest_vol = volumes[-1]
    ratio = round(latest_vol / vol_ma20, 2) if vol_ma20 > 0 else 1.0

    price_up = closes[-1] > closes[-2]
    vol_above_ma = vol_ma5 > vol_ma20

    if price_up and vol_above_ma:
        signal = "放量上涨"
        score = 1       # 正向
    elif price_up and not vol_above_ma:
        signal = "缩量上涨"
        score = -0.5    # 警惕
    elif not price_up and vol_above_ma:
        signal = "放量下跌"
        score = -1      # 负向
    else:
        signal = "缩量下跌"
        score = 0.3     # 可能企稳

    return {
        "signal": signal,
        "ratio": ratio,          # 当日量 / 20日均量
        "vol_ma5_vs_ma20": round(vol_ma5 / vol_ma20, 2) if vol_ma20 > 0 else 1.0,
        "score": score,
        "desc": f"量比{ratio}x，{signal}"
    }


# ─────────────────────────────────────────────
# K线形态识别
# ─────────────────────────────────────────────

def detect_candlestick_pattern(candles: List[Dict]) -> Dict:
    """
    识别最近2根K线的经典形态
    返回形态名称和方向（bullish/bearish/neutral）
    """
    if len(candles) < 2:
        return {"pattern": "无", "direction": "neutral", "strength": 0}

    c0 = candles[-2]  # 前一根
    c1 = candles[-1]  # 最新一根

    o0, h0, l0, c_0 = c0["open"], c0["high"], c0["low"], c0["close"]
    o1, h1, l1, c_1 = c1["open"], c1["high"], c1["low"], c1["close"]

    body1 = abs(c_1 - o1)
    range1 = h1 - l1
    upper_shadow = h1 - max(o1, c_1)
    lower_shadow = min(o1, c_1) - l1

    # 十字星（实体极小）
    if range1 > 0 and body1 / range1 < 0.1:
        return {"pattern": "十字星", "direction": "neutral", "strength": 0.5}

    # 锤子线（下影线长，实体在上方，出现在下跌末端）
    if (lower_shadow > body1 * 2 and upper_shadow < body1 * 0.5
            and range1 > 0 and c_0 < o0):  # 前一根为阴线
        return {"pattern": "锤子线", "direction": "bullish", "strength": 0.7}

    # 射击之星（上影线长，实体在下方，出现在上涨末端）
    if (upper_shadow > body1 * 2 and lower_shadow < body1 * 0.5
            and range1 > 0 and c_0 > o0):
        return {"pattern": "射击之星", "direction": "bearish", "strength": 0.7}

    # 看涨吞没（阳线完全吞没前一根阴线）
    if (c_1 > o1 and c_0 < o0 and o1 < c_0 and c_1 > o0):
        return {"pattern": "看涨吞没", "direction": "bullish", "strength": 0.8}

    # 看跌吞没（阴线完全吞没前一根阳线）
    if (c_1 < o1 and c_0 > o0 and o1 > c_0 and c_1 < o0):
        return {"pattern": "看跌吞没", "direction": "bearish", "strength": 0.8}

    # 早晨之星（三根K线，暂不实现，留扩展）
    direction = "bullish" if c_1 > o1 else "bearish"
    return {"pattern": "普通K线", "direction": direction, "strength": 0.2}


# ─────────────────────────────────────────────
# 支撑阻力位
# ─────────────────────────────────────────────

def find_support_resistance(prices: List[float], highs: List[float],
                             lows: List[float], lookback: int = 20) -> Dict:
    """近期重要支撑/阻力位（基于近期高低点）"""
    recent_highs = highs[-lookback:]
    recent_lows = lows[-lookback:]
    current = prices[-1]

    resistance_candidates = sorted([h for h in recent_highs if h > current])
    support_candidates = sorted([l for l in recent_lows if l < current], reverse=True)

    resistance = resistance_candidates[0] if resistance_candidates else current * 1.03
    support = support_candidates[0] if support_candidates else current * 0.97

    return {
        "resistance": round(resistance, 3),
        "support": round(support, 3),
        "distance_to_resistance_pct": round((resistance - current) / current * 100, 2),
        "distance_to_support_pct": round((current - support) / current * 100, 2),
    }


# ─────────────────────────────────────────────
# 动态仓位计算
# ─────────────────────────────────────────────

def calc_position_size(account_value: float, risk_pct: float,
                        entry: float, stop_loss: float) -> Dict:
    """
    Kelly-风险百分比混合仓位计算
    公式：shares = (账户净值 × 风险比例) / (入场价 - 止损价)
    """
    risk_amount = account_value * risk_pct
    stop_distance = abs(entry - stop_loss)
    if stop_distance == 0:
        return {"shares": 0, "amount": 0, "pct_of_account": 0}

    shares = risk_amount / stop_distance
    amount = shares * entry
    pct = amount / account_value

    # 上限：单笔不超过账户30%
    if pct > 0.30:
        pct = 0.30
        amount = account_value * 0.30
        shares = amount / entry

    return {
        "shares": int(shares),
        "amount": round(amount, 0),
        "pct_of_account": round(pct * 100, 1),
    }


# ─────────────────────────────────────────────
# 信号评分（归一化）
# ─────────────────────────────────────────────

def score_signals(
    current_price: float,
    closes: List[float],
    ema5: float, ema10: float, ema20: float,
    rsi: float,
    macd: Dict,
    boll: Dict,
    daily_trend: str,
    weekly_trend: str,
    vol_analysis: Dict,
    pattern: Dict,
    sr: Dict,
) -> Tuple[float, float, List[str], List[str]]:
    """
    归一化评分，买卖各项权重合计100分
    返回：(buy_score_0_to_1, sell_score_0_to_1, buy_reasons, sell_reasons)
    """
    buy_score = 0.0
    sell_score = 0.0
    buy_reasons = []
    sell_reasons = []

    # --- 趋势（权重30）---
    if daily_trend == "上涨":
        buy_score += 20
        buy_reasons.append("日线多头排列")
    elif daily_trend == "下跌":
        sell_score += 20
        sell_reasons.append("日线空头排列")

    if weekly_trend == "上涨":
        buy_score += 10
        buy_reasons.append("周线趋势向上")
    elif weekly_trend == "下跌":
        sell_score += 10
        sell_reasons.append("周线趋势向下")

    # --- RSI（权重20）---
    if 40 < rsi < 60:
        pass  # 中性，不加分
    elif 30 < rsi <= 40:
        buy_score += 10
        buy_reasons.append(f"RSI={rsi} 超卖区边缘回升")
    elif rsi <= 30:
        buy_score += 20
        buy_reasons.append(f"RSI={rsi} 深度超卖，反弹机会")
    elif 60 <= rsi < 70:
        sell_score += 5
        sell_reasons.append(f"RSI={rsi} 偏高注意回调")
    elif rsi >= 70:
        sell_score += 20
        sell_reasons.append(f"RSI={rsi} 超买，回调风险大")

    # --- MACD（权重20）---
    cross = macd["cross"]
    if cross == "golden":
        buy_score += 20
        buy_reasons.append("MACD金叉")
    elif cross == "bullish":
        buy_score += 10
        buy_reasons.append("MACD红柱扩大")
    elif cross == "dead":
        sell_score += 20
        sell_reasons.append("MACD死叉")
    elif cross == "bearish":
        sell_score += 10
        sell_reasons.append("MACD绿柱扩大")

    # --- 布林带（权重10）---
    pb = boll["pct_b"]
    if pb < 0.2:
        buy_score += 10
        buy_reasons.append(f"价格接近布林下轨（%B={pb}）")
    elif pb > 0.8:
        sell_score += 10
        sell_reasons.append(f"价格接近布林上轨（%B={pb}）")
    # 带宽收窄预示突破（中性，不加分偏向）
    if boll["bandwidth"] < 0.05:
        buy_reasons.append("布林带收窄，酝酿突破")

    # --- 成交量（权重10）---
    vscore = vol_analysis.get("score", 0)
    if vscore >= 1:
        buy_score += 10
        buy_reasons.append(vol_analysis["desc"])
    elif vscore <= -1:
        sell_score += 10
        sell_reasons.append(vol_analysis["desc"])
    elif vscore < 0:
        sell_score += 5
        sell_reasons.append(vol_analysis["desc"])

    # --- K线形态（权重10）---
    pd = pattern["direction"]
    ps = pattern["strength"]
    if pd == "bullish" and ps >= 0.6:
        buy_score += int(10 * ps)
        buy_reasons.append(f"K线形态：{pattern['pattern']}")
    elif pd == "bearish" and ps >= 0.6:
        sell_score += int(10 * ps)
        sell_reasons.append(f"K线形态：{pattern['pattern']}")

    # 归一化到 0-1
    return (
        round(min(buy_score, 100) / 100, 3),
        round(min(sell_score, 100) / 100, 3),
        buy_reasons,
        sell_reasons,
    )


# ─────────────────────────────────────────────
# 主决策引擎
# ─────────────────────────────────────────────

def generate_trading_decision(
    code: str,
    name: str,
    current_position: str = "无",
    account_value: float = 100000.0,
    risk_pct: float = 0.02,
) -> Dict:
    """
    生成结构化交易决策

    Args:
        code:             股票代码，如 HK.02359
        name:             股票名称
        current_position: 无 / 轻仓 / 半仓 / 重仓 / 持有
        account_value:    账户总资产（用于动态仓位计算）
        risk_pct:         单笔最大风险比例（默认2%）
    """
    # 统一持仓状态
    has_position = current_position in {"轻仓", "半仓", "重仓", "持有"}

    print(f"[Step 1] 获取 {name} ({code}) 数据...")
    snapshot = get_snapshot(code)
    daily_kline = get_kline(code, "1d", 120)
    weekly_kline = get_kline(code, "1w", 52)

    if not daily_kline or not daily_kline.get("data"):
        return _empty_decision("无法获取K线数据，禁止交易", code, name, current_position)

    daily_data = daily_kline["data"]
    weekly_data = weekly_kline.get("data", []) if weekly_kline else []

    closes = [d["close"] for d in daily_data]
    opens = [d["open"] for d in daily_data]
    highs = [d["high"] for d in daily_data]
    lows = [d["low"] for d in daily_data]
    volumes = [d.get("volume", 0) for d in daily_data]

    current_price = closes[-1]
    prev_price = closes[-2] if len(closes) > 1 else current_price

    print("[Step 2] 计算技术指标...")
    ema5_series = calculate_ema(closes, 5)
    ema10_series = calculate_ema(closes, 10)
    ema20_series = calculate_ema(closes, 20)
    ema5, ema10, ema20 = ema5_series[-1], ema10_series[-1], ema20_series[-1]

    rsi = calculate_rsi(closes, 14)
    macd = calculate_macd(closes)
    boll = calculate_boll(closes, 20)
    atr = calculate_atr(closes, highs, lows, 14)
    vol_analysis = analyze_volume(closes, volumes)
    pattern = detect_candlestick_pattern([
        {"open": o, "high": h, "low": l, "close": c}
        for o, h, l, c in zip(opens, highs, lows, closes)
    ])
    sr = find_support_resistance(closes, highs, lows, lookback=30)

    print("[Step 3] 市场判断...")
    daily_trend, daily_strength = analyze_trend(closes)
    weekly_closes = [d["close"] for d in weekly_data] if weekly_data else []
    weekly_trend = analyze_weekly_trend(weekly_closes)

    if daily_trend == "上涨" and weekly_trend in {"上涨", "震荡"}:
        overall_trend = "上涨"
    elif daily_trend == "下跌" and weekly_trend in {"下跌", "震荡"}:
        overall_trend = "下跌"
    elif daily_trend == weekly_trend:
        overall_trend = daily_trend
    else:
        overall_trend = "震荡"

    momentum = "超买" if rsi > 70 else ("超卖" if rsi < 30 else "中性")

    print("[Step 4] 信号评分...")
    buy_score, sell_score, buy_reasons, sell_reasons = score_signals(
        current_price, closes, ema5, ema10, ema20,
        rsi, macd, boll,
        daily_trend, weekly_trend,
        vol_analysis, pattern, sr,
    )

    print("[Step 5] 生成决策 + 风控...")
    # 止盈止损优先用支撑阻力位，ATR兜底
    sl_by_sr = sr["support"]
    sl_by_atr = round(current_price - atr * 2, 3)
    stop_loss = max(sl_by_sr, sl_by_atr)  # 取较高的止损（更保守）

    tp_by_sr = sr["resistance"]
    tp_by_atr = round(current_price + atr * 3, 3)
    take_profit = min(tp_by_sr, tp_by_atr) if tp_by_sr > current_price else tp_by_atr

    # 动态仓位
    pos_calc = calc_position_size(account_value, risk_pct, current_price, stop_loss)
    risk_reward = round((take_profit - current_price) / max(current_price - stop_loss, 0.001), 2)

    # ── 决策逻辑 ──
    if has_position:
        # 持仓状态：优先保护利润
        if sell_score > 0.5 or overall_trend == "下跌":
            action = "SELL"
            reduce = "50%" if current_position == "重仓" else ("30%" if current_position in {"半仓", "持有"} else "清仓")
            reason = f"持仓风险上升，建议减仓{reduce}。" + "；".join(sell_reasons[:3])
            confidence = round(sell_score, 2)
            position_size = f"减仓{reduce}"
        elif buy_score > 0.5 and overall_trend == "上涨":
            action = "HOLD"
            reason = "趋势持续向好，持有为主。" + "；".join(buy_reasons[:3])
            confidence = round(buy_score, 2)
            position_size = "继续持有"
            # 持仓不加仓，仅更新止损
            stop_loss = round(max(ema20, stop_loss), 3)
            take_profit = round(take_profit, 3)
        else:
            action = "HOLD"
            reason = "趋势不明，维持现状，等待信号明确"
            confidence = 0.4
            position_size = "维持现状"

    else:
        # 无仓位：寻找入场机会
        if buy_score >= 0.55 and overall_trend == "上涨" and risk_reward >= 1.5:
            action = "BUY"
            reason = "多重买入信号共振，风险回报比合理。" + "；".join(buy_reasons[:3])
            confidence = round(buy_score, 2)
            position_size = f"{pos_calc['pct_of_account']}% 账户资金"
        elif buy_score >= 0.45 and overall_trend == "上涨":
            action = "HOLD"
            reason = f"买入信号存在但风险回报比({risk_reward})不足1.5，等待回调。" + "；".join(buy_reasons[:2])
            confidence = 0.4
            position_size = "0%"
        elif sell_score > 0.5:
            action = "HOLD"
            reason = "空头信号强烈，不适合买入。" + "；".join(sell_reasons[:2])
            confidence = round(sell_score, 2)
            position_size = "0%"
        else:
            action = "HOLD"
            reason = "信号不明确，耐心等待更清晰的入场机会"
            confidence = 0.3
            position_size = "0%"

    # 最终安全检查
    if action == "BUY" and stop_loss >= current_price:
        action = "HOLD"
        reason = "止损位计算异常，放弃交易"
        confidence = 0.0
        position_size = "0%"

    return {
        "stock": {
            "code": code,
            "name": name,
            "current_price": round(current_price, 3),
            "prev_close": round(prev_price, 3),
            "change_pct": round((current_price - prev_price) / prev_price * 100, 2),
        },
        "technical": {
            "ema5": round(ema5, 3),
            "ema10": round(ema10, 3),
            "ema20": round(ema20, 3),
            "rsi": rsi,
            "macd": macd,
            "boll": boll,
            "atr": round(atr, 3),
            "volume": vol_analysis,
            "pattern": pattern,
        },
        "market": {
            "daily_trend": daily_trend,
            "daily_strength": daily_strength,
            "weekly_trend": weekly_trend,
            "overall_trend": overall_trend,
            "momentum": momentum,
            "support": sr["support"],
            "resistance": sr["resistance"],
            "distance_to_resistance_pct": sr["distance_to_resistance_pct"],
            "distance_to_support_pct": sr["distance_to_support_pct"],
        },
        "signals": {
            "buy_score": buy_score,
            "sell_score": sell_score,
            "buy_reasons": buy_reasons,
            "sell_reasons": sell_reasons,
            "risk_reward_ratio": risk_reward,
        },
        "decision": {
            "action": action,
            "reason": reason,
            "confidence": confidence,
            "entry_price": round(current_price, 3) if action == "BUY" else "",
            "stop_loss": round(stop_loss, 3) if action in {"BUY", "HOLD"} and stop_loss else "",
            "take_profit": round(take_profit, 3) if action in {"BUY", "HOLD"} and take_profit else "",
            "position_size": position_size,
            "shares": pos_calc["shares"] if action == "BUY" else 0,
        },
        "risk_control": {
            "max_risk_per_trade": f"{risk_pct * 100}%",
            "risk_amount": round(account_value * risk_pct, 0),
            "current_position": current_position,
            "risk_reward_ratio": risk_reward,
            "warning": _build_warning(action, risk_reward, rsi),
        },
    }


def _empty_decision(reason: str, code: str, name: str, position: str) -> Dict:
    return {
        "stock": {"code": code, "name": name, "current_price": 0, "prev_close": 0, "change_pct": 0},
        "technical": {},
        "market": {},
        "signals": {"buy_score": 0, "sell_score": 0, "buy_reasons": [], "sell_reasons": []},
        "decision": {"action": "HOLD", "reason": reason, "confidence": 0,
                     "entry_price": "", "stop_loss": "", "take_profit": "", "position_size": "0%"},
        "risk_control": {"max_risk_per_trade": "2%", "current_position": position, "warning": reason},
    }


def _build_warning(action: str, rr: float, rsi: float) -> str:
    warnings = []
    if action == "BUY":
        warnings.append("禁止All-in，严格执行止损")
        if rr < 2:
            warnings.append(f"风险回报比{rr}偏低，可适当减少仓位")
    if rsi > 75:
        warnings.append(f"RSI={rsi} 高度超买，追涨风险极大")
    if rsi < 25:
        warnings.append(f"RSI={rsi} 深度超卖，可小仓试探")
    return "；".join(warnings) if warnings else ""


# ─────────────────────────────────────────────
# 格式化输出
# ─────────────────────────────────────────────

def print_decision(d: Dict):
    stock = d.get("stock", {})
    tech = d.get("technical", {})
    market = d.get("market", {})
    signals = d.get("signals", {})
    dec = d.get("decision", {})
    risk = d.get("risk_control", {})

    emoji_map = {"BUY": "🟢 买入", "SELL": "🔴 卖出", "HOLD": "🟡 持有/观望"}
    macd = tech.get("macd", {})
    boll = tech.get("boll", {})
    vol = tech.get("volume", {})
    pat = tech.get("pattern", {})

    print("\n" + "=" * 65)
    print(f"  📊 {stock.get('name')} ({stock.get('code')})  交易决策报告 v2")
    print("=" * 65)

    print(f"\n💰 价格   {stock.get('current_price')}  ({stock.get('change_pct'):+.2f}%)")
    print(f"   支撑   {market.get('support')}  (距-{market.get('distance_to_support_pct')}%)")
    print(f"   阻力   {market.get('resistance')}  (距+{market.get('distance_to_resistance_pct')}%)")

    print(f"\n📈 技术指标")
    print(f"   EMA5/10/20  {tech.get('ema5')} / {tech.get('ema10')} / {tech.get('ema20')}")
    print(f"   RSI(14)     {tech.get('rsi')}  [{market.get('momentum')}]")
    print(f"   MACD        DIF={macd.get('dif')}  DEA={macd.get('dea')}  [{macd.get('cross')}]")
    print(f"   BOLL        上{boll.get('upper')} 中{boll.get('middle')} 下{boll.get('lower')}  %B={boll.get('pct_b')}")
    print(f"   ATR(14)     {tech.get('atr')}")
    print(f"   成交量      {vol.get('signal')}  量比={vol.get('ratio')}x")
    print(f"   K线形态     {pat.get('pattern')}  [{pat.get('direction')}]")

    print(f"\n📊 市场判断")
    print(f"   日线  {market.get('daily_trend')} ({market.get('daily_strength')})")
    print(f"   周线  {market.get('weekly_trend')}")
    print(f"   综合  {market.get('overall_trend')}")

    print(f"\n🎯 信号评分")
    print(f"   买入  {signals.get('buy_score', 0)*100:.0f}/100   {'; '.join(signals.get('buy_reasons', []))}")
    print(f"   卖出  {signals.get('sell_score', 0)*100:.0f}/100   {'; '.join(signals.get('sell_reasons', []))}")
    print(f"   风险回报比  {signals.get('risk_reward_ratio')}")

    action_label = emoji_map.get(dec.get("action", "HOLD"), "🟡 观望")
    print(f"\n{'=' * 65}")
    print(f"  {action_label}   置信度 {dec.get('confidence', 0)*100:.0f}%")
    print(f"  {dec.get('reason', '')}")
    if dec.get("entry_price"):
        print(f"\n  入场价  {dec['entry_price']}")
        print(f"  止损价  {dec['stop_loss']}   止盈价  {dec['take_profit']}")
        print(f"  仓位    {dec['position_size']}  ({dec.get('shares', 0)} 股)")
    else:
        print(f"\n  仓位建议  {dec.get('position_size', '--')}")
        if dec.get("stop_loss"):
            print(f"  移动止损  {dec['stop_loss']}")

    print(f"\n⚠️  风控")
    print(f"   单笔风险上限  {risk.get('max_risk_per_trade')}  / 风险金额 ¥{risk.get('risk_amount', 0)}")
    print(f"   当前持仓      {risk.get('current_position')}")
    if risk.get("warning"):
        print(f"   ⚠️  {risk['warning']}")
    print("=" * 65)


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python trading_decision.py <code> [name] [position] [account_value]")
        print("       position: 无/轻仓/半仓/重仓/持有  (default: 无)")
        print("       account_value: 账户总值 (default: 100000)")
        print("Example: python trading_decision.py HK.02359 药明康德 轻仓 500000")
        sys.exit(1)

    code = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else code
    position = sys.argv[3] if len(sys.argv) > 3 else "无"
    account = float(sys.argv[4]) if len(sys.argv) > 4 else 100000.0

    decision = generate_trading_decision(code, name, position, account)
    print_decision(decision)
    print("\n📄 JSON:")
    print(json.dumps(decision, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
