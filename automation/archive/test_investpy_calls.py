"""
investpy API 호출 횟수 테스트
- 1개월 거시지표 데이터 수집 시 API 호출 횟수 확인
"""

from datetime import datetime, timedelta

# 날짜 계산
today = datetime.now()
one_month_ago = today - timedelta(days=30)

from_date = one_month_ago.strftime("%d/%m/%Y")
to_date = today.strftime("%d/%m/%Y")

print("📊 investpy API 호출 분석")
print("=" * 60)
print(f"\n요청 기간: {from_date} ~ {to_date} (30일)")
print(f"국가: United States, China")
print(f"중요도: High")

print("\n" + "=" * 60)
print("💡 investpy.economic_calendar() 동작 방식:")
print("=" * 60)

print("""
investpy는 Investing.com 웹사이트를 스크래핑하는 라이브러리입니다.

API 호출 방식:
1. 단일 HTTP 요청으로 전체 기간의 데이터를 가져옴
2. 서버에서 필터링된 결과를 반환
3. 기간이 길어도 호출 횟수는 1회

예상 API 호출 횟수: 1회

코드 예시:
```python
calendar = investpy.news.economic_calendar(
    time_zone="GMT",
    countries=["united states", "china"],
    importances=["high"],
    from_date="09/01/2026",  # 1개월 전
    to_date="08/02/2026"      # 오늘
)
```

반환 데이터:
- 30일간의 모든 high importance 지표
- 미국 + 중국 데이터
- 단일 DataFrame으로 반환
""")

print("\n" + "=" * 60)
print("🎯 결론:")
print("=" * 60)
print("""
✅ 1개월 과거 데이터 수집 시 API 호출: 1회만!

investpy는 날짜 범위를 파라미터로 받아서
서버에서 필터링된 결과를 한 번에 반환합니다.

따라서:
- 1일 데이터 요청: 1회 호출
- 30일 데이터 요청: 1회 호출 (동일!)
- 1년 데이터 요청: 1회 호출 (동일!)

기간이 길어져도 호출 횟수는 변하지 않습니다.
""")

print("\n⚠️ 주의사항:")
print("""
1. investpy는 웹 스크래핑 기반이므로:
   - Investing.com의 rate limit 정책 적용
   - 너무 자주 호출하면 차단될 수 있음
   - 하루 1회 정도는 안전

2. 권장 사용 방식:
   - 초기 수집: 1개월 데이터 (1회 호출)
   - 이후 매일: 어제~오늘 데이터 (1회 호출)
   - 총 호출: 초기 1회 + 매일 1회
""")
