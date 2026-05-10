# 디자인 시스템 (Design System)

모든 분석 결과물의 숫자 포맷, 표 구조, 분석 톤을 통일하는 가이드입니다.

---

## 숫자 포맷 (한영 혼용)

### 통화 표시 (시장별)

| 시장 | 큰 단위 | 중간 단위 | 작은 단위 | EPS |
|---|---|---|---|---|
| 한국 (KRW) | `2.5조원 (₩2.5tn)` | `2,345억원 (₩234bn)` | `12억원 (₩1.2bn)` | `1,250원 (₩1,250)` |
| 미국 (USD) | `$95.4bn` | `$2,345mm` | `$6.08` | `$1.85` |
| 일본 (JPY) | `2.5兆円 (¥2.5tn)` | `2,345億円 (¥234bn)` | `12億円 (¥1.2bn)` | `¥250` |

원칙:
- **한국 단위 + 영문 단위 병기**: `5조원 (₩5tn)` 처럼 둘 다 표시
- **숫자는 천 단위 콤마**: `2,345억원`
- **소수점 한 자리**: `2.5조원`, `42.3%`
- **음수는 괄호 또는 마이너스**: `(2.5조원)` 또는 `-2.5조원`

### 비율/배수

| 종류 | 형식 | 예시 |
|---|---|---|
| 백분율 | 소수점 한 자리 + `%` | `42.3%` |
| 멀티플 | 소수점 한 자리 + `x` | `8.5x EV/EBITDA`, `15.2x P/E` |
| 성장률 | 부호 + `%` + 맥락 | `+12.3% YoY`, `-3.5% QoQ` |
| Basis points | 부호 + `bps` | `+150bps`, `-25bps` |

### 주식 수

| 시장 | 형식 | 예시 |
|---|---|---|
| 한국 | `X.XX억주` | `1.5억주` |
| 미국 | `X.XXbn shares` 또는 `X,XXXmm shares` | `15.33bn shares` |
| 일본 | `X.XX億株` | `3.2億株` |

### 컴퓨팅 메트릭 표기

직접 계산한 값은 `(계산)` 또는 `(calc.)` 표시:
- `EBITDA (계산): 1.5조원`
- `FCF (calc.): $5.2bn`

---

## 표 구조

### 기본 원칙

- **열(컬럼) = 시간 기간** (왼쪽에서 오른쪽으로 시간순)
- **행(로우) = 메트릭** (카테고리별로 그룹화: 손익, 마진, 주당, 재무상태)
- **YoY/QoQ 성장률은 sub-row로 이탤릭 표시**
- **Beat/miss는 강조**: `1,520원 (+3.2% beat)`
- **표 하단에 출처 명시**

### 한국 시장 표 예시

```html
<table>
<thead>
<tr>
  <th>지표</th>
  <th>2024Q1</th>
  <th>2024Q2</th>
  <th>2024Q3</th>
  <th>2024Q4</th>
</tr>
</thead>
<tbody>
<tr>
  <td>매출액 (Revenue)</td>
  <td>23.5조원 (₩23.5tn)</td>
  <td>25.0조원 (₩25.0tn)</td>
  <td>27.3조원 (₩27.3tn)</td>
  <td>30.1조원 (₩30.1tn)</td>
</tr>
<tr><td><i>YoY 성장률</i></td><td><i>+5.2%</i></td><td><i>+8.3%</i></td><td><i>+12.1%</i></td><td><i>+15.4%</i></td></tr>
<tr>
  <td>영업이익 (Operating Income)</td>
  <td>2.5조원</td>
  <td>3.1조원</td>
  <td>3.8조원</td>
  <td>4.5조원</td>
</tr>
<tr>
  <td>영업이익률 (Op. Margin)</td>
  <td>10.6%</td>
  <td>12.4%</td>
  <td>13.9%</td>
  <td>15.0%</td>
</tr>
</tbody>
<tfoot>
<tr><td colspan="5"><small>출처: DART (감사보고서)</small></td></tr>
</tfoot>
</table>
```

### 다국가 비교 표

회계연도 종료가 다른 회사를 비교할 때는 calendar quarter로 정규화:

| 지표 | 삼성전자 (2025Q3) | TSMC (2025Q3) | Apple (2025Q3) |
|---|---|---|---|
| 매출 | 79조원 (₩79tn) | NT$760bn (~$23.5bn) | $94.9bn |
| OPM | 9.2% | 47.5% | 31.0% |

---

## 분석 깊이 (3-Layer Analytical Density)

각 핵심 데이터 포인트는 **3개 레이어**로 분석:

1. **데이터 포인트** (What): 숫자 자체
2. **맥락** (So What): YoY/QoQ 변화, 가이던스 대비, peer 대비
3. **시사점** (Now What): 무엇을 의미하는가, 다음에 봐야 할 것

### 좋은 예시

> 삼성전자 2024Q4 매출액 [30.1조원 (₩30.1tn)](URL) — 전년동기대비 +15.4% 성장 (전분기 +12.1% 대비 가속). DRAM ASP 상승과 HBM 수요 호조가 견인. 2025년 가이던스 +20% YoY를 감안하면 1분기에도 두 자릿수 성장 지속 예상. **Watch**: HBM3E 수율 (현재 85% → 2025Q1 90% 목표).

### 나쁜 예시 (피할 것)

> 삼성전자 2024Q4 매출액 30.1조원이었습니다. (← 데이터만, 맥락도 시사점도 없음)

---

## HTML 리포트 템플릿

Building block skills이 직접 생성하는 HTML 결과물 표준 템플릿:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{TICKER} {Company Name} — {Skill Name}</title>
<style>
  body { font-family: 'Noto Sans KR', 'Pretendard', -apple-system, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1a1a1a; }
  h1 { font-size: 28px; border-bottom: 2px solid #1a1a1a; padding-bottom: 10px; }
  h2 { font-size: 20px; margin-top: 32px; color: #1a1a1a; }
  h3 { font-size: 16px; color: #444; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }
  th, td { padding: 8px 12px; text-align: right; border-bottom: 1px solid #e0e0e0; }
  th { background: #f5f5f5; font-weight: 600; text-align: center; }
  td:first-child, th:first-child { text-align: left; }
  tr i { color: #888; font-style: italic; font-size: 12px; }
  a { color: #0066cc; text-decoration: none; border-bottom: 1px dotted #0066cc; }
  a:hover { color: #003d7a; }
  .footer { margin-top: 60px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #666; }
  .firm { font-weight: 600; }
  blockquote { border-left: 3px solid #ccc; padding-left: 16px; margin: 16px 0; color: #555; }
  .bull { color: #28a745; }
  .bear { color: #dc3545; }
  .highlight { background: #fff3cd; padding: 1px 4px; border-radius: 3px; }
</style>
</head>
<body>
  <h1>{Company Name} ({TICKER}) — {Skill Name}</h1>
  <p>Generated: {date}</p>
  
  <!-- 본문 -->
  
  <div class="footer">
    <p class="firm">Prepared by {FIRM_NAME}</p>
    <p>Data sources: DART (KR) / yfinance + SEC EDGAR (US) / yfinance (JP)</p>
    <p>Disclaimer: This report is for educational purposes only. Not investment advice.</p>
  </div>
</body>
</html>
```

---

## 분석 톤 가이드

### 권장 표현 (한국어)

- "추세적 가속화/감속" 대신 → "추세 가속" / "추세 둔화"
- "상회/하회" 적극 사용
- "시장 컨센서스 대비" 명확히
- "본 분석은 ~을 가정함"으로 가정 명시
- 강세/약세는 `bull` / `bear` CSS 클래스 활용

### 피할 표현

- 추측성 미래 단언: "주가는 오를 것이다" (X) → "현재 멀티플 대비 ~배 upside 가능" (O)
- 감정적 표현: "끔찍한 실적" (X) → "예상 대비 큰 폭 미달" (O)
- 절대적 표현: "확실히", "반드시" 사용 자제

### 객관성 원칙

- 데이터 인용 없이 주장하지 않기
- 회사 측 발언과 분석가 의견 구분
- 가이던스 vs 컨센서스 vs 실적 명확히 구분

---

## 회사명 / 티커 표기 규칙

처음 등장 시: `삼성전자 (005930.KS)` / `Apple Inc. (AAPL)` / `Toyota Motor (7203.T)`

이후: 한국은 회사명, 미국/일본은 티커 위주

---

## 색상 팔레트

| 용도 | HEX | 사용처 |
|---|---|---|
| 메인 텍스트 | `#1a1a1a` | 본문 |
| 보조 텍스트 | `#666` | 푸터, 캡션 |
| 링크 | `#0066cc` | 인용 링크 |
| 강조 | `#fff3cd` (배경) | highlight |
| Bull (긍정) | `#28a745` | 긍정 시그널 |
| Bear (부정) | `#dc3545` | 부정 시그널 |
| 표 헤더 | `#f5f5f5` (배경) | 표 헤더 |
