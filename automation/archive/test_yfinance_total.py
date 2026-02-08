"""
yfinance로 전체 암호화폐 시총 티커 확인
가능한 티커: TOTAL, TOTAL-USD, CRYPTO-USD 등
"""

import yfinance as yf
from datetime import datetime

print("🔍 yfinance로 전체 암호화폐 시총 티커 확인 중...")
print("=" * 60)

# 가능한 티커 목록
possible_tickers = [
    "TOTAL",
    "TOTAL-USD",
    "CRYPTO-USD",
    "TOTALCAP-USD",
    "TOTAL.CC",
    "^TOTAL",
    "CRYPTOCAP:TOTAL"
]

print("\n📊 티커 테스트 중...\n")

for ticker_symbol in possible_tickers:
    try:
        print(f"티커: {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol)
        
        # 최근 1개월 데이터 시도
        hist = ticker.history(period="1mo")
        
        if not hist.empty:
            print(f"✅ 성공! 데이터 발견")
            print(f"   기간: {hist.index[0]} ~ {hist.index[-1]}")
            print(f"   데이터 포인트: {len(hist)}개")
            print(f"   최근 종가: ${hist['Close'].iloc[-1]:,.0f}")
            print(f"   샘플 데이터:")
            print(hist.tail(3))
            print("\n" + "=" * 60)
            
            # 2017년부터 데이터 확인
            print(f"\n📅 2017년부터 데이터 확인 중...")
            hist_all = ticker.history(start="2017-01-01", end=datetime.now().strftime("%Y-%m-%d"))
            
            if not hist_all.empty:
                print(f"✅ 역사적 데이터 사용 가능!")
                print(f"   시작: {hist_all.index[0]}")
                print(f"   종료: {hist_all.index[-1]}")
                print(f"   총 데이터: {len(hist_all)}일")
                print(f"\n   초기 데이터 (2017):")
                print(hist_all.head(3))
                print(f"\n   최근 데이터:")
                print(hist_all.tail(3))
            else:
                print(f"⚠️ 역사적 데이터 없음")
            
            break
        else:
            print(f"❌ 데이터 없음")
            
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    print()

print("\n" + "=" * 60)
print("🎯 결론: 위에서 성공한 티커를 사용하세요!")
