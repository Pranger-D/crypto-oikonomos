# Automation Scripts

이 폴더는 Crypto Oikonomos 블로그의 데이터 자동화 스크립트를 포함합니다.

## 🚀 현재 사용 중인 스크립트

### 일일 자동화
- **`fetch_market_data.py`** - GitHub Actions로 매일 자동 실행
  - CoinGecko API로 BTC 가격, BTC 시가총액, 글로벌 시가총액 수집
  - Investing.com에서 거시경제 지표 수집
  - `dashboard-data.json` 업데이트
  - 실행: `python fetch_market_data.py`

### 유틸리티 스크립트
- **`collect_macro_history.py`** - 과거 1개월 거시지표 재수집
  - 데이터 손실 시 복구용
  - 실행: `python collect_macro_history.py`

- **`fix_nan_values.py`** - JSON 파일의 NaN 값을 null로 변환
  - JavaScript 호환성 보장
  - 실행: `python fix_nan_values.py`

- **`fix_macro_dates.py`** - 거시지표 날짜 형식 변환
  - DD/MM/YYYY → YYYY-MM-DD
  - 실행: `python fix_macro_dates.py`

- **`auto_translate_indicators.py`** - 거시지표 자동 번역 (미사용)
  - Gemini API로 새 지표 번역 시도
  - 현재는 수동 번역 파일 사용 (`indicator_translations.json`)

- **`list_indicators.py`** - 데이터에 포함된 모든 지표 목록 출력
  - 디버깅 및 확인용
  - 실행: `python list_indicators.py`

## 📦 데이터 파일
- **`indicator_translations.json`** - 거시지표 한글 번역 매핑
  - 새 지표 추가 시 여기에 번역 추가
  - TypeScript 파일 자동 생성: `components/Dashboard/indicatorTranslations.ts`

## 📂 Archive 폴더
과거에 사용했던 일회성 스크립트들이 보관되어 있습니다.
- 데이터 마이그레이션 완료
- 참고 및 복구용으로 보관

## 🔧 환경 설정
`.env` 파일에 다음 API 키 필요:
```
COINGECKO_API_KEY=your_api_key_here
GOOGLE_API_KEY=your_api_key_here  # 번역 기능 사용 시
```

## 📊 GitHub Actions
`.github/workflows/update-market-data.yml`에서 매일 UTC 15:00 (KST 자정)에 자동 실행됩니다.
