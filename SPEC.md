# Korea Stock Insight MCP — MVP 스펙 (v0.1)

> 한국 주식 분석용 MCP 서버. 무료 tier(stdio, 자체 키) + 유료 tier(SSE, 가공된 인사이트) 하이브리드.
> 작성: 2026-05-16

---

## 1. 기본 정보

| 항목 | 값 |
|---|---|
| 프로젝트명 | `korea-stock-insight-mcp` |
| 운영 위치 | dev 서버 `/root/projects/cc/korea-stock-insight-mcp/` |
| SSE 도메인 | `mcp.ywhan.com` (신규 발급 예정) |
| 라이선스 | MIT (무료 tier), 비공개 (유료 tier 서버 코드) |
| 첫 릴리즈 목표 | 무료 tier W2 / 유료 tier W4 |
| 시장 포지셔닝 | jjlabsio(무료 단순래퍼) ↔ dartpoint(B2B 영업) 사이의 **개인 구독 빈자리** |

---

## 2. 기술 스택

| 항목 | 결정 | 이유 |
|---|---|---|
| 언어 | Python 3.12 | invest_shorts/autobot/rokit 모두 Python, dev 환경 풍부 |
| MCP SDK | `mcp` (공식 Python) | Anthropic 공식 |
| 패키지 매니저 | `uv` | MCP 생태계 표준 (uvx 1-line 실행) |
| 영문 요약 | `anthropic` SDK + Claude Haiku 4.5 | 빠르고 저렴 ($/요청 ≪) |
| DART 호출 | rokit-dashboard 코드 재활용 |  |
| HTTP 서버 (SSE) | `starlette` + `uvicorn` | MCP SDK 공식 패턴 |
| 결제 | Stripe Subscription | 표준 |

---

## 3. 하이브리드 호스팅 모델

```
무료 tier (stdio, 사용자 PC)
  uvx korea-stock-insight-mcp
  사용자 자기 DART/KRX API 키 → 자기 PC에서 실행
  비용 0원, 수익 0원 (사용자 모집·노출용)

유료 tier (SSE, mcp.ywhan.com)
  Claude Desktop에 URL+토큰만 등록
  우리 키 + 우리 가공 (Claude 요약·sentiment·webhook push)
  비용: 서버 + Claude API + DART/KRX 키 (월 ~$10.56)
  수익: $19/월 × 사용자 수 (마진 ~$8.44/명, 44%)
```

---

## 4. 도구 목록

### 무료 tier (stdio, W2 출시)

| # | 도구 | 입력 | 출력 |
|---|---|---|---|
| 1 | `get_corp_code` | 회사명 OR 종목코드 | 종목코드·회사명·시장구분 |
| 2 | `get_disclosure_list` | corp_code, 기간 | 공시 목록 (날짜·제목·rcept_no) |
| 3 | `get_disclosure` | rcept_no | 공시 본문 (큰 건 TOC 반환) |
| 4 | `get_financial_statement` | corp_code, 년도, 분기 | XBRL 재무제표 |
| 5 | `get_stock_quote` | 종목코드, 기간 | 일별 OHLCV |

**차별점 vs jjlabsio**:
- tool description **영문 first** (영문권 사용자 LLM이 더 잘 활용)
- 같은 데이터지만 영문 분석가에게 친화적

### 유료 tier (SSE, W4 출시)

| # | 도구 | 가치 |
|---|---|---|
| 6 | `summarize_disclosure_en` | 공시 → 영문 3줄 요약 + 핵심 키워드 |
| 7 | `score_disclosure_impact` | 영향도 점수 -5~+5 (Claude 분류) |
| 8 | `get_news_sentiment` | 종목 최근 뉴스 sentiment (영문) |
| 9 | `subscribe_company_webhook` | 새 공시 발생 시 webhook push |
| 10 | `get_company_thesis` | thesis 자동생성 (pltr-dashboard 패턴 적용) |

---

## 5. 가격

| Tier | 가격 | 한도 | 타깃 |
|---|---|---|---|
| Free | $0 | stdio, 사용자 자체 키 | 개인 개발자·테스터 |
| **Pro** | **$19/월** | SSE, 5,000 calls/월 | 개인 투자자·analyst |
| Business | $49/월 | SSE, 50,000 calls/월 + webhook | 소형 펀드·핀테크 |

**Pro tier 비용 구조 (5,000 calls/월 기준)**

| 항목 | 월 비용 |
|---|---|
| Claude Haiku 4.5 (영문 요약 5,000건) | ~$10 |
| DART API / KRX API | 무료 |
| dev 서버 (기존 운영 중) | $0 추가 |
| Stripe 수수료 (2.9% + $0.30) | $0.56 |
| **합계** | **~$10.56** |

**수익 계산 (Pro 기준)**
- 가격: $19/월, 마진: $8.44/명 (44%)
- 월 20만원(≈$150) 목표 = **약 9명** 유료 사용자 필요
- MCPize 수수료 15% 가정 → 실수령 $16.15 → **약 10명** 필요
- 가격 anchoring: ChatGPT Plus($20)·Claude Pro($20) 동급

---

## 6. 배포 채널

| 채널 | 비용 | 역할 |
|---|---|---|
| PyPI (`uvx`) | 무료 | 1-line 설치 |
| Anthropic 공식 디렉토리 (server.json) | 무료 | Claude Desktop 검색 |
| Smithery (등록만) | 등록 무료 | 노출 |
| MCP Marketplace | Stripe 직결 | 결제 |
| **MCPize** | 15% 수수료 (85% 본인) | 결제 + 노출 |
| 자체 사이트 `mcp.ywhan.com` | 자체 호스팅 | 직거래·브랜딩 |

**1차 전략**: PyPI + Anthropic 공식 디렉토리 + Smithery 등록 (모두 무료) → 무료 사용자 모은 뒤 유료 tier 출시할 때 MCPize 결합.

---

## 7. 4주 일정

| 주차 | 작업 | 산출물 |
|---|---|---|
| **W1** | Hello world MCP 서버 + DART 1개 tool | dev에서 `uv run` 동작 확인 |
| **W2** | 5개 무료 tool 완성 + PyPI 배포 + Anthropic 디렉토리 등록 | v0.1.0 릴리즈, 첫 GitHub stars |
| **W3** | SSE 서버 + Stripe 결제 + Claude 영문 요약 도구 | mcp.ywhan.com 동작 |
| **W4** | webhook + thesis 도구 + 결제 페이지 + 런칭 | v1.0.0, 첫 유료 사용자 |

---

## 8. 성공 지표

| 지표 | 1개월 | 3개월 | 6개월 |
|---|---|---|---|
| GitHub stars | 50 | 200 | 500 |
| 무료 stdio 사용자 | 30 | 150 | 400 |
| **유료 가입자** | **3** | **10** | **25** |
| **MRR** | **$57** | **$190** | **$475** |
| 월 20만원(≈$150) 달성 | ❌ | ✅ (10명) | ✅ |

**3개월 후 평가**:
- MRR < $100 (5명 미만) → 접고 다른 방향
- MRR $100~$300 (5~15명) → 마케팅 강화
- MRR > $300 → 도구 확장 + Business tier 영업

---

## 9. 경쟁 분석 요약

| | 우리 | jjlabsio | dartpoint |
|---|---|---|---|
| 가격 | $19/월 (개인) | 무료 | 견적 (대기업) |
| 타깃 | 영문권 개인 투자자 | DIY 개발자 | 한국 기관 |
| 호스팅 | stdio + SSE | stdio | SSE |
| 데이터 가공 | 영문 요약·sentiment·push | 원본 그대로 | 한국어 분석 |
| 차별점 | 합리적 가격 + LLM 친화 가공 | 무료, 단순 래퍼 | B2B 영업, 대화형 분석 |

---

## 10. 다음 액션

1. **W1 시작**: Hello world MCP 서버 (Python SDK)
2. DART/KRX API 키 신청 (이미 rokit-dashboard에서 사용 중이면 재활용)
3. GitHub repo 생성 (`yjhann33-design/korea-stock-insight-mcp`)
4. PyPI 계정 확인
5. mcp.ywhan.com Cloudflare DNS 준비 (W3 직전)
