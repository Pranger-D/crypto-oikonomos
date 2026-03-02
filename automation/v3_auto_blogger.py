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
def process_manual_images(folder_name, target_dir):
    """
    바탕화면 작업 폴더에서 이미지를 가져와 webp로 변환하고,
    변환된 이미지 파일명 리스트를 반환합니다.
    """
    now = datetime.now()
    year = now.strftime("%Y")
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

    [작성 원칙 및 톤앤매너 - 매우 중요!]
    1. **해석의 렌즈:** [당신의 머릿속]에 있는 17개의 렌즈를 한 번에 모두 사용하려 하지 마십시오. [오늘 발생한 뉴스]의 핵심 속성에 가장 정확히 부합하는 1~3개의 렌즈만 예리하게 선택하여 깊게 파고드십시오. 단순히 수치를 나열하지 말고, 이것이 크립토 시장에 어떤 영향을 미치는지(함의)를 도출해야 합니다.
    2. **금지어 (절대 사용 금지):** "컨텍스트에 따르면", "뉴스에 따르면", "제공된 데이터에 의하면" 등 당신이 기계임을 암시하는 서론. 이미 당신의 머릿속 지식을 꺼내어 설명하듯 자연스럽게 묘사하세요.
    3. **Tone:** 전문적이지만 가독성 높고 이해하기 편한 친밀한 존댓말로 서술하세요. (예: "~했습니다.", "~보입니다.", "흥미로운 점은 ~다만이라는 것이죠.") 복문을 피하고 한 문단은 최대 3문장 이내로 짧게 끊어 시각적 여백을 확보하세요.
    4. **No Emojis:** 본문 텍스트 내에는 이모티콘(🚀, 💡, 📊 등)은 일절 추가하지 마세요.
    5. **No Greetings (인사말 절대 금지):** 문서를 시작할 때 "안녕하세요", "어느덧 몇 월 며칠이네요" 등 일체의 서론을 절대 작성하지 마세요. 
    6. **Structure (Markdown 구조 엄수):**
       - ### 💡**1. 오늘의 핵심 요약 (3줄)**: 마크다운 문서의 가장 첫 줄은 무조건 `### 오늘의 핵심 요약 (3줄)` 이라는 제목으로 시작해야 합니다.
       - ### 🔍**2. Analysis & Insights**: 최신 뉴스에 대한 이성과 팩트 그리고 시장의 함의를 분석합니다.
       - ### 🎯**3. Conclusion**: 부드럽지만 묵직한 통찰력을 주는 제언.

    [훌륭한 글쓰기 예시 (Few-Shot)]
    아래는 당신이 어떤 톤과 깊이로 글을 써야 하는지 보여주는 완벽한 예시입니다. 이 수준의 통찰력을 동일하게 보여주세요.
    {expert_writing_example}

    [이미지 매칭 지시]
    {img_instruction}

    [동적 차트 (Python Chart) 지시서]
    글의 맨 후반부(결론 직전)에 파이썬이 실시간 데이터를 그려서 삽입할 동적 차트에 대한 지시서를 JSON 형식으로 마지막에 작성해주세요. 
    지원하는 type은 4가지입니다: "asset"(단일자산등락), "compare"(두자산비교), "ma"(비트코인이동평균선), "volatility"(변동성막대차트)

    [🚨 최종 출력 전 필수 확인 (CRITICAL FORMATTING RULES)]
    1. 모든 문단은 절대 3문장을 넘지 마십시오. 가급적 1문장이나 2문장마다 마침표(.)를 찍고 반드시 줄바꿈(엔터)을 두 번 쳐서 시각적으로 완전히 띄우십시오.
    2. 복문(~하고, ~하지만)을 최대한 잘라내어 문장 호흡을 극단적으로 짧게 가져가십시오.
    3. 영어 병기 절대 금지: '진정한 시장 평균(True Market Mean)'처럼 한글 뒤에 괄호를 치고 굳이 영어를 병기하는 방식을 절대 사용하지 마십시오. 자연스러운 우리말로만 깔끔하게 쓰십시오.
    4. 컨텍스트는 글에 직접적으로 작성하지 마십시오. 컨텍스트는 최신 뉴스에 대한 날카로운 통찰력을 위한 장기보존 기억입니다.

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
            model="gemini-2.5-flash",
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
# 4. 종합 오케스트레이션
# ==========================================
def run_v3_automation():
    print("\n🚀 [V3 Semi-Auto Blogger] 수동 재료 + AI 통찰 파이프라인 시작...\n")
    
    now = datetime.now()
    year = now.strftime("%Y")
    month_day = now.strftime("%m-%d")
    today_str = now.strftime("%Y-%m-%d")
    
    category = sys.argv[1] if len(sys.argv) > 1 else "briefing"
    folder_name = f"{month_day}-{category}"
    
    target_img_dir = os.path.join(PUBLIC_IMG_DIR, year, folder_name)
    os.makedirs(target_img_dir, exist_ok=True)
    
    # 1. 수동 이미지 변환 및 가져오기
    user_images = process_manual_images(folder_name, target_img_dir)
    
    # 2. 브레인 가동 (컨텍스트 + 수동 뉴스 텍스트 읽기)
    brain_data = build_brain_data(folder_name)
    
    # 안전장치: 뉴스가 없다 하더라도 일단 진행은 가능 (매크로 브리핑만 작성)
    if not brain_data.get("vip_news"):
        print("💡 [알림] 바탕화면에 수동 텍스트가 없습니다. 기본 매크로 컨텍스트로만 글을 씁니다.")
        
    # 3. 글쓰기 & 차트 주문 (친밀한 톤)
    blog_body, chart_instruction = generate_blog_content(brain_data, user_images)
    
    if not blog_body:
         return
         
    # 4. 차트 생성공장 (V3 Expanded)
    dynamic_chart_path = generate_and_save_chart(chart_instruction, category=category)
    
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
        blog_body += f"\n### 데이터 시각화\n{html_chart}"

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

    with open(mdx_path, "w", encoding="utf-8") as f:
        f.write(mdx_content)

    print(f"\n✅ [Success] V3 반자동 블로그 포스팅 완료!")
    print(f"📄 저장 경로: {mdx_path}")

if __name__ == "__main__":
    run_v3_automation()
