import os
import json
from datetime import datetime
from tavily import TavilyClient
from dotenv import load_dotenv
from pathlib import Path

# ==========================================
# 1. 환경 설정
# ==========================================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("🚨 API 키 오류: .env 파일이 없거나 키가 비어있습니다.")

tavily = TavilyClient(api_key=TAVILY_API_KEY)

CACHE_FILE = Path(__file__).parent / "context_cache.json"

# 바탕화면 폴더 탐색용 유틸리티
def get_desktop_path():
    home = os.path.expanduser("~")
    paths = [
        os.path.join(home, "OneDrive", "바탕 화면"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "Desktop"),
        os.path.join(home, "바탕 화면")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return os.path.join(home, "Desktop")

DESKTOP_PATH = get_desktop_path()

# ==========================================
# 2. 고정 컨텍스트(Macro & Insight) 캐싱 전략
# ==========================================
CONTEXT_SOURCES = {
    # 🌊 Part 1: 유동성과 금융 배관 레이더
    "fomc_minutes": "Latest FOMC Minutes summary",
    "fed_liquidity_plumbing": "Latest reverse repo (RRP) TGA balance Fed liquidity analysis zerohedge",
    "global_macro_fx": "latest US dollar index DXY BOJ ECB rate decision fx dynamics macro analysis",
    
    # 📊 Part 1: 파생상품 & 온체인 펀더멘털 레이더
    "glassnode_onchain": "Glassnode The Week On-chain latest report insight",
    "greeks_live_options": "Latest Greeks.live crypto options expiry implied volatility skew analysis",
    "stablecoin_flows": "latest stablecoin supply USDT USDC net flow analysis coinmetrics",
    "coinshares_funds": "Latest CoinShares Digital Asset Fund Flows Weekly summary",
    
    # 🔥 Part 2: 거장의 뷰 & 투자 철학(멘탈) 레이더
    "arthur_hayes_essay": "Latest Arthur Hayes BitMEX blog post essay thesis",
    "howard_marks_memo": "Latest Howard Marks Oaktree Capital memo summary",
    "warren_buffett_charlie_munger": "Latest Warren Buffett Berkshire Hathaway shareholder letter core principles"
}

def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=4)

def fetch_and_cache_contexts():
    print("🔍 [Context] 고정 거시 경제 리포트 및 인사이트 확인 중...")
    cache = load_cache()
    current_year = str(datetime.now().year)
    updated_cache = False

    for key, query in CONTEXT_SOURCES.items():
        try:
            print(f"   -> {key} 업데이트 여부 확인...")
            search_query = f"{query} {current_year}"
            res = tavily.search(query=search_query, time_range="month", max_results=1, include_raw_content=True)
            
            if res.get("results"):
                latest_article = res["results"][0]
                latest_date = latest_article.get("published_date", "")
                
                if key not in cache or cache[key].get("date") != latest_date:
                    print(f"      ✨ [New Update] 새로운 리포트 발견! 캐시 갱신 ({latest_date})")
                    
                    # raw_content 값이 None으로 반환될 경우의 슬라이싱 에러 방지
                    raw_content = latest_article.get("raw_content") or ""
                    
                    cache[key] = {
                        "date": latest_date,
                        "title": latest_article.get("title") or "",
                        "url": latest_article.get("url") or "",
                        "content": raw_content[:10000]
                    }
                    updated_cache = True
                else:
                    print(f"      ✅ [Cached] 최신 상태 유지 (Date: {latest_date})")
            else:
                 print(f"      ⚠️ 검색 결과 없음, 캐시 유지")
                 
        except Exception as e:
            print(f"   ⚠️ 검색 에러 ({key}): {e}")

    if updated_cache:
        save_cache(cache)
    
    return cache

# ==========================================
# 3. [V3 추가] 바탕화면 수동 뉴스(Text) 추출
# ==========================================
def fetch_manual_news(folder_name):
    """
    바탕화면의 특정 폴더(예: Desktop/blog/2026/02-21-briefing) 안의 
    모든 .txt 파일을 읽어 배열로 반환합니다.
    """
    now = datetime.now()
    year = now.strftime("%Y")
    source_dir = os.path.join(DESKTOP_PATH, "blog", year, folder_name)
    
    print(f"📂 [Local Input] 수동 뉴스 폴더 스캔 중: {source_dir}")
    
    if not os.path.exists(source_dir):
        print(f"   ⚠️ 바탕화면에 작업 폴더가 없습니다. 빈 텍스트로 대체합니다.")
        return []

    manual_news = []
    text_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.txt')]

    if not text_files:
        print(f"   ⚠️ 폴더 안에 전달된 .txt 속보 파일이 없습니다.")
    else:
        for tf in text_files:
            file_path = os.path.join(source_dir, tf)
            content = None
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, "r", encoding="cp949") as file:
                        content = file.read()
                except Exception as e:
                    print(f"   ❌ {tf} cp949 읽기 실패: {e}")
            except Exception as e:
                print(f"   ❌ {tf} 읽기 실패: {e}")
                
            if content is not None:
                manual_news.append({
                    "filename": tf,
                    "content": content
                })
                print(f"   ✅ [Text Found] {tf} 텍스트 확보 ({len(content)}자)")
                
    return manual_news

# ==========================================
# 4. 브레인 통합 실행기
# ==========================================
def build_brain_data(folder_name):
    """
    Auto Blogger(메인 스크립트)에게 컨텍스트와 수동 입력된 뉴스를 공급
    """
    # 1. 고정 컨텍스트 획득 (캐싱)
    context_data = fetch_and_cache_contexts()
    
    # 2. 수동 뉴스 속보 (텍스트 파일 읽기)
    manual_news = fetch_manual_news(folder_name)
    
    return {
        "context": context_data,
        "vip_news": manual_news
    }

if __name__ == "__main__":
    # Test
    now = datetime.now()
    category = "briefing"
    folder_name = f"{now.strftime('%m-%d')}-{category}"
    data = build_brain_data(folder_name)
    print("\n[🎯 V3 Brain Output Preview]")
    print(f"Context loaded: {len(data['context'])} keys")
    print(f"Manual texts loaded: {len(data['vip_news'])} files")
