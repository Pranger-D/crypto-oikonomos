import os
import sys

# Windows 콘솔 ?�코??문제 방�? (?�모지 ???�니코드 출력)
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
# 1. ?�경 ?�정
# ==========================================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("?�� API ???�류: .env ?�일???�거??TAVILY_API_KEY가 비어?�습?�다.")
if not GOOGLE_API_KEY:
    raise ValueError("?�� API ???�류: .env ?�일???�거??GOOGLE_API_KEY가 비어?�습?�다.")

tavily = TavilyClient(api_key=TAVILY_API_KEY)
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)


# ==========================================
# 2. 바탕?�면 경로 ?�색
# ==========================================
def get_desktop_path() -> str:
    home = os.path.expanduser("~")
    paths = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "바탕 ?�면"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "OneDrive", "바탕 ?�면"),
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return os.path.join(home, "Desktop")


DESKTOP_PATH = get_desktop_path()


# ==========================================
# 3. 바탕?�면 ?�동 ?�스(.txt) ?�기
# ==========================================
def fetch_manual_news(folder_name: str, year: str = None) -> list:
    """
    바탕?�면 blog/{year}/{folder_name}/ ?�의 모든 .txt ?�일???�어 리스?�로 반환.
    """
    if not year:
        year = datetime.now().strftime("%Y")
    source_dir = os.path.join(DESKTOP_PATH, "blog", year, folder_name)

    print(f"?�� [Manual News] ?�동 ?�스 ?�더 ?�캔 �? {source_dir}")

    if not os.path.exists(source_dir):
        print("   ?�️ 바탕?�면???�업 ?�더가 ?�습?�다. ?�동 ?�스 ?�이 진행?�니??")
        return []

    manual_news = []
    text_files = [f for f in os.listdir(source_dir) if f.lower().endswith(".txt")]

    if not text_files:
        print("   ?�️ ?�더 ?�에 .txt ?�보 ?�일???�습?�다.")
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
                print(f"   ??{tf} cp949 ?�기 ?�패: {e}")
        except Exception as e:
            print(f"   ??{tf} ?�기 ?�패: {e}")

        if content is not None:
            manual_news.append({"filename": tf, "content": content})
            print(f"   ??[Text] {tf} ?�보 ({len(content)}??")

    return manual_news


# ==========================================
# 4. Gemini�??�심 ?�워??추출
# ==========================================
def extract_keywords(user_prompt: str, manual_news: list) -> list:
    """
    ?�용???�롬?�트 + ?�동 ?�스�?Gemini?�게 주고 ?�심 ?�워??5~8개�? JSON 배열�?추출.
    """
    print("?�� [Keyword] Gemini�??�심 ?�워??추출 �?..")

    news_text = ""
    for n in manual_news:
        news_text += f"\n[{n['filename']}]\n{n['content']}\n"

    prompt = f"""
?�신?� 금융·?�립??분야??리서처입?�다.
?�래 [글??방향??�?[?�동 ?�스]�??�고, ??주제�??�층 분석?�는 ???�요???�심 검???�워?��? 5~8�?추출?�주?�요.

[글??방향??
{user_prompt}

[?�동 ?�스]
{news_text if news_text.strip() else "(?�음)"}

[출력 ?�식 ??JSON 배열�?출력?�세?? ?�른 ?�스?�는 ?��? ?�함?��? 마세??
["?�워??", "?�워??", "?�워??", ...]

규칙:
- ?�워?�는 Tavily ??검?�에 ?�합???�어 ?�는 ?�국??검?�어�??�성?�세??
- 글??방향?�과 ?�스 ?�용??모두 반영?�세??
- 5~8�??�이�?추출?�세??
"""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview", contents=prompt
        )
        text = response.text.strip()

        # JSON 배열 ?�싱
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            keywords = json.loads(match.group())
            print(f"   ???�워??추출 ?�료: {keywords}")
            return keywords
        else:
            print(f"   ?�️ JSON ?�싱 ?�패, ?�문: {text[:200]}")
            return []
    except Exception as e:
        print(f"   ???�워??추출 ?�패: {e}")
        return []


# ==========================================
# 5. Tavily Search ???�워?�별 검??# ==========================================
def search_by_keywords(keywords: list) -> dict:
    """
    ?�워?�별�?Tavily Search API ?�출 (?�워?�당 max_results=3).
    반환: {keyword: [{"title", "url", "content", "raw_content"}]}
    """
    print(f"?�� [Search] Tavily ?�워??검???�작 ({len(keywords)}�??�워??...")
    results = {}

    for kw in keywords:
        try:
            print(f"   -> 검??�? '{kw}'")
            res = tavily.search(
                query=kw,
                max_results=3,
                include_raw_content=True,  # ?�문 ?�함 ?�청
            )
            items = []
            for r in res.get("results", []):
                items.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),       # 짧�? ?�약
                    "raw_content": r.get("raw_content") or "",  # ?�문 (?�을 경우)
                })
            results[kw] = items
            print(f"      ??{len(items)}�??�집")
        except Exception as e:
            print(f"   ?�️ '{kw}' 검???�패: {e}")
            results[kw] = []

    return results


# ==========================================
# 6. Tavily Extract ??URL�??�문 추출
# ==========================================
def extract_full_content(search_results: dict) -> dict:
    """
    Search 결과??URL?�에 ?�??Tavily Extract API�??�문 추출.
    raw_content가 ?��? ?�는 URL?� Extract 건너?�.
    반환: {keyword: [{"title", "url", "raw_content"}]}
    """
    print("?�� [Extract] Tavily Extract API�??�문 추출 �?..")

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
            print(f"   -> '{kw}': {len(urls_to_extract)}�?URL Extract ?�도")
            extract_res = tavily.extract(urls=urls_to_extract)
            for r in extract_res.get("results", []):
                url = r.get("url", "")
                raw = r.get("raw_content") or ""
                if url in url_map:
                    items[url_map[url]]["raw_content"] = raw
                    print(f"      ??Extract ?�료: {url[:60]}... ({len(raw)}??")
        except Exception as e:
            print(f"   ?�️ '{kw}' Extract ?�패: {e}")

    return search_results


# ==========================================
# 7. ?�마???�림
# ==========================================
def smart_trim(raw_content: str, keyword: str, max_chars: int = 5000) -> str:
    """
    - raw_content <= max_chars: ?�본 그�?�?반환 (가�??�음)
    - raw_content > max_chars: ?�워???�함 문단 + ?�뒤 2�?문단 조합 ??~max_chars??    """
    if len(raw_content) <= max_chars:
        return raw_content

    paragraphs = raw_content.split("\n\n")

    # ?�워?��? ?�함??문단 ?�덱??    keyword_indices = [
        i for i, p in enumerate(paragraphs)
        if keyword.lower() in p.lower()
    ]

    # ?�워??미매�????�에?��????�라?�기
    if not keyword_indices:
        return raw_content[:max_chars]

    # ?�워??문단 + ?�뒤 2�?문단 ?�집
    selected = set()
    for idx in keyword_indices:
        for offset in range(-2, 3):  # -2, -1, 0, +1, +2
            neighbor = idx + offset
            if 0 <= neighbor < len(paragraphs):
                selected.add(neighbor)

    # ?�서 ?��??�며 max_chars ?�내�?조합
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
# 8. 검??결과???�마???�림 ?�용
# ==========================================
def apply_smart_trim(search_results: dict) -> dict:
    """
    �?기사??raw_content??smart_trim???�용.
    raw_content가 ?�을 경우 Search??짧�? content(?�약)�??�용.
    """
    trimmed = {}
    for kw, items in search_results.items():
        trimmed_items = []
        for item in items:
            raw = item.get("raw_content", "")
            fallback = item.get("content", "")

            if raw:
                final_content = smart_trim(raw, kw)
            else:
                # Extract ?�패 케?�스: 짧�? ?�약?�라???�용
                final_content = fallback

            trimmed_items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": final_content,
            })
        trimmed[kw] = trimmed_items
    return trimmed


# ==========================================
# 9. 참고 링크 ?�집
# ==========================================
def build_reference_links(search_results: dict) -> list:
    """검??결과?�서 중복 ?�거??참고 링크 리스???�성."""
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
# 10. ?�체 브레???��??�트?�이??# ==========================================
def build_brain_data(
    folder_name: str,
    user_prompt: str,
    year: str = None,
    lite_mode: bool = False,
) -> dict:
    """
    V4 브레??메인 ?�트리포?�트.
    
    Args:
        folder_name: 바탕?�면 ?�업 ?�더�?(?? '04-21-insight')
        user_prompt: ?�용?��? ?�력??글??방향??        year: ?�도 (기본: ?�해)
        lite_mode: True�?Tavily Extract API ?�략 (?�레???�약)
    
    Returns:
        {
            "user_prompt": str,
            "vip_news": list,        # ?�동 ?�스 (주재�?
            "keyword_context": dict, # ?�워?�별 Tavily 결과 (보완??
            "reference_links": list, # 참고 링크 (글 ?�단)
        }
    """
    if not year:
        year = datetime.now().strftime("%Y")

    # 1. ?�동 ?�스 ?�기
    vip_news = fetch_manual_news(folder_name, year)

    # 2. ?�워??추출
    keywords = extract_keywords(user_prompt, vip_news)

    keyword_context = {}
    reference_links = []

    if keywords:
        # 3. Tavily 검??        search_results = search_by_keywords(keywords)

        if not lite_mode:
            # 4. Extract API�??�문 추출 (기본 모드)
            search_results = extract_full_content(search_results)
        else:
            print("?�� [Lite Mode] Extract API ?�략. Search ?�약�??�용?�니??")

        # 5. ?�마???�림 ?�용
        keyword_context = apply_smart_trim(search_results)

        # 6. 참고 링크 ?�집
        reference_links = build_reference_links(search_results)
    else:
        print("?�️ ?�워??추출 ?�패. ?�동 ?�스만으�?진행?�니??")

    return {
        "user_prompt": user_prompt,
        "vip_news": vip_news,
        "keyword_context": keyword_context,
        "reference_links": reference_links,
    }


# ==========================================
# ?�독 ?�행 ?�스??# ==========================================
if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "비트코인 ?�러 ?�세 ?�동??
    now = datetime.now()
    folder = f"{now.strftime('%m-%d')}-insight"
    data = build_brain_data(folder, prompt, lite_mode=True)
    print("\n[?�� Brain Output Preview]")
    print(f"Keywords found: {list(data['keyword_context'].keys())}")
    print(f"Manual news: {len(data['vip_news'])}�?)
    print(f"Reference links: {len(data['reference_links'])}�?)
