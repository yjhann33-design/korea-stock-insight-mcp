"""KRX (Korea Exchange) price data via yfinance.

v0.1 uses yfinance for daily OHLCV — no API key required, works globally.
v0.2 may add official KRX OpenAPI (requires KRX_API_KEY) for intraday and
more accurate market cap / shares outstanding.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import yfinance as yf

# KOSPI = .KS, KOSDAQ = .KQ. We try both since stock_code alone is ambiguous.
SUFFIXES = (".KS", ".KQ")


def _try_yf(stock_code: str, period: str) -> Optional[tuple[str, "pd.DataFrame"]]:
    for suffix in SUFFIXES:
        ticker = f"{stock_code}{suffix}"
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period, auto_adjust=False)
            if hist is not None and not hist.empty:
                return ticker, hist
        except Exception:
            continue
    return None


def get_stock_quote(stock_code: str, days: int = 30) -> dict:
    """Daily OHLCV for a Korean-listed stock (KOSPI/KOSDAQ).

    Args:
      stock_code: 6-digit Korean ticker (e.g. "005930" for Samsung Electronics).
                  KOSPI/KOSDAQ both supported; we auto-detect by trying both.
      days: Lookback window in trading days (default 30, max 365 recommended).
            Note: yfinance returns trading days only, so 30d ≈ 22 trading days.

    Returns:
      {"status", "ticker", "currency":"KRW", "count", "bars":[{date, open, high, low, close, volume}, ...]}
      Sorted oldest → newest. Prices in KRW (Korean won), integer-ish.
    """
    if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
        return {"status": "error", "message": "stock_code must be 6-digit numeric string"}

    # period 표기는 yfinance 규칙 (1mo/3mo/6mo/1y/2y/5y/max). days로 근사.
    if days <= 7:
        period = "7d"
    elif days <= 31:
        period = "1mo"
    elif days <= 90:
        period = "3mo"
    elif days <= 180:
        period = "6mo"
    elif days <= 365:
        period = "1y"
    else:
        period = "2y"

    result = _try_yf(stock_code, period)
    if result is None:
        return {"status": "error", "message": f"No data found for {stock_code} on KOSPI or KOSDAQ"}

    ticker, hist = result
    bars = []
    for idx, row in hist.iterrows():
        bars.append({
            "date": idx.strftime("%Y-%m-%d"),
            "open": float(row["Open"]) if not _na(row["Open"]) else None,
            "high": float(row["High"]) if not _na(row["High"]) else None,
            "low": float(row["Low"]) if not _na(row["Low"]) else None,
            "close": float(row["Close"]) if not _na(row["Close"]) else None,
            "volume": int(row["Volume"]) if not _na(row["Volume"]) else 0,
        })
    # 요청한 days로 trim (yfinance period가 보통 더 많이 반환)
    bars = bars[-days:]
    return {
        "status": "ok",
        "ticker": ticker,
        "currency": "KRW",
        "count": len(bars),
        "bars": bars,
    }


def _na(v) -> bool:
    try:
        return v != v  # NaN check
    except Exception:
        return v is None
