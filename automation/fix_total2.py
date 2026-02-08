"""
Total2 데이터 수정 스크립트
- 기존 잘못된 계산 방식 대신 실제 Total2 데이터 사용
- CoinGecko API 또는 수동 계산 방식
"""

import json
from pathlib import Path

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

print("🔧 Total2 데이터 수정 중...")
print("=" * 60)

# 기존 데이터 로드
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Total2 값을 1/3로 수정 (임시 조치)
# 실제로는 CoinGecko API나 다른 소스 사용 필요
print("\n⚠️ 임시 조치: Total2 값을 1/3로 조정")
print("   (실제 API 연동은 별도 작업 필요)\n")

fixed_count = 0
for item in data['priceData']:
    if item['total2'] is not None:
        # 기존 값이 3배 과대평가되어 있으므로 1/3로 조정
        item['total2'] = int(item['total2'] / 3)
        fixed_count += 1

# 메타데이터 업데이트
data['metadata']['dataSource']['total2'] = "Adjusted (temporary fix - needs proper API)"

# 파일 저장
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ {fixed_count}개 데이터 포인트 수정 완료")
print(f"📁 파일: {DATA_FILE}")
print("\n⚠️ 주의: 이것은 임시 수정입니다.")
print("   향후 CoinGecko API나 다른 정확한 소스로 교체 필요")
