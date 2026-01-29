import os
import datetime
from pathlib import Path
import google.generativeai as genai
from tavily import TavilyClient
from dotenv import load_dotenv

# ==========================================
# 1. 환경 설정 및 API 키 로드
# ==========================================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    print(f"📂 .env 탐색 경로: {env_path}")
    raise ValueError("🚨 API 키 오류: .env 파일이 없거나 키가 비어있습니다.")
else:
    print("✅ API Key 로드 성공")

# ==========================================
# 2. 클라이언트 초기화
# ==========================================
tavily = TavilyClient(api_key=TAVILY_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


# ==========================================
# 3. 함수 정의
# ==========================================


def fetch_news_with_options(query, count, days):
    """
    Tavily API를 사용하여 24시간 이내(day)의 최신 뉴스만 정밀 검색합니다.
    """
    print(f"   🔍 Searching (Strict 24h for News): {query}...")

    trusted_domains = [
        "bloomberg.com",
        "reuters.com",
        "wsj.com",
        "ft.com",
        "theblock.co",
        "coindesk.com",
        "cointelegraph.com",
        "federalreserve.gov",
        "sec.gov",
        "whitehouse.gov",
        "congress.gov",
    ]

    try:
        search_topic = "news" if days <= 3 else "general"
        time_filter = "day" if days <= 1 else "year"

        response = tavily.search(
            query=query,
            search_depth="advanced",
            topic=search_topic,  # [수정] 뉴스 카테고리 명시
            time_range=time_filter,  # [수정] 'day'로 설정 시 24시간 이내 데이터 우선
            include_domains=trusted_domains,  # 해당 도메인에서 뉴스 탐색
            include_raw_content=True,
            max_results=count,
        )
        return response.get("results", [])
    except Exception as e:
        print(f"   ⚠️ Error searching {query}: {e}")
        return []


def get_morning_investment_briefing():
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    current_month_str = today.strftime("%B %Y")

    print(f"--------\n[{today_str}] 🚀 맥킨지 스타일 Hybrid 브리핑 생성 시작...")

    # [투 트랙 전략: News(1일) vs Context(360일)]
    search_plan = [
        # ---------------------------------------------------------
        # Track A: Breaking News (최신성 집중 - days=1)
        # ---------------------------------------------------------
        # 1-A. 크립토: 제도권, 규제, 기관 움직임 (10개)
        {
            "category": "Breaking: Crypto Regulation & Institutions",
            "query": f"Cryptocurrency regulation news institutional adoption major market movers financial policy change updates {current_month_str}",  # 이번 달 한정
            "count": 10,
            "days": 1,
            "type": "news",
        },
        # 1-B. 크립토: 시장 트렌드, 온체인, 기술 (10개)
        {
            "category": "Breaking: Market Dynamics & Tech",
            "query": f"Crypto market trends innovation on-chain data whale activity Bitcoin Dominence fear and greed index trending news crypto policy {current_month_str}",
            "count": 10,
            "days": 1,
            "type": "news",
        },
        # 2. 글로벌 매크로 (7개)
        {
            "category": "Breaking: Global Macro Economy",
            "query": "US economic indicators CPI PPI PMI unemployment rate GDP growth Federal Reserve interest rate policy impact {current_month_str}",
            "count": 7,
            "days": 1,
            "type": "news",
        },
        # 3. 지정학 & 원자재 (5개)
        {
            "category": "Breaking: Geopolitics & Commodities",
            "query": "Global supply chain disruption energy crisis oil gold food security commodities market trending news",
            "count": 5,
            "days": 1,
            "type": "news",
        },
        # ---------------------------------------------------------
        # Track B: Deep Context (통찰력 집중 - days=360)
        # 중요: 'Report', 'Outlook', 'Minutes' 같은 키워드로 깊이 있는 자료 확보
        # ---------------------------------------------------------
        {
            "category": "Context: Fed & Macro Reports",
            "query": "Federal Reserve monetary policy report FOMC minutes economic outlook summary 2025 2026",
            "count": 5,
            "days": 360,  # 연간주요 보고서 참조
            "type": "context",
        },
        {
            "category": "Context: Institutional Crypto Insights",
            "query": "BlackRock Grayscale crypto market quarterly report institutional adoption outlook 2026",
            "count": 5,
            "days": 360,  # 연간 주요 보고서 참조
            "type": "context",
        },
    ]

    full_context = ""
    source_verification_list = []
    article_idx = 1

    current_year = str(today.year)

    for plan in search_plan:
        print(
            f"Step 1-{article_idx//6 + 1}. {plan['category']} 수집 중... (Type: {plan['type']})"
        )

        # 설정된 days 옵션에 따라 검색 수행
        articles = fetch_news_with_options(plan["query"], plan["count"], plan["days"])

        for article in articles:
            content = article.get("raw_content", "")
            pub_date = article.get("published_date", "")
            title = article.get("title", "")

            # [스마트 필터링]
            # News 타입인데 날짜가 없거나 너무 옛날이면 과감히 삭제
            if plan["type"] == "news":
                if (
                    pub_date and str(int(current_year) - 1) in pub_date
                ):  # 작년 뉴스 필터링
                    continue

            # Context 타입은 날짜가 좀 지나도 OK, 단 너무 오래된(2년 전) 건 삭제
            if plan["type"] == "context":
                if pub_date and str(int(current_year) - 2) in pub_date:
                    continue

            if not content:
                continue

            # Context 자료는 본문을 좀 더 길게 가져와서 깊이를 더함
            limit = 8000 if plan["type"] == "context" else 4000
            truncated_content = content[:limit]

            # AI에게 줄 데이터에 [TYPE] 태그를 붙여서 구분시킴
            full_context += f"\n[Article ID: {article_idx} | Type: {plan['type'].upper()} | Category: {plan['category']}]\n"
            full_context += f"Title: {title}\n"
            full_context += f"Date: {pub_date}\n"
            full_context += f"Content: {truncated_content}\n"
            full_context += "-" * 30 + "\n"

            # 출처 리스트 (Context 자료는 별도 표기)
            # Context 자료는 (Report/Context)라고 명시하여 사용자가 구분하게 함
            label = "📄 REPORT" if plan["type"] == "context" else "📰 NEWS"
            style = (
                "color:#005a9c; font-weight:bold;"
                if plan["type"] == "context"
                else "color:#666;"
            )

            source_verification_list.append(
                f"<li style='margin-bottom: 5px;'><b>[{article_idx}]</b> <span style='font-size:0.8em; {style}'>[{label}]</span> <span style='color:#666; font-size:0.9em'>({pub_date})</span> <a href='{article['url']}' target='_blank' style='color:#051c2c; text-decoration:none; border-bottom:1px solid #ccc;'>{title}</a></li>"
            )
            article_idx += 1

    print(f"Step 2. AI 분석 (News + Context 융합) 및 리포트 생성 중...")

    # [디자인 업그레이드: McKinsey Style HTML Template]
    prompt = f"""
    당신은 글로벌 최상위 컨설팅펌(McKinsey & Company)의 '수석 매크로 전략가'입니다.
    아래 제공된 [Source Data]는 **'최신 속보(NEWS)'**와 **'배경 리포트(CONTEXT)'**로 구분되어 있습니다.
    이 두 가지를 유기적으로 결합하여, 단순한 사실 나열이 아닌 **'깊이 있는 통찰'**이 담긴, **모바일에서 완벽하게 보이는 반응형 HTML 리포트**를 작성하십시오.

    [Source Data]
    {full_context}

    [Output Rules]
    1. **Format:** 오직 `<html>`로 시작해서 `</html>`로 끝나는 소스 코드만 출력하십시오. (마크다운 코드블록 ```html 사용 금지)
       - 강조하고 싶은 날짜나 수치에 `**` (별표)를 쓰지 마십시오. (화면에 지저분하게 보입니다)
    2. **Tone:** 권위 있고, 분석적이며, 냉철한 프로페셔널 톤.
    3. **Strict Date Check (중요):** - 최신 속보의 경우, `Date:` 필드를 확인하십시오. 
       - 오늘 날짜({today_str}) 기준, 24시간 이상 과거 뉴스는 절대 인용하지 마십시오.
    4. **Anti-Hallucination:** 모든 문장에 출처 ID 표기 필수.
       - 문장 끝에 출처 ID를 표시할 때, 투박한 `[1]` 대신 반드시 **HTML 윗첨자 태그**를 사용하십시오.
       - 예시: ...상승했습니다.<sup>[1]</sup>
       - **절대로** `[ID 1]` 처럼 길게 쓰지 마십시오. 오직 숫자만 쓰십시오.
    
    [Technical Requirements for Mobile - 중요]
    1. **Meta Tags:** `<head>` 태그 안에 반드시 다음 두 줄을 포함하십시오.
       - `<meta charset="UTF-8">` (한글 깨짐 방지)
       - `<meta name="viewport" content="width=device-width, initial-scale=1.0">` (모바일 화면 맞춤)
    2. **CSS:** 작은 화면에서도 글자가 잘리거나 표가 깨지지 않도록 `max-width: 100%`, `word-wrap: break-word` 등을 활용하십시오.
    
    [Insight Generation Rules]
    1. **Connect the Dots:** [NEWS]의 사건을 [CONTEXT]의 흐름 속에서 해석하십시오.
    2. **Strict Separation:** 과거 자료([CONTEXT]) 인용 시 반드시 "최근 보고서에 따르면..." 등으로 시점을 명시하십시오.

    [Report Structure (Strict Order)]
    1. **Header:** McKinsey Style Title & Date
    2. **Section 1: Market Ticker** (속보 중심)
       - Crypto, Macro, Geo 섹터별로 핵심 뉴스 한 줄 헤드라인 나열(중요도 순 최대 2개)
    3. **Section 2: Deep Dive Analysis** (통찰 중심)
       - **Executive Insight:** (회색 박스) 시장 흐름 5줄 요약.
       - **Theme 1: Macro & Policy (거시 경제 및 동향):** 정책, 경제 지표 분석, 지정학적 이슈.
       - **Theme 2: Crypto Dynamics(암호화폐 시장 동향):** 규제 및 기관 동향.
    4. **Section 3: Conclusion** (결론 및 전망) 낙관적이되, 현실적인 어조로 마무리.
    5. **Language:** 한국어 (전문 용어는 유지하되 자연스럽게)
    
    [HTML & CSS Design System: McKinsey Style]
        <style>
            body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #fff; word-break: keep-all; }}
            h1 {{ font-family: "Georgia", "Times New Roman", serif; font-size: 1.8em; color: #051c2c; border-bottom: 3px solid #051c2c; padding-bottom: 10px; margin-bottom: 20px; letter-spacing: -0.5px; }}
            h2 {{ font-family: "Georgia", serif; font-size: 1.4em; color: #051c2c; margin-top: 40px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            h3 {{ font-size: 1.1em; font-weight: bold; color: #051c2c; margin-top: 25px; }}
            
            /* 모바일 가독성 최적화 */
            p {{ font-size: 16px; text-align: justify; line-height: 1.7; margin-bottom: 10px; }} 
            
            /* Section 1 리스트 (점 없애기) */
            ul.ticker-list {{ 
                list-style: none; /* 점 제거 */
                padding-left: 0;  /* 들여쓰기 제거 */
                margin: 0; 
            }}
            
            /* 첨자(Superscript) 디자인: 작고 깔끔하게 */
            sup {{
                color: #005a9c; 
                font-weight: bold;
                font-size: 0.7em;
                margin-left: 2px;
                vertical-align: super;
            }}
            a {{ text-decoration: none; color: #005a9c; }}

            .exec-box {{ background-color: #f4f6f8; padding: 20px; border-left: 5px solid #051c2c; margin: 20px 0; border-radius: 4px; }}
            .exec-title {{ display: block; font-weight: bold; color: #051c2c; margin-bottom: 8px; text-transform: uppercase; font-size: 0.8em; letter-spacing: 1px; }}
            
            .footer {{ margin-top: 50px; font-size: 0.85em; color: #888; border-top: 1px solid #eee; padding-top: 20px; }}
            .footer ul {{ padding-left: 0; list-style: none; }}
            .footer li {{ margin-bottom: 10px; font-size: 0.9em; }}
         </style>
         
    [Output Format]
    ```html
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Global Market Briefing</title>
        </head>
    <body>
        <h1>Global Market Morning Briefing <br><span style='font-size:0.6em; font-weight:normal; color:#555'>{today_str}</span></h1>
        
        <h2>SECTION 1: Market Ticker (24h)</h2>       
        <h2>SECTION 2: Deep Dive Analysis</h2>
        <div class="exec-box">
            <span class="exec-title">Executive Insight</span>
            </div>
        <h2>SECTION 3: Conclusion</h2>
        </body>
    </html>
    ```
    """

    response = model.generate_content(prompt)

    # HTML 정리 (가끔 마크다운 ```html 태그가 붙어 나올 경우 제거)
    final_html = response.text.replace("```html", "").replace("```", "")

    # 혹시 <!DOCTYPE html>이 빠져있으면 강제 삽입 (모바일 렌더링 위해 필수)
    if "<!DOCTYPE html>" not in final_html:
        final_html = "<!DOCTYPE html>\n" + final_html

    # 출처 리스트 HTML 추가
    source_html = (
        "<div class='footer'><h3>✅ Source Verification</h3>"
        + "".join(source_verification_list)
        + "</div></body></html>"
    )

    # </body> 태그 직전에 출처 삽입
    if "</body>" in final_html:
        final_html = (
            final_html.replace("</body>", "").replace("</html>", "") + source_html
        )
    else:
        final_html += source_html

    return final_html


# ==========================================
# 4. 실행부
# ==========================================
if __name__ == "__main__":
    try:
        final_report_html = get_morning_investment_briefing()

        # 구글 드라이브 경로 (없으면 로컬 저장)
        save_folder = "G:/내 드라이브/News_Briefing"
        if not os.path.exists(save_folder):
            save_folder = os.getcwd()
            print(f"⚠️ 저장 경로를 현재 폴더로 변경: {save_folder}")

        filename = f"{save_folder}/Briefing_{datetime.date.today()}.html"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_report_html)

        print(f"\n✅ [McKinsey Style] 리포트 생성 완료!")
        print(f"📄 파일 열기: {filename}")

    except Exception as e:
        print(f"❌ Error: {e}")
