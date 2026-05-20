# Korea Stock Insight MCP

mcp-name: io.github.yjhann33-design/korea-stock-insight-mcp

[![PyPI](https://img.shields.io/pypi/v/korea-stock-insight-mcp)](https://pypi.org/project/korea-stock-insight-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **English-first MCP — built for global LLM analysts, not Korean fluency speakers.**

Drop-in for Claude Desktop, Cursor, Cline, and any [MCP-compatible client](https://modelcontextprotocol.io/clients). Ask in English, get Korean filings, financials, and KOSPI/KOSDAQ prices in one tool call chain — DART corp_code lookup, disclosures, XBRL statements, daily OHLCV.

## What you get

| Tool | What it does |
|---|---|
| `get_today_date` | Today in KST/UTC (YYYYMMDD) — call before any date-range query |
| `get_corp_code` | Resolve Korean company name or 6-digit ticker → DART corp_code |
| `get_disclosure_list` | Recent DART filings (date, title, type, receipt no.) |
| `get_disclosure` | Filing metadata + canonical viewer URL |
| `get_financial_statement` | Full XBRL financial statements (consolidated/separate, quarterly/annual) |
| `get_stock_quote` | Daily OHLCV from KOSPI/KOSDAQ (via yfinance, no key required) |

DART (전자공시시스템) is South Korea's electronic disclosure system — the SEC EDGAR equivalent, operated by the Financial Supervisory Service (FSS).

## Why English-first matters

Korean public filings are written in Korean, ticker codes are 6-digit numerics with no global mnemonic, and the disclosure system (DART) has no English equivalent of EDGAR's full-text search. For a non-Korean analyst, that's three friction layers before any actual research.

This server collapses them. Tool descriptions, parameter names, and examples are all written for an LLM that *doesn't read Korean* — company resolution accepts English names ("Samsung Electronics", "Naver"), responses include English context where useful, and the workflow is one Claude/Cursor turn instead of three browser tabs.

- **English-first tool descriptions** — names, params, examples all in English
- **DART + KRX in one place** — disclosures, financials, daily prices through a single MCP
- **One-line install, no account** — `uvx korea-stock-insight-mcp` and you're done (only a free DART key needed)
- **Local stdio, MIT, no telemetry** — your queries don't leave your machine

## Quick start (Claude Desktop)

### 1. Get a free DART API key

Register at [opendart.fss.or.kr](https://opendart.fss.or.kr/) and grab your API key from the user page. Instant, free, no credit card.

### 2. Add to your Claude Desktop config

Edit `claude_desktop_config.json` (location: macOS `~/Library/Application Support/Claude/`, Windows `%APPDATA%\Claude\`):

```json
{
  "mcpServers": {
    "korea-stock-insight": {
      "command": "uvx",
      "args": ["korea-stock-insight-mcp"],
      "env": {
        "DART_API_KEY": "YOUR_DART_KEY_HERE"
      }
    }
  }
}
```

If you don't have `uvx`, install [uv](https://docs.astral.sh/uv/) first (one-liner on macOS/Linux/Windows), or use `pipx`:

```json
{
  "mcpServers": {
    "korea-stock-insight": {
      "command": "pipx",
      "args": ["run", "korea-stock-insight-mcp"],
      "env": {"DART_API_KEY": "YOUR_DART_KEY_HERE"}
    }
  }
}
```

### 3. Restart Claude Desktop and try

> *"What were Samsung Electronics' most recent disclosures? Pull their last quarter's revenue and operating profit."*

Claude will chain `get_corp_code("Samsung Electronics")` → `get_disclosure_list("005930")` → `get_financial_statement(corp_code, 2025, "FY")` automatically.

## Sample queries (30 seconds, copy-paste into Claude)

Three workflows global analysts actually run on Korean equities. Each one chains 2–4 tool calls automatically.

### 1. Memory-cycle peer comparison
> *"Compare Samsung Electronics and SK Hynix on revenue, operating margin, and capex for the most recent annual filing. Highlight where they diverge."*

Resolves both names to corp_codes → pulls latest XBRL → returns a side-by-side. Useful for tracking the HBM/DRAM cycle.

### 2. Disclosure radar before a catalyst
> *"Show me Naver's last 30 days of DART filings. Flag anything about earnings, M&A, share buybacks, or executive changes."*

`get_disclosure_list` with date range, then Claude triages titles. No Korean reading required — the tool description tells Claude what filing types to look for.

### 3. Price + filing context in one turn
> *"What did Kakao file most recently, and how has the stock moved on KOSPI over the past 90 days?"*

Combines `get_disclosure_list` + `get_stock_quote` so you get the news and the price reaction in the same answer.

### Other examples

- *"Pull LG Energy Solution's last annual report and summarize the management discussion."*
- *"What's the KODEX 200 ETF's 6-month trend?"* (works with ETFs too)
- *"For Hyundai Motor, list every disclosure tagged as a major decision (주요사항보고서) in 2025."*

## Roadmap

- **v0.2** — Full disclosure body extraction (zipped XBRL → plain text)
- **v0.3** — Multi-company batch queries, sector aggregations
- **Future** — Optional hosted tier with English-summarized disclosures and webhook push (no ETA; track progress in [GitHub Issues](https://github.com/yjhann33-design/korea-stock-insight-mcp/issues))

## Feedback & contributions

This is solo-maintained, and stdio mode means I can't see who's using it. The only signals I get are PyPI downloads, GitHub stars, and what you tell me.

**If this helps you, please let me know:**

- 🐛 [Open an issue](https://github.com/yjhann33-design/korea-stock-insight-mcp/issues) — bugs, missing tools, broken queries
- 💬 [Discussions](https://github.com/yjhann33-design/korea-stock-insight-mcp/discussions) — "anyone analyzed [ticker]?", "is this the right tool for X?", general questions
- ⭐ Star the repo — easiest way to signal demand and shape the roadmap

If you actually analyze Korean stocks with Claude/Cursor, I'd genuinely love to hear what queries you run and what's missing.

## License

MIT. See [LICENSE](./LICENSE).

## Acknowledgments

- DART OpenAPI by Korea's Financial Supervisory Service
- KRX daily prices via [yfinance](https://github.com/ranaroussi/yfinance)
- [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic
