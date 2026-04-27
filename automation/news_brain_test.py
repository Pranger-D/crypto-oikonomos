import os
import sys

# Windows 콘솔 인코딩 문제 방지 (이모지 등 유니코드 출력)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from tavily import TavilyClient
from google import genai

# ==========================================
# 1. 환경 설정
# ==========================================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("🚨 API 키 오류: .env 파일이 없거나 TAVILY_API_KEY가 비어있습니다.")
if not GOOGLE_API_KEY:
    raise ValueError("🚨 API 키 오류: .env 파일이 없거나 GOOGLE_API_KEY가 비어있습니다.")

tavily = TavilyClient(api_key=TAVILY_API_KEY)
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)


# ==========================================
# 2. 바탕화면 경로 탐색
# ==========================================
def get_desktop_path() -> str:
    home = os.path.expanduser("~")
    paths = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "바탕 화면"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "OneDrive", "바탕 화면"),
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return os.path.join(home, "Desktop")


DESKTOP_PATH = get_desktop_path()


# ==========================================
# 3. 바탕화면 수동 뉴스(.txt) 읽기
# ==========================================
def fetch_manual_news(folder_name: str, year: str = None) -> list:
    """
    바탕화면 blog/{year}/{folder_name}/ 안의 모든 .txt 파일을 읽어 리스트로 반환.
    """
    if not year:
        year = datetime.now().strftime("%Y")
    source_dir = os.path.join(DESKTOP_PATH, "blog", year, folder_name)

    print(f"📂 [Manual News] 수동 뉴스 폴더 스캔 중: {source_dir}")

    if not os.path.exists(source_dir):
        print("   ⚠️ 바탕화면에 작업 폴더가 없습니다. 수동 뉴스 없이 진행합니다.")
        return []

    manual_news = []
    text_files = [f for f in os.listdir(source_dir) if f.lower().endswith(".txt")]

    if not text_files:
        print("   ⚠️ 폴더 안에 .txt 속보 파일이 없습니다.")
        return []

    for tf in text_files:
        file_path = os.path.join(source_dir, tf)
        content = None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="cp949") as f:
                    content = f.read()
            except Exception as e:
                print(f"   ❌ {tf} cp949 읽기 실패: {e}")
        except Exception as e:
            print(f"   ❌ {tf} 읽기 실패: {e}")

        if content is not None:
            manual_news.append({"filename": tf, "content": content})
            print(f"   ✅ [Text] {tf} 확보 ({len(content)}자)")

    return manual_news


# ==========================================
# 4. Gemini로 핵심 키워드 추출
# ==========================================
def extract_keywords(user_prompt: str, manual_news: list) -> list:
    """
    사용자 프롬프트 + 수동 뉴스를 Gemini에게 주고 핵심 키워드 5~8개를 JSON 배열로 추출.
    """
    print("🔑 [Keyword] Gemini로 핵심 키워드 추출 중...")

    news_text = ""
    for n in manual_news:
        news_text += f"\n[{n['filename']}]\n{n['content']}\n"

    prompt = f"""
당신은 금융·크립토 분야의 리서처입니다.
아래 [글의 방향성]과 [수동 뉴스]를 읽고, 이 주제를 심층 분석하는 데 필요한 핵심 검색 키워드를 5~8개 추출해주세요.

[글의 방향성]
{user_prompt}

[수동 뉴스]
{news_text if news_text.strip() else "(없음)"}

[출력 형식 — JSON 배열만 출력하세요. 다른 텍스트는 절대 포함하지 마세요]
["키워드1", "키워드2", "키워드3", ...]

규칙:
- 키워드는 Tavily 웹 검색에 적합한 영어 또는 한국어 검색어로 작성하세요.
- 글의 방향성과 뉴스 내용을 모두 반영하세요.
- 5~8개 사이로 추출하세요.
"""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview", contents=prompt
        )
        text = response.text.strip()

        # JSON 배열 파싱
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            keywords = json.loads(match.group())
            print(f"   ✅ 키워드 추출 완료: {keywords}")
            return keywords
        else:
            print(f"   ⚠️ JSON 파싱 실패, 원문: {text[:200]}")
            return []
    except Exception as e:
        print(f"   ❌ 키워드 추출 실패: {e}")
        return []


# ==========================================
# 5. Tavily Search — 키워드별 검색
# ==========================================
def search_by_keywords(keywords: list) -> dict:
    """
    키워드별로 Tavily Search API 호출 (키워드당 max_results=3).
    반환: {keyword: [{"title", "url", "content", "raw_content"}]}
    """
    print(f"🔍 [Search] Tavily 키워드 검색 시작 ({len(keywords)}개 키워드)...")
    results = {}

    for idx, kw in enumerate(keywords):
        try:
            print(f"   -> 검색 중: '{kw}'")
            # 핵심 키워드(상위 2개)는 max_results=5, 나머지는 2로 가중치 적용
            res = tavily.search(
                query=kw,
                max_results=5 if idx < 2 else 2,
                include_raw_content=True,  # 전문 포함 요청
            )
            items = []
            for r in res.get("results", []):
                items.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),       # 짧은 요약
                    "raw_content": r.get("raw_content") or "",  # 전문 (있을 경우)
                })
            results[kw] = items
            print(f"      ✅ {len(items)}건 수집")
        except Exception as e:
            print(f"   ⚠️ '{kw}' 검색 실패: {e}")
            results[kw] = []

    return results


# ==========================================
# 6. Tavily Extract — URL별 전문 추출
# ==========================================
def extract_full_content(search_results: dict) -> dict:
    """
    Search 결과의 URL들에 대해 Tavily Extract API로 전문 추출.
    raw_content가 이미 있는 URL은 Extract 건너뜀.
    반환: {keyword: [{"title", "url", "raw_content"}]}
    """
    print("📄 [Extract] Tavily Extract API로 전문 추출 중...")

    for kw, items in search_results.items():
        urls_to_extract = []
        url_map = {}  # url -> item index

        for i, item in enumerate(items):
            if not item.get("raw_content"):
                urls_to_extract.append(item["url"])
                url_map[item["url"]] = i

        if not urls_to_extract:
            continue

        try:
            print(f"   -> '{kw}': {len(urls_to_extract)}개 URL Extract 시도")
            extract_res = tavily.extract(urls=urls_to_extract)
            for r in extract_res.get("results", []):
                url = r.get("url", "")
                raw = r.get("raw_content") or ""
                if url in url_map:
                    items[url_map[url]]["raw_content"] = raw
                    print(f"      ✅ Extract 완료: {url[:60]}... ({len(raw)}자)")
        except Exception as e:
            print(f"   ⚠️ '{kw}' Extract 실패: {e}")

    return search_results


# ==========================================
# 7. 스마트 트림
# ==========================================
def smart_trim(raw_content: str, keyword: str, max_chars: int = 5000) -> str:
    """
    - raw_content <= max_chars: 원본 그대로 반환 (가공 없음)
    - raw_content > max_chars: 키워드 포함 문단 + 앞뒤 2개 문단 조합 → ~max_chars자
    """
    if len(raw_content) <= max_chars:
        return raw_content

    paragraphs = raw_content.split("\n\n")

    # 키워드가 포함된 문단 인덱스
    keyword_indices = [
        i for i, p in enumerate(paragraphs)
        if keyword.lower() in p.lower()
    ]

    # 키워드 미매칭 → 앞에서부터 잘라내기
    if not keyword_indices:
        return raw_content[:max_chars]

    # 키워드 문단 + 앞뒤 2개 문단 수집
    selected = set()
    for idx in keyword_indices:
        for offset in range(-2, 3):  # -2, -1, 0, +1, +2
            neighbor = idx + offset
            if 0 <= neighbor < len(paragraphs):
                selected.add(neighbor)

    # 순서 유지하며 max_chars 이내로 조합
    result_parts = []
    char_count = 0
    for i in sorted(selected):
        part = paragraphs[i]
        if char_count + len(part) > max_chars:
            break
        result_parts.append(part)
        char_count += len(part)

    return "\n\n".join(result_parts)


# ==========================================
# 8. 검색 결과에 스마트 트림 적용
# ==========================================
def apply_smart_trim(search_results: dict) -> dict:
    """
    각 기사의 raw_content에 smart_trim을 적용.
    raw_content가 없을 경우 Search의 짧은 content(요약)를 사용.
    """
    trimmed = {}
    kw_idx = 0
    for kw, items in search_results.items():
        trimmed_items = []
        for item_idx, item in enumerate(items):
            raw = item.get("raw_content", "")
            fallback = item.get("content", "")

            # 핵심 키워드(상위 2개)의 최상단 기사 1개는 10,000자까지 넓게 트림 (전문 활용)
            # 나머지는 토큰 예산을 위해 3,000자로 트림
            if kw_idx < 2 and item_idx == 0:
                trim_limit = 10000
            else:
                trim_limit = 3000

            if raw:
                final_content = smart_trim(raw, kw, max_chars=trim_limit)
            else:
                # Extract 실패 케이스: 짧은 요약이라도 사용
                final_content = fallback

            trimmed_items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": final_content,
            })
        trimmed[kw] = trimmed_items
        kw_idx += 1
    return trimmed


# ==========================================
# 9. 참고 링크 수집
# ==========================================
def build_reference_links(search_results: dict) -> list:
    """검색 결과에서 중복 제거된 참고 링크 리스트 생성."""
    seen_urls = set()
    links = []
    for items in search_results.values():
        for item in items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                links.append({
                    "title": item.get("title", url),
                    "url": url,
                })
    return links


# ==========================================
# 10. 전체 브레인 오케스트레이션
# ==========================================
def build_brain_data(
    folder_name: str,
    user_prompt: str,
    year: str = None,
    lite_mode: bool = False,
) -> dict:
    """
    V4 브레인 메인 엔트리포인트.
    
    Args:
        folder_name: 바탕화면 작업 폴더명 (예: '04-21-insight')
        user_prompt: 사용자가 입력한 글의 방향성
        year: 연도 (기본: 올해)
        lite_mode: True면 Tavily Extract API 생략 (크레딧 절약)
    
    Returns:
        {
            "user_prompt": str,
            "vip_news": list,        # 수동 뉴스 (주재료)
            "keyword_context": dict, # 키워드별 Tavily 결과 (보완재)
            "reference_links": list, # 참고 링크 (글 하단)
        }
    """
    if not year:
        year = datetime.now().strftime("%Y")

    # 1. 수동 뉴스 읽기
    vip_news = fetch_manual_news(folder_name, year)

    # 2. 키워드 추출
    keywords = extract_keywords(user_prompt, vip_news)

    keyword_context = {}
    reference_links = []

    if keywords:
        # 3. Tavily 검색
        search_results = search_by_keywords(keywords)

        if not lite_mode:
            # 4. Extract API로 전문 추출 (기본 모드)
            search_results = extract_full_content(search_results)
        else:
            print("💡 [Lite Mode] Extract API 생략. Search 요약만 사용합니다.")

        # 5. 스마트 트림 적용
        keyword_context = apply_smart_trim(search_results)

        # 6. 참고 링크 수집
        reference_links = build_reference_links(search_results)
    else:
        print("⚠️ 키워드 추출 실패. 수동 뉴스만으로 진행합니다.")

    return {
        "user_prompt": user_prompt,
        "vip_news": vip_news,
        "keyword_context": keyword_context,
        "reference_links": reference_links,
    }


# ==========================================
# 단독 실행 테스트
# ==========================================
if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "비트코인 달러 약세 유동성"
    now = datetime.now()
    folder = f"{now.strftime('%m-%d')}-insight"
    data = build_brain_data(folder, prompt, lite_mode=True)
    print("\n[🎯 Brain Output Preview]")
    print(f"Keywords found: {list(data['keyword_context'].keys())}")
    print(f"Manual news: {len(data['vip_news'])}건")
    print(f"Reference links: {len(data['reference_links'])}건")
