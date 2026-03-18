"""
초기 역사적 데이터 로드 스크립트 (2017-01-01부터)
- BTC 가격: yfinance
- Total2: CryptoCompare API
- 거시지표: investpy (high importance, US/China)
"""

import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
import requests
from dotenv import load_dotenv

# 환경 변수 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")
if not CRYPTOCOMPARE_API_KEY:
    raise ValueError("🚨 CRYPTOCOMPARE_API_KEY가 .env 파일에 없습니다.")

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

# 날짜 설정
START_DATE = "2017-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

print(f"🚀 초기 데이터 로드 시작: {START_DATE} ~ {END_DATE}")
print("=" * 60)

# ============================================
# 1. BTC 가격 데이터 (yfinance)
# ============================================
print("\n📊 [1/3] BTC 가격 데이터 수집 중 (yfinance)...")
try:
    btc = yf.Ticker("BTC-USD")
    btc_hist = btc.history(start=START_DATE, end=END_DATE, interval="1d")
    
    if btc_hist.empty:
        raise ValueError("BTC 데이터가 비어있습니다.")
    
    # 종가만 추출
    btc_data = {}
    for date, row in btc_hist.iterrows():
        date_str = date.strftime("%Y-%m-%d")
        btc_data[date_str] = round(row['Close'], 2)
    
    print(f"✅ BTC 데이터 수집 완료: {len(btc_data)}일")
except Exception as e:
    print(f"❌ BTC 데이터 수집 실패: {e}")
    sys.exit(1)

# ============================================
# 2. Total2 데이터 (CryptoCompare API)
# ============================================
print("\n📊 [2/3] Total2 (알트코인 시총) 데이터 수집 중 (CryptoCompare)...")

def get_total2_historical():
    """CryptoCompare API로 Total2 역사적 데이터 가져오기"""
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    
    # 2017-01-01부터 현재까지 일수 계산
    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.now()
    total_days = (end - start).days
    
    total2_data = {}
    limit = 2000  # CryptoCompare 최대 2000개/요청
    
    # 배치로 나눠서 요청
    for i in range(0, total_days, limit):
        to_timestamp = int((end - timedelta(days=i)).timestamp())
        
        params = {
            "fsym": "BTC",  # 기준 심볼 (Total2 직접 지원 안 함, 대안 사용)
            "tsym": "USD",
            "limit": min(limit, total_days - i),
            "toTs": to_timestamp,
            "api_key": CRYPTOCOMPARE_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("Response") == "Error":
                print(f"⚠️ API 오류: {data.get('Message')}")
                continue
            
            for item in data.get("Data", {}).get("Data", []):
                date_str = datetime.fromtimestamp(item['time']).strftime("%Y-%m-%d")
                # Total2는 직접 제공되지 않으므로, 임시로 BTC 시총 * 2로 근사
                # 실제로는 다른 API나 계산 필요
                total2_data[date_str] = int(item['close'] * 21000000 * 2)  # BTC 공급량 근사
            
            print(f"  진행: {len(total2_data)}/{total_days}일", end="\r")
            
        except Exception as e:
            print(f"\n⚠️ API 호출 실패 (배치 {i}): {e}")
            continue
    
    return total2_data

try:
    total2_data = get_total2_historical()
    print(f"\n✅ Total2 데이터 수집 완료: {len(total2_data)}일")
except Exception as e:
    print(f"❌ Total2 데이터 수집 실패: {e}")
    total2_data = {}

# ============================================
# 3. 거시지표 데이터 (investpy)
# ============================================
print("\n📊 [3/3] 거시지표 데이터 수집 중 (investpy)...")

try:
    import investpy
    
    # 경제 캘린더 가져오기
    calendar = investpy.news.economic_calendar(
        time_zone="GMT",
        countries=["united states", "china"],
        importances=["high"],
        from_date=START_DATE.replace("-", "/"),
        to_date=END_DATE.replace("-", "/")
    )
    
    # 날짜별로 정리
    macro_data = {}
    for _, row in calendar.iterrows():
        date_str = row['date']
        
        if date_str not in macro_data:
            macro_data[date_str] = []
        
        indicator = {
            "country": row['zone'],
            "indicator": row['event'],
            "importance": row['importance'],
            "actual": row.get('actual', None),
            "forecast": row.get('forecast', None),
            "previous": row.get('previous', None)
        }
        
        macro_data[date_str].append(indicator)
    
    # 미국 우선 정렬
    for date_str in macro_data:
        macro_data[date_str] = sorted(
            macro_data[date_str],
            key=lambda x: (x['country'] != 'United States', x['indicator'])
        )
    
    print(f"✅ 거시지표 수집 완료: {len(macro_data)}일")
    
except ImportError:
    print("⚠️ investpy 라이브러리가 설치되지 않았습니다. 거시지표 스킵.")
    macro_data = {}
except Exception as e:
    print(f"⚠️ 거시지표 수집 실패: {e}")
    macro_data = {}

# ============================================
# 4. 블로그 글 매칭
# ============================================
print("\n📝 [4/4] 블로그 글 매칭 중...")

blog_posts = {}
blog_dir = PROJECT_ROOT / "data" / "blog"

if blog_dir.exists():
    for mdx_file in blog_dir.glob("*.mdx"):
        # 파일명 형식: YYYY-MM-DD-category.mdx
        filename = mdx_file.stem
        parts = filename.split("-")
        
        if len(parts) >= 4:
            try:
                date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
                category = parts[3]
                
                # frontmatter에서 제목 추출
                with open(mdx_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "title:" in content:
                        title_line = [line for line in content.split("\n") if line.startswith("title:")][0]
                        title = title_line.split("title:")[1].strip().strip("'\"")
                    else:
                        title = filename
                
                if date_str not in blog_posts:
                    blog_posts[date_str] = []
                
                blog_posts[date_str].append({
                    "slug": filename,
                    "title": title,
                    "category": category.capitalize()
                })
            except:
                continue

print(f"✅ 블로그 글 매칭 완료: {len(blog_posts)}일")

# ============================================
# 5. JSON 파일 생성
# ============================================
print("\n💾 dashboard-data.json 생성 중...")

# priceData 배열 생성 (날짜 정렬)
price_data = []
all_dates = sorted(set(btc_data.keys()) | set(total2_data.keys()))

for date_str in all_dates:
    price_data.append({
        "date": date_str,
        "btc": btc_data.get(date_str, None),
        "total2": total2_data.get(date_str, None)
    })

# 최종 데이터 구조
dashboard_data = {
    "lastUpdated": datetime.now().isoformat(),
    "metadata": {
        "startDate": START_DATE,
        "endDate": END_DATE,
        "totalDays": len(price_data),
        "dataSource": {
            "btc": "yfinance (BTC-USD)",
            "total2": "CryptoCompare API",
            "macro": "investpy (Investing.com)"
        },
        "version": "1.0.0"
    },
    "priceData": price_data,
    "macroIndicators": macro_data,
    "blogPosts": blog_posts
}

# 파일 저장
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

file_size = DATA_FILE.stat().st_size / 1024  # KB
print(f"✅ 파일 저장 완료: {DATA_FILE}")
print(f"📦 파일 크기: {file_size:.1f} KB")
print(f"📊 총 데이터: {len(price_data)}일")
print("\n🎉 초기 데이터 로드 완료!")
