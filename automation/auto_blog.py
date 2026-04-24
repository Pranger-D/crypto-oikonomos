import os
import sys

# Windows 콘솔 인코딩 문제 방지 (이모지 등 유니코드 출력)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import json
import argparse
import markdown
from PIL import Image
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai

from news_brain import build_brain_data, get_desktop_path

# ==========================================
# 1. 설정 및 경로
# ==========================================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("🚨 API 키 오류: .env 파일에서 GOOGLE_API_KEY를 찾을 수 없습니다.")

gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(PROJECT_ROOT, "data", "blog")
PUBLIC_IMG_DIR = os.path.join(PROJECT_ROOT, "public", "static", "images")
DESKTOP_PATH = get_desktop_path()


# ==========================================
# 2. 바탕화면 이미지 → webp 변환
# ==========================================
def process_manual_images(folder_name: str, target_dir: str, year: str = None) -> list:
    """바탕화면 작업 폴더의 이미지를 webp로 변환하고 파일명 리스트 반환."""
    if not year:
        year = datetime.now().strftime("%Y")
    source_dir = os.path.join(DESKTOP_PATH, "blog", year, folder_name)
    processed = []

    if not os.path.exists(source_dir):
        return processed

    valid_exts = (".png", ".jpg", ".jpeg", ".bmp")
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(valid_exts):
            file_path = os.path.join(source_dir, filename)
            pure_name = os.path.splitext(filename)[0]
            webp_name = f"{pure_name}.webp"
            target_path = os.path.join(target_dir, webp_name)

            try:
                with Image.open(file_path) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    if img.width > 1200:
                        ratio = 1200 / float(img.width)
                        new_height = int(float(img.height) * ratio)
                        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
                    img.save(target_path, "WEBP", quality=85)
                    print(f"   🖼️ [Image] {filename} → {webp_name} 변환 완료")
                    processed.append(webp_name)
            except Exception as e:
                print(f"   ❌ [Image Error] {filename} 처리 실패: {e}")

    return processed


# ==========================================
# 3. 글쓰기 프롬프트 조립
# ==========================================
def _build_writing_prompt(brain_data: dict, image_list: list, today_str: str, category: str = "briefing") -> str:
    """Gemini에게 전달할 최종 글쓰기 프롬프트 조립."""

    # core_insights.md
    core_insights_str = "(핵심 투자 철학 데이터를 찾을 수 없습니다.)"
    insights_path = os.path.join(PROJECT_ROOT, "data", "core_insights.md")
    if os.path.exists(insights_path):
        with open(insights_path, "r", encoding="utf-8") as f:
            core_insights_str = f.read()

    # expert_writing_examples.md
    expert_examples_str = "(글쓰기 예시 데이터를 찾을 수 없습니다.)"
    examples_path = os.path.join(PROJECT_ROOT, "data", "expert_writing_examples.md")
    if os.path.exists(examples_path):
        with open(examples_path, "r", encoding="utf-8") as f:
            expert_examples_str = f.read()

    # 수동 뉴스 (주재료)
    vip_news_str = ""
    for n in brain_data.get("vip_news", []):
        vip_news_str += f"\n[소스: {n['filename']}]\n{n['content']}\n"
    if not vip_news_str.strip():
        vip_news_str = "(없음 — 프롬프트와 키워드 검색 결과로만 작성하세요.)"

    # 키워드 기반 보강 데이터 (보완재)
    keyword_context_str = ""
    for kw, items in brain_data.get("keyword_context", {}).items():
        keyword_context_str += f'\n키워드 "{kw}":\n'
        for item in items:
            title = item.get("title", "")
            content = item.get("content", "")
            url = item.get("url", "")
            keyword_context_str += f"  제목: {title}\n  URL: {url}\n  내용:\n{content}\n\n"
    if not keyword_context_str.strip():
        keyword_context_str = "(없음)"

    # 이미지 지시
    img_instruction = ""
    if image_list:
        img_instruction = (
            "다음은 사용자가 제공한 이미지 파일 리스트입니다: " + ", ".join(image_list)
            + "\n글을 작성하다가 이 이미지가 들어가면 완벽하겠다 싶은 문단 직후에 "
            + "`[IMAGE_파일이름.webp]` 형식으로 정확히 한 번씩만 삽입하세요."
        )

    # 참고 링크
    ref_links = brain_data.get("reference_links", [])
    ref_text = "\n".join(f"- [{l['title']}]({l['url']})" for l in ref_links)

    user_prompt = brain_data.get("user_prompt", "")

    # 카테고리별 구조 선택
    if category == "study":
        structure_guide = """
## Hook
오늘 작성할 글의 핵심 결론이나 반직관적 시각을 먼저 1~2문장으로 던져 독자의 관심을 끄세요.
단, 과장("충격!", "대폭락 임박!")이나 선정적 표현은 금지합니다.
전문가다운 절제된 톤으로, 읽고 싶게 만드세요.

## 오늘의 핵심 요약
3개의 포인트로 요약. 서술형 말고 '단어'로 끝맺음.

## [소제목 1 — 수동 자료의 핵심 논점 중 하나를 제목으로 직접 결정하세요]
수동 자료의 논리 흐름을 따라 깊이 있게 서술하세요.
뉴스 나열 금지. 숨겨진 연결고리와 인사이트를 중심으로 쓰세요.
본문 중간중간 독자에게 질문을 던져 참여감을 유도하세요.
한 문단은 최대 2~3문장. 복문(~하고, ~하지만)을 잘라 짧게 끊으세요.

## [소제목 2 — 두 번째 핵심 논점 (필요한 경우만 작성, 선택)]
[소제목 1과 같은 방식으로 심층 서술]

## [소제목 3 — 세 번째 핵심 논점 (필요한 경우만 작성, 선택, 최대 3개까지)]
[소제목 1과 같은 방식으로 심층 서술]

⚠️ 결론, FAQ, 참고자료 섹션은 절대 작성하지 마세요."""
    else:  # briefing, insight
        structure_guide = """
## Hook
오늘 작성할 글의 핵심 결론이나 반직관적 시각을 먼저 1~2문장으로 던져 독자의 관심을 끄세요.
단, 과장("충격!", "대폭락 임박!")이나 선정적 표현은 금지합니다.
전문가다운 절제된 톤으로, 읽고 싶게 만드세요.

## 오늘의 핵심 요약
3개의 포인트로 요약. 서술형 말고 '단어'로 끝맺음.

## 분석과 통찰
메타 서사를 도출하세요. 뉴스 나열 금지. 숨겨진 연결고리를 찾으세요.
본문 중간중간 독자에게 질문을 던져 참여감을 유도하세요.
한 문단은 최대 2~3문장. 복문(~하고, ~하지만)을 잘라 짧게 끊으세요.

## 결론
통찰의 함의를 정리하되, 구체적인 매수/매도/비중 조언은 절대 하지 마세요.
"지켜보겠습니다" 같은 무의미한 마무리도 피하세요.
"이 흐름이 의미하는 것은 ~입니다" 식으로 독자가 스스로 판단할 수 있는 시각을 제공하세요.

⚠️ FAQ, 참고자료 섹션은 절대 작성하지 마세요."""

    prompt = f"""
당신은 전문 투자 블로거입니다.
오늘 날짜는 {today_str}입니다.
독자와 카페에서 대화하듯 친근하게 쓰되, 전문성은 절대 잃지 마세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[글의 방향성 — 사용자 프롬프트]
{user_prompt}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[투자 철학 렌즈]
아래 렌즈들 중 오늘 뉴스에 가장 정확히 부합하는 1~2개만 선택하여 통찰 하나를 도출하세요.
렌즈를 설명하거나 나열하지 마세요.
{core_insights_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[오늘의 핵심 속보 — 수동 뉴스 (이것이 글의 주재료입니다)]
{vip_news_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[키워드 기반 보강 데이터 — 보완 참고용]
아래는 키워드로 검색한 보조 자료입니다.
수동 뉴스를 뒷받침하거나 맥락을 넓히는 용도로 활용하세요.
이 자료에 수치(금액, 개수, %, 날짜, 법안명, 기관명 등)가 나온다면 본문에 적극 활용하세요.
수동 뉴스와 충돌하면 수동 뉴스를 무조건 우선하세요.
{keyword_context_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[글쓰기 핵심 원칙]

[톤 규칙]
- 부드러운 구어체 존댓말을 자연스럽게 섞으세요.
- 독자에게 직접 질문을 던지는 대화형 장치를 활용하세요 ("한번 생각해보시죠", "여기서 핵심은요").
- "~ㅋㅋ", "~요ㅎㅎ" 같은 지나친 캐주얼은 금지. 전문가의 품격을 유지하세요.
- 이모티콘 금지. 영어 병기 금지 (예: 리밸런싱(Rebalancing) 이런 형식 금지).
- 인사말 금지 ("안녕하세요", "어느덧 ~월이네요" 등).
- "컨텍스트에 따르면", "뉴스에 따르면", "제공된 데이터에 의하면" 등 기계임을 드러내는 서론 금지.

[수치·데이터 활용 규칙]
- 수동 뉴스 또는 보강 데이터에 수치(금액, 개수, %, 날짜, 법안·기관명)가 있다면, 분석을 뒷받침하는 근거로 지연스럽게 본문에 반영하세요.
- ⚠️ 자료에 없는 수치는 절대 만들거나 추측하지 마세요. 수치가 자료에 없으면 사용하지 마세요.
- "상당히", "크게", "많이" 같은 모호한 형용사로 수치를 대신하는 것을 피하세요.
  자료에 구체적인 숫자가 있을 때: "단 4주 만에 22,048 BTC를 추가 매수했다"처럼 직접 인용하세요.
  자료에 수치가 없을 때: 억지로 숫자를 채워넣지 말고, 사실 관계와 맥락으로 서술하세요.
- 수치를 단순 나열하지 말고, 깊이 있는 인사이트를 설명하기 위한 근거로써 사용하세요.

[피상적 서술 금지]
- 추상적인 메타포만으로 문단을 채우는 것을 금지합니다.
  (잘못된 예: "금융의 배관이 바뀌고 있습니다" — 어떤 배관이, 어떤 사실로, 어떻게 바뀌는지 명시하세요.)
- 독자가 "그래서 구체적으로 뭔데?"라고 물을 수 없도록, 주장에는 항상 근거 사실을 붙이세요.

[구조 — 아래 순서를 반드시 따르세요]
{structure_guide}

[이미지 매칭 지시]
{img_instruction if img_instruction else "(이미지 없음)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[글쓰기 서식 예시 (참고용)]
아래는 서식(## 헤딩, 문단 구조, 줄바꿈)의 사용법을 보여주는 참고 예시입니다.
글의 톤·길이·관점은 이 예시에 묶이지 말고 자유롭게 쓰되, 서식 규칙만 따르세요.
{expert_examples_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[출력 형식]
반드시 첫 줄에 `# 제목`을 작성하세요. 제목은 오늘 글의 핵심 인사이트를 담은 한 문장입니다.
위 구조대로 순수 마크다운으로 본문만 작성하세요.
JSON, 지시서, 설명 등 본문 외 텍스트는 절대 포함하지 마세요.
"""
    return prompt


# ==========================================
# 4. Gemini 글쓰기
# ==========================================
def generate_blog_content(brain_data: dict, image_list: list, category: str = "briefing") -> str:
    """Gemini로 블로그 본문 생성."""
    print("✍️ [AI Editor V4] 블로그 본문 작성 중...")
    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    prompt = _build_writing_prompt(brain_data, image_list, today_str, category=category)

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview", contents=prompt
        )
        blog_body = response.text.strip()
        print("   ✅ 본문 생성 완료")
        return blog_body
    except Exception as e:
        print(f"   ❌ 글쓰기 실패: {e}")
        return None


# ==========================================
# 5. 이미지 플레이스홀더 치환
# ==========================================
def replace_image_placeholders(blog_body: str, image_list: list, year: str, folder_name: str) -> str:
    """[IMAGE_xxx.webp] 플레이스홀더를 <img> 태그로 치환."""
    import urllib.parse
    for img_name in image_list:
        encoded = urllib.parse.quote(img_name)
        img_path = f"/static/images/{year}/{folder_name}/{encoded}"
        alt_text = os.path.splitext(img_name)[0]
        img_html = (
            f'\n\n<div style="text-align:center;margin:2rem 0;">\n'
            f'  <img src="{img_path}" alt="{alt_text}" '
            f'style="max-width:100%;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.12);" />\n'
            f'  <p style="font-size:0.85rem;color:#888;margin-top:0.5rem;">{alt_text}</p>\n'
            f'</div>\n\n'
        )
        tag = f"[IMAGE_{img_name}]"
        if tag in blog_body:
            blog_body = blog_body.replace(tag, img_html)
    return blog_body


# ==========================================
# 6. HTML 출력 빌드
# ==========================================
def build_html_output(blog_body: str, title: str, ref_links: list) -> str:
    """마크다운 본문 → 스타일링된 단일 HTML 파일 생성."""

    # 참고 자료 섹션 — 사용자 설정에 의해 비활성화
    # (자동 삽입 제거: briefing/insight/study 모두 본문에 포함하지 않음)

    # 면책조항
    disclaimer = (
        "\n\n---\n"
        "*이 글은 투자 정보 제공을 목적으로 하며, 특정 자산의 매수·매도를 권유하지 않습니다. "
        "투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.*"
    )
    blog_body += disclaimer

    # 마크다운 → HTML
    body_html = markdown.markdown(
        blog_body,
        extensions=["extra", "nl2br"],
    )

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <style>
    /* Reset */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 17px;
      line-height: 1.9;
      color: #1a1a1a;
      background: #fafaf9;
      padding: 0 1rem;
    }}

    .container {{
      max-width: 720px;
      margin: 2.5rem auto 5rem;
      background: #ffffff;
      border-radius: 12px;
      padding: 2.5rem 2.2rem;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 4px 24px rgba(0,0,0,0.04);
    }}

    /* 제목 */
    .post-title {{
      font-size: 1.55rem;
      font-weight: 700;
      line-height: 1.45;
      color: #111;
      margin-bottom: 0.4rem;
    }}
    .post-date {{
      font-size: 0.85rem;
      color: #999;
      margin-bottom: 2rem;
    }}

    hr {{
      border: none;
      border-top: 1px solid #e8e8e8;
      margin: 2rem 0;
    }}

    /* 헤딩 */
    h2 {{
      font-size: 1.2rem;
      font-weight: 700;
      color: #111;
      margin: 2.2rem 0 0.8rem;
      padding-bottom: 0.3rem;
      border-bottom: 2px solid #f0f0f0;
    }}
    h3 {{
      font-size: 1.05rem;
      font-weight: 600;
      color: #333;
      margin: 1.6rem 0 0.5rem;
    }}

    /* 본문 */
    p {{
      margin-bottom: 1.1rem;
      word-break: keep-all;
      overflow-wrap: break-word;
    }}

    /* 인용 */
    blockquote {{
      border-left: 3px solid #d0d0d0;
      padding: 0.5rem 1rem;
      margin: 1.2rem 0;
      color: #555;
      background: #f8f8f8;
      border-radius: 0 6px 6px 0;
    }}

    /* 리스트 */
    ul, ol {{
      padding-left: 1.4rem;
      margin-bottom: 1.1rem;
    }}
    li {{
      margin-bottom: 0.4rem;
    }}

    /* 강조 */
    strong {{ font-weight: 700; }}
    em {{ font-style: italic; color: #444; }}

    /* 코드 */
    code {{
      background: #f3f3f3;
      padding: 0.15em 0.4em;
      border-radius: 4px;
      font-size: 0.88em;
      font-family: 'SF Mono', 'Fira Code', monospace;
    }}

    /* 링크 */
    a {{
      color: #2563eb;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}

    /* 이미지 */
    img {{
      max-width: 100%;
      border-radius: 8px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.12);
    }}

    /* 면책조항 */
    .disclaimer {{
      font-size: 0.8rem;
      color: #aaa;
      margin-top: 2.5rem;
      padding-top: 1rem;
      border-top: 1px solid #f0f0f0;
    }}

    /* 반응형 */
    @media (max-width: 600px) {{
      .container {{ padding: 1.5rem 1rem; }}
      .post-title {{ font-size: 1.3rem; }}
      h2 {{ font-size: 1.1rem; }}
      body {{ font-size: 16px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1 class="post-title">{title}</h1>
    <p class="post-date">{datetime.now().strftime("%Y년 %m월 %d일")}</p>
    <hr />
    <div class="content">
{body_html}
    </div>
  </div>
</body>
</html>"""

    return html


# ==========================================
# 7. 메인 오케스트레이터
# ==========================================
def run_automation():
    print("\n🚀 [V4 Auto Blogger] 파이프라인 시작...\n")

    # CLI 인수 파싱
    parser = argparse.ArgumentParser(description="V4 Semi-Auto Blogger")
    parser.add_argument("category", nargs="?", default="briefing",
                        help="카테고리 (briefing / insight / study)")
    parser.add_argument("prompt", nargs="?", default=None,
                        help="글의 방향성 프롬프트")
    parser.add_argument("--date", default=None,
                        help="과거 날짜 테스트용 (형식: YYYY-MM-DD)")
    parser.add_argument("--lite", action="store_true",
                        help="Tavily Extract API 생략 (크레딧 절약 모드)")
    args = parser.parse_args()

    # 프롬프트 필수 확인
    if not args.prompt:
        print("❌ 글의 방향성 프롬프트를 입력해주세요.")
        print('   예: python auto_blog.py insight "트럼프 관세와 달러 약세의 본질"')
        sys.exit(1)

    # 날짜 설정
    if args.date:
        now = datetime.strptime(args.date, "%Y-%m-%d")
        print(f"🕒 [Time Override] 테스트 모드: {args.date} 기준으로 실행합니다.")
    else:
        now = datetime.now()

    year = now.strftime("%Y")
    month_day = now.strftime("%m-%d")
    today_str = now.strftime("%Y-%m-%d")
    category = args.category
    folder_name = f"{month_day}-{category}"

    # 이미지 저장 경로 생성
    target_img_dir = os.path.join(PUBLIC_IMG_DIR, year, folder_name)
    os.makedirs(target_img_dir, exist_ok=True)

    # 1. 이미지 변환
    print("🖼️ [Step 1] 바탕화면 이미지 변환 중...")
    user_images = process_manual_images(folder_name, target_img_dir, year)

    # 2. 브레인 데이터 수집
    print("\n🧠 [Step 2] 브레인 데이터 수집 중...")
    brain_data = build_brain_data(
        folder_name=folder_name,
        user_prompt=args.prompt,
        year=year,
        lite_mode=args.lite,
    )

    if not brain_data.get("vip_news"):
        print("💡 [알림] 수동 뉴스 없음. 프롬프트 + Tavily 데이터로만 작성합니다.")

    # 3. 글쓰기
    print("\n✍️ [Step 3] Gemini 글쓰기...")
    blog_body = generate_blog_content(brain_data, user_images, category=category)

    if not blog_body:
        print("❌ 글쓰기 실패. 종료합니다.")
        sys.exit(1)

    # 4. 이미지 플레이스홀더 치환
    blog_body = replace_image_placeholders(blog_body, user_images, year, folder_name)

    # 5. 제목 추출 (첫 번째 # 헤딩이 있으면 사용, 없으면 기본값)
    import re
    title_match = re.search(r"^#\s+(.+)$", blog_body, re.MULTILINE)
    if title_match:
        post_title = title_match.group(1).strip()
        # 제목 헤딩을 본문에서 제거 (HTML 제목과 중복 방지)
        blog_body = blog_body[:title_match.start()] + blog_body[title_match.end():]
        blog_body = blog_body.strip()
    else:
        # AI가 # 헤딩을 쓰지 않았을 때, 본문 기반으로 제목 생성
        title_prompt = f"다음 블로그 글의 핵심을 담은 한국어 제목을 한 줄만 작성하세요. 다른 설명은 절대 쓰지 마세요.\n\n{blog_body[:2000]}"
        try:
            title_res = gemini_client.models.generate_content(
                model="gemini-3-flash-preview", contents=title_prompt
            )
            post_title = title_res.text.strip().lstrip("#").strip()
        except Exception:
            post_title = f"시장 브리핑: 오늘의 크립토 인사이트 ({today_str})"


    # 6. HTML 빌드
    print("\n🏗️ [Step 4] HTML 파일 빌드 중...")
    html_content = build_html_output(blog_body, post_title, brain_data.get("reference_links", []))

    # 7. HTML 저장
    os.makedirs(BLOG_DIR, exist_ok=True)
    html_filename = f"{today_str}-{category}.html"
    html_path = os.path.join(BLOG_DIR, html_filename)

    # 기존 파일 버전 처리
    version = 1
    while os.path.exists(html_path):
        version += 1
        html_filename = f"{today_str}-{category}-v{version}.html"
        html_path = os.path.join(BLOG_DIR, html_filename)
    if version > 1:
        print(f"💡 기존 파일 존재 → 버전 저장: -v{version}")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n✅ [완료] HTML 파일 저장:")
    print(f"   📄 {html_path}")

    # 8. Google Drive 백업
    import shutil
    GDRIVE_BACKUP_DIR = r"G:\내 드라이브\News_Briefing"
    try:
        os.makedirs(GDRIVE_BACKUP_DIR, exist_ok=True)
        gdrive_dest = os.path.join(GDRIVE_BACKUP_DIR, html_filename)
        shutil.copy2(html_path, gdrive_dest)
        print(f"   ☁️  Google Drive 백업 완료: {gdrive_dest}")
    except Exception as e:
        print(f"   ⚠️  Google Drive 백업 실패 (건너뜀): {e}")

    # 9. 브라우저 자동 열기
    try:
        os.startfile(html_path)
        print("   🌐 브라우저에서 자동으로 열었습니다.")
    except Exception as e:
        print(f"   ⚠️ 브라우저 자동 열기 실패: {e}")
        print(f"   → 수동으로 여세요: {html_path}")


if __name__ == "__main__":
    run_automation()
