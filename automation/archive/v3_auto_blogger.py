import os
import sys
import json
import shutil
from PIL import Image
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# V3 모듈
from v3_news_brain import build_brain_data, get_desktop_path
from v3_chart_maker import generate_and_save_chart

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
# 2. 바탕화면 이미지 -> 프로젝트 이전 및 변환
# ==========================================
def process_manual_images(folder_name, target_dir, year=None):
    """
    바탕화면 작업 폴더에서 이미지를 가져와 webp로 변환하고,
    변환된 이미지 파일명 리스트를 반환합니다.
    """
    if not year:
        year = datetime.now().strftime("%Y")
    source_dir = os.path.join(DESKTOP_PATH, "blog", year, folder_name)
    
    processed_images = []
    
    if not os.path.exists(source_dir):
        return processed_images
        
    valid_exts = (".png", ".jpg", ".jpeg", ".bmp")
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(valid_exts):
            file_path = os.path.join(source_dir, filename)
            pure_name = os.path.splitext(filename)[0]
            webp_name = f"{pure_name}.webp"
            target_path = os.path.join(target_dir, webp_name)
            
            try:
                with Image.open(file_path) as img:
                    # RGB 변환 (png 알파채널 대비)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                        
                    if img.width > 1200:
                        ratio = 1200 / float(img.width)
                        new_height = int(float(img.height) * ratio)
                        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
                        
                    img.save(target_path, "WEBP", quality=85)
                    print(f"   🖼️ [Image] {filename} -> {webp_name} 최적화 완료")
                    processed_images.append(webp_name)
            except Exception as e:
                print(f"   ❌ [Image Error] {filename} 처리 실패: {e}")
                
    return processed_images

# ==========================================
# 3. 메인 글쓰기 & 차트 오더 (친근한 V3 톤)
# ==========================================
def generate_blog_content(brain_data, image_list):
    print("✍️ [AI Editor V3] 선생님이 주신 재료로 친근한 블로그 전문을 작성 중입니다...")
    
    # 1. 핵심 인사이트 & 글쓰기 예시 로드
    core_insights_str = "핵심 원리 데이터를 찾을 수 없습니다."
    try:
        insights_path = os.path.join(PROJECT_ROOT, "data", "core_insights.md")
        if os.path.exists(insights_path):
            with open(insights_path, "r", encoding="utf-8") as f:
                core_insights_str = f.read()
    except Exception as e:
        print(f"⚠️ Core Insights 로드 실패: {e}")

    expert_writing_example = "글쓰기 예시 데이터를 찾을 수 없습니다."
    try:
        examples_path = os.path.join(PROJECT_ROOT, "data", "expert_writing_examples.md")
        if os.path.exists(examples_path):
            with open(examples_path, "r", encoding="utf-8") as f:
                expert_writing_example = f.read()
    except Exception as e:
        print(f"⚠️ Expert Examples 로드 실패: {e}")

    # 2. 컨텍스트 및 뉴스 데이터 정리
    context_str = json.dumps(brain_data["context"], ensure_ascii=False, indent=2)
    vip_news_str = ""
    for n in brain_data["vip_news"]:
        vip_news_str += f"\n[소스: {n['filename']}]\n{n['content']}\n"
        
    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    
    # 이미지 리스트를 안내문구로 변환
    img_instruction = ""
    if image_list:
        img_instruction = "다음은 사용자가 제공한 이미지 파일 리스트입니다: " + ", ".join(image_list)
        img_instruction += "\n글을 작성하다가 이 이미지가 들어가면 완벽하겠다 싶은 문단 직후에 `[IMAGE_파일이름.webp]` 형식으로 정확히 한 번씩만 삽입하세요."

    prompt = f"""
    당신은 월스트리트 최상위 매크로/크립토 애널리스트이자 블로그의 수석 에디터입니다.
    오늘 날짜는 {today_str} 입니다.
    당신은 뉴스를 앵무새처럼 요약하는 봇이 아닙니다. 현상 이면의 구조적 진실과 유동성 흐름을 꿰뚫어 보는 통찰력 있는 사상가입니다.

    [당신의 머릿속: 핵심 투자 철학 및 시장 작동 원리]
    {core_insights_str}

    [오늘 발생한 최신 데이터 및 뉴스]
    - Macro Context (매크로 지표): {context_str}
    - User Manual News (오늘의 핵심 속보): {vip_news_str}

    [인사이트 도출의 핵심 — 퍼즐 합성 (가장 중요!)]
    당신은 단순히 각 뉴스를 개별적으로 해석하는 앵무새가 아닙니다.
    여러 사건이 입력되면 반드시 다음 프로세스를 거치십시오:
    1. 개별 조각 파악: 오늘 입력된 뉴스/사건들을 각각 파악합니다.
    2. 숨겨진 연결고리 탐색: "이 사건들이 겉으로는 별개처럼 보이지만, 하나의 일관된 전략이나 구조적 흐름의 일부가 아닌가?"를 자문합니다.
    3. 메타 서사 도출: 흩어진 조각들을 관통하는 큰 그림(메타 서사)을 하나의 명확한 문장으로 제시합니다.
    4. 함의 도출: 그 메타 서사가 크립토 시장과 우리의 자산 배분에 어떤 실질적 의미를 갖는지 결론짓습니다.
    금지: 각 뉴스를 1번 뉴스, 2번 뉴스처럼 나열식으로 해석하지 마십시오.
    필수: 조각들을 꿰뚫는 하나의 통찰을 반드시 도출하십시오.

    [작성 원칙 및 톤앤매너 - 매우 중요!]
    1. **해석의 렌즈:** [당신의 머릿속]에 있는 16개의 렌즈 중 오늘 뉴스에 가장 정확히 부합하는 1~2개만 예리하게 선택하여 깊게 파고드십시오. 렌즈를 설명하거나 나열하지 말고, 오직 통찰 하나만 도출하십시오.
    2. **금지어 (절대 사용 금지):** "컨텍스트에 따르면", "뉴스에 따르면", "제공된 데이터에 의하면" 등 당신이 기계임을 암시하는 서론.
    3. **Tone:** 전문적이지만 가독성 높고 이해하기 편한 친밀한 존댓말로 서술하세요. (예: "~했습니다.", "~보입니다.") 복문을 피하고 한 문단은 최대 2~3문장 이내로 짧게 끊어 시각적 여백을 확보하세요.
    4. **No Emojis:** 본문 텍스트 내에는 이모티콘(🚀, 💡, 📊 등)은 일절 추가하지 마세요.
    5. **No Greetings (인사말 절대 금지):** 문서를 시작할 때 "안녕하세요", "어느덧 몇 월 며칠이네요" 등 일체의 서론을 절대 작성하지 마세요.
    6. **분량 억제 (최우선 규칙):** 글 전체가 짧을수록 성공한 글입니다. 길게 쓰려는 유혹을 버리십시오. 핵심 통찰 하나를 짧고 강렬하게 전달하는 것이 목표입니다.
    7. **Structure (Markdown 구조 엄수 — 협상 불가):**
       - `## 💡**1. 오늘의 핵심 요약**`: 반드시 `##`(두 개의 샵)으로 시작. 3개의 포인트로 요약.
       - `## 🔍**2. Analysis & Insights**`: 반드시 `##`으로 시작. 이 섹션의 본문 전체는 `<div className="text-center whitespace-pre-wrap">` 로 시작하고 `</div>`로 닫아야 합니다.
       - `## 🎯**3. Conclusion**`: 반드시 `##`으로 시작. 이 섹션의 본문 전체는 `<div className="text-center whitespace-pre-wrap">` 로 시작하고 `</div>`로 닫아야 합니다.
    8. **`<br/>` 줄바꿈 규칙 (협상 불가):** `<div className="text-center whitespace-pre-wrap">` 내부에서, 같은 생각의 흐름에 속하는 문장들은 문장 끝에 `<br/>`를 붙여 다음 줄로 흐르게 하십시오. 생각이 완전히 전환될 때만 빈 줄로 단락을 분리하십시오. 단락의 마지막 문장에는 `<br/>`를 붙이지 마십시오.

    [훌륭한 글쓰기 예시 (Few-Shot) — 이 형식을 반드시 그대로 따르십시오]
    아래 예시는 당신이 출력해야 할 정확한 서식(## 헤딩, <div> 래퍼, <br/> 줄바꿈)과 톤을 모두 보여줍니다.
    {expert_writing_example}

    [이미지 매칭 지시]
    {img_instruction}

    [동적 차트 (Python Chart) 지시서]
    글의 맨 후반부(결론 직전)에 파이썬이 실시간 데이터를 그려서 삽입할 동적 차트에 대한 지시서를 JSON 형식으로 마지막에 작성해주세요.
    지원하는 type은 4가지입니다: "asset"(단일자산등락), "compare"(두자산비교), "ma"(비트코인이동평균선), "volatility"(변동성막대차트)

    [🚨 최종 출력 전 필수 확인 (CRITICAL FORMATTING RULES)]
    1. 모든 섹션 제목은 반드시 `##`(두 개의 샵)이어야 합니다.
    2. Analysis & Insights 섹션과 Conclusion 섹션의 본문은 반드시 `<div className="text-center whitespace-pre-wrap">` 로 감싸야 합니다.
    3. `<div className="text-center whitespace-pre-wrap">` 내부에서 연속되는 문장 끝에는 `<br/>`를 붙이십시오. 단락 마지막 문장에는 `<br/>` 없음.
    4. 복문(~하고, ~하지만)을 잘라내어 문장 호흡을 극단적으로 짧게 가져가십시오.
    5. 영어 병기 절대 금지: 한글 뒤에 괄호로 영어를 병기하는 방식을 절대 사용하지 마십시오.
    6. 컨텍스트는 글에 직접 작성하지 마십시오. 통찰을 위한 배경 지식으로만 활용하십시오.

    [출력 포맷 엄수]
    (블로그 포스팅 본문 마크다운으로 쭉 작성...)
    
    ---JSON_START---
    {{
      "type": "asset",
      "ticker": "BTC-USD",
      "title": "Bitcoin Recent Movement"
    }}
    ---JSON_END---
    """
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        text = response.text
        
        # Parse output
        if "---JSON_START---" in text and "---JSON_END---" in text:
            parts = text.split("---JSON_START---")
            blog_body = parts[0].strip()
            json_str = parts[1].split("---JSON_END---")[0].strip()
            if json_str.startswith("```json"): json_str = json_str[7:]
            if json_str.endswith("```"): json_str = json_str[:-3]
            try:
                 chart_inst = json.loads(json_str)
            except:
                 chart_inst = {"type": "asset", "ticker": "BTC-USD", "title": "Market View"}
        else:
            blog_body = text
            chart_inst = {"type": "asset", "ticker": "BTC-USD", "title": "Market View"}
            
        return blog_body, chart_inst
    except Exception as e:
        print(f"❌ [AI Editor Error]: {e}")
        return None, None

# ==========================================
# 3.5 자기비평 루프 (Generate → Critique → Refine)
# ==========================================
def refine_with_self_critique(blog_body):
    """초안을 편집장 관점에서 자기비평하고 개선된 최종본을 반환합니다."""
    print("🔍 [Self-Critique] 편집장이 초안을 검토하고 개선합니다...")
    
    critique_prompt = f"""
    당신은 월스트리트 최상위 매크로/크립토 애널리스트 블로그의 수석 편집장입니다.
    아래는 방금 작성된 초안입니다. 다음 5가지 기준으로 검토하고, 부족한 부분을 직접 수정하여 개선된 최종본을 출력하세요.

    [검토 기준]
    1. 메타 서사 존재 여부: 여러 뉴스를 관통하는 큰 그림(숨겨진 연결고리)이 명확히 도출되어 있는가? 단순 뉴스 나열이라면 반드시 메타 서사를 추가하세요.
    2. 인사이트 깊이: 표면적 해석에 그치지 않고, 독자가 "아, 이렇게 연결되는 거구나!"라고 감탄할 만한 통찰이 있는가?
    3. 결론의 구체성: "지켜봐야 합니다" 같은 막연한 결론이 아닌, 자산 배분이나 멘탈 관리에 대한 구체적 행동 지침이 있는가?
    4. 가독성: 문장 호흡이 짧은가? 한 문단이 3문장을 넘지 않는가? 복문이 남아있다면 쪼개세요.
    5. 논리 비약: 전체 흐름에서 갑자기 뛰어넘는 논리가 없는가?

    [🚨 절대 하지 말 것 — 서식 파괴 금지]
    - 검토 결과를 별도로 출력하지 마세요. 개선된 최종 본문만 출력하세요.
    - 초안에 있는 `<div className="text-center whitespace-pre-wrap">` 와 `</div>` 태그를 절대 삭제하거나 변경하지 마세요.
    - 초안에 있는 `<br/>` 태그를 절대 삭제하지 마세요. 문장 끝의 `<br/>` 서식을 반드시 그대로 유지하세요.
    - 이미지 태그(`<div className="my-8 flex justify-center">...</div>`)를 삭제하거나 이동하지 마세요.
    - 영어 병기 금지, 이모티콘 금지 규칙을 그대로 유지하세요.

    [초안]
    {blog_body}

    [출력]
    개선된 최종 본문만 마크다운으로 출력하세요.
    """
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=critique_prompt
        )
        refined = response.text.strip()
        
        if len(refined) > 200:  # 유효한 응답인지 최소 확인
            print("✅ [Self-Critique] 개선 완료!")
            return refined
        else:
            print("⚠️ [Self-Critique] 응답이 너무 짧아 원본 유지")
            return blog_body
    except Exception as e:
        print(f"⚠️ [Self-Critique Error] 자기비평 실패, 원본 유지: {e}")
        return blog_body

# ==========================================
# 4. 종합 오케스트레이션
# ==========================================
def run_v3_automation():
    print("\n🚀 [V3 Semi-Auto Blogger] 수동 재료 + AI 통찰 파이프라인 시작...\n")
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("category", nargs="?", default="briefing")
    parser.add_argument("--date", help="과거 날짜 테스트용 (형식: YYYY-MM-DD)", default=None)
    args = parser.parse_args()

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
    
    target_img_dir = os.path.join(PUBLIC_IMG_DIR, year, folder_name)
    os.makedirs(target_img_dir, exist_ok=True)
    
    # 1. 수동 이미지 변환 및 가져오기 (년도 전달)
    user_images = process_manual_images(folder_name, target_img_dir, year)
    
    # 2. 브레인 가동 (컨텍스트 + 수동 뉴스 텍스트 읽기, 년도 전달)
    brain_data = build_brain_data(folder_name, year)
    
    # 안전장치: 뉴스가 없다 하더라도 일단 진행은 가능 (매크로 브리핑만 작성)
    if not brain_data.get("vip_news"):
        print("💡 [알림] 바탕화면에 수동 텍스트가 없습니다. 기본 매크로 컨텍스트로만 글을 씁니다.")
        
    # 3. 글쓰기 & 차트 주문 (친밀한 톤)
    blog_body, chart_instruction = generate_blog_content(brain_data, user_images)
    
    if not blog_body:
         return

    # 3.5 자기비평 루프 (초안 → 편집장 검토 → 개선본)
    blog_body = refine_with_self_critique(blog_body)
    
    if not blog_body:
         return
         
    # 4. 차트 생성공장 (V3 Expanded, 테스트용 날짜 전달)
    dynamic_chart_path = generate_and_save_chart(chart_instruction, category=category, target_date=args.date)
    
    # 5. 본문내 플레이스홀더 치환 작업
    import urllib.parse
    # (1) 선생님이 올린 이미지들 치환
    for img_name in user_images:
        encoded_img_name = urllib.parse.quote(img_name)
        mdx_path_for_user_img = f"/static/images/{year}/{folder_name}/{encoded_img_name}"
        # 확장자를 제외한 순수 파일명을 추출하여 alt 속성으로 사용
        alt_text = os.path.splitext(img_name)[0]
        html_img = f'\n<div className="flex justify-center my-8">\n  <img src="{mdx_path_for_user_img}" alt="{alt_text}" className="rounded-lg shadow-lg border border-gray-200" />\n</div>\n'
        
        # 프롬프트에서 요청한 [IMAGE_xxx.webp] 태그를 찾아서 치환
        tag = f"[IMAGE_{img_name}]"
        if tag in blog_body:
            blog_body = blog_body.replace(tag, html_img)
            
    # (2) 동적 생성된 파이썬 차트 강제 삽입 (JSON 지시서 반영)
    if dynamic_chart_path:
        html_chart = f'\n<div className="flex justify-center my-8">\n  <img src="{dynamic_chart_path}" alt="{chart_instruction.get("title", "Market Chart")}" className="rounded-lg shadow-lg border border-gray-200" />\n</div>\n'
        # 결론 직전에 넣기 위해 (임의로 맨 뒤에 붙임)
        blog_body += f"\n## 암호화폐 차트\n{html_chart}"

    # 6. Frontmatter 조립 & Disclaimer 추가
    summary_text = f"오늘의 글로벌 암호화폐 인사이트 브리핑입니다."
    
    mdx_content = f"""---
title: '시장 브리핑: 오늘의 크립토 브리핑 ({today_str})'
date: '{today_str}'
tags: ['{category.capitalize()}', 'Bitcoin', 'Fed', 'Macro']
draft: true
summary: '{summary_text}'
---

{blog_body}

---
_Disclaimer: 이 보고서는 제공된 데이터에 기반한 분석이며, 투자 조언을 목적으로 하지 않습니다._
"""

    mdx_content = mdx_content.replace("$", "\\$")
    mdx_filename = f"{today_str}-{category}.mdx" 
    mdx_path = os.path.join(BLOG_DIR, mdx_filename)

    # V3 테스트 환경: 이미 파일이 있다면 파일명에 버전을 붙여 기존 글과 비교 가능하게 함
    version = 1
    while os.path.exists(mdx_path):
        version += 1
        mdx_filename = f"{today_str}-{category}-v{version}.mdx"
        mdx_path = os.path.join(BLOG_DIR, mdx_filename)
        
    if version > 1:
        print(f"💡 기존 글이 존재하므로 테스트 버전으로 저장합니다. (-v{version} appended)")

    with open(mdx_path, "w", encoding="utf-8") as f:
        f.write(mdx_content)

    print(f"\n✅ [Success] V3 반자동 블로그 포스팅 완료!")
    print(f"📄 저장 경로: {mdx_path}")

if __name__ == "__main__":
    run_v3_automation()
