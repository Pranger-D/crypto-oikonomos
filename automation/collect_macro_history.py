"""
과거 1개월 거시지표 데이터 수집
- Investing.com에서 미국 + 중국 High importance 지표
- API 호출: 1회만
- dashboard-data.json에 추가
"""

import os
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

# 날짜 계산
today = datetime.now()
one_month_ago = today - timedelta(days=30)

from_date = one_month_ago.strftime("%d/%m/%Y")
to_date = today.strftime("%d/%m/%Y")

# NaN을 None으로 변환하는 헬퍼 함수
def safe_value(val):
    """NaN을 None으로 변환 (JSON 호환성)"""
    if isinstance(val, float) and math.isnan(val):
        return None
    return val

print("📊 과거 1개월 거시지표 데이터 수집")
print("=" * 60)
print(f"\n기간: {from_date} ~ {to_date} (30일)")
print(f"국가: United States, China")
print(f"중요도: High")

# 기존 데이터 로드
print(f"\n📂 dashboard-data.json 로드 중...")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"✅ 기존 거시지표 데이터: {len(data['macroIndicators'])}일")

# investpy로 데이터 수집
print(f"\n🔄 Investing.com에서 데이터 수집 중...")

try:
    import investpy
    
    # 1개월 데이터 수집 (API 호출 1회)
    calendar = investpy.news.economic_calendar(
        time_zone="GMT",
        countries=["united states", "china"],
        importances=["high"],
        from_date=from_date,
        to_date=to_date
    )
    
    if not calendar.empty:
        print(f"✅ 수집 완료: {len(calendar)}개 지표")
        
        # 날짜별로 그룹화
        added_count = 0
        updated_count = 0
        
        for _, row in calendar.iterrows():
            # investpy는 DD/MM/YYYY 형식 반환 → YYYY-MM-DD로 변환
            raw_date = row['date']
            try:
                date_obj = datetime.strptime(raw_date, "%d/%m/%Y")
                date_str = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                # 이미 YYYY-MM-DD 형식이면 그대로 사용
                date_str = raw_date
            
            # 해당 날짜 데이터 초기화
            if date_str not in data['macroIndicators']:
                data['macroIndicators'][date_str] = []
            
            indicator = {
                "country": row['zone'],
                "indicator": row['event'],
                "importance": row['importance'],
                "actual": safe_value(row.get('actual', None)),
                "forecast": safe_value(row.get('forecast', None)),
                "previous": safe_value(row.get('previous', None))
            }
            
            # 중복 체크
            existing = [i for i in data['macroIndicators'][date_str] 
                       if i['indicator'] == indicator['indicator']]
            
            if not existing:
                data['macroIndicators'][date_str].append(indicator)
                added_count += 1
            else:
                updated_count += 1
        
        # 미국 우선 정렬
        for date_str in data['macroIndicators']:
            data['macroIndicators'][date_str] = sorted(
                data['macroIndicators'][date_str],
                key=lambda x: (x['country'] != 'United States', x['indicator'])
            )
        
        print(f"\n✅ 데이터 처리 완료:")
        print(f"   - 새로 추가: {added_count}개")
        print(f"   - 중복 건너뜀: {updated_count}개")
        print(f"   - 총 날짜: {len(data['macroIndicators'])}일")
        
        # 샘플 출력 (최근 3일)
        print(f"\n📊 샘플 데이터 (최근 3일):")
        recent_dates = sorted(data['macroIndicators'].keys(), reverse=True)[:3]
        for date_str in recent_dates:
            indicators = data['macroIndicators'][date_str]
            print(f"\n   {date_str}: {len(indicators)}개 지표")
            for ind in indicators[:2]:  # 각 날짜당 2개만 출력
                print(f"      - [{ind['country']}] {ind['indicator']}")
        
    else:
        print("⚠️ 데이터가 없습니다.")
        
except ImportError:
    print("❌ investpy 미설치")
    print("   설치: pip install investpy")
    exit(1)
except Exception as e:
    print(f"❌ 데이터 수집 실패: {e}")
    exit(1)

# 파일 저장
print(f"\n💾 파일 저장 중...")

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

file_size = DATA_FILE.stat().st_size / 1024
print(f"✅ 파일 저장 완료: {file_size:.1f} KB")

print(f"\n🎉 과거 1개월 거시지표 데이터 수집 완료!")
print(f"\n📊 최종 통계:")
print(f"   - 총 날짜: {len(data['macroIndicators'])}일")
print(f"   - 새로 추가: {added_count}개 지표")
print(f"   - API 호출: 1회")
