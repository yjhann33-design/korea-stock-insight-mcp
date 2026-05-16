"""Korea Stock Insight MCP — entrypoint.

English-first MCP server exposing Korean stock market data to LLM clients
(Claude, Cursor, etc). Free tier: stdio transport, user-supplied DART_API_KEY.

Architecture mirrors jjlabsio's pattern: thin entrypoint that registers tools,
real work delegated to per-source modules (dart.py, krx.py).
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")  # .env는 모듈 import 전에 로드해야 함

from mcp.server.fastmcp import FastMCP  # noqa: E402

import dart  # noqa: E402
import krx  # noqa: E402
from datetime import datetime, timezone, timedelta  # noqa: E402

KST = timezone(timedelta(hours=9))
mcp = FastMCP("korea-stock-insight-mcp")


# ─── common ────────────────────────────────────────────────────────────
@mcp.tool()
def get_today_date() -> dict:
    """Return today's date in KST and UTC (YYYYMMDD format).

    Use before any date-range query — Korean market APIs require YYYYMMDD
    and KST is the trading-day timezone.
    """
    now_utc = datetime.now(timezone.utc)
    now_kst = now_utc.astimezone(KST)
    return {
        "kst": now_kst.strftime("%Y%m%d"),
        "utc": now_utc.strftime("%Y%m%d"),
        "kst_iso": now_kst.isoformat(),
    }


# ─── DART ──────────────────────────────────────────────────────────────
@mcp.tool()
def get_corp_code(query: str) -> dict:
    """Resolve Korean company name or stock code to DART corp_code (8-digit).

    DART corp_code is the unique identifier needed for financial-statement
    and detailed-disclosure lookups. Accepts either a 6-digit stock code
    (exact match) or a Korean company name (partial, case-insensitive).

    For non-Korean speakers: search the company's English name first via
    web search, then pass the official Korean name to this tool.
    """
    return dart.get_corp_code(query)


@mcp.tool()
def get_disclosure_list(stock_code: str, days: int = 30) -> dict:
    """List recent DART disclosures for a Korean-listed company.

    Returns filing metadata (date, title, type, receipt number) for the
    last `days` calendar days. Use `rcept_no` with `get_disclosure` to
    open a specific filing.
    """
    return dart.get_disclosure_list(stock_code, days)


@mcp.tool()
def get_disclosure(rcept_no: str) -> dict:
    """Fetch metadata + viewer URL for a specific DART filing.

    v0.1 returns the canonical dart.fss.or.kr viewer URL. v0.2 will add
    in-process body extraction (DART filings are zipped XBRL).
    """
    return dart.get_disclosure(rcept_no)


@mcp.tool()
def get_financial_statement(corp_code: str, year: int, quarter: str = "FY", fs_div: str = "CFS") -> dict:
    """Full XBRL financial statements for a Korean company.

    Returns every account line from the periodic report. Use `get_corp_code`
    first to resolve a name/ticker to the 8-digit corp_code.

    Args:
      corp_code: 8-digit DART code.
      year: Business year (e.g. 2025).
      quarter: "Q1" / "H1" / "Q3" / "FY" (default "FY" = annual report).
      fs_div: "CFS" (consolidated, default) or "OFS" (separate).
    """
    return dart.get_financial_statement(corp_code, year, quarter, fs_div)


# ─── KRX ───────────────────────────────────────────────────────────────
@mcp.tool()
def get_stock_quote(stock_code: str, days: int = 30) -> dict:
    """Daily OHLCV bars for a Korean-listed stock (KOSPI/KOSDAQ).

    Auto-detects the market by trying .KS then .KQ. Prices in KRW.
    v0.1 uses yfinance (no API key required); v0.2 may add official KRX
    OpenAPI for intraday and accurate market cap.
    """
    return krx.get_stock_quote(stock_code, days)


def main() -> None:
    """Console-script entrypoint (referenced by pyproject.toml [project.scripts])."""
    mcp.run()


if __name__ == "__main__":
    main()
