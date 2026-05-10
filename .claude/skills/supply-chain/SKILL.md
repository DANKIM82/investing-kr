---
name: supply-chain
description: 공급망 분석
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 공급망 (supply chain) 구조 분석.

⚠️ **호환성 약함**: Daloopa의 고유 강점인 공급망 데이터는 free 소스에서 매우 제한적. 결과는 본문 추출 + 추정에 의존.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

## 2. 공급망 위치 식별

회사가 공급망에서 어디에 있는가:
- **Upstream**: 원자재, 부품 공급사
- **Midstream**: 제조, 조립
- **Downstream**: 유통, 소매
- **Vertically integrated**: 수직 통합

예시:
- 삼성전자: 반도체 (downstream으로 폰/가전), 부품 자체 생산
- TSMC: pure-play foundry (midstream)
- Apple: design + assembly outsourcing

## 3. 주요 공급사 / 고객사

`documents`로 사업보고서에서 추출:
```bash
python infra/free_data_kr.py documents "supplier customer concentration" --tickers $ARGUMENTS
```

10-K의 "Risk Factors" 또는 한국 사업보고서의 "주요 거래처" 섹션 활용.

| 관계 | 회사명 | 비중 (%) | 의존도 |
|---|---|---|---|
| 주요 공급사 1 | | | |
| 주요 공급사 2 | | | |
| 주요 고객사 1 | | | |
| 주요 고객사 2 | | | |

## 4. 집중도 리스크

- 상위 5개 공급사 의존도
- 상위 5개 고객사 매출 비중
- 단일 점포 (single point of failure) 식별

## 5. 지역적 집중도

`documents`로 지역별 매출/생산 정보:
- 생산 거점 지역
- 매출 지역 분포
- 정치적 리스크 (예: 중국 비중)

## 6. 재고 회전 추이 (공급망 stress 지표)

```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods Q-7,...,Q+0 \
  --series revenue,inventory
```

DIO 추이로 공급망 건강도 추정.

## 7. 최근 공급망 이슈

`documents`로 최근 공시:
- "shortage", "delay", "constraint" 키워드 검색
- 회사 측 공급망 관련 코멘트

## 8. 경쟁사와 비교

같은 산업 peer와:
- 공급망 다양성
- 지역 집중도
- 재고 회전

## 9. HTML 보고서 저장

`reports/{TICKER}_supply_chain.html`

⚠️ 본 보고서 한계 명시: "Free 데이터의 한계로 정성적 분석이 큼. 정확한 supplier/customer 데이터는 별도 검증 필요."
