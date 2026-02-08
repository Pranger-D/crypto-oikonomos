# 수동 JSON 편집 가이드

## 📋 개요

`data/dashboard-data.json` 파일은 대시보드의 모든 데이터를 담고 있습니다. API 호출 실패나 데이터 누락 시 수동으로 편집할 수 있습니다.

## 📂 파일 구조

```json
{
  "lastUpdated": "2026-02-08T00:00:00Z",
  "metadata": { ... },
  "priceData": [ ... ],
  "macroIndicators": { ... },
  "blogPosts": { ... }
}
```

## ✏️ 수동 편집 방법

### 1. 가격 데이터 추가/수정

`priceData` 배열에 새 항목 추가:

```json
{
  "date": "2026-02-09",
  "btc": 46500.00,
  "total2": 860000000000
}
```

**주의사항:**
- `date`는 `YYYY-MM-DD` 형식
- `btc`는 소수점 2자리까지
- `total2`는 정수 (달러 단위)
- 날짜순으로 정렬 유지

### 2. 거시지표 추가/수정

`macroIndicators` 객체에 날짜별로 추가:

```json
"2026-02-09": [
  {
    "country": "United States",
    "indicator": "CPI m/m",
    "importance": "high",
    "actual": 0.3,
    "forecast": 0.2,
    "previous": 0.1
  }
]
```

**주의사항:**
- 같은 날짜에 여러 지표 가능 (배열)
- `country`는 "United States" 또는 "China"
- `importance`는 "high"만 사용
- 미국 지표를 먼저 배치

### 3. 블로그 글 추가/수정

`blogPosts` 객체에 날짜별로 추가:

```json
"2026-02-09": [
  {
    "slug": "2026-02-09-briefing",
    "title": "시장 브리핑: 오늘의 크립토 인사이트",
    "category": "Briefing"
  }
]
```

**주의사항:**
- `slug`는 실제 MDX 파일명과 일치해야 함
- `category`는 "Briefing", "Insight", "Study" 중 하나

## 🔍 유효성 검사

편집 후 JSON 문법 오류 확인:

```bash
python -c "import json; json.load(open('data/dashboard-data.json'))"
```

오류가 없으면 아무 출력 없이 종료됩니다.

## ⚠️ 백업

편집 전 항상 백업:

```bash
copy data\dashboard-data.json data\dashboard-data.backup.json
```

## 🔄 자동 업데이트 재실행

수동 편집 후 자동 업데이트 스크립트 실행:

```bash
.\automation\venv\Scripts\python.exe .\automation\fetch_market_data.py
```

## 📞 문제 해결

- **JSON 문법 오류**: [JSONLint](https://jsonlint.com/)에서 검증
- **데이터 누락**: 해당 날짜 항목이 `null`이 아닌지 확인
- **차트 표시 안 됨**: 브라우저 콘솔에서 에러 확인

---

**마지막 업데이트**: 2026-02-08
