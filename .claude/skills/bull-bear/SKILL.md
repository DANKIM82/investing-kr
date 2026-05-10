---
name: bull-bear
description: 강세/약세/기본 시나리오 프레임워크
argument-hint: TICKER
---

`$ARGUMENTS` 회사에 대해 Bull / Base / Bear 3가지 시나리오 분석을 수행하세요.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 + 시장 데이터

```bash
python infra/free_data_kr.py companies $ARGUMENTS
python infra/market_data.py quote $ARGUMENTS
```

## 2. 핵심 thesis 변수 식별

이 회사의 가치를 결정하는 3-5개 핵심 변수:
- 매출 성장률 (3-5년 CAGR)
- 영업이익률
- TAM (시장 규모)
- 시장 점유율
- 경쟁 강도

회사별로 다름. 예시:
- **반도체**: AI/HBM 수요, ASP 추이, 가동률
- **자동차**: EV 전환 속도, 평균 판매가, 지역별 성장
- **플랫폼**: ARPU, 광고 단가, 사용자 성장

## 3. 시나리오 정의

각 시나리오마다 핵심 변수의 값 정의:

| 변수 | Bull | Base | Bear |
|---|---|---|---|
| 매출 CAGR (5Y) | | | |
| 영업이익률 (5Y avg) | | | |
| Terminal multiple | | | |
| 시장 점유율 | | | |

각 가정의 근거 + 발생 확률 (주관적 추정 30/50/20 등).

## 4. 시나리오별 주당 가치

각 시나리오에 대해:
- 5년 후 매출, 영업이익 추정
- 적용 멀티플 → Enterprise Value
- (-) 순부채, ÷ 발행주식수 = 주당가치

또는 DCF 방식 (`/dcf` skill 결과 활용).

## 5. 확률가중 적정가

`Probability-Weighted Fair Value = Σ (Probability × Value per scenario)`

현재 주가 vs 가중 적정가:
- Upside/downside %
- 시나리오별 max/min 범위

## 6. Catalysts (촉매제)

- **Bull catalyst**: 어떤 이벤트가 Bull 시나리오로 끌고 가는가? (3-5개)
- **Bear catalyst**: 어떤 이벤트가 Bear 시나리오로 끌고 가는가? (3-5개)
- 각 catalyst의 시점 (분기 단위)

## 7. Probability Tree 시각화

`infra/chart_generator.py scenario-bar` 활용해서 3 시나리오 시각화.

## 8. HTML 보고서 저장

`reports/{TICKER}_bull_bear.html`

구조:
1. 요약 (3개 시나리오 헤드라인)
2. 핵심 변수 표
3. 각 시나리오 상세 (가정, 계산, 결과)
4. 확률가중 적정가
5. Catalysts (Bull/Bear)
6. 시각화
7. 결론 + 모니터링 항목
