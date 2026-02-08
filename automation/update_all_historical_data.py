"""
2013년부터 현재까지 전체 데이터 업데이트
- BTC 가격, BTC 시총: btc-usd-max.csv
- 전체 시총: CoinGecko-GlobalCryptoMktCap-2026-02-08.csv
- 도미넌스 = (BTC 시총 / 전체 시총) * 100
- 2013-04-28부터 현재까지 모든 데이터 포함
"""

import csv
import json
from datetime import datetime
from pathlib import Path

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
BTC_CSV_FILE = PROJECT_ROOT / "public" / "data" / "btc-usd-max.csv"
GLOBAL_CSV_FILE = PROJECT_ROOT / "public" / "data" / "CoinGecko-GlobalCryptoMktCap-2026-02-08.csv"
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

print("📊 2013년부터 전체 데이터 업데이트")
print("=" * 60)

# 1. BTC 데이터 CSV 읽기
btc_data = {}

print(f"\n📂 BTC CSV 파일 로드: {BTC_CSV_FILE}")

with open(BTC_CSV_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        # 날짜 파싱
        date_str = row['snapped_at'].split(' ')[0]  # "2013-04-28 00:00:00 UTC" -> "2013-04-28"
        
        # BTC 가격
        btc_price = float(row['price'])
        
        # BTC 시총 (세 번째 컬럼)
        btc_market_cap = float(row['market_cap'])
        
        btc_data[date_str] = {
            'price': btc_price,
            'market_cap': btc_market_cap
        }

print(f"✅ BTC 데이터 로드 완료: {len(btc_data)}일")
print(f"   기간: {min(btc_data.keys())} ~ {max(btc_data.keys())}")

# 2. 전체 시총 CSV 읽기
global_market_caps = {}

print(f"\n📂 전체 시총 CSV 파일 로드: {GLOBAL_CSV_FILE}")

with open(GLOBAL_CSV_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        # 타임스탬프 (밀리초) -> 날짜
        timestamp_ms = int(row['snapped_at'])
        date_str = datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")
        
        # 전체 시총
        market_cap = float(row['market_cap'])
        
        global_market_caps[date_str] = market_cap

print(f"✅ 전체 시총 데이터 로드 완료: {len(global_market_caps)}일")
print(f"   기간: {min(global_market_caps.keys())} ~ {max(global_market_caps.keys())}")

# 3. 모든 날짜 수집 (BTC와 전체 시총 합집합)
all_dates = sorted(set(btc_data.keys()) | set(global_market_caps.keys()))

print(f"\n📅 전체 날짜 범위: {all_dates[0]} ~ {all_dates[-1]}")
print(f"   총 {len(all_dates)}일")

# 4. 새로운 priceData 생성
print(f"\n🔄 데이터 생성 중...")

new_price_data = []
btc_count = 0
dominance_count = 0

for date_str in all_dates:
    item = {
        'date': date_str,
        'btc': None,
        'btc_dominance': None
    }
    
    # BTC 가격
    if date_str in btc_data:
        item['btc'] = round(btc_data[date_str]['price'], 2)
        btc_count += 1
        
        # 도미넌스 계산 (BTC 시총과 전체 시총 모두 있는 경우)
        if date_str in global_market_caps:
            btc_market_cap = btc_data[date_str]['market_cap']
            global_cap = global_market_caps[date_str]
            
            dominance = (btc_market_cap / global_cap) * 100
            item['btc_dominance'] = round(dominance, 1)
            dominance_count += 1
    
    new_price_data.append(item)

print(f"✅ 데이터 생성 완료:")
print(f"   - 총 날짜: {len(new_price_data)}일")
print(f"   - BTC 가격: {btc_count}일")
print(f"   - 도미넌스: {dominance_count}일")

# 샘플 출력 (처음 5개)
print(f"\n📊 샘플 데이터 (초기):")
for i in range(min(5, len(new_price_data))):
    item = new_price_data[i]
    if item['btc'] and item['btc_dominance']:
        btc_cap = btc_data[item['date']]['market_cap']
        global_cap = global_market_caps[item['date']]
        print(f"   {item['date']}: BTC ${btc_cap / 1e9:.1f}B / Global ${global_cap / 1e9:.1f}B = {item['btc_dominance']}%")

# 5. dashboard-data.json 로드 및 업데이트
print(f"\n📂 dashboard-data.json 로드 중...")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# priceData 교체
old_count = len(data['priceData'])
data['priceData'] = new_price_data

# 메타데이터 업데이트
data['metadata']['startDate'] = all_dates[0]
data['metadata']['endDate'] = all_dates[-1]
data['metadata']['totalDays'] = len(all_dates)
data['metadata']['dataSource']['btc'] = "CoinGecko (historical BTC price & market cap)"
data['metadata']['dataSource']['btc_dominance'] = "CoinGecko (BTC market cap / Global market cap)"

print(f"✅ 데이터 교체:")
print(f"   - 이전: {old_count}일")
print(f"   - 현재: {len(new_price_data)}일")
print(f"   - 증가: +{len(new_price_data) - old_count}일")

# 6. macroIndicators와 blogPosts는 기존 날짜 범위 유지
# (2017년 이전 데이터는 없을 것이므로 그대로 유지)

# 파일 저장
print(f"\n💾 파일 저장 중...")

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

file_size = DATA_FILE.stat().st_size / 1024
print(f"✅ 파일 저장 완료: {file_size:.1f} KB")

print(f"\n🎉 전체 역사적 데이터 업데이트 완료!")
print(f"\n📊 최종 통계:")
print(f"   - 전체 기간: {all_dates[0]} ~ {all_dates[-1]}")
print(f"   - 총 날짜: {len(new_price_data)}일")
print(f"   - BTC 가격: {btc_count}일 ({btc_count / len(new_price_data) * 100:.1f}%)")
print(f"   - 도미넌스: {dominance_count}일 ({dominance_count / len(new_price_data) * 100:.1f}%)")
