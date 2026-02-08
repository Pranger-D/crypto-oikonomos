"""
CoinGecko CSV에서 전체 시총 데이터 추출 및 도미넌스 계산
- CSV 파일: CoinGecko-GlobalCryptoMktCap-2026-02-08.csv
- 2017-01-01부터 데이터 사용
- BTC 시총은 기존 BTC 가격 * 유통량으로 계산
- 도미넌스 = (BTC 시총 / 전체 시총) * 100
"""

import csv
import json
from datetime import datetime
from pathlib import Path

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
CSV_FILE = PROJECT_ROOT / "public" / "data" / "CoinGecko-GlobalCryptoMktCap-2026-02-08.csv"
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

print("📊 CoinGecko CSV 데이터 처리 중...")
print("=" * 60)

# CSV 파일 읽기
global_market_caps = {}

print(f"\n📂 CSV 파일 로드: {CSV_FILE}")

with open(CSV_FILE, "r", encoding="utf-8") as f:
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

print(f"✅ CSV 데이터 로드 완료: {len(global_market_caps)}일")
print(f"   기간: {min(global_market_caps.keys())} ~ {max(global_market_caps.keys())}")

# dashboard-data.json 로드
print(f"\n📂 dashboard-data.json 로드 중...")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"✅ 기존 데이터: {len(data['priceData'])}일")

# 도미넌스 계산
print(f"\n🔄 도미넌스 계산 중...")

updated_count = 0
missing_count = 0

for item in data['priceData']:
    date_str = item['date']
    
    # 전체 시총 데이터가 있고, BTC 가격이 있는 경우
    if date_str in global_market_caps and item['btc'] is not None:
        global_cap = global_market_caps[date_str]
        btc_price = item['btc']
        
        # BTC 유통량 계산 (2017: 16.5M, 연간 약 328,767 BTC 증가)
        year = int(date_str.split('-')[0])
        circulating_supply = 16500000 + (year - 2017) * 328767
        
        # BTC 시총
        btc_market_cap = btc_price * circulating_supply
        
        # 도미넌스 계산
        dominance = (btc_market_cap / global_cap) * 100
        
        item['btc_dominance'] = round(dominance, 1)
        updated_count += 1
        
        # 샘플 출력 (처음 5개)
        if updated_count <= 5:
            print(f"   {date_str}: BTC ${btc_market_cap / 1e9:.1f}B / Global ${global_cap / 1e9:.1f}B = {dominance:.1f}%")
    else:
        if date_str >= "2017-01-01":
            missing_count += 1

print(f"\n✅ 도미넌스 업데이트: {updated_count}일")
if missing_count > 0:
    print(f"⚠️ 데이터 없음: {missing_count}일")

# 메타데이터 업데이트
data['metadata']['dataSource']['btc_dominance'] = "CoinGecko (historical global market cap)"

# 파일 저장
print(f"\n💾 파일 저장 중...")

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

file_size = DATA_FILE.stat().st_size / 1024
print(f"✅ 파일 저장 완료: {file_size:.1f} KB")

print(f"\n🎉 실제 도미넌스 데이터 적용 완료!")
print(f"\n📊 통계:")
print(f"   - 전체 시총 데이터: {len(global_market_caps)}일")
print(f"   - 도미넌스 계산: {updated_count}일")
print(f"   - 성공률: {updated_count / len(data['priceData']) * 100:.1f}%")
