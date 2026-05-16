"""W2 smoke test — all 6 tools (1 common + 4 DART + 1 KRX) end-to-end.

Boots server.py as a stdio subprocess, runs an MCP client, and validates
that every tool returns a coherent payload for real Korean stocks.
"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).parent
SAMSUNG_STOCK = "005930"   # 삼성전자 — 가장 큰 KOSPI 종목, 항상 데이터 있음


def _unpack(call_result) -> dict:
    return json.loads(call_result.content[0].text)


async def main() -> int:
    params = StdioServerParameters(
        command=str(HERE / "venv" / "bin" / "python"),
        args=[str(HERE / "server.py")],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"[OK] tools/list ({len(names)}) → {names}")
            expected = {"get_today_date", "get_corp_code", "get_disclosure_list",
                        "get_disclosure", "get_financial_statement", "get_stock_quote"}
            assert expected.issubset(set(names)), f"missing: {expected - set(names)}"

            # 1. get_today_date
            r = _unpack(await session.call_tool("get_today_date", {}))
            print(f"[OK] get_today_date → kst={r['kst']}")

            # 2. get_corp_code — by stock_code (fast path)
            r = _unpack(await session.call_tool("get_corp_code", {"query": SAMSUNG_STOCK}))
            print(f"[OK] get_corp_code('{SAMSUNG_STOCK}') → status={r['status']} count={r.get('count')}")
            assert r["status"] == "ok" and r["count"] >= 1
            samsung_corp_code = r["matches"][0]["corp_code"]
            print(f"      → corp_code={samsung_corp_code} ({r['matches'][0]['corp_name']})")

            # 3. get_corp_code — by Korean name (partial match)
            r = _unpack(await session.call_tool("get_corp_code", {"query": "삼성전자"}))
            print(f"[OK] get_corp_code('삼성전자') → count={r['count']}")
            assert r["status"] == "ok" and r["count"] >= 1

            # 4. get_disclosure_list
            r = _unpack(await session.call_tool(
                "get_disclosure_list", {"stock_code": SAMSUNG_STOCK, "days": 30}
            ))
            print(f"[OK] get_disclosure_list → status={r['status']} count={r['count']}")
            assert r["status"] == "ok"
            rcept_no = r["disclosures"][0]["rcept_no"] if r["disclosures"] else None

            # 5. get_disclosure (need at least one rcept_no)
            if rcept_no:
                r = _unpack(await session.call_tool("get_disclosure", {"rcept_no": rcept_no}))
                print(f"[OK] get_disclosure({rcept_no}) → {r['status']}, url present={bool(r.get('url'))}")
                assert r["status"] == "ok" and r["url"].startswith("https://dart.fss.or.kr/")

            # 6. get_financial_statement (annual 2024 — definitely filed by 2026-05)
            r = _unpack(await session.call_tool(
                "get_financial_statement",
                {"corp_code": samsung_corp_code, "year": 2024, "quarter": "FY"}
            ))
            print(f"[OK] get_financial_statement(2024 FY) → status={r['status']} accounts={r.get('count')}")
            assert r["status"] == "ok"

            # 7. get_stock_quote
            r = _unpack(await session.call_tool(
                "get_stock_quote", {"stock_code": SAMSUNG_STOCK, "days": 7}
            ))
            print(f"[OK] get_stock_quote → status={r['status']} bars={r.get('count')} ticker={r.get('ticker')}")
            if r["bars"]:
                last = r["bars"][-1]
                print(f"      last: {last['date']} close={last['close']:,.0f} KRW vol={last['volume']:,}")

    print("\n[PASS] All 6 tools end-to-end ✓")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
