# Korea Stock Insight MCP

mcp-name: io.github.yjhann33-design/korea-stock-insight-mcp

[![PyPI](https://img.shields.io/pypi/v/korea-stock-insight-mcp)](https://pypi.org/project/korea-stock-insight-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**MCP server for Korean stock market analysis.** Drop-in for Claude Desktop, Cursor, Cline, and any [MCP-compatible client](https://modelcontextprotocol.io/clients). English-first tool descriptions for global LLM analysts researching Korean equities.

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

## Why this server?

- **English-first tool descriptions** — built for global LLM analysts, no Korean fluency required
- **DART + KRX in one place** — disclosures, financials, and prices through a single MCP
- **No vendor lock-in** — runs locally via stdio with your own free DART API key
- **MIT licensed, no telemetry, no account required**

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

## Sample queries

- *"Compare the Q1 2025 operating margins of Samsung Electronics, SK Hynix, and LG Energy Solution."*
- *"Show me all M&A-related disclosures for Naver in the last 60 days."*
- *"What's KODEX 200's price trend over the past 3 months?"*
- *"Pull Kakao's most recent annual report."*

## Roadmap

- **v0.2** — Full disclosure body extraction (zipped XBRL → plain text)
- **v0.3** — Multi-company batch queries, sector aggregations
- **Future** — Optional hosted tier with English-summarized disclosures and webhook push (no ETA; track progress in [GitHub Issues](https://github.com/yjhann33-design/korea-stock-insight-mcp/issues))

## License

MIT. See [LICENSE](./LICENSE).

## Acknowledgments

- DART OpenAPI by Korea's Financial Supervisory Service
- KRX daily prices via [yfinance](https://github.com/ranaroussi/yfinance)
- [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic
