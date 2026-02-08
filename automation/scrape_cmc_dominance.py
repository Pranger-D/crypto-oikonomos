"""
CoinMarketCap BTC Dominance 스크래핑 (완전판)
- Selenium으로 동적 페이지 로드
- 2017-01-01부터 현재까지 일별 도미넌스
- dashboard-data.json 업데이트
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "public" / "data" / "dashboard-data.json"

print("🔍 CoinMarketCap BTC Dominance 스크래핑")
print("=" * 60)

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument('--headless')  # 백그라운드 실행
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

print("\n🌐 브라우저 시작 중...")

try:
    # Chrome 드라이버 초기화
    driver = webdriver.Chrome(options=chrome_options)
    
    url = "https://coinmarketcap.com/charts/bitcoin-dominance/"
    print(f"📊 페이지 로드 중: {url}")
    
    driver.get(url)
    
    # 페이지 로드 대기
    print("⏳ 차트 로딩 대기 중...")
    time.sleep(10)  # 차트 로드 대기
    
    # 페이지 소스에서 차트 데이터 추출
    page_source = driver.page_source
    
    # JavaScript 변수에서 데이터 추출 시도
    # CoinMarketCap은 보통 window.__NEXT_DATA__ 또는 유사한 변수에 데이터 저장
    
    # 스크립트 실행으로 데이터 가져오기
    try:
        # Next.js 데이터 추출
        next_data = driver.execute_script("return window.__NEXT_DATA__")
        
        if next_data:
            print("✅ Next.js 데이터 발견!")
            
            # JSON 저장 (디버깅용)
            debug_file = PROJECT_ROOT / "automation" / "cmc_debug.json"
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(next_data, f, indent=2)
            print(f"📝 디버그 데이터 저장: {debug_file}")
            
            # 도미넌스 데이터 추출 (구조는 실제 응답에 따라 조정 필요)
            # 일반적으로 props.pageProps.initialData 등에 위치
            
    except Exception as e:
        print(f"⚠️ Next.js 데이터 추출 실패: {e}")
    
    # 대안: 네트워크 요청 가로채기
    # Selenium은 기본적으로 네트워크 로그를 제공하지 않으므로
    # Chrome DevTools Protocol 사용 필요
    
    print("\n💡 CoinMarketCap API 직접 호출 시도...")
    
    # CoinMarketCap의 실제 API 엔드포인트 사용
    # 브라우저 개발자 도구 네트워크 탭에서 확인한 엔드포인트
    
    import requests
    
    # CoinMarketCap 차트 API (비공식)
    api_url = "https://api.coinmarketcap.com/data-api/v3/global-metrics/quotes/historical"
    
    params = {
        "format": "chart_crypto_details",
        "interval": "1d",
        "time_start": int(datetime(2017, 1, 1).timestamp()),
        "time_end": int(datetime.now().timestamp())
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"🔄 API 호출 중: {api_url}")
    
    response = requests.get(api_url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    api_data = response.json()
    
    print(f"✅ API 응답 수신!")
    
    # 응답 구조 확인
    debug_api_file = PROJECT_ROOT / "automation" / "cmc_api_debug.json"
    with open(debug_api_file, "w", encoding="utf-8") as f:
        json.dump(api_data, f, indent=2)
    print(f"📝 API 응답 저장: {debug_api_file}")
    
    # 도미넌스 데이터 추출
    dominance_data = {}
    
    if 'data' in api_data and 'quotes' in api_data['data']:
        for quote in api_data['data']['quotes']:
            timestamp_str = quote.get('timestamp')
            btc_dominance = quote.get('btcDominance')
            
            if timestamp_str and btc_dominance:
                # ISO 문자열을 datetime으로 파싱
                from dateutil import parser as date_parser
                dt = date_parser.parse(timestamp_str)
                date_str = dt.strftime("%Y-%m-%d")
                dominance_data[date_str] = round(btc_dominance, 1)
        
        print(f"✅ 도미넌스 데이터 추출: {len(dominance_data)}일")
        
        # 샘플 출력
        sample_dates = list(dominance_data.keys())[:5]
        print(f"\n📊 샘플 데이터:")
        for date in sample_dates:
            print(f"   {date}: {dominance_data[date]}%")

    
    # dashboard-data.json 업데이트
    if dominance_data:
        print("\n📝 dashboard-data.json 업데이트 중...")
        
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        updated_count = 0
        for item in data['priceData']:
            date_str = item['date']
            if date_str in dominance_data:
                item['btc_dominance'] = dominance_data[date_str]
                updated_count += 1
        
        print(f"✅ {updated_count}일 도미넌스 업데이트")
        
        # 메타데이터 업데이트
        data['metadata']['dataSource']['btc_dominance'] = "CoinMarketCap (historical) + CoinGecko (current)"
        
        # 파일 저장
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        file_size = DATA_FILE.stat().st_size / 1024
        print(f"\n✅ 파일 저장 완료: {file_size:.1f} KB")
        print("\n🎉 CoinMarketCap 도미넌스 스크래핑 완료!")
    else:
        print("\n⚠️ 도미넌스 데이터를 추출하지 못했습니다.")
        print("   디버그 파일을 확인하여 API 응답 구조를 분석하세요.")
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

finally:
    try:
        driver.quit()
        print("\n🔒 브라우저 종료")
    except:
        pass

print("\n" + "=" * 60)
