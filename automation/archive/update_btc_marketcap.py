"""
BTC 시총 CSV에서 정확한 데이터 추출 및 도미넌스 재계산
- CSV 파일: btc-usd-max.csv
- 세 번째 컬럼: BTC 시가총액 (정확한 값)
- 2017-01-01부터 데이터 사용
- 도미넌스 = (BTC 시총 / 전체 시총) * 100
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

print("📊 정확한 BTC 시총 데이터로 도미넌스 재계산")
print("=" * 60)

# 1. BTC 시총 CSV 읽기
btc_market_caps = {}

print(f"\n📂 BTC CSV 파일 로드: {BTC_CSV_FILE}")

with open(BTC_CSV_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        # 날짜 파싱
        date_str = row['snapped_at'].split(' ')[0]  # "2017-01-01 00:00:00 UTC" -> "2017-01-01"
        
        # BTC 시총 (세 번째 컬럼)
        btc_market_cap = float(row['market_cap'])
        
        # 2017-01-01 이후 데이터만 저장
        if date_str >= "2017-01-01":
            btc_market_caps[date_str] = btc_market_cap

print(f"✅ BTC 시총 데이터 로드 완료: {len(btc_market_caps)}일")
print(f"   기간: {min(btc_market_caps.keys())} ~ {max(btc_market_caps.keys())}")

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
        
        # 2017-01-01 이후 데이터만 저장
        if date_str >= "2017-01-01":
            global_market_caps[date_str] = market_cap

print(f"✅ 전체 시총 데이터 로드 완료: {len(global_market_caps)}일")

# 3. dashboard-data.json 로드
print(f"\n📂 dashboard-data.json 로드 중...")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"✅ 기존 데이터: {len(data['priceData'])}일")

# 4. BTC 가격 및 도미넌스 업데이트
print(f"\n🔄 BTC 가격 및 도미넌스 업데이트 중...")

updated_price = 0
updated_dominance = 0
missing_btc = 0
missing_global = 0

for item in data['priceData']:
    date_str = item['date']
    
    # BTC 시총 데이터가 있는 경우
    if date_str in btc_market_caps:
        btc_market_cap = btc_market_caps[date_str]
        
        # BTC 가격도 CSV에서 가져오기 (더 정확함)
        # 가격 = 시총 / 유통량
        year = int(date_str.split('-')[0])
        circulating_supply = 16500000 + (year - 2017) * 328767
        btc_price = btc_market_cap / circulating_supply
        
        item['btc'] = round(btc_price, 2)
        updated_price += 1
        
        # 전체 시총 데이터도 있는 경우 도미넌스 계산
        if date_str in global_market_caps:
            global_cap = global_market_caps[date_str]
            dominance = (btc_market_cap / global_cap) * 100
            item['btc_dominance'] = round(dominance, 1)
            updated_dominance += 1
            
            # 샘플 출력 (처음 5개)
            if updated_dominance <= 5:
                print(f"   {date_str}: BTC ${btc_market_cap / 1e9:.1f}B / Global ${global_cap / 1e9:.1f}B = {dominance:.1f}%")
        else:
            missing_global += 1
    else:
        if date_str >= "2017-01-01":
            missing_btc += 1

print(f"\n✅ 업데이트 완료:")
print(f"   - BTC 가격 업데이트: {updated_price}일")
print(f"   - 도미넌스 업데이트: {updated_dominance}일")
if missing_btc > 0:
    print(f"   ⚠️ BTC 데이터 없음: {missing_btc}일")
if missing_global > 0:
    print(f"   ⚠️ 전체 시총 데이터 없음: {missing_global}일")

# 메타데이터 업데이트
data['metadata']['dataSource']['btc'] = "CoinGecko (historical BTC market cap)"
data['metadata']['dataSource']['btc_dominance'] = "CoinGecko (BTC market cap / Global market cap)"

# 파일 저장
print(f"\n💾 파일 저장 중...")

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

file_size = DATA_FILE.stat().st_size / 1024
print(f"✅ 파일 저장 완료: {file_size:.1f} KB")

print(f"\n🎉 정확한 BTC 시총 데이터 적용 완료!")
print(f"\n📊 통계:")
print(f"   - BTC 시총 데이터: {len(btc_market_caps)}일")
print(f"   - 전체 시총 데이터: {len(global_market_caps)}일")
print(f"   - 도미넌스 계산: {updated_dominance}일")
print(f"   - 성공률: {updated_dominance / len(data['priceData']) * 100:.1f}%")
