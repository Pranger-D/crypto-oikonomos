# Archive - 과거 스크립트

이 폴더는 과거에 사용했던 일회성 데이터 마이그레이션 및 테스트 스크립트를 보관합니다.

## 📜 보관된 스크립트

### 데이터 마이그레이션 (완료)
- **`update_all_historical_data.py`** - 2013년부터 전체 데이터 업데이트
  - BTC 가격/시가총액 CSV 파싱
  - 글로벌 시가총액 CSV 파싱
  - 도미넌스 계산 및 병합
  - ✅ 완료: 4,668일 데이터 업데이트

- **`update_btc_marketcap.py`** - BTC 시가총액 데이터 업데이트
  - CSV에서 정확한 시가총액 추출
  - ✅ 완료: 마이그레이션 완료

### API 마이그레이션 테스트
- **`calculate_dominance_coingecko.py`** - CoinGecko API 테스트
  - 도미넌스 계산 로직 검증
  - ✅ 완료: 프로덕션 적용

- **`migrate_to_coingecko.py`** - CryptoCompare → CoinGecko 마이그레이션
  - API 전환 테스트
  - ✅ 완료: 마이그레이션 완료

- **`accumulate_global_cap.py`** - 글로벌 시가총액 일일 수집 시스템
  - 초기 접근 방식 테스트
  - ✅ 완료: CSV 데이터로 대체

### 데이터 소스 테스트
- **`scrape_cmc_dominance.py`** - CoinMarketCap 스크래핑 시도
  - 동적 로딩으로 실패
  - ❌ 미사용: CoinGecko API 사용

- **`test_yfinance_total.py`** - Yahoo Finance 티커 테스트
  - 총 암호화폐 시가총액 티커 탐색
  - ❌ 실패: 유효한 티커 없음

- **`test_investpy_calls.py`** - investpy API 동작 분석
  - 1개월 데이터 수집 방식 확인
  - ✅ 완료: 프로덕션 적용

## 💡 사용 목적
- **참고 자료**: 과거 로직 확인
- **복구**: 데이터 손실 시 재수집
- **학습**: 마이그레이션 과정 이해

## ⚠️ 주의사항
이 스크립트들은 더 이상 일상적으로 사용되지 않습니다.
현재 사용 중인 스크립트는 상위 폴더의 `README.md`를 참고하세요.
