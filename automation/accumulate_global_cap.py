"""
대안: 매일 CoinGecko API로 전체 시총 데이터 축적
- 기존 데이터 파일에 전체 시총 저장
- GitHub Actions로 매일 실행
- 시간이 지나면서 역사적 데이터 자동 축적
"""

import os
import json
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

# 환경 변수 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"
GLOBAL_CAP_FILE = PROJECT_ROOT / "public" / "data" / "global-market-cap.json"

print("📊 전체 시총 데이터 축적 시스템")
print("=" * 60)

# 전체 시총 히스토리 파일 로드 (없으면 생성)
if GLOBAL_CAP_FILE.exists():
    with open(GLOBAL_CAP_FILE, "r", encoding="utf-8") as f:
        global_cap_history = json.load(f)
    print(f"✅ 기존 히스토리 로드: {len(global_cap_history)}일")
else:
    global_cap_history = {}
    print("📝 새 히스토리 파일 생성")

# CoinGecko API로 현재 전체 시총 가져오기
headers = {
    "accept": "application/json",
    "x-cg-demo-api-key": COINGECKO_API_KEY
} if COINGECKO_API_KEY else {"accept": "application/json"}

try:
    url = "https://api.coingecko.com/api/v3/global"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    if 'data' in result and 'total_market_cap' in result['data']:
        current_global_cap = result['data']['total_market_cap'].get('usd', 0)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 오늘 데이터 저장
        global_cap_history[today] = {
            "date": today,
            "global_market_cap": current_global_cap,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n✅ 오늘 전체 시총: ${current_global_cap / 1e9:.1f}B")
        print(f"   날짜: {today}")
        
        # 히스토리 파일 저장
        with open(GLOBAL_CAP_FILE, "w", encoding="utf-8") as f:
            json.dump(global_cap_history, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 히스토리 저장 완료: {len(global_cap_history)}일")
        
        # dashboard-data.json 업데이트
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 오늘 날짜의 도미넌스 계산
        for item in data['priceData']:
            if item['date'] == today and item['btc'] is not None:
                # BTC 시총 계산
                btc_price = item['btc']
                year = int(today.split('-')[0])
                circulating_supply = 16500000 + (year - 2017) * 328767
                btc_market_cap = btc_price * circulating_supply
                
                # 도미넌스 계산
                dominance = (btc_market_cap / current_global_cap) * 100
                item['btc_dominance'] = round(dominance, 1)
                
                print(f"\n✅ 도미넌스 업데이트: {dominance:.1f}%")
                print(f"   BTC 시총: ${btc_market_cap / 1e9:.1f}B")
                print(f"   전체 시총: ${current_global_cap / 1e9:.1f}B")
                break
        
        # 과거 날짜들도 히스토리 데이터가 있으면 업데이트
        updated_past = 0
        for item in data['priceData']:
            date_str = item['date']
            if date_str in global_cap_history and date_str != today and item['btc'] is not None:
                past_global_cap = global_cap_history[date_str]['global_market_cap']
                
                # BTC 시총 계산
                btc_price = item['btc']
                year = int(date_str.split('-')[0])
                circulating_supply = 16500000 + (year - 2017) * 328767
                btc_market_cap = btc_price * circulating_supply
                
                # 도미넌스 계산
                dominance = (btc_market_cap / past_global_cap) * 100
                item['btc_dominance'] = round(dominance, 1)
                updated_past += 1
        
        if updated_past > 0:
            print(f"✅ 과거 데이터 업데이트: {updated_past}일")
        
        # 파일 저장
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ dashboard-data.json 업데이트 완료")
        print(f"\n🎉 전체 시총 데이터 축적 완료!")
        print(f"\n💡 매일 실행하면 역사적 데이터가 자동으로 축적됩니다.")
        
    else:
        print("❌ 전체 시총 데이터 없음")
        
except Exception as e:
    print(f"❌ API 오류: {e}")
