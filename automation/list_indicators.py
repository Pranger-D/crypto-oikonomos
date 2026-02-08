"""
실제 데이터에 저장된 거시지표 이름 확인 및 파일 저장
"""

import json
from pathlib import Path

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"
OUTPUT_FILE = Path(__file__).parent / "indicator_list.txt"

# 데이터 로드
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# 모든 지표 이름 수집
all_indicators = set()
for indicators in data['macroIndicators'].values():
    for ind in indicators:
        all_indicators.add(ind['indicator'])

# 정렬
sorted_indicators = sorted(all_indicators)

# 파일에 저장
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("📊 실제 데이터에 저장된 거시지표 이름:\n")
    f.write("=" * 60 + "\n\n")
    
    for idx, indicator in enumerate(sorted_indicators, 1):
        f.write(f"{idx:2d}. {indicator}\n")
    
    f.write(f"\n총 {len(all_indicators)}개 지표\n")

print(f"✅ 지표 목록 저장 완료: {OUTPUT_FILE}")
print(f"총 {len(all_indicators)}개 지표")

# 화면에도 출력
for idx, indicator in enumerate(sorted_indicators, 1):
    print(f"{idx:2d}. {indicator}")
