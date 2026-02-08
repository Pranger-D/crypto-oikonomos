"""
일일 증분 업데이트 스크립트 (CoinGecko API 사용)
- 매일 자정 실행 (GitHub Actions)
- 최신 종가 데이터만 추가 (기존 데이터 수정 안 함)
- BTC 가격, BTC 시총, 전체 시총, 도미넌스 자동 계산
"""

import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

# 환경 변수 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
if not COINGECKO_API_KEY:
    print("⚠️ COINGECKO_API_KEY가 없습니다. API 키 없이 시도합니다.")

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

# 어제와 오늘 날짜
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
today = datetime.now().strftime("%Y-%m-%d")

print(f"🔄 일일 데이터 업데이트: {today}")
print("=" * 60)

# 기존 데이터 로드
if not DATA_FILE.exists():
    print("❌ dashboard-data.json 파일이 없습니다.")
    sys.exit(1)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# 기존 날짜 목록
existing_dates = {item['date'] for item in data['priceData']}

# CoinGecko API 헤더
headers = {
    "accept": "application/json"
}
if COINGECKO_API_KEY:
    headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

# ============================================
# 1. CoinGecko에서 BTC 데이터 가져오기
# ============================================
print(f"\n📊 [1/3] CoinGecko에서 BTC 데이터 수집 중...")

btc_data = None

try:
    # BTC 현재 데이터 (가격, 시총)
    url = "https://api.coingecko.com/api/v3/coins/bitcoin"
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false"
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    if 'market_data' in result:
        btc_price = result['market_data']['current_price']['usd']
        btc_market_cap = result['market_data']['market_cap']['usd']
        
        btc_data = {
            'price': round(btc_price, 2),
            'market_cap': btc_market_cap
        }
        
        print(f"✅ BTC 가격: ${btc_price:,.2f}")
        print(f"✅ BTC 시총: ${btc_market_cap / 1e9:.1f}B")
    else:
        print("⚠️ BTC 데이터를 가져올 수 없습니다.")
        
except Exception as e:
    print(f"❌ BTC 데이터 수집 실패: {e}")

# ============================================
# 2. CoinGecko에서 전체 시총 가져오기
# ============================================
print(f"\n📊 [2/3] CoinGecko에서 전체 시총 수집 중...")

global_market_cap = None

try:
    url = "https://api.coingecko.com/api/v3/global"
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    if 'data' in result and 'total_market_cap' in result['data']:
        global_market_cap = result['data']['total_market_cap']['usd']
        print(f"✅ 전체 시총: ${global_market_cap / 1e9:.1f}B")
    else:
        print("⚠️ 전체 시총 데이터를 가져올 수 없습니다.")
        
except Exception as e:
    print(f"❌ 전체 시총 수집 실패: {e}")

# ============================================
# 3. 도미넌스 계산 및 데이터 추가
# ============================================
print(f"\n📊 [3/3] 데이터 업데이트 중...")

if btc_data and global_market_cap:
    # 도미넌스 계산
    dominance = (btc_data['market_cap'] / global_market_cap) * 100
    
    # 오늘 날짜가 기존 데이터에 없으면 추가
    if today not in existing_dates:
        new_entry = {
            "date": today,
            "btc": btc_data['price'],
            "btc_dominance": round(dominance, 1)
        }
        
        data['priceData'].append(new_entry)
        print(f"✅ 새 데이터 추가: {today}")
        print(f"   - BTC: ${btc_data['price']:,.2f}")
        print(f"   - 도미넌스: {dominance:.1f}%")
        
        # 날짜순 정렬
        data['priceData'] = sorted(data['priceData'], key=lambda x: x['date'])
        
    else:
        print(f"ℹ️ {today} 데이터가 이미 존재합니다. 기존 데이터 유지.")
        
else:
    print("⚠️ 데이터가 불완전하여 업데이트를 건너뜁니다.")

# ============================================
# 4. 거시지표 업데이트 (오늘 발표분)
# ============================================
print(f"\n📊 [4/5] 거시지표 업데이트 중...")
try:
    import investpy
    
    # 오늘 발표된 지표만 가져오기
    calendar = investpy.news.economic_calendar(
        time_zone="GMT",
        countries=["united states", "china"],
        importances=["high"],
        from_date=yesterday.replace("-", "/"),
        to_date=today.replace("-", "/")
    )
    
    if not calendar.empty:
        for _, row in calendar.iterrows():
            date_str = row['date']
            
            if date_str not in data['macroIndicators']:
                data['macroIndicators'][date_str] = []
            
            indicator = {
                "country": row['zone'],
                "indicator": row['event'],
                "importance": row['importance'],
                "actual": row.get('actual', None),
                "forecast": row.get('forecast', None),
                "previous": row.get('previous', None)
            }
            
            # 중복 체크
            existing = [i for i in data['macroIndicators'][date_str] 
                       if i['indicator'] == indicator['indicator']]
            
            if not existing:
                data['macroIndicators'][date_str].append(indicator)
        
        # 미국 우선 정렬
        for date_str in data['macroIndicators']:
            data['macroIndicators'][date_str] = sorted(
                data['macroIndicators'][date_str],
                key=lambda x: (x['country'] != 'United States', x['indicator'])
            )
        
        print(f"✅ 거시지표 업데이트 완료")
    else:
        print("ℹ️ 오늘 발표된 high importance 지표 없음")
        
except ImportError:
    print("⚠️ investpy 미설치, 거시지표 스킵")
except Exception as e:
    print(f"⚠️ 거시지표 업데이트 실패: {e}")

# ============================================
# 5. 블로그 글 업데이트
# ============================================
print(f"\n📝 [5/5] 블로그 글 업데이트 중...")

blog_dir = PROJECT_ROOT / "data" / "blog"
if blog_dir.exists():
    # 최근 7일 파일만 체크
    for i in range(7):
        check_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        
        for mdx_file in blog_dir.glob(f"{check_date}-*.mdx"):
            filename = mdx_file.stem
            parts = filename.split("-")
            
            if len(parts) >= 4:
                try:
                    date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
                    category = parts[3]
                    
                    with open(mdx_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        if "title:" in content:
                            title_line = [line for line in content.split("\n") 
                                        if line.startswith("title:")][0]
                            title = title_line.split("title:")[1].strip().strip("'\"")
                        else:
                            title = filename
                    
                    if date_str not in data['blogPosts']:
                        data['blogPosts'][date_str] = []
                    
                    # 중복 체크
                    existing = [p for p in data['blogPosts'][date_str] 
                               if p['slug'] == filename]
                    
                    if not existing:
                        data['blogPosts'][date_str].append({
                            "slug": filename,
                            "title": title,
                            "category": category.capitalize()
                        })
                        print(f"✅ 블로그 글 추가: {date_str} - {title}")
                except:
                    continue

# ============================================
# 6. 메타데이터 업데이트 및 저장
# ============================================
data['lastUpdated'] = datetime.now().isoformat()
data['metadata']['endDate'] = today
data['metadata']['totalDays'] = len(data['priceData'])

# 파일 저장
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

file_size = DATA_FILE.stat().st_size / 1024
print(f"\n✅ 업데이트 완료: {DATA_FILE}")
print(f"📦 파일 크기: {file_size:.1f} KB")
print(f"📊 총 데이터: {len(data['priceData'])}일")
print("🎉 일일 업데이트 완료!")
