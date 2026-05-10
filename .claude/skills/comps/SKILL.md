---
name: comps
description: Trading multiples 동종업계 비교
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 trading multiples를 동종업계 peer와 비교 분석.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보 + Peer 식별

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

`industry`, `sector` 캡처. 같은 산업의 peer 5-10개 식별.

한국 시장 peer 예시:
- **반도체**: 005930 (삼성전자), 000660 (SK하이닉스), 042700 (한미반도체)
- **이차전지**: 373220 (LG에너지솔루션), 006400 (삼성SDI), 247540 (에코프로비엠)
- **자동차**: 005380 (현대차), 000270 (기아), 012330 (현대모비스)
- **인터넷**: 035420 (NAVER), 035720 (카카오)

미국 시장:
- **반도체**: NVDA, AMD, INTC, MU, AVGO, TSM
- **빅테크**: AAPL, MSFT, GOOG, META, AMZN
- **클라우드**: CRM, NOW, DDOG, NET, ZS

일본 시장:
- **자동차**: 7203.T (Toyota), 7267.T (Honda), 7201.T (Nissan)
- **반도체**: 8035.T (Tokyo Electron), 6857.T (Advantest)

## 2. Multiples 데이터 수집

각 peer에 대해:
```bash
python infra/market_data.py multiples TICKER
```

수집할 multiples:
- P/E (TTM, NTM)
- EV/EBITDA (TTM, NTM)
- P/S (TTM)
- P/B
- Dividend yield
- PEG ratio

## 3. 비교 표 구성

| 회사 | 시가총액 | P/E (TTM) | P/E (NTM) | EV/EBITDA | P/S | P/B | DivYield |
|---|---|---|---|---|---|---|---|
| {Target} | | | | | | | |
| Peer 1 | | | | | | | |
| ... | | | | | | | |
| **Peer Median** | | | | | | | |
| **Peer Mean** | | | | | | | |

## 4. 비교 분석

- Target이 peer median 대비 프리미엄/디스카운트?
- 어떤 multiple에서 가장 차이?
- 그 차이가 정당한가? (성장률, 마진, ROE 차이로 설명되나?)

## 5. Quality 정량 비교

같은 peer 그룹에 대해:
| 회사 | 매출성장률 (TTM) | 영업이익률 | ROE | Net Cash Position |

Quality와 valuation 매트릭스에서 target의 위치 평가.

## 6. Implied Valuation

Peer median × target 메트릭 = implied 가치:
- Peer median P/E × target NTM EPS = implied 주가
- Peer median EV/EBITDA × target NTM EBITDA = implied EV

## 7. 한계점 명시

⚠️ **Free 데이터의 한계**: 
- 컨센서스 NTM 추정치는 yfinance에서 일부만 제공
- 정확한 forward multiples는 Bloomberg/Refinitiv 수준 데이터 필요
- Peer 선정의 주관성

## 8. HTML 보고서 저장

`reports/{TICKER}_comps.html`

구조: 비교 표 + 산점도 (성장률 vs P/E 등) + implied valuation + 결론.
