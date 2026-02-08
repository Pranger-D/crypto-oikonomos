"""
거시지표 날짜 형식 변환
- DD/MM/YYYY → YYYY-MM-DD
- priceData와 동일한 형식으로 통일
"""

import json
from datetime import datetime
from pathlib import Path

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

print("🔧 거시지표 날짜 형식 변환")
print("=" * 60)

# 데이터 로드
print(f"\n📂 파일 로드 중...")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"✅ 기존 거시지표: {len(data['macroIndicators'])}일")

# 날짜 형식 변환
print(f"\n🔄 날짜 형식 변환 중 (DD/MM/YYYY → YYYY-MM-DD)...")

new_macro_indicators = {}

for date_str, indicators in data['macroIndicators'].items():
    try:
        # DD/MM/YYYY → YYYY-MM-DD 변환
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        new_date_str = date_obj.strftime("%Y-%m-%d")
        
        new_macro_indicators[new_date_str] = indicators
        
        # 샘플 출력 (처음 3개)
        if len(new_macro_indicators) <= 3:
            print(f"   {date_str} → {new_date_str} ({len(indicators)}개 지표)")
    
    except ValueError as e:
        print(f"⚠️ 날짜 변환 실패: {date_str} - {e}")
        # 이미 YYYY-MM-DD 형식이면 그대로 유지
        new_macro_indicators[date_str] = indicators

# 데이터 교체
data['macroIndicators'] = new_macro_indicators

print(f"\n✅ 변환 완료: {len(new_macro_indicators)}일")

# 샘플 날짜 출력
print(f"\n📊 변환된 날짜 샘플:")
sample_dates = sorted(new_macro_indicators.keys(), reverse=True)[:5]
for date_str in sample_dates:
    count = len(new_macro_indicators[date_str])
    print(f"   {date_str}: {count}개 지표")

# 파일 저장
print(f"\n💾 파일 저장 중...")
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

file_size = DATA_FILE.stat().st_size / 1024
print(f"✅ 파일 저장 완료: {file_size:.1f} KB")

print(f"\n🎉 날짜 형식 변환 완료!")
print(f"\n💡 이제 브라우저에서 차트의 날짜를 클릭하면 거시지표가 표시됩니다!")
