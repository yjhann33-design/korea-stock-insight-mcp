"""Daily stats collector for korea-stock-insight-mcp.

Pulls metrics from 3 channels (GitHub / PyPI / MCP Registry), compares with
previous day, and pushes a one-line summary to Telegram.

Run via cron once per day (KST 09:00 = UTC 00:00).
State (yesterday's metrics) persisted in .daily_stats_state.json next to this
file, ignored by git.

Env required:
  GITHUB_TOKEN          — for GitHub traffic API (owner-scope)
                          (gh CLI 자동 인증 안 되므로 명시 env or gh CLI 우회)
  TELEGRAM_BOT_TOKEN    — invest_shorts 봇 토큰 재사용
  TELEGRAM_CHAT_ID      — 동일
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# ─── env: 두 .env 모두 로드 (텔레그램 토큰은 invest_shorts 쪽에 있음) ───
HERE = Path(__file__).parent
PROJECT = HERE.parent
load_dotenv(PROJECT / ".env")  # DART_API_KEY (안 써도 무방)
load_dotenv("/root/projects/cc/invest_shorts/.env")  # TELEGRAM_*

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")

OWNER = "yjhann33-design"
REPO = "korea-stock-insight-mcp"
PKG = "korea-stock-insight-mcp"
MCP_NAME = "io.github.yjhann33-design/korea-stock-insight-mcp"

STATE_FILE = HERE / ".daily_stats_state.json"
KST = timezone(timedelta(hours=9))


# ─── helpers ────────────────────────────────────────────────────────────
def gh_api(path: str) -> dict:
    """Call GitHub API via gh CLI (uses already-authenticated token)."""
    r = subprocess.run(
        ["gh", "api", path],
        capture_output=True, text=True, timeout=15,
    )
    if r.returncode != 0:
        return {"_error": r.stderr.strip()[:120]}
    try:
        return json.loads(r.stdout)
    except Exception as e:
        return {"_error": f"json decode: {e}"}


def collect_github() -> dict:
    """Stars / forks / watchers / open_issues + 14d traffic (views/clones)."""
    repo = gh_api(f"repos/{OWNER}/{REPO}")
    views = gh_api(f"repos/{OWNER}/{REPO}/traffic/views")
    clones = gh_api(f"repos/{OWNER}/{REPO}/traffic/clones")
    return {
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "watchers": repo.get("subscribers_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "views_14d": views.get("count", 0),
        "uniques_14d": views.get("uniques", 0),
        "clones_14d": clones.get("count", 0),
        "clone_uniques_14d": clones.get("uniques", 0),
    }


def collect_pypi() -> dict:
    """PyPI downloads via pypistats.org public API.

    신규 패키지는 stats 노출까지 1~3일 걸림 (그 동안 404 반환). 0으로 채워 메시지 깨지지 않게.
    """
    out = {"downloads_yesterday": 0, "downloads_7d": 0, "downloads_30d": 0}
    try:
        r = requests.get(
            f"https://pypistats.org/api/packages/{PKG}/recent",
            timeout=15,
        )
        if r.status_code == 404:
            out["_pypi_note"] = "404 (stats not yet available — new package)"
            return out
        if r.status_code != 200:
            out["_pypi_error"] = f"HTTP {r.status_code}"
            return out
        data = r.json().get("data") or {}
        out["downloads_yesterday"] = data.get("last_day", 0) or 0
        out["downloads_7d"] = data.get("last_week", 0) or 0
        out["downloads_30d"] = data.get("last_month", 0) or 0
    except Exception as e:
        out["_pypi_error"] = str(e)[:100]
    return out


def collect_registry() -> dict:
    """MCP Registry: confirm our server is listed + return latest version.

    Same name has multiple versions; we want the one tagged isLatest=True.
    """
    try:
        r = requests.get(
            "https://registry.modelcontextprotocol.io/v0/servers",
            params={"search": "korea-stock-insight"},
            timeout=15,
        )
        for s in r.json().get("servers", []):
            srv = s.get("server", {})
            meta = s.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {})
            if srv.get("name") == MCP_NAME and meta.get("isLatest"):
                return {"registry_version": srv.get("version", "?")}
        return {"registry_version": "NOT_FOUND"}
    except Exception as e:
        return {"_error": f"registry: {e}"}


def load_prev() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(stats: dict) -> None:
    STATE_FILE.write_text(json.dumps(stats, indent=2))


def delta(curr: int, prev: int | None) -> str:
    """+5 / -2 / ±0 / (first) 형태로 변화량 포맷."""
    if prev is None:
        return "(first)"
    diff = curr - prev
    if diff > 0:
        return f"(+{diff})"
    if diff < 0:
        return f"({diff})"
    return "(±0)"


def fmt_message(curr: dict, prev: dict) -> str:
    today = datetime.now(KST).strftime("%Y-%m-%d")
    lines = [
        f"📊 *korea-stock-insight-mcp* — {today}",
        "",
        "*GitHub*",
        f"  ⭐ stars: {curr['stars']} {delta(curr['stars'], prev.get('stars'))}",
        f"  🍴 forks: {curr['forks']} {delta(curr['forks'], prev.get('forks'))}",
        f"  👀 watchers: {curr['watchers']} {delta(curr['watchers'], prev.get('watchers'))}",
        f"  🐛 issues: {curr['open_issues']} {delta(curr['open_issues'], prev.get('open_issues'))}",
        f"  📈 views 14d: {curr['views_14d']} ({curr['uniques_14d']} unique)",
        f"  📥 clones 14d: {curr['clones_14d']} ({curr['clone_uniques_14d']} unique)",
        "",
        "*PyPI*",
        f"  📦 yesterday: {curr['downloads_yesterday']} {delta(curr['downloads_yesterday'], prev.get('downloads_yesterday'))}",
        f"  📦 last 7d: {curr['downloads_7d']}",
        f"  📦 last 30d: {curr['downloads_30d']}",
        "",
        "*MCP Registry*",
        f"  🏷️ version: {curr['registry_version']}",
    ]
    return "\n".join(lines)


def send_telegram(text: str) -> None:
    if not TG_TOKEN or not TG_CHAT:
        print("[WARN] TELEGRAM_* not set — printing instead", file=sys.stderr)
        print(text)
        return
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={
            "chat_id": TG_CHAT,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    if not r.ok:
        print(f"[ERR] telegram: {r.status_code} {r.text[:200]}", file=sys.stderr)


def main() -> int:
    curr = {}
    curr.update(collect_github())
    curr.update(collect_pypi())
    curr.update(collect_registry())

    prev = load_prev()
    msg = fmt_message(curr, prev)
    send_telegram(msg)
    save_state(curr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
