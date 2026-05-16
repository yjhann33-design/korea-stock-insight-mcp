"""DART (Korean electronic disclosure) API client.

Wraps the official opendart.fss.or.kr API. Free tier — user supplies their own
DART_API_KEY via .env. No external transformation, raw data passthrough with
English-friendly response shapes.
"""
from __future__ import annotations

import io
import json
import os
import time
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import requests

DART_API_KEY = os.environ.get("DART_API_KEY", "")
DART_BASE = "https://opendart.fss.or.kr/api"
HTTP_TIMEOUT = 30
ZIP_TIMEOUT = 300  # corp_code zip is ~10MB and KR→global is slow

KST = timezone(timedelta(hours=9))

# corp_code XML zip은 ~10MB, 매 호출 다운로드는 비용·시간 낭비.
# 사용자 홈 디렉토리에 캐시 (XDG style). 24h TTL.
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "korea-stock-insight-mcp"
CORP_CODE_CACHE = CACHE_DIR / "corp_codes.json"
CORP_CODE_TTL_SEC = 24 * 3600

# 분기 코드: DART API 표준
REPRT_CODES = {
    "Q1": "11013",
    "H1": "11012",   # 반기 = 1H 누적
    "Q3": "11014",   # 3Q 누적
    "FY": "11011",   # 사업보고서 = 연간 누적
}


# ─── helpers ────────────────────────────────────────────────────────────
def _require_key() -> Optional[dict]:
    if not DART_API_KEY:
        return {"status": "error", "message": "DART_API_KEY not configured in .env"}
    return None


def _fetch_corp_code_zip() -> list[dict]:
    """Download and parse DART's master corp_code list (one big zip).

    Returns full list of [{corp_code, corp_name, stock_code, modify_date}, ...].
    All listed AND unlisted Korean companies registered with DART.
    """
    r = requests.get(
        f"{DART_BASE}/corpCode.xml",
        params={"crtfc_key": DART_API_KEY},
        timeout=ZIP_TIMEOUT,
    )
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    xml_bytes = z.read(z.namelist()[0])
    root = ET.fromstring(xml_bytes)
    out = []
    for el in root.findall("list"):
        out.append({
            "corp_code": (el.findtext("corp_code") or "").strip(),
            "corp_name": (el.findtext("corp_name") or "").strip(),
            "stock_code": (el.findtext("stock_code") or "").strip(),
            "modify_date": (el.findtext("modify_date") or "").strip(),
        })
    return out


def _load_corp_codes() -> list[dict]:
    """Return cached corp_code list, refreshing if older than 24h."""
    if CORP_CODE_CACHE.exists():
        age = time.time() - CORP_CODE_CACHE.stat().st_mtime
        if age < CORP_CODE_TTL_SEC:
            return json.loads(CORP_CODE_CACHE.read_text())
    # cache miss → fetch + persist
    data = _fetch_corp_code_zip()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CORP_CODE_CACHE.write_text(json.dumps(data, ensure_ascii=False))
    return data


# ─── tools ──────────────────────────────────────────────────────────────
def get_corp_code(query: str) -> dict:
    """Resolve corp_name or stock_code → DART corp_code (8-digit).

    Args:
      query: Korean company name (partial match, e.g. "삼성전자") OR
             6-digit stock code (e.g. "005930").

    Returns:
      {"status":"ok"|"error", "matches":[{corp_code, corp_name, stock_code}, ...]}
      Up to 20 matches returned (most recent first).
    """
    err = _require_key()
    if err:
        return err

    try:
        codes = _load_corp_codes()
    except Exception as e:
        return {"status": "error", "message": f"corp_code list fetch failed: {e}"}

    q = query.strip()
    # stock_code (6-digit): exact match
    if q.isdigit() and len(q) == 6:
        matches = [c for c in codes if c["stock_code"] == q]
    else:
        # corp_name: case-insensitive partial match
        ql = q.lower()
        matches = [c for c in codes if ql in c["corp_name"].lower()]
        # listed first (stock_code 있는 것 우선)
        matches.sort(key=lambda c: (not c["stock_code"], c["corp_name"]))

    return {"status": "ok", "count": len(matches), "matches": matches[:20]}


def get_disclosure_list(stock_code: str, days: int = 30) -> dict:
    """List recent DART disclosures for a Korean-listed company.

    DART = Korea's electronic disclosure system (equivalent to SEC EDGAR),
    operated by the Financial Supervisory Service (FSS).

    Args:
      stock_code: 6-digit Korean ticker (e.g. "005930" for Samsung Electronics).
      days: Lookback window in days (default 30, recommended max 90).

    Returns:
      {"status", "count", "disclosures":[{date, corp_name, title, report_type, rcept_no}, ...]}
      Use `rcept_no` with `get_disclosure` to fetch the full filing.
    """
    err = _require_key()
    if err:
        return err

    end = datetime.now(KST)
    start = end - timedelta(days=days)
    try:
        r = requests.get(
            f"{DART_BASE}/list.json",
            params={
                "crtfc_key": DART_API_KEY,
                "stock_code": stock_code,
                "bgn_de": start.strftime("%Y%m%d"),
                "end_de": end.strftime("%Y%m%d"),
                "page_count": "100",
            },
            timeout=HTTP_TIMEOUT,
        )
        data = r.json()
    except Exception as e:
        return {"status": "error", "message": f"DART list.json request failed: {e}"}

    if data.get("status") == "013":
        return {"status": "ok", "count": 0, "disclosures": []}
    if data.get("status") != "000":
        return {"status": "error", "message": data.get("message", "DART error")}

    disclosures = [
        {
            "date": x.get("rcept_dt"),
            "corp_name": x.get("corp_name"),
            "title": x.get("report_nm"),
            "report_type": x.get("pblntf_ty"),
            "rcept_no": x.get("rcept_no"),
        }
        for x in (data.get("list") or [])
    ]
    return {"status": "ok", "count": len(disclosures), "disclosures": disclosures}


def get_disclosure(rcept_no: str) -> dict:
    """Fetch metadata and viewer URL for a specific DART filing.

    Returns the canonical web URL on dart.fss.or.kr (use a separate fetch
    tool to download the filing body itself; DART filings are zipped XBRL
    and full extraction is on the v0.2 roadmap).

    Args:
      rcept_no: 14-digit receipt number from `get_disclosure_list`.

    Returns:
      {"status", "rcept_no", "url", "viewer_url"}
    """
    if not rcept_no or len(rcept_no) != 14 or not rcept_no.isdigit():
        return {"status": "error", "message": "rcept_no must be 14-digit numeric string"}
    return {
        "status": "ok",
        "rcept_no": rcept_no,
        "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}",
        "viewer_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}",
        "note": "v0.1 returns viewer URL only; full body parsing in v0.2",
    }


def get_financial_statement(corp_code: str, year: int, quarter: str = "FY", fs_div: str = "CFS") -> dict:
    """Fetch full XBRL financial statements for a single company.

    Returns every account line (revenue, operating profit, net income, etc.)
    from the periodic report. Listed companies (KOSPI/KOSDAQ) and major
    unlisted issuers under IFRS are supported.

    Args:
      corp_code: 8-digit DART code (use `get_corp_code` to resolve).
      year: Business year (e.g. 2025).
      quarter: One of "Q1","H1","Q3","FY" (default "FY" = annual report).
      fs_div: "CFS" (consolidated, default) or "OFS" (separate).

    Returns:
      {"status", "count", "accounts":[{account_id, account_nm, thstrm_amount, ...}, ...]}
    """
    err = _require_key()
    if err:
        return err

    reprt_code = REPRT_CODES.get(quarter.upper())
    if not reprt_code:
        return {"status": "error", "message": f"quarter must be one of {list(REPRT_CODES)}"}

    try:
        r = requests.get(
            f"{DART_BASE}/fnlttSinglAcntAll.json",
            params={
                "crtfc_key": DART_API_KEY,
                "corp_code": corp_code,
                "bsns_year": str(year),
                "reprt_code": reprt_code,
                "fs_div": fs_div.upper(),
            },
            timeout=HTTP_TIMEOUT,
        )
        data = r.json()
    except Exception as e:
        return {"status": "error", "message": f"DART fnlttSinglAcntAll failed: {e}"}

    if data.get("status") == "013":
        return {"status": "ok", "count": 0, "accounts": [],
                "note": f"No filing submitted for {year} {quarter} (likely future quarter)"}
    if data.get("status") != "000":
        return {"status": "error", "message": data.get("message", "DART error")}

    rows = data.get("list") or []
    return {"status": "ok", "count": len(rows), "accounts": rows}
