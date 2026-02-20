import os
import json
from datetime import datetime, date
from bs4 import BeautifulSoup
from lxml import etree
import google.generativeai as genai
from tavily import TavilyClient
import requests

from dotenv import load_dotenv
from pathlib import Path

# ==========================================
# 1. 환경 설정
# ==========================================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    raise ValueError("🚨 API 키 오류: .env 파일이 없거나 키가 비어있습니다.")

tavily = TavilyClient(api_key=TAVILY_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

CACHE_FILE = Path(__file__).parent / "context_cache.json"

# ==========================================
# 2. 고정 컨텍스트(Macro & Insight) 캐싱 전략
# ==========================================
CONTEXT_SOURCES = {
    "fomc": "Latest FOMC Minutes summary",
    "world_bank": "Latest World Bank / IMF Global Economic Prospects",
    "glassnode": "Glassnode latest on-chain week report summary",
    "a16z": "latest a16z (Andreessen Horowitz) State of Crypto"
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
    current_month_str = datetime.now().strftime("%B %Y")
    updated_cache = False

    for key, query in CONTEXT_SOURCES.items():
        # 가벼운 핑 용도로 최근 1달 뉴스를 검색하여 발행일을 체크
        try:
            print(f"   -> {key} 업데이트 여부 확인...")
            search_query = f"{query} {current_year}"
            res = tavily.search(query=search_query, time_range="month", max_results=1, include_raw_content=True)
            
            if res.get("results"):
                latest_article = res["results"][0]
                latest_date = latest_article.get("published_date", "")
                
                # 캐시가 없거나 날짜가 경신되었을 때만 업데이트
                if key not in cache or cache[key].get("date") != latest_date:
                    print(f"      ✨ [New Update] 새로운 리포트 발견! 캐시를 갱신합니다. ({latest_date})")
                    # 내용 갱신
                    cache[key] = {
                        "date": latest_date,
                        "title": latest_article.get("title", ""),
                        "url": latest_article.get("url", ""),
                        "content": latest_article.get("raw_content", "")[:10000] # 핵심 1만자만 저장
                    }
                    updated_cache = True
                else:
                    print(f"      ✅ [Cached] 최신 상태 유지 중 (Date: {latest_date})")
            else:
                 print(f"      ⚠️ 검색 결과 없음, 캐시 유지")
                 
        except Exception as e:
            print(f"   ⚠️ 검색 에러 ({key}): {e}")

    if updated_cache:
        save_cache(cache)
    
    return cache

# ==========================================
# 3. 코인니스(Coinness) 24시간 속보 크롤링
# ==========================================
def fetch_coinness_news():
    """
    Coinness의 API나 웹 구조(React 기반)를 파악하여 최근 24시간 속보를 가져옵니다.
    여기서는 Coinness의 공개 RSS 피드를 활용하거나 크롤링하는 방식을 사용합니다.
    (Coinness 공식 RSS가 없으므로 html 파싱 활용 시뮬레이션)
    """
    print("🌐 [Coinness] 최근 속보 크롤링 시작...")
    # 참고: 코인니스는 보통 API 호출 방식이거나 스크롤 로딩입니다.
    # 단순화를 위해 일단 주요 트렌딩 뉴스 타겟팅 (추후 코인니스 구조에 맞춰 상세 크롤링 고도화)
    # 여기서는 검색 API(Tavily)로 최근 1일치 주요 뉴스를 쓸어담는 것으로 대체하거나 
    # 코인니스 특정 뉴스 페이지를 requests로 긁어옵니다.
    
    # -----------------------------
    # [임시 브릿지] 코인니스 차단 방지용 크롤링 대신, 
    # Tavily를 통해 "오늘의 크립토/매크로/기관 속보 50개"를 무차별 수집합니다.
    # (코인니스와 동일한 속보 풀 확보)
    # -----------------------------
    today_str = datetime.now().strftime("%Y-%m-%d")
    raw_news_list = []
    
    queries = [
        "Cryptocurrency regulation policy SEC CFTC breaking news",
        "Crypto institutional adoption BlackRock ETF breaking news",
        "Federal reserve Powell inflation macro economy breaking news",
        "Bitcoin Ethereum on-chain anomaly movement breaking news"
    ]
    
    for q in queries:
        try:
            res = tavily.search(query=f"{q} {today_str}", search_depth="basic", time_range="day", max_results=15)
            for r in res.get("results", []):
                raw_news_list.append({
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                    "image": "" # 코인니스 긁을시 og:image 추출 
                })
        except Exception as e:
            continue
            
    print(f"   📊 총 {len(raw_news_list)}개의 최신 뉴스 조각 수집 완료.")
    return raw_news_list

# ==========================================
# 4. AI 기반 '진짜 중요한 뉴스' 판별망 (수석 에디터 프롬프트)
# ==========================================
def filter_vip_news(raw_news_list):
    print("🧠 [AI Filter] 수십 개의 뉴스 중 '시장 이동의 핵심(VIP)'을 분류 중...")
    
    # 리스트를 텍스트 블록으로 변환
    news_text = ""
    for idx, news in enumerate(raw_news_list):
        news_text += f"[ID: {idx}] Title: {news['title']}\nSummary: {news['content']}\nLink: {news['url']}\n---\n"
        
    prompt = f"""
    당신은 10년 이상 월스트리트와 크립토 시장에서 경험을 쌓은 최상위 헷지펀드 매니저이자 수석 에디터입니다.
    아래 [최근 24시간 속보 원시 데이터]에는 시장의 진정한 내러티브와 쓰레기(Noise)가 섞여 있습니다.
    
    [당신의 임무]
    이 텍스트 무더기 속에서, **"오늘의 블로그 브리핑"에 담을 가장 중요하고 파괴력 있는 뉴스 딱 5개만** 골라주십시오.
    단순한 알트코인 파트너십, 거래소 상장 찌라시는 모두 버리십시오.
    
    [중요도 판별 기준 (Strict Rules)]
    A. Macro & Key Figures (거시 & 주요 인사): 연준(Fed) 인사들의 금리/경제 발언, 미국 정부 요인, 일론 머스크/래리 핑크 등 거물들의 심도 있는 시장 뷰.
    B. Regulation & Policy (규제 & 정책): SEC, CFTC의 소송, 가이드라인 발표, ETF 승인 등 구조적 변화.
    C. Institutional (기관 동향): 메이저 자산운용사, 전통 금융권의 굵직한 자금 이동.
    D. Dynamic On-chain (온체인 이상): 평소와 완전히 다른 이상치(Anomaly - 휴면 고래의 천문학적 이동 등). 사소한 이동은 무시.
    E. 중복 배제: 완벽히 같은 주제를 다루는 뉴스는 가장 정보가 풍부한 1개만 남길 것.

    [원시 데이터]
    {news_text}
    
    [출력 형식]
    반드시 아래의 **JSON 형식**으로만 출력하십시오. 마크다운(` ```json `) 블록을 쓰지 말고 순수 JSON만 반환하세요.
    
    [
      {{
        "category": "분류 (예: Macro & Policy)",
        "title": "선택한 뉴스의 제목",
        "reason": "이 뉴스가 왜 오늘 시장에서 중요한가에 대한 날카로운 코멘트 (1줄)",
        "original_id": "원문 ID 숫자",
        "url": "원문 Link"
      }},
      ... (정확히 5개)
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        # JSON 파싱 정제
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()
            
        filtered_news = json.loads(result_text)
        print("   ✅ AI VIP 필터링 완료!")
        return filtered_news
    except Exception as e:
        print(f"   ❌ JSON 파싱 실패 혹은 AI 에러: {e}")
        return []

# ==========================================
# 5. 브레인 통합 실행기
# ==========================================
def build_brain_data():
    """
    Auto Blogger(메인 스크립트)에게 컨텍스트와 필터링된 뉴스를 공급하는 함수
    """
    # 1. 고정 컨텍스트 획득 (캐싱)
    context_data = fetch_and_cache_contexts()
    
    # 2. 속보 수집
    raw_news = fetch_coinness_news()
    
    # 3. AI 필터링
    vip_news = filter_vip_news(raw_news)
    
    return {
        "context": context_data,
        "vip_news": vip_news
    }

if __name__ == "__main__":
    # 테스트 구동
    data = build_brain_data()
    print("\n[🎯 Final Brain Output Preview]")
    print(json.dumps(data["vip_news"], indent=2, ensure_ascii=False))
