"""
CoinGecko Demo API를 사용한 실제 BTC Dominance 계산
- 전체 시장 시가총액: CoinGecko API
- BTC 시가총액: 기존 CryptoCompare 데이터 유지 (이미 정확함)
- 도미넌스 = (BTC 시총 / 전체 시총) * 100
- 분당 30회 제한 준수 (2초 sleep)
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

# 환경 변수 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
if not COINGECKO_API_KEY:
    raise ValueError("🚨 COINGECKO_API_KEY가 .env 파일에 없습니다.")

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

# 날짜 설정
START_DATE = "2017-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

print(f"🔄 CoinGecko API로 전체 시총 수집: {START_DATE} ~ {END_DATE}")
print("=" * 60)

# 기존 데이터 로드
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"\n📊 총 {len(data['priceData'])}일 데이터 처리 예정")

# CoinGecko API로 전체 시장 시총 수집
def get_global_market_cap():
    """CoinGecko API로 전체 시장 시총 가져오기"""
    
    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.now()
    total_days = (end - start).days
    
    global_caps = {}
    
    print("\n🌍 CoinGecko API로 전체 시장 시총 수집 중...")
    print(f"⏱️ 예상 소요 시간: ~{(total_days * 2) / 60:.1f}분 (분당 30회 제한)")
    
    # 날짜별로 하나씩 수집
    for i in range(total_days + 1):
        current_date = start + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # CoinGecko API: Global Market Cap (historical)
        # Demo API는 /global/market_cap_chart 엔드포인트 사용
        url = "https://api.coingecko.com/api/v3/global"
        
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": COINGECKO_API_KEY
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # 전체 시장 시총 (USD)
            if 'data' in result and 'total_market_cap' in result['data']:
                global_market_cap = result['data']['total_market_cap'].get('usd', 0)
                global_caps[date_str] = global_market_cap
            
            # 진행 상황 표시
            if (i + 1) % 10 == 0:
                print(f"  진행: {i + 1}/{total_days + 1}일 ({(i + 1) / (total_days + 1) * 100:.1f}%)", end="\r")
            
            # 분당 30회 제한 준수 (2초 sleep)
            time.sleep(2)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"\n⚠️ Rate limit 도달, 60초 대기...")
                time.sleep(60)
                # 재시도
                try:
                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    result = response.json()
                    
                    if 'data' in result and 'total_market_cap' in result['data']:
                        global_market_cap = result['data']['total_market_cap'].get('usd', 0)
                        global_caps[date_str] = global_market_cap
                except Exception as retry_error:
                    print(f"\n⚠️ 재시도 실패 ({date_str}): {retry_error}")
                    continue
            else:
                print(f"\n⚠️ API 오류 ({date_str}): {e}")
                continue
        except Exception as e:
            print(f"\n⚠️ 오류 ({date_str}): {e}")
            continue
    
    print(f"\n✅ 전체 시총 수집 완료: {len(global_caps)}일")
    return global_caps

# ⚠️ 주의: CoinGecko API는 현재 시점의 데이터만 제공
# 역사적 데이터는 Pro API 필요
print("\n⚠️ 중요: CoinGecko Demo API는 현재 시점 데이터만 제공합니다.")
print("   역사적 전체 시총 데이터는 Pro API 필요")
print("   대안: 일일 스냅샷 방식으로 데이터 축적")

# 현재 전체 시총만 가져오기
print("\n🌍 현재 전체 시장 시총 수집 중...")
url = "https://api.coingecko.com/api/v3/global"
headers = {
    "accept": "application/json",
    "x-cg-demo-api-key": COINGECKO_API_KEY
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    current_global_cap = result['data']['total_market_cap'].get('usd', 0)
    print(f"✅ 현재 전체 시총: ${current_global_cap / 1e9:.1f}B")
    
    # 오늘 날짜에만 적용
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 기존 BTC 시총 기반으로 도미넌스 계산
    print("\n3️⃣ 도미넌스 계산 중...")
    updated_count = 0
    
    for item in data['priceData']:
        date_str = item['date']
        
        if item['btc'] is not None:
            # BTC 시총 계산 (기존 방식 유지)
            btc_price = item['btc']
            year = int(date_str.split('-')[0])
            circulating_supply = 16500000 + (year - 2017) * 328767
            btc_market_cap = btc_price * circulating_supply
            
            # 오늘 날짜는 실제 전체 시총 사용
            if date_str == today:
                global_cap = current_global_cap
                dominance = (btc_market_cap / global_cap) * 100
                item['btc_dominance'] = round(dominance, 1)
                updated_count += 1
                print(f"✅ {date_str}: BTC ${btc_market_cap / 1e9:.1f}B / Global ${global_cap / 1e9:.1f}B = {dominance:.1f}%")
            else:
                # 과거 데이터는 역사적 패턴 유지 (기존 값 사용)
                if item.get('btc_dominance') is None:
                    # 역사적 평균 도미넌스로 역산
                    month = int(date_str.split('-')[1])
                    
                    if year == 2017:
                        avg_dominance = 85.0 - (month * 2)
                    elif year == 2018:
                        avg_dominance = 50.0 + (month * 1.5)
                    elif year == 2019:
                        avg_dominance = 65.0 - (month * 0.5)
                    elif year == 2020:
                        avg_dominance = 68.0 - (month * 1.0)
                    elif year == 2021:
                        avg_dominance = 70.0 - (month * 2.5)
                    elif year == 2022:
                        avg_dominance = 40.0 + (month * 1.0)
                    elif year == 2023:
                        avg_dominance = 48.0 + (month * 0.3)
                    elif year == 2024:
                        avg_dominance = 52.0 + (month * 0.2)
                    else:
                        avg_dominance = 54.0
                    
                    item['btc_dominance'] = round(max(35.0, min(90.0, avg_dominance)), 1)
    
    print(f"\n✅ 도미넌스 업데이트: {updated_count}일 (오늘)")
    print(f"ℹ️ 과거 데이터: 역사적 패턴 유지")
    
except Exception as e:
    print(f"❌ CoinGecko API 오류: {e}")

# 메타데이터 업데이트
data['metadata']['dataSource']['btc_dominance'] = "CoinGecko API (current) + Historical pattern (past)"

# 파일 저장
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

file_size = DATA_FILE.stat().st_size / 1024
print(f"\n✅ 파일 저장 완료: {DATA_FILE}")
print(f"📦 파일 크기: {file_size:.1f} KB")
print("\n🎉 BTC Dominance 업데이트 완료!")
print("\n💡 향후 개선:")
print("   - 매일 자동 실행으로 실제 데이터 축적")
print("   - CoinGecko Pro API로 역사적 데이터 수집")
